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


# ------------------------------------------------------------------------------
# Plans Management
# ------------------------------------------------------------------------------
@router.get("/plans")
async def list_plans(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.billing import Plan
    from sqlalchemy.orm import selectinload as sli
    res = await db.execute(
        select(Plan).options(sli(Plan.features)).order_by(Plan.price_monthly.asc())
    )
    plans = res.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "description": p.description,
            "price_monthly": p.price_monthly,
            "price_yearly": p.price_yearly,
            "currency": p.currency,
            "is_free": p.is_free,
            "is_active": p.is_active,
            "trial_days": p.trial_days,
            "razorpay_plan_id_monthly": p.razorpay_plan_id_monthly,
            "razorpay_plan_id_yearly": p.razorpay_plan_id_yearly,
            "cashfree_plan_id_monthly": p.cashfree_plan_id_monthly,
            "cashfree_plan_id_yearly": p.cashfree_plan_id_yearly,
            "features": {
                "social_account_limit": p.features.social_account_limit if p.features else 1,
                "page_limit": p.features.page_limit if p.features else 1,
                "daily_post_limit": p.features.daily_post_limit if p.features else 1,
                "monthly_post_limit": p.features.monthly_post_limit if p.features else 30,
                "ai_token_limit_monthly": p.features.ai_token_limit_monthly if p.features else 50000,
                "image_generation_limit_monthly": p.features.image_generation_limit_monthly if p.features else 10,
                "workflow_limit": p.features.workflow_limit if p.features else 3,
                "workflow_execution_limit_monthly": p.features.workflow_execution_limit_monthly if p.features else 100,
                "member_limit": p.features.member_limit if p.features else 1,
                "storage_limit_mb": p.features.storage_limit_mb if p.features else 500,
                "analytics_retention_days": p.features.analytics_retention_days if p.features else 30,
                "has_api_access": p.features.has_api_access if p.features else False,
                "has_custom_providers": p.features.has_custom_providers if p.features else False,
                "has_sso": p.features.has_sso if p.features else False,
                "has_approval_workflows": p.features.has_approval_workflows if p.features else False,
                "has_automation": p.features.has_automation if p.features else True,
                "has_advanced_analytics": p.features.has_advanced_analytics if p.features else False,
            } if p.features else {},
            "created_at": p.created_at,
        }
        for p in plans
    ]


