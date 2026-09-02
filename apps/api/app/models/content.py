import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel

class Campaign(BaseModel):
    __tablename__ = "campaigns"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    objective = Column(String(100), nullable=True) # awareness, conversion, engagement, retention
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="active", nullable=False) # draft, active, paused, completed, archived
    budget = Column(String(100), nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    organisation = relationship("Organisation", back_populates="campaigns")
    content_items = relationship("Content", back_populates="campaign")

class Content(BaseModel):
    __tablename__ = "contents"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    content_type = Column(String(50), default="text", nullable=False) # text, image, video, link, carousel
    
    status = Column(String(50), default="draft", nullable=False, index=True) 
    # draft, ai_generated, review, approved, scheduled, publishing, published, failed, cancelled, rejected, archived
    
    platforms = Column(JSON, nullable=False) # list of platform names e.g. ["facebook", "x", "linkedin"]
    account_ids = Column(JSON, nullable=True) # list of target social_account_ids
    page_ids = Column(JSON, nullable=True) # list of target social_page_ids
    media_urls = Column(JSON, nullable=True) # list of media URLs
    
    approval_required = Column(Boolean, default=False, nullable=False)
    current_approver_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # AI provenance tracking
    ai_provider_id = Column(String(36), nullable=True)
    ai_model = Column(String(100), nullable=True)
    ai_prompt = Column(Text, nullable=True)
    
    # Fingerprint to prevent accidental duplicate posts
    content_fingerprint = Column(String(64), nullable=True, index=True)
    
    # Publishing result details
    external_post_ids = Column(JSON, nullable=True) # map of provider/page -> post_id
    error_message = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    version = Column(Integer, default=1, nullable=False)

    organisation = relationship("Organisation", back_populates="content_items")
    campaign = relationship("Campaign", back_populates="content_items")
    assets = relationship("ContentAsset", back_populates="content", cascade="all, delete-orphan")
    versions = relationship("ContentVersion", back_populates="content", cascade="all, delete-orphan")
    approvals = relationship("ContentApproval", back_populates="content", cascade="all, delete-orphan")
    schedule = relationship("ContentSchedule", back_populates="content", uselist=False, cascade="all, delete-orphan")

class ContentAsset(BaseModel):
    __tablename__ = "content_assets"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    content_id = Column(String(36), ForeignKey("contents.id", ondelete="CASCADE"), nullable=True, index=True)
    uploader_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    dimensions = Column(String(50), nullable=True) # e.g. "1200x630"
    is_ai_generated = Column(Boolean, default=False, nullable=False)
    prompt = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)

    content = relationship("Content", back_populates="assets")

class ContentVersion(BaseModel):
    __tablename__ = "content_versions"

    content_id = Column(String(36), ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    media_urls = Column(JSON, nullable=True)
    edited_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_summary = Column(String(255), nullable=True)

    content = relationship("Content", back_populates="versions")

class ContentApproval(BaseModel):
    __tablename__ = "content_approvals"

    content_id = Column(String(36), ForeignKey("contents.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False) # approved, rejected, changes_requested
    comments = Column(Text, nullable=True)

    content = relationship("Content", back_populates="approvals")

class ContentSchedule(BaseModel):
    __tablename__ = "content_schedules"

    content_id = Column(String(36), ForeignKey("contents.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String(100), default="UTC", nullable=False)
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    idempotency_key = Column(String(100), unique=True, nullable=False, index=True)

    content = relationship("Content", back_populates="schedule")
