from fastapi import APIRouter
from app.api.v1.admin import router as admin_router
from app.api.v1.ai import router as ai_router
from app.api.v1.ai_providers import router as ai_providers_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.cms import router as cms_router
from app.api.v1.content import router as content_router
from app.api.v1.media import router as media_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.organisations import router as organisations_router
from app.api.v1.setup import router as setup_router
from app.api.v1.social import router as social_router
from app.api.v1.workflows import router as workflows_router

api_router = APIRouter()

api_router.include_router(setup_router, prefix="/setup", tags=["Setup Wizard"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(organisations_router, prefix="/organisations", tags=["Organisations"])
api_router.include_router(social_router, prefix="/social", tags=["Social Media"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI Studio"])
api_router.include_router(ai_providers_router, prefix="/ai/providers", tags=["AI Providers"])
api_router.include_router(content_router, prefix="/content", tags=["Content & Calendar"])
api_router.include_router(campaigns_router, prefix="/campaigns", tags=["Campaigns"])
api_router.include_router(media_router, prefix="/media", tags=["Media Library"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(workflows_router, prefix="/workflows", tags=["No-Code Workflows"])
api_router.include_router(billing_router, prefix="/billing", tags=["Billing & Payments"])
api_router.include_router(cms_router, prefix="/cms", tags=["Dynamic CMS"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(admin_router, prefix="/admin", tags=["Platform Administration"])
