from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ConflictException, PravahException
from app.models.system import AuditLog, SystemSetting
from app.models.user import User
from app.schemas.setup import SetupRequest, SetupStatusResponse
from app.services.auth_service import AuthService
from app.services.billing_service import BillingService
from app.services.cms_service import CMSService
from app.services.organisation_service import OrganisationService
from app.services.rbac_service import RBACService
from app.services.social_service import SocialService

router = APIRouter()

@router.get("/status", response_model=SetupStatusResponse)
async def get_setup_status(db: AsyncSession = Depends(get_db)):
    # Check if a super admin user exists in DB
    query = select(func.count(User.id)).where(User.is_super_admin == True)
    res = await db.execute(query)
    super_admin_count = res.scalar() or 0

    is_init = super_admin_count > 0
    return SetupStatusResponse(
        is_initialized=is_init,
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
    )

@router.post("/initialize", status_code=status.HTTP_201_CREATED)
async def initialize_platform(payload: SetupRequest, db: AsyncSession = Depends(get_db)):
    # Prevent concurrent or repeated initialization
    query = select(func.count(User.id)).where(User.is_super_admin == True)
    res = await db.execute(query)
    if (res.scalar() or 0) > 0:
        raise ConflictException("Platform is already initialized. Please login with Super Admin credentials.")

    if payload.super_admin.password != payload.super_admin.confirm_password:
        raise PravahException("Passwords do not match")

    auth_svc = AuthService(db)
    rbac_svc = RBACService(db)
    billing_svc = BillingService(db)
    social_svc = SocialService(db)
    cms_svc = CMSService(db)
    org_svc = OrganisationService(db)

    # 1. Seed RBAC Permissions & Roles
    await rbac_svc.seed_system_permissions_and_roles()

    # 2. Seed Billing Plans (including Free Plan)
    await billing_svc.seed_plans()

    # 3. Seed Social Providers & CMS Legal Pages
    await social_svc.seed_providers()
    await cms_svc.seed_system_pages()

    # 4. Create Super Admin User
    super_admin = await auth_svc.register_user(
        email=payload.super_admin.email,
        password=payload.super_admin.password,
        first_name=payload.super_admin.first_name,
        middle_name=payload.super_admin.middle_name,
        last_name=payload.super_admin.last_name,
        phone=payload.super_admin.phone,
        is_super_admin=True,
        auto_verify=True,
    )

    # 5. Create Default Primary Organisation for Super Admin
    default_org = await org_svc.create_organisation(
        name=f"{payload.super_admin.first_name}'s Workspace",
        user=super_admin,
        timezone_str=payload.system.timezone or "UTC",
        locale=payload.system.locale or "en",
    )

    # 6. Save System Settings
    sys_setting = SystemSetting(
        key="platform_config",
        value={
            "app_name": payload.system.app_name,
            "app_url": payload.system.app_url,
            "timezone": payload.system.timezone,
            "locale": payload.system.locale,
            "currency": payload.system.currency,
        },
        is_public=True,
        description="Core platform configuration",
    )
    db.add(sys_setting)

    # 7. Audit log
    audit = AuditLog(
        actor_id=super_admin.id,
        actor_email=super_admin.email,
        action="platform.setup_completed",
        target_type="system",
        result="success",
        details={"super_admin_email": super_admin.email, "org_id": default_org.id},
    )
    db.add(audit)
    await db.commit()

    # Issue initial tokens
    tokens = await auth_svc.issue_tokens(super_admin)
    return {
        "message": "PRAVAH platform initialized successfully.",
        "tokens": tokens,
        "default_organisation_id": default_org.id,
    }

@router.post("/reset")
async def reset_platform_setup(db: AsyncSession = Depends(get_db)):
    """Allows resetting the setup state for initial setup testing."""
    from app.core.database import Base, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    return {"message": "Platform reset successfully. You may now run the Setup Wizard at /setup."}

