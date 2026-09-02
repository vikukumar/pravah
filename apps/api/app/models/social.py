import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel

class SocialProvider(BaseModel):
    __tablename__ = "social_providers"

    name = Column(String(50), unique=True, index=True, nullable=False) # facebook, instagram, x, linkedin, youtube
    display_name = Column(String(100), nullable=False)
    icon_url = Column(String(500), nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    # Provider capability matrix
    supports_text = Column(Boolean, default=True, nullable=False)
    supports_image = Column(Boolean, default=True, nullable=False)
    supports_video = Column(Boolean, default=True, nullable=False)
    supports_carousel = Column(Boolean, default=False, nullable=False)
    supports_pages = Column(Boolean, default=True, nullable=False)
    supports_analytics = Column(Boolean, default=True, nullable=False)
    supports_scheduling = Column(Boolean, default=True, nullable=False)
    supports_comments = Column(Boolean, default=False, nullable=False)
    max_char_limit = Column(Integer, default=280, nullable=False)
    
    auth_config = Column(JSON, nullable=True) # OAuth scopes, endpoints

class SocialAccount(BaseModel):
    __tablename__ = "social_accounts"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True) # facebook, instagram, x, linkedin, youtube
    account_id = Column(String(255), nullable=False, index=True) # External platform account/user ID
    account_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    is_connected = Column(Boolean, default=True, nullable=False)
    health_status = Column(String(50), default="healthy", nullable=False) # healthy, warning, expired, error
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(Text, nullable=True)

    organisation = relationship("Organisation", back_populates="social_accounts")
    tokens = relationship("SocialToken", back_populates="social_account", cascade="all, delete-orphan")
    pages = relationship("SocialPage", back_populates="social_account", cascade="all, delete-orphan")
    profile = relationship("SocialProfile", back_populates="social_account", uselist=False, cascade="all, delete-orphan")
    summaries = relationship("SocialProfileSummary", back_populates="social_account", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_org_provider_account", "organisation_id", "provider", "account_id", unique=True),
    )

class SocialToken(BaseModel):
    __tablename__ = "social_tokens"

    social_account_id = Column(String(36), ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_type = Column(String(50), default="Bearer", nullable=False)
    scopes = Column(String(500), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_valid = Column(Boolean, default=True, nullable=False)

    social_account = relationship("SocialAccount", back_populates="tokens")

class SocialPage(BaseModel):
    __tablename__ = "social_pages"

    social_account_id = Column(String(36), ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    page_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    page_url = Column(String(500), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    access_token_encrypted = Column(Text, nullable=True)
    is_connected = Column(Boolean, default=True, nullable=False)
    health_status = Column(String(50), default="healthy", nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)

    social_account = relationship("SocialAccount", back_populates="pages")

    __table_args__ = (
        Index("ix_org_platform_page", "organisation_id", "platform", "page_id", unique=True),
    )

class SocialProfile(BaseModel):
    __tablename__ = "social_profiles"

    social_account_id = Column(String(36), ForeignKey("social_accounts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    raw_metadata = Column(JSON, nullable=True)
    followers_count = Column(Integer, default=0, nullable=False)
    following_count = Column(Integer, default=0, nullable=False)
    posts_count = Column(Integer, default=0, nullable=False)
    biography = Column(Text, nullable=True)
    synced_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    social_account = relationship("SocialAccount", back_populates="profile")

class SocialProfileSummary(BaseModel):
    __tablename__ = "social_profile_summaries"

    social_account_id = Column(String(36), ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    brand_identity = Column(Text, nullable=False)
    business_category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    audience_signals = Column(JSON, nullable=True)
    content_themes = Column(JSON, nullable=True)
    tone = Column(String(100), nullable=False)
    keywords = Column(JSON, nullable=True)
    hashtags = Column(JSON, nullable=True)
    posting_patterns = Column(Text, nullable=True)
    content_formats = Column(JSON, nullable=True)
    engagement_patterns = Column(Text, nullable=True)

    social_account = relationship("SocialAccount", back_populates="summaries")
