from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class ContentCreate(BaseModel):
    title: Optional[str] = None
    body: str = Field(..., min_length=1)
    content_type: str = "text"
    platforms: List[str] = Field(..., min_length=1)
    account_ids: Optional[List[str]] = None
    page_ids: Optional[List[str]] = None
    media_urls: Optional[List[str]] = None
    campaign_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    approval_required: bool = False
    ai_provider_id: Optional[str] = None
    ai_model: Optional[str] = None
    ai_prompt: Optional[str] = None

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    content_type: Optional[str] = None
    platforms: Optional[List[str]] = None
    account_ids: Optional[List[str]] = None
    page_ids: Optional[List[str]] = None
    media_urls: Optional[List[str]] = None
    campaign_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    approval_required: Optional[bool] = None

class ContentResponse(BaseModel):
    id: str
    organisation_id: str
    campaign_id: Optional[str]
    title: Optional[str]
    body: str
    content_type: str
    status: str
    platforms: List[str]
    account_ids: Optional[List[str]]
    page_ids: Optional[List[str]]
    media_urls: Optional[List[str]]
    approval_required: bool
    current_approver_id: Optional[str]
    ai_provider_id: Optional[str]
    ai_model: Optional[str]
    ai_prompt: Optional[str]
    external_post_ids: Optional[Dict[str, Any]]
    error_message: Optional[str]
    published_at: Optional[datetime]
    scheduled_at: Optional[datetime] = None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ContentApprovalRequest(BaseModel):
    action: str # approve, reject, changes_requested
    comments: Optional[str] = None

class BestTimeRecommendationResponse(BaseModel):
    day_of_week: str
    recommended_time: str
    recommended_datetime: datetime
    confidence_score: float
    reason: str
    is_historical_data: bool

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    objective: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[str] = None

class CampaignResponse(BaseModel):
    id: str
    organisation_id: str
    name: str
    description: Optional[str]
    objective: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    status: str
    budget: Optional[str]
    content_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
