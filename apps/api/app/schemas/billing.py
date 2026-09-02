from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class PlanFeatureSchema(BaseModel):
    social_account_limit: int = 1
    page_limit: int = 1
    daily_post_limit: int = 1
    monthly_post_limit: int = 30
    ai_token_limit_monthly: int = 50000
    image_generation_limit_monthly: int = 10
    workflow_limit: int = 3
    workflow_execution_limit_monthly: int = 100
    member_limit: int = 1
    storage_limit_mb: int = 500
    analytics_retention_days: int = 30
    has_api_access: bool = False
    has_custom_providers: bool = False
    has_sso: bool = False
    has_2fa: bool = True
    has_approval_workflows: bool = False
    has_automation: bool = True
    has_advanced_analytics: bool = False

class PlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    currency: str = "USD"
    is_free: bool = False
    trial_days: int = 30
    features: PlanFeatureSchema

class PlanResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    currency: str
    is_free: bool
    is_active: bool
    trial_days: int
    features: PlanFeatureSchema

    model_config = ConfigDict(from_attributes=True)

class SubscriptionResponse(BaseModel):
    id: str
    organisation_id: str
    plan_id: str
    plan_name: str
    status: str
    billing_period: str
    current_period_start: datetime
    current_period_end: datetime
    trial_end: Optional[datetime]
    cancel_at_period_end: bool
    payment_gateway: Optional[str]

class RazorpayOrderCreateRequest(BaseModel):
    plan_id: str
    billing_period: str = "monthly" # monthly, yearly

class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan_id: str
    billing_period: str = "monthly"

class CashfreeOrderCreateRequest(BaseModel):
    plan_id: str
    billing_period: str = "monthly"

class CashfreeVerifyRequest(BaseModel):
    order_id: str
    plan_id: str
    billing_period: str = "monthly"

class UsageMetricsResponse(BaseModel):
    connected_social_accounts: int
    social_account_limit: int
    posts_published_this_month: int
    monthly_post_limit: int
    posts_published_today: int
    daily_post_limit: int
    ai_tokens_used_this_month: int
    ai_token_limit_monthly: int
    images_generated_this_month: int
    image_generation_limit_monthly: int
    active_workflows: int
    workflow_limit: int
    workflow_executions_this_month: int
    workflow_execution_limit_monthly: int
    team_members: int
    member_limit: int
    storage_used_mb: float
    storage_limit_mb: int
