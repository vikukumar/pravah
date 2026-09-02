from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class AdminMetricsResponse(BaseModel):
    total_users: int
    active_users: int
    total_organisations: int
    active_subscriptions: int
    total_revenue_usd: float
    total_published_posts: int
    total_workflow_executions: int
    total_ai_tokens_consumed: int
    system_health: str = "operational"

class SystemSettingUpdate(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None
    is_public: bool = False
    is_encrypted: bool = False

class FeatureFlagUpdate(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    is_enabled_globally: bool = True
    allowed_plans: Optional[List[str]] = None
    allowed_organisations: Optional[List[str]] = None
    allowed_users: Optional[List[str]] = None

class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str]
    actor_email: Optional[str]
    organisation_id: Optional[str]
    action: str
    target_type: Optional[str]
    target_id: Optional[str]
    result: str
    ip_address: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DashboardLayoutSaveRequest(BaseModel):
    widgets: List[Dict[str, Any]]