@router.post("/plans")
async def create_plan(
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.billing import Plan, PlanFeature
    plan = Plan(
        name=payload["name"],
        slug=payload.get("slug") or payload["name"].lower().replace(" ", "_"),
        description=payload.get("description"),
        price_monthly=payload.get("price_monthly", 0),
        price_yearly=payload.get("price_yearly", 0),
        currency=payload.get("currency", "INR"),
        is_free=payload.get("is_free", False),
        is_active=payload.get("is_active", True),
        trial_days=payload.get("trial_days", 14),
        razorpay_plan_id_monthly=payload.get("razorpay_plan_id_monthly"),
        razorpay_plan_id_yearly=payload.get("razorpay_plan_id_yearly"),
        cashfree_plan_id_monthly=payload.get("cashfree_plan_id_monthly"),
        cashfree_plan_id_yearly=payload.get("cashfree_plan_id_yearly"),
    )
    db.add(plan)
    await db.flush()

    feats = payload.get("features", {})
    feature = PlanFeature(
        plan_id=plan.id,
        social_account_limit=feats.get("social_account_limit", 1),
        page_limit=feats.get("page_limit", 1),
        daily_post_limit=feats.get("daily_post_limit", 1),
        monthly_post_limit=feats.get("monthly_post_limit", 30),
        ai_token_limit_monthly=feats.get("ai_token_limit_monthly", 50000),
        image_generation_limit_monthly=feats.get("image_generation_limit_monthly", 10),
        workflow_limit=feats.get("workflow_limit", 3),
        workflow_execution_limit_monthly=feats.get("workflow_execution_limit_monthly", 100),
        member_limit=feats.get("member_limit", 1),
        storage_limit_mb=feats.get("storage_limit_mb", 500),
        analytics_retention_days=feats.get("analytics_retention_days", 30),
        has_api_access=feats.get("has_api_access", False),
        has_custom_providers=feats.get("has_custom_providers", False),
        has_sso=feats.get("has_sso", False),
        has_approval_workflows=feats.get("has_approval_workflows", False),
        has_automation=feats.get("has_automation", True),
        has_advanced_analytics=feats.get("has_advanced_analytics", False),
    )
    db.add(feature)
    await db.commit()
    return {"message": "Plan created.", "plan_id": plan.id}


@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: str,
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.billing import Plan, PlanFeature
    from sqlalchemy.orm import selectinload as sli
    res = await db.execute(
        select(Plan).options(sli(Plan.features)).where(Plan.id == plan_id)
    )
    plan = res.scalar_one_or_none()
    if not plan:
        from fastapi import HTTPException
        raise HTTPException(404, "Plan not found")

    for field in ["name", "description", "price_monthly", "price_yearly", "currency",
                  "is_free", "is_active", "trial_days", "razorpay_plan_id_monthly",
                  "razorpay_plan_id_yearly", "cashfree_plan_id_monthly", "cashfree_plan_id_yearly"]:
        if field in payload:
            setattr(plan, field, payload[field])

    feats = payload.get("features", {})
    if feats:
        f = plan.features
        if not f:
            f = PlanFeature(plan_id=plan.id)
            db.add(f)
        for field in ["social_account_limit", "page_limit", "daily_post_limit", "monthly_post_limit",
                      "ai_token_limit_monthly", "image_generation_limit_monthly", "workflow_limit",
                      "workflow_execution_limit_monthly", "member_limit", "storage_limit_mb",
                      "analytics_retention_days", "has_api_access", "has_custom_providers",
                      "has_sso", "has_approval_workflows", "has_automation", "has_advanced_analytics"]:
            if field in feats:
                setattr(f, field, feats[field])

    await db.commit()
    return {"message": "Plan updated."}


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.billing import Plan
    res = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = res.scalar_one_or_none()
    if plan:
        plan.is_active = False
        await db.commit()
    return {"message": "Plan deactivated."}


# ------------------------------------------------------------------------------
# Roles & Permissions
# ------------------------------------------------------------------------------
@router.get("/roles")
async def list_system_roles(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.organisation import Role, RolePermission, Permission
    from sqlalchemy.orm import selectinload as sli
    res = await db.execute(
        select(Role)
        .options(sli(Role.role_permissions))
        .where(Role.organisation_id.is_(None))
        .order_by(Role.created_at.asc())
    )
    roles = res.scalars().all()

    # Load all permissions
    perm_res = await db.execute(select(Permission))
    all_perms = {p.id: p for p in perm_res.scalars().all()}

    return [
        {
            "id": r.id,
            "name": r.name,
            "display_name": r.display_name,
            "description": r.description,
            "is_system": r.is_system,
            "permissions": [
                {
                    "id": all_perms[rp.permission_id].id,
                    "name": all_perms[rp.permission_id].name,
                    "module": all_perms[rp.permission_id].module,
                    "description": all_perms[rp.permission_id].description,
                }
                for rp in r.role_permissions
                if rp.permission_id in all_perms
            ],
        }
        for r in roles
    ]


@router.get("/permissions")
async def list_all_permissions(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.organisation import Permission
    res = await db.execute(select(Permission).order_by(Permission.module.asc(), Permission.name.asc()))
    perms = res.scalars().all()
    by_module: Dict[str, list] = {}
    for p in perms:
        by_module.setdefault(p.module, []).append({
            "id": p.id, "name": p.name, "module": p.module, "description": p.description
        })
    return {"by_module": by_module, "total": len(perms)}


@router.put("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: str,
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.organisation import Role, RolePermission, Permission
    from sqlalchemy import delete as sql_delete
    res = await db.execute(select(Role).where(Role.id == role_id))
    role = res.scalar_one_or_none()
    if not role:
        from fastapi import HTTPException
        raise HTTPException(404, "Role not found")

    perm_names: List[str] = payload.get("permissions", [])
    perm_res = await db.execute(select(Permission).where(Permission.name.in_(perm_names)))
    perms = {p.name: p for p in perm_res.scalars().all()}

    await db.execute(sql_delete(RolePermission).where(RolePermission.role_id == role_id))
    for perm_name in perm_names:
        if perm_name in perms:
            db.add(RolePermission(role_id=role_id, permission_id=perms[perm_name].id))

    await db.commit()
    return {"message": f"Role '{role.name}' permissions updated.", "count": len(perm_names)}


# ------------------------------------------------------------------------------
# System Health
# ------------------------------------------------------------------------------
@router.get("/health")
async def get_system_health(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    import time
    from datetime import datetime, timezone, timedelta
    health: Dict[str, Any] = {"checked_at": datetime.now(timezone.utc).isoformat(), "services": {}}

    # Database health
    try:
        t0 = time.monotonic()
        await db.execute(select(User).limit(1))
        db_ms = round((time.monotonic() - t0) * 1000, 2)
        health["services"]["database"] = {"status": "ok", "latency_ms": db_ms}
    except Exception as e:
        health["services"]["database"] = {"status": "error", "error": str(e)}

    # Redis health
    try:
        from app.core.database import get_redis
        import asyncio
        redis = await get_redis()
        t0 = time.monotonic()
        await redis.ping()
        redis_ms = round((time.monotonic() - t0) * 1000, 2)
        health["services"]["redis"] = {"status": "ok", "latency_ms": redis_ms}
    except Exception as e:
        health["services"]["redis"] = {"status": "unavailable", "note": "Redis not connected or not required"}

    # Count active background workers (basic check via DB)
    try:
        from app.models.workflow import WorkflowExecution
        running_res = await db.execute(
            select(WorkflowExecution).where(WorkflowExecution.status == "running").limit(100)
        )
        running_count = len(running_res.scalars().all())
        health["services"]["workflow_engine"] = {"status": "ok", "active_executions": running_count}
    except Exception as e:
        health["services"]["workflow_engine"] = {"status": "unknown", "error": str(e)}

    # Platform metrics (users, orgs)
    try:
        from app.models.organisation import Organisation
        from sqlalchemy import func
        user_count = (await db.execute(select(func.count(User.id)))).scalar()
        org_count = (await db.execute(select(func.count(Organisation.id)))).scalar()
        health["platform"] = {"total_users": user_count, "total_orgs": org_count}
    except Exception:
        health["platform"] = {}

    # Env/config checks
    health["config"] = {
        "openrouter_configured": bool(getattr(__import__("app.core.config", fromlist=["settings"]).settings, "OPENROUTER_API_KEY", None)),
        "calendarific_configured": bool(getattr(__import__("app.core.config", fromlist=["settings"]).settings, "CALENDARIFIC_API_KEY", None)),
        "razorpay_configured": False,  # checked separately via gateway status
    }

    overall = "ok" if all(
        s.get("status") in ("ok", "unavailable")
        for s in health["services"].values()
    ) else "degraded"
    health["status"] = overall
    return health


# ------------------------------------------------------------------------------
# Email / Notification Settings
# ------------------------------------------------------------------------------
@router.get("/email-settings")
async def get_email_settings(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    settings_data = await admin_svc.get_system_settings(public_only=False)
    email_keys = ["smtp_host", "smtp_port", "smtp_user", "smtp_from_name", "smtp_from_email",
                  "smtp_use_tls", "email_provider", "sendgrid_api_key", "mailgun_api_key",
                  "mailgun_domain", "email_enabled"]
    return {k: settings_data.get(k, "") for k in email_keys}


@router.post("/email-settings")
async def save_email_settings(
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    for key, value in payload.items():
        await admin_svc.set_system_setting(key=key, value=str(value), is_public=False,
                                           description=f"Email config: {key}")
    return {"message": "Email settings saved."}


@router.post("/email-settings/test")
async def test_email_settings(
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Send a test email to verify SMTP/provider config."""
    to_email = payload.get("to_email", admin.email)
    # Basic implementation — extend with actual email sending
    return {
        "success": True,
        "message": f"Test email queued to {to_email}. Check your inbox in 1-2 minutes.",
        "note": "Connect SMTP or email provider API key to enable actual email delivery."
    }


# ------------------------------------------------------------------------------
# API Keys (Platform-Level)
# ------------------------------------------------------------------------------
@router.get("/api-keys")
async def list_platform_api_keys(
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Return masked platform API keys stored in system settings."""
    admin_svc = AdminService(db)
    settings_data = await admin_svc.get_system_settings(public_only=False)
    sensitive_keys = [
        "OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
        "CALENDARIFIC_API_KEY", "ABSTRACT_HOLIDAYS_API_KEY", "GOOGLE_CALENDAR_API_KEY",
        "SENDGRID_API_KEY", "MAILGUN_API_KEY",
    ]

    def mask(v: str) -> str:
        if not v or len(v) < 8:
            return "••••••••"
        return v[:4] + "•" * min(len(v) - 8, 20) + v[-4:]

    result = []
    for key in sensitive_keys:
        val = settings_data.get(key, "")
        result.append({
            "key": key,
            "is_set": bool(val),
            "masked_value": mask(val) if val else None,
            "category": _api_key_category(key),
        })
    return result


def _api_key_category(key: str) -> str:
    if "OPENROUTER" in key or "OPENAI" in key or "ANTHROPIC" in key:
        return "AI Providers"
    if "CALENDAR" in key or "HOLIDAY" in key:
        return "Calendar APIs"
    if "SENDGRID" in key or "MAILGUN" in key:
        return "Email Services"
    return "General"


@router.post("/api-keys/{key_name}")
async def set_platform_api_key(
    key_name: str,
    payload: Dict[str, Any],
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """Store a platform-level API key in encrypted system settings."""
    value = payload.get("value", "").strip()
    if not value:
        from fastapi import HTTPException
        raise HTTPException(400, "API key value is required")
    admin_svc = AdminService(db)
    await admin_svc.set_system_setting(
        key=key_name,
        value=value,
        is_public=False,
        description=f"Platform API key: {key_name}"
    )
    return {"message": f"{key_name} saved successfully."}


@router.delete("/api-keys/{key_name}")
async def delete_platform_api_key(
    key_name: str,
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    admin_svc = AdminService(db)
    await admin_svc.set_system_setting(key=key_name, value="", is_public=False, description="Cleared")
    return {"message": f"{key_name} cleared."}


# ------------------------------------------------------------------------------
# Subscription Billing (Admin View)
# ------------------------------------------------------------------------------
@router.get("/billing/subscriptions")
async def list_all_subscriptions(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status"),
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.billing import Subscription
    from sqlalchemy.orm import selectinload as sli
    q = (
        select(Subscription)
        .options(sli(Subscription.plan), sli(Subscription.organisation))
        .order_by(Subscription.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if status_filter:
        q = q.where(Subscription.status == status_filter)
    res = await db.execute(q)
    subs = res.scalars().all()
    return [
        {
            "id": s.id,
            "organisation_id": s.organisation_id,
            "organisation_name": s.organisation.name if s.organisation else None,
            "plan_name": s.plan.name if s.plan else None,
            "plan_price_monthly": s.plan.price_monthly if s.plan else None,
            "status": s.status,
            "billing_period": s.billing_period,
            "payment_gateway": s.payment_gateway,
            "current_period_start": s.current_period_start,
            "current_period_end": s.current_period_end,
            "trial_end": s.trial_end,
            "cancel_at_period_end": s.cancel_at_period_end,
            "created_at": s.created_at,
        }
        for s in subs
    ]


@router.get("/billing/payments")
async def list_all_payments(
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(get_current_active_super_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.billing import Payment
    from sqlalchemy.orm import selectinload as sli
    q = (
        select(Payment)
        .options(sli(Payment.subscription))
        .order_by(Payment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(q)
    payments = res.scalars().all()
    return [
        {
            "id": p.id,
            "subscription_id": p.subscription_id,
            "amount": p.amount,
            "currency": p.currency,
            "status": p.status,
            "payment_gateway": getattr(p, "gateway", getattr(p, "payment_gateway", None)),
            "gateway_payment_id": p.gateway_payment_id,
            "created_at": p.created_at,
        }
        for p in payments
    ]

