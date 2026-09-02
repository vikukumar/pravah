import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel

class CMSPage(BaseModel):
    __tablename__ = "cms_pages"

    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    content_json = Column(JSON, nullable=True) # visual builder layout data
    
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    is_system = Column(Boolean, default=False, nullable=False) # system pages (e.g. terms, privacy)
    published_at = Column(DateTime(timezone=True), nullable=True)
    version = Column(Integer, default=1, nullable=False)

    blocks = relationship("CMSBlock", back_populates="page", cascade="all, delete-orphan", order_by="CMSBlock.display_order")
    revisions = relationship("CMSRevision", back_populates="page", cascade="all, delete-orphan")
    seo = relationship("SEOConfiguration", back_populates="page", uselist=False, cascade="all, delete-orphan")

class CMSBlock(BaseModel):
    __tablename__ = "cms_blocks"

    page_id = Column(String(36), ForeignKey("cms_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    block_type = Column(String(50), nullable=False) # hero, features, pricing, testimonials, faq, cta, custom_html
    name = Column(String(100), nullable=False)
    content = Column(JSON, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    is_visible = Column(Boolean, default=True, nullable=False)

    page = relationship("CMSPage", back_populates="blocks")

class CMSRevision(BaseModel):
    __tablename__ = "cms_revisions"

    page_id = Column(String(36), ForeignKey("cms_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    version_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    snapshot_json = Column(JSON, nullable=False) # Full page & blocks snapshot
    summary = Column(String(255), nullable=True)

    page = relationship("CMSPage", back_populates="revisions")

class Menu(BaseModel):
    __tablename__ = "menus"

    name = Column(String(100), unique=True, index=True, nullable=False) # header_main, footer_nav, etc.
    location = Column(String(50), nullable=False) # header, footer, sidebar
    items = Column(JSON, nullable=False) # list of { title, url, open_new_tab, order, children: [] }
    is_active = Column(Boolean, default=True, nullable=False)

class Form(BaseModel):
    __tablename__ = "forms"

    name = Column(String(100), unique=True, index=True, nullable=False) # e.g. "contact_us", "lead_capture"
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notification_emails = Column(JSON, nullable=True) # list of emails to notify
    success_message = Column(String(255), default="Thank you! We have received your submission.", nullable=False)

    fields = relationship("FormField", back_populates="form", cascade="all, delete-orphan", order_by="FormField.display_order")
    submissions = relationship("FormSubmission", back_populates="form", cascade="all, delete-orphan")

class FormField(BaseModel):
    __tablename__ = "form_fields"

    form_id = Column(String(36), ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False) # e.g. email, message, company
    field_label = Column(String(100), nullable=False)
    field_type = Column(String(50), default="text", nullable=False) # text, email, phone, number, textarea, select, checkbox
    placeholder = Column(String(255), nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    options = Column(JSON, nullable=True) # For select/radio
    display_order = Column(Integer, default=0, nullable=False)

    form = relationship("Form", back_populates="fields")

class FormSubmission(BaseModel):
    __tablename__ = "form_submissions"

    form_id = Column(String(36), ForeignKey("forms.id", ondelete="CASCADE"), nullable=False, index=True)
    data = Column(JSON, nullable=False)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(50), default="new", nullable=False) # new, read, replied, archived

    form = relationship("Form", back_populates="submissions")

class SEOConfiguration(BaseModel):
    __tablename__ = "seo_configurations"

    page_id = Column(String(36), ForeignKey("cms_pages.id", ondelete="CASCADE"), unique=True, nullable=True, index=True)
    path = Column(String(255), unique=True, index=True, nullable=False) # e.g. "/", "/pricing", "/features"
    meta_title = Column(String(255), nullable=False)
    meta_description = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=True)
    canonical_url = Column(String(500), nullable=True)
    og_image_url = Column(String(500), nullable=True)
    og_type = Column(String(50), default="website", nullable=False)
    twitter_card = Column(String(50), default="summary_large_image", nullable=False)
    structured_data = Column(JSON, nullable=True) # JSON-LD schema
    no_index = Column(Boolean, default=False, nullable=False)

    page = relationship("CMSPage", back_populates="seo")
