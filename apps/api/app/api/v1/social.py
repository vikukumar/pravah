import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import TenantContext, get_db, get_tenant_context, require_permission
from app.core.config import settings
from app.schemas.social import (
    SocialAccountResponse,
    SocialProfileSummaryResponse,
    SocialProviderResponse,
)
from app.services.social_service import SocialService

logger = logging.getLogger("pravah.social")

router = APIRouter()


@router.get("/providers/available")
async def list_available_providers(
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns social providers available for user connection.
    Only providers where admin has configured valid credentials AND is_enabled=True.
    Never returns unconfigured providers.
    """
    social_svc = SocialService(db)
    return await social_svc.get_available_providers()


@router.get("/providers")
async def list_social_providers(
    db: AsyncSession = Depends(get_db),
):
    """
    Admin-facing: Returns all provider definitions with capability matrix.
    Does NOT include credential status -- use /admin/social/credential-status for that.
    """
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
    tenant: TenantContext = Depends(require_permission("social.connect")),
    db: AsyncSession = Depends(get_db),
):
    """
    Generates real OAuth authorization URL using admin DB-configured credentials.
    Returns error if provider is not configured or disabled.
    """
    social_svc = SocialService(db)
    result = await social_svc.get_oauth_authorization_url(
        provider_name=provider,
        redirect_uri=redirect_uri,
        org_id=tenant.organisation.id,
        user_id=tenant.user.id,
    )
    return result


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Real OAuth callback endpoint. Provider redirects here after user grants authorization.
    Validates CSRF state, exchanges code for tokens, fetches real profile, stores account.
    Redirects to frontend with success/error.
    """
    frontend_base = settings.APP_URL

    # Handle provider error
    if error:
        logger.warning(f"OAuth callback error for {provider}: {error} — {error_description}")
        error_msg = error_description or error
        return HTMLResponse(content=f"""
        <script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'SOCIAL_OAUTH_ERROR',
                    provider: '{provider}',
                    error: '{error_msg}'
                }}, '*');
                window.close();
            }} else {{
                window.location.href = '{frontend_base}/dashboard/social?error={error}';
            }}
        </script>
        """)

    if not code or not state:
        return HTMLResponse(content=f"""
        <script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'SOCIAL_OAUTH_ERROR',
                    provider: '{provider}',
                    error: 'Missing authorization code or state parameter.'
                }}, '*');
                window.close();
            }} else {{
                window.location.href = '{frontend_base}/dashboard/social?error=missing_params';
            }}
        </script>
        """)

    social_svc = SocialService(db)

    # Validate CSRF state
    state_data = await social_svc.validate_and_consume_state(state)
    if not state_data:
        return HTMLResponse(content=f"""
        <script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'SOCIAL_OAUTH_ERROR',
                    provider: '{provider}',
                    error: 'Invalid or expired security state. Please try again.'
                }}, '*');
                window.close();
            }} else {{
                window.location.href = '{frontend_base}/dashboard/social?error=invalid_state';
            }}
        </script>
        """)

    org_id = state_data.get("org_id")
    user_id = state_data.get("user_id")
    redirect_uri = state_data.get("redirect_uri")

    # Load user for actor
    from sqlalchemy import select
    from app.models.user import User as UserModel
    user_res = await db.execute(select(UserModel).where(UserModel.id == user_id))
    actor = user_res.scalar_one_or_none()

    try:
        # Exchange code for real tokens
        token_data = await social_svc.exchange_oauth_code(
            provider_name=provider,
            code=code,
            redirect_uri=redirect_uri,
        )

        access_token = token_data.get("access_token", "")
        if not access_token:
            raise ValueError("Provider returned empty access token.")

        # Fetch real profile
        profile = await social_svc.fetch_provider_profile(provider, access_token)
        account_id = profile.get("id") or f"{provider}_{state[:8]}"
        account_name = profile.get("name") or f"{provider.capitalize()} Account"
        username = profile.get("username") or ""
        profile_image_url = profile.get("profile_image_url") or ""

        # Store encrypted tokens and create real social account
        account = await social_svc.connect_account_with_token(
            org_id=org_id,
            provider=provider,
            account_id=account_id,
            account_name=account_name,
            access_token=access_token,
            refresh_token=token_data.get("refresh_token"),
            token_expires_in=token_data.get("expires_in", 3600),
            username=username,
            profile_image_url=profile_image_url,
            actor=actor,
        )

        logger.info(f"Successfully connected {provider} account {account_id} for org {org_id}")

        return HTMLResponse(content=f"""
        <script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'SOCIAL_OAUTH_SUCCESS',
                    provider: '{provider}',
                    account_id: '{account.id}',
                    account_name: '{account_name}'
                }}, '*');
                window.close();
            }} else {{
                window.location.href = '{frontend_base}/dashboard/social?success=connected&provider={provider}';
            }}
        </script>
        """)

    except Exception as e:
        logger.error(f"OAuth connection failed for {provider}: {str(e)}")
        error_detail = str(e)[:200]
        return HTMLResponse(content=f"""
        <script>
            if (window.opener) {{
                window.opener.postMessage({{
                    type: 'SOCIAL_OAUTH_ERROR',
                    provider: '{provider}',
                    error: '{error_detail}'
                }}, '*');
                window.close();
            }} else {{
                window.location.href = '{frontend_base}/dashboard/social?error=connection_failed';
            }}
        </script>
        """)


@router.get("/accounts", response_model=List[SocialAccountResponse])
async def list_social_accounts(
    tenant: TenantContext = Depends(require_permission("social.view")),
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
):
    social_svc = SocialService(db)
    await social_svc.disconnect_account(tenant.organisation.id, account_id, tenant.user)
    return {"message": "Account disconnected successfully."}


@router.get("/accounts/{account_id}/profile-summary", response_model=SocialProfileSummaryResponse)
async def get_profile_summary(
    account_id: str,
    tenant: TenantContext = Depends(require_permission("social.view")),
    db: AsyncSession = Depends(get_db),
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
