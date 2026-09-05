"""
PRAVAH Calendar Models
Stores festival/holiday data, calendar source configurations, and AI content suggestions.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel


class CalendarSource(BaseModel):
    """
    Tracks external calendar connections (Google Calendar, etc.)
    and built-in sources (indian_festivals, national_holidays).
    """
    __tablename__ = "calendar_sources"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # google_calendar, indian_festivals, national_holidays, custom
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    color = Column(String(20), nullable=True)  # hex color for calendar display

    # Google Calendar OAuth fields
    google_calendar_id = Column(String(255), nullable=True)
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # Sync configuration
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    sync_config = Column(JSON, nullable=True)  # platform-specific sync options

    organisation = relationship("Organisation")
    events = relationship("CalendarEvent", back_populates="source", cascade="all, delete-orphan")


class CalendarEvent(BaseModel):
    """
    Individual calendar events — festivals, holidays, custom events.
    Built-in events (festivals/holidays) are org-scoped but seeded from global data.
    """
    __tablename__ = "calendar_events"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("calendar_sources.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=False)  # festival, national_holiday, religious, custom, google
    category = Column(String(50), nullable=True)  # hindu, muslim, christian, sikh, buddhist, jain, national, secular

    # Date fields (timezone-naive for all-day events)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    event_end_date = Column(DateTime(timezone=True), nullable=True)
    is_all_day = Column(Boolean, default=True, nullable=False)
    recurring_year = Column(Integer, nullable=True)  # year this instance applies to (for annual recurring)

    emoji = Column(String(20), nullable=True)  # festival emoji (🪔, 🎆, 🌙, etc.)
    color = Column(String(20), nullable=True)  # #hex for display on calendar
    importance = Column(Integer, default=2, nullable=False)  # 1=major, 2=standard, 3=minor

    # External calendar reference
    external_event_id = Column(String(255), nullable=True)  # Google Calendar event ID
    external_data = Column(JSON, nullable=True)

    source = relationship("CalendarSource", back_populates="events")
    suggestions = relationship("ContentSuggestion", back_populates="event", cascade="all, delete-orphan")


class ContentSuggestion(BaseModel):
    """
    AI-generated content suggestions tied to specific calendar events/dates.
    Pre-generated suggestions that users can one-click expand into content.
    """
    __tablename__ = "content_suggestions"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(String(36), ForeignKey("calendar_events.id", ondelete="CASCADE"), nullable=True)

    # Can also be tied directly to a date without a specific event
    suggestion_date = Column(DateTime(timezone=True), nullable=False, index=True)

    platform = Column(String(50), nullable=True)  # target platform or null = generic
    topic = Column(String(500), nullable=False)  # suggested topic/theme
    sample_text = Column(Text, nullable=True)  # brief sample of content
    hashtags = Column(JSON, nullable=True)
    image_prompt = Column(Text, nullable=True)  # image generation prompt for this suggestion

    ai_provider_id = Column(String(36), nullable=True)  # which AI generated this suggestion
    ai_model = Column(String(100), nullable=True)

    is_used = Column(Boolean, default=False, nullable=False)  # true if user clicked to use this
    used_content_id = Column(String(36), ForeignKey("contents.id", ondelete="SET NULL"), nullable=True)

    event = relationship("CalendarEvent", back_populates="suggestions")
