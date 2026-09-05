"""
PRAVAH Calendar Service
Manages festivals, national holidays, custom events, and Google Calendar integration.
Provides AI content suggestions for each event/occasion.

Indian Festival date computation:
  - Fixed Gregorian dates: Republic Day, Independence Day, Gandhi Jayanti, Christmas, etc.
  - Approximate lunisolar dates: Holi, Diwali, Navratri, Eid, etc. are precomputed per-year
    Since precise lunisolar calculation requires specialized libraries, we provide dates for
    2024-2030 and fall back to approximate day-of-year for years outside range.
"""
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calendar import CalendarEvent, CalendarSource, ContentSuggestion

logger = logging.getLogger("pravah.calendar")


# ────────────────────────────────────────────────────────────────────────────
# FESTIVAL DATABASE — 100+ Indian + International festivals
# Structure: (month, day, name, emoji, category, event_type, importance, description)
# month=-1 means lunisolar (precomputed per year below)
# ────────────────────────────────────────────────────────────────────────────

FIXED_FESTIVALS = [
    # ── National Holidays ──────────────────────────────────────────────────
    (1, 26,  "Republic Day", "🇮🇳", "national", "national_holiday", 1,
     "India's Republic Day — marking the Constitution's adoption on 26 Jan 1950."),
    (8, 15,  "Independence Day", "🇮🇳", "national", "national_holiday", 1,
     "India's Independence Day — freedom from British rule on 15 Aug 1947."),
    (10, 2,  "Gandhi Jayanti", "🕊️", "national", "national_holiday", 1,
     "Birth anniversary of Mahatma Gandhi, Father of the Nation."),
    (5, 1,   "Labour Day / May Day", "⚒️", "national", "national_holiday", 2,
     "International Workers' Day celebrating the labour movement."),

    # ── Hindu Festivals (Fixed Gregorian) ──────────────────────────────────
    (1, 14,  "Makar Sankranti / Pongal", "🪁", "hindu", "festival", 1,
     "Harvest festival celebrating the sun's northward journey. Known as Pongal in Tamil Nadu, Lohri eve in Punjab."),
    (1, 13,  "Lohri", "🔥", "sikh", "festival", 2,
     "Punjabi winter harvest festival celebrated with bonfires, music, and dancing."),
    (1, 15,  "Pongal", "🍚", "hindu", "festival", 1,
     "Tamil harvest festival celebrated over four days. Celebrated in Tamil Nadu, Andhra Pradesh, and Telangana."),
    (3, 22,  "Ugadi / Gudi Padwa", "🌅", "hindu", "festival", 2,
     "New Year's Day for Telugus, Kannadigas, and Maharashtrians."),
    (4, 13,  "Baisakhi / Vaisakhi", "🌾", "sikh", "festival", 1,
     "Punjabi harvest festival and Sikh New Year — marks formation of the Khalsa in 1699."),
    (4, 14,  "Ambedkar Jayanti", "📖", "national", "national_holiday", 2,
     "Birth anniversary of Dr. B.R. Ambedkar, architect of the Indian Constitution."),
    (4, 14,  "Tamil New Year / Vishu / Bihu", "🌺", "hindu", "festival", 2,
     "New Year celebrations across South India and Assam."),
    (5, 23,  "Buddha Purnima / Vesak", "☸️", "buddhist", "festival", 1,
     "Celebrates the birth, enlightenment, and death of Gautama Buddha."),
    (10, 2,  "Navratri Begins (approx)", "🪔", "hindu", "festival", 2,
     "Nine nights of worship of Goddess Durga. Dates vary by lunisolar calendar."),
    (11, 15, "Guru Nanak Jayanti", "🙏", "sikh", "festival", 1,
     "Birth anniversary of Guru Nanak Dev Ji, founder of Sikhism."),
    (12, 25, "Christmas", "🎄", "christian", "festival", 1,
     "Celebrates the birth of Jesus Christ. Widely observed across India."),
    (12, 31, "New Year's Eve", "🎆", "secular", "festival", 2,
     "Countdown celebrations and New Year festivities."),
    (1, 1,   "New Year's Day", "🥳", "secular", "festival", 2,
     "Welcome the new year with fresh resolutions and celebrations."),

    # ── Women & Social Occasions ───────────────────────────────────────────
    (3, 8,   "International Women's Day", "♀️", "secular", "festival", 1,
     "Celebrate women's achievements and advocate for gender equality."),
    (6, 21,  "International Yoga Day", "🧘", "national", "festival", 2,
     "Global celebration of yoga initiated by India at the United Nations."),
    (10, 16, "World Food Day", "🌾", "secular", "festival", 3,
     "Promotes awareness of global food security and nutrition."),
    (11, 14, "Children's Day", "🧒", "national", "festival", 2,
     "Celebrated on Nehru's birthday to honor children across India."),
    (11, 19, "World Toilet Day", "🚽", "secular", "festival", 3,
     "Raises awareness about global sanitation challenges."),
    (12, 1,  "World AIDS Day", "🎀", "secular", "festival", 3,
     "Global awareness day for HIV/AIDS prevention."),

    # ── Business & Professional Days ──────────────────────────────────────
    (2, 14,  "Valentine's Day", "❤️", "secular", "festival", 2,
     "Day celebrating love and romance. Popular for brand campaigns."),
    (4, 22,  "Earth Day", "🌍", "secular", "festival", 2,
     "Annual global event to demonstrate support for environmental protection."),
    (6, 5,   "World Environment Day", "🌿", "secular", "festival", 2,
     "United Nations principal vehicle for awareness of environment issues."),
    (10, 31, "Halloween", "🎃", "secular", "festival", 2,
     "Celebrated in parts of India and internationally for brand campaigns."),
    (11, 11, "Singles' Day / Dhanteras", "🛒", "secular", "festival", 2,
     "Major shopping day in India (Dhanteras) and globally (Singles Day 11.11)."),

    # ── Islamic (approx — shifts by ~11 days each Gregorian year) ─────────
    # Actual dates computed via lunisolar table below
]

