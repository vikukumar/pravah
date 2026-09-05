"""
PRAVAH Calendar Service — API-First Architecture
=================================================

Festival data source priority (highest → lowest):
  1. Calendarific API      — Most accurate, lunisolar computed, 100+ Indian festivals
                             Requires CALENDARIFIC_API_KEY in .env (free: 1000 calls/month)
                             https://calendarific.com/api-documentation
  2. Abstract Holidays API — Free tier, no credit card needed, good national coverage
                             Requires ABSTRACT_HOLIDAYS_API_KEY in .env
                             https://app.abstractapi.com/api/holidays
  3. Nager.Date API        — Completely free, no key needed, national public holidays only
                             https://date.nager.at/api/v3/PublicHolidays/{year}/IN
  4. Static fallback       — Built-in hardcoded table used only if ALL APIs fail

All results are cached in CalendarEvent table per org/year.
Cached data is NOT re-fetched until explicitly invalidated (via admin action).

Google Calendar Integration (personal calendars):
  - Requires GOOGLE_CALENDAR_CLIENT_ID + GOOGLE_CALENDAR_CLIENT_SECRET for OAuth
  - User-specific; tokens stored encrypted in CalendarSource table

Public Indian Google Calendars (read-only, API key only):
  - Hindu Holidays:   en.hinduism#holiday@group.v.calendar.google.com
  - Islamic Holidays: en.islamic#holiday@group.v.calendar.google.com
  - Indian Holidays:  en.indian#holiday@group.v.calendar.google.com
  - Requires GOOGLE_CALENDAR_API_KEY (no OAuth needed for public calendars)
"""
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.calendar import CalendarEvent, CalendarSource, ContentSuggestion

logger = logging.getLogger("pravah.calendar")

# ── Category/Emoji Mapping for API responses ──────────────────────────────────

KEYWORD_CATEGORY_MAP = [
    # (keywords_lower, category, emoji, importance)
    (["republic", "independence", "gandhi", "ambedkar", "constitution"], "national", "🇮🇳", 1),
    (["diwali", "deepavali", "lakshmi puja", "dhanteras", "bhai dooj", "govardhan"], "hindu", "🪔", 1),
    (["holi", "holika"], "hindu", "🎨", 1),
    (["navratri", "navaratri", "durga puja", "vijayadashami", "dussehra", "dusshera"], "hindu", "🏹", 1),
    (["ganesh chaturthi", "ganesh", "vinayaka"], "hindu", "🐘", 1),
    (["janmashtami", "krishna", "gokulashtami"], "hindu", "🪈", 1),
    (["ram navami", "rama navami", "hanuman jayanti", "hanuman"], "hindu", "🙏", 1),
    (["maha shivaratri", "shivaratri", "shiva"], "hindu", "🌙", 1),
    (["makar sankranti", "pongal", "lohri", "bihu", "makara"], "hindu", "🪁", 1),
    (["baisakhi", "vaisakhi", "guru nanak", "khalsa"], "sikh", "🌾", 1),
    (["onam", "vishu", "ugadi", "gudi padwa", "ugadi", "yugadi"], "hindu", "🌺", 1),
    (["chhath puja", "chhath"], "hindu", "🌅", 1),
    (["raksha bandhan", "rakhi"], "hindu", "🪢", 1),
    (["karva chauth", "karwa"], "hindu", "🌕", 2),
    (["eid ul-fitr", "eid al-fitr", "eid-ul-fitr", "eid ul fitr", "ramzan eid", "bakrid"], "muslim", "🌙", 1),
    (["eid ul-adha", "eid al-adha", "bakra eid", "eid-ul-adha", "eid ul adha"], "muslim", "🐑", 1),
    (["muharram", "ashura", "milad"], "muslim", "☪️", 2),
    (["christmas", "xmas"], "christian", "🎄", 1),
    (["easter", "good friday", "ash wednesday"], "christian", "✝️", 1),
    (["buddha purnima", "vesak", "buddha jayanti"], "buddhist", "☸️", 1),
    (["mahavir jayanti", "mahavir"], "jain", "🙏", 2),
    (["labour day", "labor day", "may day", "workers"], "secular", "⚒️", 2),
    (["new year"], "secular", "🥳", 2),
    (["women's day", "womens day"], "secular", "♀️", 2),
    (["yoga day", "environment day", "earth day"], "secular", "🌍", 2),
    (["children's day", "childrens day"], "national", "🧒", 2),
]

CALENDARIFIC_TYPE_TO_CATEGORY = {
    "National holiday": "national",
    "Local holiday": "national",
    "Government holiday": "national",
    "Religious": "hindu",  # refined by keyword map below
    "Observance": "secular",
    "Season": "secular",
    "Clock change/Daylight Saving Time": "secular",
}

