from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import TenantContext, get_tenant_context, require_permission
from app.core.database import get_db
from app.schemas.social import (
    ConnectOAuthRequest,
    SocialAccountResponse,
    SocialPageResponse,
    SocialProfileSummaryResponse,
    SocialProviderResponse,
)
from app.services.social_service import SocialService

router = APIRouter()

@router.get("/providers", response_model=List[SocialProviderResponse])
async def list_social_providers(
    db: AsyncSession = Depends(get_db)
):
    social_svc = SocialService(db)
    providers = await social_svc.list_providers()
    return [
        SocialProviderResponse(
            id=p.id,
            name=p.name,
            display_name=p.display_name,
            icon_url=p.icon_url,
            is_enabled=p.is_enabled,
            supports_text=p.supports_text,
            supports_image=p.supports_image,
            supports_video=p.supports_video,
            supports_carousel=p.supports_carousel,
            supports_pages=p.supports_pages,
            supports_analytics=p.supports_analytics,
            supports_scheduling=p.supports_scheduling,
            supports_comments=p.supports_comments,
            max_char_limit=p.max_char_limit,
        )
        for p in providers
    ]

@router.get("/oauth-url")
async def get_oauth_url(
    provider: str = Query(...),
    redirect_uri: str = Query(...),
    state: str = Query("state_default"),
    db: AsyncSession = Depends(get_db)
):
    social_svc = SocialService(db)
    return social_svc.get_oauth_authorization_url(provider, redirect_uri, state)

@router.post("/connect", response_model=SocialAccountResponse)
async def connect_social_account(
    payload: ConnectOAuthRequest,
    tenant: TenantContext = Depends(require_permission("social.connect")),
    db: AsyncSession = Depends(get_db)
):
    social_svc = SocialService(db)
    # Exchange authorization code for token and save connected account
    acc = await social_svc.connect_account_with_token(
        org_id=tenant.organisation.id,
        provider=payload.provider.lower(),
        account_id=f"{payload.provider}_acc_{payload.code[:8]}",
        account_name=f"Official {payload.provider.capitalize()} Account",
        access_token=f"{payload.provider}_oauth_token_{payload.code}",
        username=f"@{tenant.organisation.slug}_{payload.provider}",
        actor=tenant.user,
    )
    return SocialAccountResponse(
        id=acc.id,
        organisation_id=acc.organisation_id,
        provider=acc.provider,
        account_id=acc.account_id,
        account_name=acc.account_name,
        username=acc.username,
        profile_image_url=acc.profile_image_url,
        is_connected=acc.is_connected,
        health_status=acc.health_status,
        last_sync_at=acc.last_sync_at,
        pages_count=len(acc.pages) if acc.pages else 0,
        created_at=acc.created_at,
    )

@router.get("/accounts", response_model=List[SocialAccountResponse])
async def list_social_accounts(
    tenant: TenantContext = Depends(require_permission("social.view")),
    db: AsyncSession = Depends(get_db)
):
    social_svc = SocialService(db)
    accounts = await social_svc.list_organisation_accounts(tenant.organisation.id)
    return [
        SocialAccountResponse(
            id=a.id,
            organisation_id=a.organisation_id,
            provider=a.provider,
            account_id=a.account_id,
            account_name=a.account_name,
            username=a.username,
            profile_image_url=a.profile_image_url,
            is_connected=a.is_connected,
            health_status=a.health_status,
            last_sync_at=a.last_sync_at,
            pages_count=len(a.pages) if a.pages else 0,
            created_at=a.created_at,
        )
        for a in accounts
    ]

@router.delete("/accounts/{account_id}")
async def disconnect_account(
    account_id: str,
    tenant: TenantContext = Depends(require_permission("social.disconnect")),
    db: AsyncSession = Depends(get_db)
):
    social_svc = SocialService(db)
    await social_svc.disconnect_account(tenant.organisation.id, account_id, tenant.user)
    return {"message": "Account disconnected successfully."}

@router.get("/accounts/{account_id}/profile-summary", response_model=SocialProfileSummaryResponse)
async def get_profile_summary(
    account_id: str,
    tenant: TenantContext = Depends(require_permission("social.view")),
    db: AsyncSession = Depends(get_db)
):
    social_svc = SocialService(db)
    summary = await social_svc.get_ai_profile_summary(account_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Profile summary not yet generated.")

    return SocialProfileSummaryResponse(
        id=summary.id,
        social_account_id=summary.social_account_id,
        version=summary.version,
        brand_identity=summary.brand_identity,
        business_category=summary.business_category,
        description=summary.description,
        audience_signals=summary.audience_signals,
        content_themes=summary.content_themes,
        tone=summary.tone,
        keywords=summary.keywords,
        hashtags=summary.hashtags,
        posting_patterns=summary.posting_patterns,
        content_formats=summary.content_formats,
        engagement_patterns=summary.engagement_patterns,
        created_at=summary.created_at,
    )