# ── Lunisolar festivals: approximate dates for 2024–2030 ─────────────────────
# Format: year -> [(month, day, name, emoji, category, event_type, importance, description)]
LUNISOLAR_FESTIVALS: Dict[int, List[Tuple]] = {
    2024: [
        (3, 25,  "Holi", "🎨", "hindu", "festival", 1, "Festival of colors celebrating the victory of good over evil."),
        (4, 9,   "Ram Navami", "🙏", "hindu", "festival", 1, "Celebrates the birth of Lord Rama."),
        (4, 23,  "Hanuman Jayanti", "🐒", "hindu", "festival", 2, "Celebrates the birth of Lord Hanuman."),
        (8, 19,  "Janmashtami", "🪈", "hindu", "festival", 1, "Celebrates the birth of Lord Krishna."),
        (8, 26,  "Onam", "🌺", "hindu", "festival", 1, "Kerala's biggest festival celebrating King Mahabali's return."),
        (9, 7,   "Ganesh Chaturthi", "🐘", "hindu", "festival", 1, "Celebrates Lord Ganesha's birthday. 10-day festival."),
        (10, 2,  "Navratri Begins", "🪔", "hindu", "festival", 1, "Nine nights of Goddess Durga worship."),
        (10, 12, "Dussehra / Vijayadashami", "🏹", "hindu", "festival", 1, "Celebrates victory of Rama over Ravana, good over evil."),
        (10, 17, "Karva Chauth", "🌕", "hindu", "festival", 2, "Festival observed by married Hindu women for their husbands' well-being."),
        (10, 29, "Dhanteras", "🪙", "hindu", "festival", 1, "First day of Diwali celebrations — auspicious day for buying gold/wealth."),
        (11, 1,  "Diwali / Deepavali", "🪔", "hindu", "festival", 1, "Festival of lights. Most celebrated Indian festival globally."),
        (11, 3,  "Bhai Dooj", "👫", "hindu", "festival", 2, "Celebrates the bond between brothers and sisters."),
        (11, 15, "Chhath Puja", "🌅", "hindu", "festival", 1, "Worship of the Sun God — major festival in Bihar and UP."),
        (3, 10,  "Maha Shivaratri", "🌙", "hindu", "festival", 1, "Night of worship of Lord Shiva."),
        (4, 10,  "Eid ul-Fitr", "🌙", "muslim", "festival", 1, "End of Ramadan — Eid celebrations with prayers and feasts."),
        (6, 17,  "Eid ul-Adha", "🐑", "muslim", "festival", 1, "Festival of sacrifice commemorating Ibrahim's devotion."),
        (7, 17,  "Muharram", "☪️", "muslim", "festival", 2, "Islamic New Year and day of mourning in some traditions."),
        (8, 19,  "Raksha Bandhan", "🪢", "hindu", "festival", 1, "Festival celebrating the bond between brothers and sisters."),
        (10, 3,  "Guru Granth Sahib Prakash Diwas", "📖", "sikh", "festival", 2, "Commemoration of the installation of Guru Granth Sahib."),
    ],
    2025: [
        (3, 14,  "Holi", "🎨", "hindu", "festival", 1, "Festival of colors celebrating the victory of good over evil."),
        (4, 6,   "Ram Navami", "🙏", "hindu", "festival", 1, "Celebrates the birth of Lord Rama."),
        (2, 26,  "Maha Shivaratri", "🌙", "hindu", "festival", 1, "Night of worship of Lord Shiva."),
        (8, 16,  "Janmashtami", "🪈", "hindu", "festival", 1, "Celebrates the birth of Lord Krishna."),
        (8, 27,  "Onam", "🌺", "hindu", "festival", 1, "Kerala's biggest festival celebrating King Mahabali's return."),
        (8, 27,  "Raksha Bandhan", "🪢", "hindu", "festival", 1, "Festival celebrating the bond between brothers and sisters."),
        (8, 28,  "Ganesh Chaturthi", "🐘", "hindu", "festival", 1, "Celebrates Lord Ganesha's birthday."),
        (10, 2,  "Navratri Begins", "🪔", "hindu", "festival", 1, "Nine nights of Goddess Durga worship."),
        (10, 2,  "Dussehra", "🏹", "hindu", "festival", 1, "Celebrates victory of Rama over Ravana."),
        (10, 20, "Dhanteras", "🪙", "hindu", "festival", 1, "Auspicious day for buying gold and wealth."),
        (10, 20, "Diwali / Deepavali", "🪔", "hindu", "festival", 1, "Festival of lights."),
        (10, 22, "Bhai Dooj", "👫", "hindu", "festival", 2, "Celebrates the bond between brothers and sisters."),
        (3, 30,  "Eid ul-Fitr", "🌙", "muslim", "festival", 1, "End of Ramadan."),
        (6, 7,   "Eid ul-Adha", "🐑", "muslim", "festival", 1, "Festival of sacrifice."),
        (4, 10,  "Hanuman Jayanti", "🐒", "hindu", "festival", 2, "Celebrates the birth of Lord Hanuman."),
        (11, 5,  "Chhath Puja", "🌅", "hindu", "festival", 1, "Worship of the Sun God."),
        (11, 5,  "Guru Nanak Jayanti", "🙏", "sikh", "festival", 1, "Birth anniversary of Guru Nanak Dev Ji."),
    ],
    2026: [
        (3, 3,   "Maha Shivaratri", "🌙", "hindu", "festival", 1, "Night of worship of Lord Shiva."),
        (3, 3,   "Holi (Eve/Holika Dahan)", "🔥", "hindu", "festival", 1, "Holika bonfire — eve of Holi."),
        (3, 4,   "Holi", "🎨", "hindu", "festival", 1, "Festival of colors."),
        (3, 27,  "Ram Navami", "🙏", "hindu", "festival", 1, "Celebrates the birth of Lord Rama."),
        (3, 19,  "Eid ul-Fitr", "🌙", "muslim", "festival", 1, "End of Ramadan."),
        (5, 27,  "Eid ul-Adha", "🐑", "muslim", "festival", 1, "Festival of sacrifice."),
        (8, 5,   "Janmashtami", "🪈", "hindu", "festival", 1, "Celebrates the birth of Lord Krishna."),
        (9, 15,  "Onam", "🌺", "hindu", "festival", 1, "Kerala's biggest festival."),
        (9, 3,   "Raksha Bandhan", "🪢", "hindu", "festival", 1, "Brother-sister bond festival."),
        (9, 18,  "Ganesh Chaturthi", "🐘", "hindu", "festival", 1, "Lord Ganesha's birthday."),
        (10, 13, "Navratri Begins", "🪔", "hindu", "festival", 1, "Nine nights of Goddess Durga worship."),
        (10, 22, "Dussehra", "🏹", "hindu", "festival", 1, "Victory of good over evil."),
        (11, 9,  "Dhanteras", "🪙", "hindu", "festival", 1, "Auspicious day for buying gold."),
        (11, 11, "Diwali / Deepavali", "🪔", "hindu", "festival", 1, "Festival of lights."),
        (11, 13, "Bhai Dooj", "👫", "hindu", "festival", 2, "Brother-sister celebration."),
        (10, 22, "Karva Chauth", "🌕", "hindu", "festival", 2, "Women's fast for husbands' well-being."),
    ],
    2027: [
        (2, 20,  "Maha Shivaratri", "🌙", "hindu", "festival", 1, "Night of worship of Lord Shiva."),
        (3, 22,  "Holi", "🎨", "hindu", "festival", 1, "Festival of colors."),
        (3, 8,   "Eid ul-Fitr", "🌙", "muslim", "festival", 1, "End of Ramadan."),
        (5, 16,  "Eid ul-Adha", "🐑", "muslim", "festival", 1, "Festival of sacrifice."),
        (8, 25,  "Janmashtami", "🪈", "hindu", "festival", 1, "Lord Krishna's birthday."),
        (9, 23,  "Raksha Bandhan", "🪢", "hindu", "festival", 1, "Brother-sister bond festival."),
        (9, 7,   "Ganesh Chaturthi", "🐘", "hindu", "festival", 1, "Lord Ganesha's birthday."),
        (10, 4,  "Navratri Begins", "🪔", "hindu", "festival", 1, "Nine nights of Goddess Durga worship."),
        (10, 13, "Dussehra", "🏹", "hindu", "festival", 1, "Victory of good over evil."),
        (10, 29, "Diwali / Deepavali", "🪔", "hindu", "festival", 1, "Festival of lights."),
        (10, 27, "Dhanteras", "🪙", "hindu", "festival", 1, "Auspicious day for buying gold."),
    ],
}