CATEGORY_COLORS = {
    "hindu":    "#FF6B35",
    "muslim":   "#2ECC71",
    "christian":"#3498DB",
    "sikh":     "#F39C12",
    "buddhist": "#9B59B6",
    "jain":     "#E74C3C",
    "national": "#2C3E50",
    "secular":  "#1ABC9C",
    "custom":   "#6366F1",
    "google":   "#4285F4",
}

CONTENT_SUGGESTION_TEMPLATES = {
    "festival": [
        "Share how your team/brand celebrates {name}! Show the human side of your business. {emoji}",
        "Wish your community a happy {name}! Post warm greetings with the significance of this occasion. {emoji}",
        "Behind-the-scenes of {name} preparations at your office/store. Authenticity wins! 📸",
        "A special {name} offer for your community. Limited time = urgency! 🛒",
        "Share a fact or story about the history of {name}. Educational content performs well! 📚",
    ],
    "national_holiday": [
        "Honor the significance of {name} with a patriotic message reflecting your brand's values. 🇮🇳",
        "Recognize your team and customers on {name}. Employee spotlights and appreciation posts work great.",
        "Share a historical fact or inspiring quote for {name}. Education + patriotism = high engagement. 📖",
    ],
}


def _classify_event(name: str, calendarific_type: str = "") -> Tuple[str, str, int]:
    """
    Returns (category, emoji, importance) from event name keywords.
    Used to enrich API responses with proper categorization.
    """
    name_lower = name.lower()
    for keywords, category, emoji, importance in KEYWORD_CATEGORY_MAP:
        if any(kw in name_lower for kw in keywords):
            return category, emoji, importance

    # Fallback from Calendarific type field
    category = CALENDARIFIC_TYPE_TO_CATEGORY.get(calendarific_type, "secular")
    return category, "📅", 2


# ──────────────────────────────────────────────────────────────────────────────
# API Fetchers
# ──────────────────────────────────────────────────────────────────────────────

async def _fetch_calendarific(year: int) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch Indian holidays from Calendarific API.
    Returns normalized list of event dicts or None if not configured / failed.
    Docs: https://calendarific.com/api-documentation
    """
    api_key = getattr(settings, "CALENDARIFIC_API_KEY", None)
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://calendarific.com/api/v2/holidays",
                params={
                    "api_key": api_key,
                    "country": "IN",
                    "year": year,
                    "type": "national,religious,local",
                    "language": "en",
                },
            )
            if resp.status_code == 401:
                logger.error("Calendarific: Invalid API key")
                return None
            if resp.status_code != 200:
                logger.warning(f"Calendarific returned {resp.status_code}")
                return None

            data = resp.json()
            holidays = data.get("response", {}).get("holidays", [])
            if not holidays:
                return []

            results = []
            for h in holidays:
                date_info = h.get("date", {}).get("datetime", {})
                m = date_info.get("month")
                d = date_info.get("day")
                if not m or not d:
                    continue

                name = h.get("name", "Holiday")
                h_type = h.get("type", [""])[0] if h.get("type") else ""
                description = h.get("description") or f"{name} — celebrated across India."
                category, emoji, importance = _classify_event(name, h_type)

                results.append({
                    "title": name,
                    "description": description[:500],
                    "month": int(m),
                    "day": int(d),
                    "category": category,
                    "emoji": emoji,
                    "importance": importance,
                    "event_type": "national_holiday" if category == "national" else "festival",
                    "source_api": "calendarific",
                })

            logger.info(f"Calendarific: fetched {len(results)} holidays for India {year}")
            return results

    except Exception as e:
        logger.error(f"Calendarific fetch error: {e}")
        return None


async def _fetch_abstract_holidays(year: int) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch Indian public holidays from Abstract API (free, no credit card needed).
    Docs: https://www.abstractapi.com/api/holidays
    """
    api_key = getattr(settings, "ABSTRACT_HOLIDAYS_API_KEY", None)
    if not api_key:
        return None

    try:
        results = []
        # Abstract API requires month-level requests; we fetch all 12
        async with httpx.AsyncClient(timeout=20.0) as client:
            for month in range(1, 13):
                resp = await client.get(
                    "https://holidays.abstractapi.com/v1/",
                    params={
                        "api_key": api_key,
                        "country": "IN",
                        "year": year,
                        "month": month,
                    },
                )
                if resp.status_code == 401:
                    logger.error("Abstract Holidays: Invalid API key")
                    return None
                if resp.status_code != 200:
                    continue

                for h in resp.json():
                    name = h.get("name", "Holiday")
                    date_str = h.get("date", "")
                    if not date_str:
                        continue
                    try:
                        dt = datetime.strptime(date_str, "%m/%d/%Y")
                    except ValueError:
                        try:
                            dt = datetime.strptime(date_str, "%Y-%m-%d")
                        except ValueError:
                            continue

                    h_type = h.get("type", "")
                    category, emoji, importance = _classify_event(name, h_type)
                    results.append({
                        "title": name,
                        "description": h.get("description") or f"{name} — public holiday in India.",
                        "month": dt.month,
                        "day": dt.day,
                        "category": category,
                        "emoji": emoji,
                        "importance": importance,
                        "event_type": "national_holiday" if category == "national" else "festival",
                        "source_api": "abstract",
                    })

        logger.info(f"Abstract Holidays: fetched {len(results)} holidays for India {year}")
        return results

    except Exception as e:
        logger.error(f"Abstract Holidays fetch error: {e}")
        return None


