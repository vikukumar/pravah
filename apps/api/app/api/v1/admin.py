from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import get_current_active_super_admin
from app.core.database import get_db
from app.models.organisation import Organisation
from app.models.user import User
from app.schemas.admin import (
    AdminMetricsResponse,
    AuditLogResponse,
    SystemSettingUpdate,
)
from app.services.admin_service import AdminService

router = APIRouter()

@router.get("/metrics", response_model=AdminMetricsResponse)
async def get_metrics(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    metrics = await admin_svc.get_platform_metrics()
    return AdminMetricsResponse(**metrics)

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    org_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    logs = await admin_svc.list_audit_logs(org_id=org_id, action=action, limit=limit, offset=offset)
    return [AuditLogResponse.model_validate(l) for l in logs]

@router.get("/users")
async def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    res = await db.execute(query)
    users = res.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "is_super_admin": u.is_super_admin,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "created_at": u.created_at,
        }
        for u in users
    ]

@router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    query = select(User).where(User.id == user_id)
    res = await db.execute(query)
    user = res.scalar_one_or_none()
    if user:
        user.is_active = not user.is_active
        await db.commit()
    return {"message": "User status updated.", "is_active": user.is_active if user else False}

@router.get("/organisations")
async def list_all_organisations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Organisation)
        .options(selectinload(Organisation.subscription))
        .order_by(Organisation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(query)
    orgs = res.scalars().all()
    return [
        {
            "id": o.id,
            "name": o.name,
            "slug": o.slug,
            "is_active": o.is_active,
            "publishing_paused": o.publishing_paused,
            "subscription_status": o.subscription.status if o.subscription else "none",
            "created_at": o.created_at,
        }
        for o in orgs
    ]

@router.post("/emergency-stop")
async def toggle_emergency_stop(
    pause_all: bool = Query(...),
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    await admin_svc.toggle_platform_emergency_stop(pause_all, admin)
    return {"message": f"Global publishing pause set to {pause_all}."}

@router.get("/settings")
async def get_settings(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    return await admin_svc.get_system_settings(public_only=False)

@router.post("/settings")
async def set_setting(
    payload: SystemSettingUpdate,
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    await admin_svc.set_system_setting(
        key=payload.key,
        value=payload.value,
        is_public=payload.is_public,
        description=payload.description,
    )
    return {"message": "Setting saved successfully."}

# ------------------------------------------------------------------------------
# AI Models & Providers Management
# ------------------------------------------------------------------------------
@router.get("/ai/catalog")
async def get_ai_provider_catalog(
    admin: User = Depends(get_current_active_super_admin),
):
    from app.services.ai_service import AIService
    return AIService.get_provider_catalog()

@router.post("/ai/test-connection")
async def test_ai_provider_connection(
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.services.ai_service import AIService
    provider_id = payload.get("provider_id", "openrouter")
    base_uri = payload.get("base_uri", "https://openrouter.ai/api/v1")
    api_key = payload.get("api_key", "")

    ai_svc = AIService(db)
    return await ai_svc.test_provider_connection(provider_id, base_uri, api_key)

@router.get("/ai/providers")
async def get_admin_ai_providers(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    settings_dict = await admin_svc.get_system_settings(public_only=False)
    ai_config = settings_dict.get("ai_config", {
        "active_provider": "openrouter",
        "providers_config": {},
        "openrouter_api_key": "",
        "default_text_model": "anthropic/claude-3.5-sonnet",
        "default_image_model": "stabilityai/stable-diffusion-xl",
        "custom_providers": [],
    })
    # Mask key for security
    key = ai_config.get("openrouter_api_key", "")
    masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else ("****" if key else "")
    return {
        "active_provider": ai_config.get("active_provider", "openrouter"),
        "providers_config": ai_config.get("providers_config", {}),
        "openrouter_configured": bool(key),
        "openrouter_key_masked": masked_key,
        "default_text_model": ai_config.get("default_text_model", "anthropic/claude-3.5-sonnet"),
        "default_image_model": ai_config.get("default_image_model", "stabilityai/stable-diffusion-xl"),
        "custom_providers": ai_config.get("custom_providers", []),
    }

@router.post("/ai/providers")
async def update_admin_ai_providers(
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    settings_dict = await admin_svc.get_system_settings(public_only=False)
    existing_config = settings_dict.get("ai_config", {})

    new_key = payload.get("openrouter_api_key")
    if new_key and not new_key.startswith("****"):
        existing_config["openrouter_api_key"] = new_key

    if "default_text_model" in payload:
        existing_config["default_text_model"] = payload["default_text_model"]
    if "default_image_model" in payload:
        existing_config["default_image_model"] = payload["default_image_model"]
    if "custom_providers" in payload:
        existing_config["custom_providers"] = payload["custom_providers"]

    await admin_svc.set_system_setting(
        key="ai_config",
        value=existing_config,
        is_public=False,
        description="Global AI providers, keys and model routing configuration",
    )
    return {"message": "AI providers configuration updated successfully."}

# ------------------------------------------------------------------------------
# Payment Gateway Configuration (Razorpay + Cashfree)
# DB -> EnvVar -> Disabled priority chain
# ------------------------------------------------------------------------------
@router.get("/payment-gateways/status")
async def get_payment_gateway_status(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns configuration status for all payment gateways.
    Shows which gateways are active and where credentials come from (db / env / disabled).
    """
    from app.services.credential_resolver import CredentialResolver
    resolver = CredentialResolver(db)
    return await resolver.get_all_status()

@router.get("/payment-gateways/razorpay")
async def get_razorpay_config(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Returns Razorpay credential status (masked key, source, webhook configured)."""
    from app.services.credential_resolver import CredentialResolver
    resolver = CredentialResolver(db)
    return await resolver.get_razorpay_status()

@router.post("/payment-gateways/razorpay")
async def update_razorpay_config(
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Save Razorpay credentials to DB. These override environment variables.
    Accepts: key_id, key_secret, webhook_secret, environment (test/live).
    """
    from app.core.encryption import encrypt_string
    from app.services.admin_service import AdminService
    admin_svc = AdminService(db)
    existing = await admin_svc.get_system_settings(public_only=False)
    cfg = existing.get("payment_gateway_config", {})
    rzp = cfg.get("razorpay", {})

    if "key_id" in payload and payload["key_id"]:
        rzp["key_id"] = payload["key_id"].strip()
    if "key_secret" in payload and payload["key_secret"] and not payload["key_secret"].startswith("xxxx"):
        rzp["key_secret_encrypted"] = encrypt_string(payload["key_secret"].strip())
    if "webhook_secret" in payload and payload["webhook_secret"] and not payload["webhook_secret"].startswith("xxxx"):
        rzp["webhook_secret_encrypted"] = encrypt_string(payload["webhook_secret"].strip())
    if "environment" in payload:
        rzp["environment"] = payload["environment"]  # "live" or "test"

    cfg["razorpay"] = rzp
    await admin_svc.set_system_setting(
        key="payment_gateway_config",
        value=cfg,
        is_public=False,
        description="Payment gateway credentials (Razorpay, Cashfree) — encrypted at rest",
    )
    return {"message": "Razorpay configuration saved. DB credentials now override environment variables."}

@router.delete("/payment-gateways/razorpay")
async def clear_razorpay_config(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Remove Razorpay credentials from DB — system falls back to environment variables."""
    from app.services.admin_service import AdminService
    admin_svc = AdminService(db)
    existing = await admin_svc.get_system_settings(public_only=False)
    cfg = existing.get("payment_gateway_config", {})
    cfg.pop("razorpay", None)
    await admin_svc.set_system_setting(key="payment_gateway_config", value=cfg, is_public=False,
                                       description="Payment gateway credentials")
    return {"message": "Razorpay DB credentials cleared. System will now use environment variables."}

@router.get("/payment-gateways/cashfree")
async def get_cashfree_config(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Returns Cashfree credential status (masked app_id, environment, source)."""
    from app.services.credential_resolver import CredentialResolver
    resolver = CredentialResolver(db)
    return await resolver.get_cashfree_status()

@router.post("/payment-gateways/cashfree")
async def update_cashfree_config(
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Save Cashfree credentials to DB. These override environment variables.
    Accepts: app_id, secret_key, environment (TEST/PROD).
    """
    from app.core.encryption import encrypt_string
    from app.services.admin_service import AdminService
    admin_svc = AdminService(db)
    existing = await admin_svc.get_system_settings(public_only=False)
    cfg = existing.get("payment_gateway_config", {})
    cf = cfg.get("cashfree", {})

    if "app_id" in payload and payload["app_id"]:
        cf["app_id"] = payload["app_id"].strip()
    if "secret_key" in payload and payload["secret_key"] and not payload["secret_key"].startswith("xxxx"):
        cf["secret_key_encrypted"] = encrypt_string(payload["secret_key"].strip())
    if "environment" in payload:
        cf["environment"] = payload["environment"].upper()  # "TEST" or "PROD"

    cfg["cashfree"] = cf
    await admin_svc.set_system_setting(
        key="payment_gateway_config",
        value=cfg,
        is_public=False,
        description="Payment gateway credentials (Razorpay, Cashfree) — encrypted at rest",
    )
    return {"message": "Cashfree configuration saved. DB credentials now override environment variables."}

@router.delete("/payment-gateways/cashfree")
async def clear_cashfree_config(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Remove Cashfree credentials from DB — system falls back to environment variables."""
    from app.services.admin_service import AdminService
    admin_svc = AdminService(db)
    existing = await admin_svc.get_system_settings(public_only=False)
    cfg = existing.get("payment_gateway_config", {})
    cfg.pop("cashfree", None)
    await admin_svc.set_system_setting(key="payment_gateway_config", value=cfg, is_public=False,
                                       description="Payment gateway credentials")
    return {"message": "Cashfree DB credentials cleared. System will now use environment variables."}

# ------------------------------------------------------------------------------
@router.get("/social/credentials")
async def get_admin_social_credentials(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    settings_dict = await admin_svc.get_system_settings(public_only=False)
    creds = settings_dict.get("social_oauth_credentials", {})

    providers = ["x", "facebook", "instagram", "linkedin", "youtube"]
    results = {}
    for p in providers:
        p_data = creds.get(p, {})
        results[p] = {
            "client_id": p_data.get("client_id", ""),
            "has_secret": bool(p_data.get("client_secret_encrypted")),
            "redirect_uri": p_data.get("redirect_uri", f"https://pravah.app/api/v1/social/callback/{p}"),
            "is_enabled": p_data.get("is_enabled", True),
        }
    return results

@router.get("/social/credential-status")
async def get_social_credential_status(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns configuration status for all social providers.
    Shows which providers are fully ready (credentials + enabled) for users to connect.
    """
    from app.services.social_service import SocialService
    social_svc = SocialService(db)
    return await social_svc.get_provider_credential_status()

@router.post("/social/credentials")
async def update_admin_social_credentials(
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.core.encryption import encrypt_string
    admin_svc = AdminService(db)
    settings_dict = await admin_svc.get_system_settings(public_only=False)
    existing_creds = settings_dict.get("social_oauth_credentials", {})

    for provider, data in payload.items():
        if provider not in existing_creds:
            existing_creds[provider] = {}

        if "client_id" in data:
            existing_creds[provider]["client_id"] = data["client_id"]
        if "redirect_uri" in data:
            existing_creds[provider]["redirect_uri"] = data["redirect_uri"]
        if "is_enabled" in data:
            existing_creds[provider]["is_enabled"] = data["is_enabled"]
        if "client_secret" in data and data["client_secret"] and not data["client_secret"].startswith("****"):
            existing_creds[provider]["client_secret_encrypted"] = encrypt_string(data["client_secret"])

    await admin_svc.set_system_setting(
        key="social_oauth_credentials",
        value=existing_creds,
        is_public=False,
        description="Encrypted OAuth application keys and secrets for third-party social networks",
    )
    return {"message": "Social media OAuth credentials saved and encrypted."}

# ------------------------------------------------------------------------------
# CMS & Legal Pages Management
# ------------------------------------------------------------------------------
@router.get("/cms/pages")
async def get_admin_cms_pages(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.cms import CMSPage
    query = select(CMSPage).options(selectinload(CMSPage.blocks), selectinload(CMSPage.seo)).order_by(CMSPage.created_at.asc())
    res = await db.execute(query)
    pages = res.scalars().all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "slug": p.slug,
            "description": p.description,
            "is_published": p.is_published,
            "is_system": p.is_system,
            "version": p.version,
            "blocks_count": len(p.blocks),
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
        for p in pages
    ]

@router.post("/cms/pages")
async def save_admin_cms_page(
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.cms import CMSPage
    slug = payload.get("slug", "").lower().strip()
    title = payload.get("title", "").strip()

    query = select(CMSPage).where(CMSPage.slug == slug)
    res = await db.execute(query)
    page = res.scalar_one_or_none()

    if not page:
        page = CMSPage(
            title=title,
            slug=slug,
            description=payload.get("description"),
            is_published=payload.get("is_published", True),
            is_system=payload.get("is_system", False),
        )
        db.add(page)
        await db.flush()
    else:
        page.title = title
        page.description = payload.get("description")
        page.is_published = payload.get("is_published", True)
        page.version += 1

    await db.commit()
    return {"message": "CMS Page saved successfully.", "page_id": page.id}