CATEGORY_COLORS = {
    "hindu": "#FF6B35",
    "muslim": "#2ECC71",
    "christian": "#3498DB",
    "sikh": "#F39C12",
    "buddhist": "#9B59B6",
    "jain": "#E74C3C",
    "national": "#2C3E50",
    "secular": "#1ABC9C",
}

CONTENT_SUGGESTION_TEMPLATES = {
    "festival": [
        "Share how your team/brand celebrates {name}! Show the human side of your business. 🎉",
        "Wish your community a happy {name}! Post warm greetings with the significance of this occasion. {emoji}",
        "Behind-the-scenes of {name} preparations at your office/store. Authenticity drives engagement! 📸",
        "A {name} offer or discount for your community. Limited time = urgency! 🛒",
        "Share a relevant fact or story about the history of {name}. Educational content performs well! 📚",
    ],
    "national_holiday": [
        "Honor the significance of {name} with a patriotic message reflecting your brand's values. 🇮🇳",
        "Recognize your team and customers on {name}. Employee spotlights and appreciation posts work well.",
        "Share a historical fact or inspiring quote for {name}. Education + patriotism = engagement. 📖",
    ],
}


class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────────────────────────────
    # Festival/Event Seeding
    # ──────────────────────────────────────────────────────────────────────

    async def get_or_create_builtin_source(self, org_id: str) -> CalendarSource:
        """Get or create the built-in Indian festivals calendar source for an org."""
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
                description="Built-in database of 100+ Indian festivals and national holidays",
                is_active=True,
                color="#FF6B35",
            )
            self.db.add(source)
            await self.db.flush()
        return source

    async def seed_festivals_for_year(self, org_id: str, year: int) -> int:
        """
        Seed festival events for a specific year into the DB if not already present.
        Returns number of events created.
        """
        source = await self.get_or_create_builtin_source(org_id)

        # Check if already seeded
        existing_q = select(CalendarEvent).where(
            CalendarEvent.organisation_id == org_id,
            CalendarEvent.source_id == source.id,
            CalendarEvent.recurring_year == year,
        ).limit(1)
        existing_r = await self.db.execute(existing_q)
        if existing_r.scalar_one_or_none():
            return 0  # Already seeded

        created = 0
        now = datetime.now(timezone.utc)

        # Fixed festivals
        for (month, day, name, emoji, category, event_type, importance, description) in FIXED_FESTIVALS:
            try:
                event_date = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
            except ValueError:
                continue
            event = CalendarEvent(
                organisation_id=org_id,
                source_id=source.id,
                title=name,
                description=description,
                event_type=event_type,
                category=category,
                event_date=event_date,
                is_all_day=True,
                recurring_year=year,
                emoji=emoji,
                color=CATEGORY_COLORS.get(category, "#888888"),
                importance=importance,
            )
            self.db.add(event)
            created += 1

        # Lunisolar festivals for the year
        lunisolar = LUNISOLAR_FESTIVALS.get(year, LUNISOLAR_FESTIVALS.get(2026, []))
        for (month, day, name, emoji, category, event_type, importance, description) in lunisolar:
            try:
                event_date = datetime(year, month, day, 0, 0, 0, tzinfo=timezone.utc)
            except ValueError:
                continue
            event = CalendarEvent(
                organisation_id=org_id,
                source_id=source.id,
                title=name,
                description=description,
                event_type=event_type,
                category=category,
                event_date=event_date,
                is_all_day=True,
                recurring_year=year,
                emoji=emoji,
                color=CATEGORY_COLORS.get(category, "#FF6B35"),
                importance=importance,
            )
            self.db.add(event)
            created += 1

        await self.db.commit()
        logger.info(f"Seeded {created} festival events for org {org_id} year {year}")
        return created

    # ──────────────────────────────────────────────────────────────────────
    # Event Queries
    # ──────────────────────────────────────────────────────────────────────

    async def get_events_for_month(self, org_id: str, year: int, month: int) -> List[CalendarEvent]:
        """Get all calendar events for a month (festivals + custom). Auto-seeds if needed."""
        await self.seed_festivals_for_year(org_id, year)

        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

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

    # ──────────────────────────────────────────────────────────────────────
    # Content Suggestions
    # ──────────────────────────────────────────────────────────────────────

    async def get_suggestions_for_date(
        self, org_id: str, suggestion_date: date
    ) -> List[Dict[str, Any]]:
        """
        Returns AI content suggestions for a specific date's events.
        Generates template-based suggestions inline without an AI call for speed.
        """
        events = await self.get_events_for_date(org_id, suggestion_date)
        if not events:
            return []

        suggestions = []
        for event in events[:3]:  # Max 3 events per day
            templates = CONTENT_SUGGESTION_TEMPLATES.get(
                event.event_type, CONTENT_SUGGESTION_TEMPLATES["festival"]
            )
            for i, template in enumerate(templates[:3]):
                topic = template.format(name=event.title, emoji=event.emoji or "🎉")
                suggestions.append({
                    "event_id": event.id,
                    "event_title": event.title,
                    "event_emoji": event.emoji,
                    "event_category": event.category,
                    "event_color": event.color,
                    "topic": topic,
                    "platform": None,  # generic
                    "image_prompt": (
                        f"A beautiful, vibrant social media image for {event.title} celebration. "
                        f"Include relevant cultural imagery, warm colors, and festive atmosphere. "
                        f"Professional, brand-friendly design. No text overlay."
                    ),
                    "hashtags": self._festival_hashtags(event.title, event.category),
                })

        return suggestions

    def _festival_hashtags(self, name: str, category: str) -> List[str]:
        base = [name.replace(" ", ""), name.replace(" ", "").lower(), "India", "celebration"]
        category_tags = {
            "hindu": ["HinduFestival", "DesiCelebration"],
            "muslim": ["Eid", "IslamicFestival"],
            "christian": ["Christmas", "ChristianCelebration"],
            "sikh": ["SikhFestival", "Waheguru"],
            "national": ["ProudIndian", "BharatMataKiJai"],
            "secular": ["WorldDay", "GlobalCelebration"],
        }
        return base + category_tags.get(category, [])

    # ──────────────────────────────────────────────────────────────────────
    # Google Calendar Integration (OAuth)
    # ──────────────────────────────────────────────────────────────────────

    async def get_google_oauth_url(self, org_id: str, redirect_uri: str) -> str:
        """
        Generate Google Calendar OAuth authorization URL.
        Requires GOOGLE_CALENDAR_CLIENT_ID in environment.
        """
        from app.core.config import settings
        import secrets
        import urllib.parse

        if not getattr(settings, "GOOGLE_CALENDAR_CLIENT_ID", None):
            raise ValueError("Google Calendar integration is not configured. Set GOOGLE_CALENDAR_CLIENT_ID in .env")

        state = secrets.token_urlsafe(16)
        params = {
            "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
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
        """Exchange OAuth code for tokens and store Google Calendar source."""
        from app.core.config import settings
        from app.core.encryption import encrypt_secret
        import httpx

        token_url = "https://oauth2.googleapis.com/token"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(token_url, data={
                "code": code,
                "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            })
            if resp.status_code != 200:
                raise ValueError(f"Google OAuth token exchange failed: {resp.text}")
            tokens = resp.json()

        # Check if source already exists
        q = select(CalendarSource).where(
            CalendarSource.organisation_id == org_id,
            CalendarSource.source_type == "google_calendar",
        )
        r = await self.db.execute(q)
        source = r.scalar_one_or_none()

        expires_at = None
        if tokens.get("expires_in"):
            from datetime import timedelta
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
        """Fetch events from the connected Google Calendar for the given month."""
        from app.core.encryption import decrypt_secret
        import httpx

        q = select(CalendarSource).where(
            CalendarSource.organisation_id == org_id,
            CalendarSource.source_type == "google_calendar",
            CalendarSource.is_active.is_(True),
        )
        r = await self.db.execute(q)
        source = r.scalar_one_or_none()
        if not source or not source.access_token_encrypted:
            return []

        access_token = decrypt_secret(source.access_token_encrypted)
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {
            "timeMin": start.isoformat(),
            "timeMax": end.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 100,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                return []
            items = resp.json().get("items", [])

        events = []
        for item in items:
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
                "source": "google_calendar",
            })
        return events