async def _fetch_nager_date(year: int) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch Indian public holidays from Nager.Date (completely free, no API key).
    Only national/public holidays — no religious festivals.
    Docs: https://date.nager.at
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://date.nager.at/api/v3/PublicHolidays/{year}/IN"
            )
            if resp.status_code != 200:
                return None

            results = []
            for h in resp.json():
                date_str = h.get("date", "")
                if not date_str:
                    continue
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    continue

                name = h.get("localName") or h.get("name", "Holiday")
                category, emoji, importance = _classify_event(name, "National holiday")
                results.append({
                    "title": name,
                    "description": h.get("name") or f"{name} — public holiday in India.",
                    "month": dt.month,
                    "day": dt.day,
                    "category": category,
                    "emoji": emoji,
                    "importance": importance,
                    "event_type": "national_holiday",
                    "source_api": "nager",
                })

            logger.info(f"Nager.Date: fetched {len(results)} public holidays for India {year}")
            return results

    except Exception as e:
        logger.error(f"Nager.Date fetch error: {e}")
        return None


def _get_static_fallback(year: int) -> List[Dict[str, Any]]:
    """
    Hardcoded static festival data used ONLY when all live APIs fail.
    Covers the most important Indian festivals with pre-computed lunisolar dates.
    """
    # Fixed Gregorian festivals (always the same date)
    FIXED = [
        (1, 26, "Republic Day", "🇮🇳", "national", "national_holiday", 1,
         "India's Republic Day — marking the Constitution's adoption on 26 Jan 1950."),
        (1, 14, "Makar Sankranti / Pongal", "🪁", "hindu", "festival", 1,
         "Harvest festival marking the sun's northward journey."),
        (1, 13, "Lohri", "🔥", "sikh", "festival", 2,
         "Punjabi winter harvest festival celebrated with bonfires."),
        (3, 8,  "International Women's Day", "♀️", "secular", "festival", 2,
         "Celebrate women's achievements and advocate for gender equality."),
        (4, 13, "Baisakhi / Vaisakhi", "🌾", "sikh", "festival", 1,
         "Punjabi harvest festival and Sikh New Year."),
        (4, 14, "Ambedkar Jayanti", "📖", "national", "national_holiday", 2,
         "Birth anniversary of Dr. B.R. Ambedkar, architect of the Indian Constitution."),
        (5, 1,  "Labour Day / May Day", "⚒️", "national", "national_holiday", 2,
         "International Workers' Day."),
        (6, 21, "International Yoga Day", "🧘", "national", "festival", 2,
         "Global celebration of yoga initiated by India at the United Nations."),
        (8, 15, "Independence Day", "🇮🇳", "national", "national_holiday", 1,
         "India's Independence Day — freedom from British rule on 15 Aug 1947."),
        (10, 2, "Gandhi Jayanti", "🕊️", "national", "national_holiday", 1,
         "Birth anniversary of Mahatma Gandhi, Father of the Nation."),
        (11, 14, "Children's Day", "🧒", "national", "festival", 2,
         "Celebrated on Nehru's birthday to honor children across India."),
        (12, 25, "Christmas", "🎄", "christian", "festival", 1,
         "Celebrates the birth of Jesus Christ."),
        (12, 31, "New Year's Eve", "🎆", "secular", "festival", 2, "Countdown celebrations."),
        (1, 1,  "New Year's Day", "🥳", "secular", "festival", 2, "Welcome the new year."),
        (2, 14, "Valentine's Day", "❤️", "secular", "festival", 2,
         "Day celebrating love and romance."),
    ]

    # Lunisolar festivals — pre-computed for 2024–2030
    LUNISOLAR: Dict[int, List[Tuple]] = {
        2024: [
            (3, 10, "Maha Shivaratri", "🌙", "hindu", "festival", 1, "Night of worship of Lord Shiva."),
            (3, 25, "Holi", "🎨", "hindu", "festival", 1, "Festival of colors."),
            (4, 9,  "Ram Navami", "🙏", "hindu", "festival", 1, "Celebrates the birth of Lord Rama."),
            (4, 10, "Eid ul-Fitr", "🌙", "muslim", "festival", 1, "End of Ramadan."),
            (4, 23, "Hanuman Jayanti", "🐒", "hindu", "festival", 2, "Birth of Lord Hanuman."),
            (6, 17, "Eid ul-Adha", "🐑", "muslim", "festival", 1, "Festival of sacrifice."),
            (7, 17, "Muharram", "☪️", "muslim", "festival", 2, "Islamic New Year."),
            (8, 19, "Janmashtami", "🪈", "hindu", "festival", 1, "Birth of Lord Krishna."),
            (8, 19, "Raksha Bandhan", "🪢", "hindu", "festival", 1, "Brother-sister bond festival."),
            (8, 26, "Onam", "🌺", "hindu", "festival", 1, "Kerala's harvest festival."),
            (9, 7,  "Ganesh Chaturthi", "🐘", "hindu", "festival", 1, "Lord Ganesha's birthday."),
            (10, 2, "Navratri Begins", "🪔", "hindu", "festival", 1, "Nine nights of Goddess Durga."),
            (10, 12, "Dussehra / Vijayadashami", "🏹", "hindu", "festival", 1, "Victory of Rama over Ravana."),
            (10, 17, "Karva Chauth", "🌕", "hindu", "festival", 2, "Women's fast for husbands."),
            (10, 29, "Dhanteras", "🪙", "hindu", "festival", 1, "Auspicious day for buying gold."),
            (11, 1, "Diwali / Deepavali", "🪔", "hindu", "festival", 1, "Festival of lights."),
            (11, 3, "Bhai Dooj", "👫", "hindu", "festival", 2, "Brother-sister celebration."),
            (11, 15, "Chhath Puja", "🌅", "hindu", "festival", 1, "Worship of the Sun God."),
            (11, 15, "Guru Nanak Jayanti", "🙏", "sikh", "festival", 1, "Birth of Guru Nanak Dev Ji."),
        ],
        2025: [
            (2, 26, "Maha Shivaratri", "🌙", "hindu", "festival", 1, "Night of worship of Lord Shiva."),
            (3, 14, "Holi", "🎨", "hindu", "festival", 1, "Festival of colors."),
            (3, 30, "Eid ul-Fitr", "🌙", "muslim", "festival", 1, "End of Ramadan."),
            (4, 6,  "Ram Navami", "🙏", "hindu", "festival", 1, "Celebrates the birth of Lord Rama."),
            (4, 10, "Hanuman Jayanti", "🐒", "hindu", "festival", 2, "Birth of Lord Hanuman."),
            (6, 7,  "Eid ul-Adha", "🐑", "muslim", "festival", 1, "Festival of sacrifice."),
            (8, 16, "Janmashtami", "🪈", "hindu", "festival", 1, "Birth of Lord Krishna."),
            (8, 27, "Raksha Bandhan", "🪢", "hindu", "festival", 1, "Brother-sister bond festival."),
            (8, 28, "Ganesh Chaturthi", "🐘", "hindu", "festival", 1, "Lord Ganesha's birthday."),
            (8, 27, "Onam", "🌺", "hindu", "festival", 1, "Kerala's harvest festival."),
            (10, 2, "Navratri Begins", "🪔", "hindu", "festival", 1, "Nine nights of Goddess Durga."),
            (10, 2, "Dussehra", "🏹", "hindu", "festival", 1, "Victory of good over evil."),
            (10, 20, "Dhanteras", "🪙", "hindu", "festival", 1, "Auspicious day for buying gold."),
            (10, 20, "Diwali / Deepavali", "🪔", "hindu", "festival", 1, "Festival of lights."),
            (10, 22, "Bhai Dooj", "👫", "hindu", "festival", 2, "Brother-sister celebration."),
            (11, 5, "Chhath Puja", "🌅", "hindu", "festival", 1, "Worship of the Sun God."),
            (11, 5, "Guru Nanak Jayanti", "🙏", "sikh", "festival", 1, "Birth of Guru Nanak Dev Ji."),
        ],
        2026: [
            (3, 3,  "Maha Shivaratri", "🌙", "hindu", "festival", 1, "Night of worship of Lord Shiva."),
            (3, 4,  "Holi", "🎨", "hindu", "festival", 1, "Festival of colors."),
            (3, 19, "Eid ul-Fitr", "🌙", "muslim", "festival", 1, "End of Ramadan."),
            (3, 27, "Ram Navami", "🙏", "hindu", "festival", 1, "Celebrates the birth of Lord Rama."),
            (4, 16, "Hanuman Jayanti", "🐒", "hindu", "festival", 2, "Birth of Lord Hanuman."),
            (5, 27, "Eid ul-Adha", "🐑", "muslim", "festival", 1, "Festival of sacrifice."),
            (8, 5,  "Janmashtami", "🪈", "hindu", "festival", 1, "Birth of Lord Krishna."),
            (9, 3,  "Raksha Bandhan", "🪢", "hindu", "festival", 1, "Brother-sister bond festival."),
            (9, 15, "Onam", "🌺", "hindu", "festival", 1, "Kerala's harvest festival."),
            (9, 18, "Ganesh Chaturthi", "🐘", "hindu", "festival", 1, "Lord Ganesha's birthday."),
            (10, 13, "Navratri Begins", "🪔", "hindu", "festival", 1, "Nine nights of Goddess Durga."),
            (10, 22, "Dussehra", "🏹", "hindu", "festival", 1, "Victory of good over evil."),
            (10, 22, "Karva Chauth", "🌕", "hindu", "festival", 2, "Women's fast for husbands."),
            (11, 9, "Dhanteras", "🪙", "hindu", "festival", 1, "Auspicious day for buying gold."),
            (11, 11, "Diwali / Deepavali", "🪔", "hindu", "festival", 1, "Festival of lights."),
            (11, 13, "Bhai Dooj", "👫", "hindu", "festival", 2, "Brother-sister celebration."),
        ],
        2027: [
            (2, 20, "Maha Shivaratri", "🌙", "hindu", "festival", 1, "Night of worship of Lord Shiva."),
            (3, 8,  "Eid ul-Fitr", "🌙", "muslim", "festival", 1, "End of Ramadan."),
            (3, 22, "Holi", "🎨", "hindu", "festival", 1, "Festival of colors."),
            (3, 27, "Ram Navami", "🙏", "hindu", "festival", 1, "Birth of Lord Rama."),
            (5, 16, "Eid ul-Adha", "🐑", "muslim", "festival", 1, "Festival of sacrifice."),
            (8, 25, "Janmashtami", "🪈", "hindu", "festival", 1, "Birth of Lord Krishna."),
            (9, 7,  "Ganesh Chaturthi", "🐘", "hindu", "festival", 1, "Lord Ganesha's birthday."),
            (9, 23, "Raksha Bandhan", "🪢", "hindu", "festival", 1, "Brother-sister bond festival."),
            (10, 4, "Navratri Begins", "🪔", "hindu", "festival", 1, "Nine nights of Goddess Durga."),
            (10, 13, "Dussehra", "🏹", "hindu", "festival", 1, "Victory of good over evil."),
            (10, 29, "Diwali / Deepavali", "🪔", "hindu", "festival", 1, "Festival of lights."),
            (10, 27, "Dhanteras", "🪙", "hindu", "festival", 1, "Auspicious day for buying gold."),
        ],
    }

    events = []
    for (month, day, name, emoji, category, event_type, importance, description) in FIXED:
        try:
            datetime(year, month, day)
            events.append({
                "title": name, "description": description, "month": month, "day": day,
                "category": category, "emoji": emoji, "importance": importance,
                "event_type": event_type, "source_api": "static_fallback",
            })
        except ValueError:
            continue

    for (month, day, name, emoji, category, event_type, importance, description) in LUNISOLAR.get(
        year, LUNISOLAR.get(2026, [])
    ):
        try:
            datetime(year, month, day)
            events.append({
                "title": name, "description": description, "month": month, "day": day,
                "category": category, "emoji": emoji, "importance": importance,
                "event_type": event_type, "source_api": "static_fallback",
            })
        except ValueError:
            continue

    return events


