from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class SocialProviderResponse(BaseModel):
    id: str
    name: str
    display_name: str
    icon_url: Optional[str]
    is_enabled: bool
    supports_text: bool
    supports_image: bool
    supports_video: bool
    supports_carousel: bool
    supports_pages: bool
    supports_analytics: bool
    supports_scheduling: bool
    supports_comments: bool
    max_char_limit: int

class SocialAccountResponse(BaseModel):
    id: str
    organisation_id: str
    provider: str
    account_id: str
    account_name: str
    username: Optional[str]
    profile_image_url: Optional[str]
    is_connected: bool
    health_status: str
    last_sync_at: Optional[datetime]
    pages_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SocialPageResponse(BaseModel):
    id: str
    social_account_id: str
    organisation_id: str
    platform: str
    page_id: str
    name: str
    username: Optional[str]
    page_url: Optional[str]
    profile_image_url: Optional[str]
    is_connected: bool
    health_status: str
    last_sync_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class SocialProfileSummaryResponse(BaseModel):
    id: str
    social_account_id: str
    version: int
    brand_identity: str
    business_category: str
    description: str
    audience_signals: Optional[List[str]]
    content_themes: Optional[List[str]]
    tone: str
    keywords: Optional[List[str]]
    hashtags: Optional[List[str]]
    posting_patterns: Optional[str]
    content_formats: Optional[List[str]]
    engagement_patterns: Optional[str]
    created_at: datetime

class ConnectOAuthRequest(BaseModel):
    provider: str
    code: str
    redirect_uri: str
    state: Optional[str] = None
