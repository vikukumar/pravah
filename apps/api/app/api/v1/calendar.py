"""
PRAVAH Calendar API Router
Manages festival/holiday events, custom events, Google Calendar integration,
and AI content suggestions per occasion.
"""
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TenantContext, get_db, require_permission
from app.services.calendar_service import CalendarService

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class CalendarEventOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    event_type: str
    category: Optional[str]
    event_date: datetime
    is_all_day: bool
    emoji: Optional[str]
    color: Optional[str]
    importance: int
    source: str = "builtin"

    class Config:
        from_attributes = True


class CustomEventCreate(BaseModel):
    title: str
    event_date: datetime
    description: Optional[str] = None
    emoji: Optional[str] = None
    color: Optional[str] = None
    category: str = "custom"
    event_end_date: Optional[datetime] = None


class GoogleLinkRequest(BaseModel):
    redirect_uri: str


class GoogleCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/events", summary="Get all calendar events for a month")
async def get_calendar_events(
    year: int = Query(default=None),
    month: int = Query(default=None),
    include_google: bool = Query(default=True),
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns all events for the given month:
    - Built-in Indian festivals & national holidays
    - Custom org events
    - Google Calendar events (if connected)
    """
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    svc = CalendarService(db)
    events = await svc.get_events_for_month(tenant.organisation.id, year, month)

    # Group by date string
    by_date: Dict[str, List[Dict]] = {}
    for ev in events:
        ds = ev.event_date.strftime("%Y-%m-%d")
        if ds not in by_date:
            by_date[ds] = []
        by_date[ds].append({
            "id": ev.id,
            "title": ev.title,
            "description": ev.description,
            "event_type": ev.event_type,
            "category": ev.category,
            "event_date": ev.event_date.isoformat(),
            "is_all_day": ev.is_all_day,
            "emoji": ev.emoji,
            "color": ev.color,
            "importance": ev.importance,
            "source": "builtin" if ev.event_type != "custom" else "custom",
        })

    # Google Calendar events
    google_events = []
    if include_google:
        try:
            google_events = await svc.get_google_events(tenant.organisation.id, year, month)
            for gev in google_events:
                ev_date = gev.get("event_date", "")
                ds = ev_date[:10] if ev_date else ""
                if ds:
                    if ds not in by_date:
                        by_date[ds] = []
                    by_date[ds].append({**gev, "source": "google_calendar"})
        except Exception:
            pass

    return {
        "year": year,
        "month": month,
        "by_date": by_date,
        "total_events": sum(len(v) for v in by_date.values()),
        "has_google_calendar": len(google_events) > 0,
    }


@router.get("/festivals", summary="Get festivals and holidays for a month")
async def get_festivals(
    year: int = Query(default=None),
    month: int = Query(default=None),
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Returns only festival and holiday events (excludes custom and Google events)."""
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    svc = CalendarService(db)
    events = await svc.get_events_for_month(tenant.organisation.id, year, month)
    return [
        {
            "id": ev.id,
            "title": ev.title,
            "description": ev.description,
            "event_type": ev.event_type,
            "category": ev.category,
            "event_date": ev.event_date.isoformat(),
            "emoji": ev.emoji,
            "color": ev.color,
            "importance": ev.importance,
        }
        for ev in events if ev.event_type in ("festival", "national_holiday", "religious")
    ]


@router.get("/suggestions", summary="Get AI content suggestions for a date")
async def get_content_suggestions(
    event_date: str = Query(..., description="Date in YYYY-MM-DD format"),
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Returns content post suggestions for a specific date's festivals and events.
    Each suggestion includes a topic, sample text, hashtags, and an image prompt.
    """
    try:
        parsed_date = date.fromisoformat(event_date)
    except ValueError:
        return []

    svc = CalendarService(db)
    return await svc.get_suggestions_for_date(tenant.organisation.id, parsed_date)


@router.post("/events", summary="Create a custom calendar event")
async def create_custom_event(
    payload: CustomEventCreate,
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    svc = CalendarService(db)
    event = await svc.create_custom_event(
        org_id=tenant.organisation.id,
        title=payload.title,
        event_date=payload.event_date,
        description=payload.description,
        emoji=payload.emoji,
        color=payload.color,
        category=payload.category,
        event_end_date=payload.event_end_date,
    )
    return {
        "id": event.id,
        "title": event.title,
        "event_date": event.event_date.isoformat(),
        "emoji": event.emoji,
        "color": event.color,
        "category": event.category,
    }


@router.post("/link-google", summary="Get Google Calendar OAuth URL")
async def link_google_calendar(
    payload: GoogleLinkRequest,
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Returns the Google OAuth authorization URL to connect Google Calendar."""
    svc = CalendarService(db)
    try:
        url = await svc.get_google_oauth_url(tenant.organisation.id, payload.redirect_uri)
        return {"authorization_url": url, "configured": True}
    except ValueError as e:
        return {"authorization_url": None, "configured": False, "message": str(e)}


@router.post("/google-callback", summary="Handle Google Calendar OAuth callback")
async def google_calendar_callback(
    payload: GoogleCallbackRequest,
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Exchanges the OAuth code and stores the Google Calendar connection."""
    svc = CalendarService(db)
    source = await svc.exchange_google_code(
        tenant.organisation.id, payload.code, payload.redirect_uri
    )
    return {
        "connected": True,
        "source_id": source.id,
        "name": source.name,
        "last_synced_at": source.last_synced_at.isoformat() if source.last_synced_at else None,
    }


@router.get("/google-events", summary="Fetch Google Calendar events for a month")
async def get_google_events(
    year: int = Query(default=None),
    month: int = Query(default=None),
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Returns events from the connected Google Calendar for the given month."""
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    svc = CalendarService(db)
    return await svc.get_google_events(tenant.organisation.id, year, month)


@router.get("/api-status", summary="Check which calendar APIs are configured")
async def get_api_status(
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns configuration status for all calendar data sources:
    - Calendarific (most accurate, lunisolar festivals)
    - Abstract Holidays (free tier)
    - Nager.Date (always available, no key)
    - Google Calendar public (Indian/Hindu/Islamic)
    """
    svc = CalendarService(db)
    status = await svc.get_api_status()
    configured_count = sum(1 for s in status.values() if s["configured"])
    return {
        "sources": status,
        "active_sources": configured_count,
        "recommendation": (
            "Add CALENDARIFIC_API_KEY to .env for the most accurate Indian festival dates "
            "(lunisolar Holi, Diwali, Eid, etc.)"
            if not status["calendarific"]["configured"]
            else "Calendarific is active — festival dates are accurate!"
        ),
    }


@router.post("/refresh-cache", summary="Force refresh festival data from APIs")
async def refresh_festival_cache(
    year: int = Query(default=None),
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Invalidates the cached festival data for the given year and re-fetches from live APIs.
    Useful after updating API keys or to get the latest data.
    """
    now = datetime.now(timezone.utc)
    year = year or now.year
    svc = CalendarService(db)
    created = await svc.invalidate_cache(tenant.organisation.id, year)
    return {
        "success": True,
        "year": year,
        "events_created": created,
        "message": f"Festival data refreshed: {created} events loaded for {year}.",
    }