# ──────────────────────────────────────────────────────────────────────────────
# Main Calendar Service
# ──────────────────────────────────────────────────────────────────────────────

class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Source Management ─────────────────────────────────────────────────────

    async def get_or_create_builtin_source(self, org_id: str) -> CalendarSource:
        q = select(CalendarSource).where(
            CalendarSource.organisation_id == org_id,
            CalendarSource.source_type == "indian_festivals",
        )
        result = await self.db.execute(q)
        source = result.scalar_one_or_none()
        if not source:
            source = CalendarSource(
                organisation_id=org_id,
                source_type="indian_festivals",
                name="Indian Festivals & Holidays",
                description="Live data from Calendarific / Abstract / Nager APIs + static fallback",
                is_active=True,
                color="#FF6B35",
            )
            self.db.add(source)
            await self.db.flush()
        return source

    # ── Festival Seeding (API-first) ──────────────────────────────────────────

    async def seed_festivals_for_year(self, org_id: str, year: int, force: bool = False) -> int:
        """
        Fetch festivals from live APIs and cache in DB.
        On subsequent calls, skips re-fetch unless force=True.

        Source chain: Calendarific → Abstract Holidays → Nager.Date → Static fallback

        Returns: number of events created (0 if already cached and force=False)
        """
        source = await self.get_or_create_builtin_source(org_id)

        # Check if already cached
        if not force:
            existing_q = select(CalendarEvent).where(
                CalendarEvent.organisation_id == org_id,
                CalendarEvent.source_id == source.id,
                CalendarEvent.recurring_year == year,
            ).limit(1)
            existing_r = await self.db.execute(existing_q)
            if existing_r.scalar_one_or_none():
                return 0

        # If force=True, delete existing events for this year
        if force:
            await self.db.execute(
                delete(CalendarEvent).where(
                    CalendarEvent.organisation_id == org_id,
                    CalendarEvent.source_id == source.id,
                    CalendarEvent.recurring_year == year,
                )
            )

        # Try APIs in priority order
        api_events: Optional[List[Dict]] = None
        source_used = "unknown"

        # 1. Calendarific (best — lunisolar + religious festivals)
        api_events = await _fetch_calendarific(year)
        if api_events is not None:
            source_used = "calendarific"
        
        # 2. Abstract Holidays (free, good coverage)
        if api_events is None:
            api_events = await _fetch_abstract_holidays(year)
            if api_events is not None:
                source_used = "abstract_holidays"

        # 3. Nager.Date (free, no key, national holidays only)
        if api_events is None:
            api_events = await _fetch_nager_date(year)
            if api_events is not None:
                source_used = "nager_date"

        # 4. Static fallback
        if api_events is None:
            logger.warning(
                f"All calendar APIs failed for {year}. Using static fallback. "
                "Configure CALENDARIFIC_API_KEY in .env for accurate festival dates."
            )
            api_events = _get_static_fallback(year)
            source_used = "static_fallback"

        # Update source description with actual source used
        source.description = (
            f"Festival data for {year} sourced from: {source_used}. "
            "Configure CALENDARIFIC_API_KEY for most accurate results."
        )

        # Write events to DB
        now = datetime.now(timezone.utc)
        seen_titles = set()
        created = 0

        for ev in api_events:
            # Deduplicate by title (some APIs return duplicates)
            key = (ev["title"].lower().strip(), ev["month"], ev["day"])
            if key in seen_titles:
                continue
            seen_titles.add(key)

            try:
                event_date = datetime(year, ev["month"], ev["day"], 0, 0, 0, tzinfo=timezone.utc)
            except (ValueError, KeyError):
                continue

            category = ev.get("category", "secular")
            event = CalendarEvent(
                organisation_id=org_id,
                source_id=source.id,
                title=ev["title"],
                description=ev.get("description", ""),
                event_type=ev.get("event_type", "festival"),
                category=category,
                event_date=event_date,
                is_all_day=True,
                recurring_year=year,
                emoji=ev.get("emoji", "📅"),
                color=CATEGORY_COLORS.get(category, "#888888"),
                importance=ev.get("importance", 2),
            )
            self.db.add(event)
            created += 1

        await self.db.commit()
        logger.info(
            f"Calendar seeded: {created} events for org={org_id} year={year} "
            f"source={source_used}"
        )
        return created

    async def invalidate_cache(self, org_id: str, year: int) -> int:
        """
        Delete cached events for a year and re-fetch from APIs.
        Used by admin to force a refresh.
        """
        return await self.seed_festivals_for_year(org_id, year, force=True)

    # ── Event Queries ─────────────────────────────────────────────────────────

    async def get_events_for_month(self, org_id: str, year: int, month: int) -> List[CalendarEvent]:
        """Get all calendar events for a month. Auto-seeds if not yet cached."""
        await self.seed_festivals_for_year(org_id, year)

        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) if month == 12 else datetime(year, month + 1, 1, tzinfo=timezone.utc)

        query = (
            select(CalendarEvent)
            .where(
                CalendarEvent.organisation_id == org_id,
                CalendarEvent.event_date >= start,
                CalendarEvent.event_date < end,
            )
            .order_by(CalendarEvent.event_date, CalendarEvent.importance)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_events_for_date(self, org_id: str, event_date: date) -> List[CalendarEvent]:
        """Get events for a specific date."""
        await self.seed_festivals_for_year(org_id, event_date.year)
        start = datetime(event_date.year, event_date.month, event_date.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        query = (
            select(CalendarEvent)
            .where(
                CalendarEvent.organisation_id == org_id,
                CalendarEvent.event_date >= start,
                CalendarEvent.event_date < end,
            )
            .order_by(CalendarEvent.importance)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_custom_event(
        self,
        org_id: str,
        title: str,
        event_date: datetime,
        description: Optional[str] = None,
        emoji: Optional[str] = None,
        color: Optional[str] = None,
        category: str = "custom",
        event_end_date: Optional[datetime] = None,
    ) -> CalendarEvent:
        event = CalendarEvent(
            organisation_id=org_id,
            title=title,
            description=description,
            event_type="custom",
            category=category,
            event_date=event_date,
            event_end_date=event_end_date,
            is_all_day=True,
            recurring_year=event_date.year,
            emoji=emoji or "📌",
            color=color or "#6366F1",
            importance=2,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    # ── Content Suggestions ───────────────────────────────────────────────────

    async def get_suggestions_for_date(
        self, org_id: str, suggestion_date: date
    ) -> List[Dict[str, Any]]:
        """
        Returns AI content suggestions for a specific date's events.
        Template-based suggestions with image prompts and hashtags.
        """
        events = await self.get_events_for_date(org_id, suggestion_date)
        if not events:
            return []

        suggestions = []
        for event in events[:3]:
            templates = CONTENT_SUGGESTION_TEMPLATES.get(
                event.event_type, CONTENT_SUGGESTION_TEMPLATES["festival"]
            )
            for template in templates[:3]:
                topic = template.format(name=event.title, emoji=event.emoji or "🎉")
                suggestions.append({
                    "event_id": event.id,
                    "event_title": event.title,
                    "event_emoji": event.emoji,
                    "event_category": event.category,
                    "event_color": event.color,
                    "topic": topic,
                    "platform": None,
                    "image_prompt": (
                        f"A beautiful, vibrant social media image celebrating {event.title}. "
                        f"Include relevant cultural imagery, warm colors, and festive atmosphere. "
                        f"Professional, brand-friendly design. No text overlay."
                    ),
                    "hashtags": self._festival_hashtags(event.title, event.category or ""),
                })

        return suggestions

    def _festival_hashtags(self, name: str, category: str) -> List[str]:
        base = [
            name.replace(" ", ""),
            name.replace(" ", "").lower(),
            "India",
            "celebration",
        ]
        category_tags = {
            "hindu":    ["HinduFestival", "DesiCelebration", "IndianFestival"],
            "muslim":   ["Eid", "IslamicFestival", "IndianMuslim"],
            "christian":["Christmas", "ChristianCelebration"],
            "sikh":     ["SikhFestival", "Waheguru", "Punjab"],
            "buddhist": ["Buddha", "BuddhistFestival"],
            "national": ["ProudIndian", "BharatMataKiJai", "JaiHind"],
            "secular":  ["WorldDay", "GlobalCelebration"],
        }
        return base + category_tags.get(category, [])

    # ── API Health / Status ───────────────────────────────────────────────────

    async def get_api_status(self) -> Dict[str, Any]:
        """Returns which calendar APIs are configured."""
        return {
            "calendarific": {
                "configured": bool(getattr(settings, "CALENDARIFIC_API_KEY", None)),
                "description": "Most accurate — covers all Indian religious + national holidays",
                "signup_url": "https://calendarific.com/",
                "env_var": "CALENDARIFIC_API_KEY",
                "free_tier": "1000 calls/month",
            },
            "abstract_holidays": {
                "configured": bool(getattr(settings, "ABSTRACT_HOLIDAYS_API_KEY", None)),
                "description": "Free tier, good national holiday coverage",
                "signup_url": "https://app.abstractapi.com/api/holidays",
                "env_var": "ABSTRACT_HOLIDAYS_API_KEY",
                "free_tier": "1000 calls/month",
            },
            "nager_date": {
                "configured": True,  # Always available — no key needed
                "description": "Free, no API key required — national holidays only",
                "signup_url": "https://date.nager.at",
                "env_var": None,
                "free_tier": "Unlimited",
            },
            "google_calendar_public": {
                "configured": bool(getattr(settings, "GOOGLE_CALENDAR_API_KEY", None)),
                "description": "Public Indian/Hindu/Islamic holiday Google Calendars",
                "signup_url": "https://console.cloud.google.com",
                "env_var": "GOOGLE_CALENDAR_API_KEY",
                "free_tier": "Generous free quota",
            },
        }

    # ── Google Calendar Integration (OAuth — personal calendars) ─────────────

    async def get_google_oauth_url(self, org_id: str, redirect_uri: str) -> str:
        """Generate Google Calendar OAuth URL for personal calendar connection."""
        import secrets
        import urllib.parse

        client_id = getattr(settings, "GOOGLE_CALENDAR_CLIENT_ID", None)
        if not client_id:
            raise ValueError(
                "Google Calendar integration is not configured. "
                "Set GOOGLE_CALENDAR_CLIENT_ID in .env"
            )

        state = secrets.token_urlsafe(16)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/calendar.readonly",
            "access_type": "offline",
            "prompt": "consent",
            "state": f"google_calendar:{org_id}:{state}",
        }
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

    async def exchange_google_code(
        self, org_id: str, code: str, redirect_uri: str
    ) -> CalendarSource:
        """Exchange OAuth code and store Google Calendar connection."""
        from app.core.encryption import encrypt_secret

        client_id = getattr(settings, "GOOGLE_CALENDAR_CLIENT_ID", None)
        client_secret = getattr(settings, "GOOGLE_CALENDAR_CLIENT_SECRET", None)

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if resp.status_code != 200:
                raise ValueError(f"Google OAuth token exchange failed: {resp.text}")
            tokens = resp.json()

        q = select(CalendarSource).where(
            CalendarSource.organisation_id == org_id,
            CalendarSource.source_type == "google_calendar",
        )
        r = await self.db.execute(q)
        source = r.scalar_one_or_none()

        expires_at = None
        if tokens.get("expires_in"):
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])

        if not source:
            source = CalendarSource(
                organisation_id=org_id,
                source_type="google_calendar",
                name="Google Calendar",
                is_active=True,
                color="#4285F4",
            )
            self.db.add(source)

        source.access_token_encrypted = encrypt_secret(tokens["access_token"])
        if tokens.get("refresh_token"):
            source.refresh_token_encrypted = encrypt_secret(tokens["refresh_token"])
        source.token_expires_at = expires_at
        source.last_synced_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(source)
        return source

    async def get_google_events(
        self, org_id: str, year: int, month: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch events from connected personal Google Calendar for the given month.
        Also tries public Indian holiday calendars if GOOGLE_CALENDAR_API_KEY is set.
        """
        from app.core.encryption import decrypt_secret

        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc) if month == 12 else datetime(year, month + 1, 1, tzinfo=timezone.utc)

        events: List[Dict] = []

        # 1. Personal Google Calendar (OAuth)
        q = select(CalendarSource).where(
            CalendarSource.organisation_id == org_id,
            CalendarSource.source_type == "google_calendar",
            CalendarSource.is_active.is_(True),
        )
        r = await self.db.execute(q)
        source = r.scalar_one_or_none()

        if source and source.access_token_encrypted:
            access_token = decrypt_secret(source.access_token_encrypted)
            params = {
                "timeMin": start.isoformat(),
                "timeMax": end.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 100,
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(
                        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                        headers={"Authorization": f"Bearer {access_token}"},
                        params=params,
                    )
                    if resp.status_code == 200:
                        for item in resp.json().get("items", []):
                            start_val = item.get("start", {})
                            events.append({
                                "id": item.get("id"),
                                "title": item.get("summary", "Untitled"),
                                "description": item.get("description"),
                                "event_date": start_val.get("date") or start_val.get("dateTime"),
                                "event_type": "google",
                                "category": "custom",
                                "emoji": "📅",
                                "color": "#4285F4",
                                "source": "google_personal",
                            })
            except Exception as e:
                logger.warning(f"Google personal calendar fetch error: {e}")

        # 2. Public Indian holiday calendars (API key, no OAuth)
        google_api_key = getattr(settings, "GOOGLE_CALENDAR_API_KEY", None)
        if google_api_key:
            PUBLIC_CALENDAR_IDS = [
                ("en.indian#holiday@group.v.calendar.google.com", "Indian Holidays", "🇮🇳"),
                ("en.hinduism#holiday@group.v.calendar.google.com", "Hindu Holidays", "🕉️"),
                ("en.islamic#holiday@group.v.calendar.google.com", "Islamic Holidays", "☪️"),
            ]
            params = {
                "key": google_api_key,
                "timeMin": start.isoformat(),
                "timeMax": end.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": 50,
            }
            for cal_id, cal_name, cal_emoji in PUBLIC_CALENDAR_IDS:
                try:
                    import urllib.parse
                    encoded_id = urllib.parse.quote(cal_id, safe="")
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.get(
                            f"https://www.googleapis.com/calendar/v3/calendars/{encoded_id}/events",
                            params=params,
                        )
                        if resp.status_code == 200:
                            for item in resp.json().get("items", []):
                                start_val = item.get("start", {})
                                name = item.get("summary", "Holiday")
                                category, emoji, _ = _classify_event(name)
                                events.append({
                                    "id": f"gcal_{item.get('id')}",
                                    "title": name,
                                    "description": item.get("description"),
                                    "event_date": start_val.get("date") or start_val.get("dateTime"),
                                    "event_type": "festival",
                                    "category": category,
                                    "emoji": emoji or cal_emoji,
                                    "color": CATEGORY_COLORS.get(category, "#4285F4"),
                                    "source": f"google_public_{cal_name.lower().replace(' ', '_')}",
                                })
                except Exception as e:
                    logger.debug(f"Public Google Calendar {cal_id} fetch: {e}")

        return events
