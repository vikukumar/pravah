from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import TenantContext, get_current_user, get_tenant_context, require_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.organisation import (
    MemberInviteRequest,
    MemberResponse,
    OrganisationCreate,
    OrganisationResponse,
    OrganisationUpdate,
    RoleCreate,
    RoleResponse,
)
from app.services.organisation_service import OrganisationService
from app.services.rbac_service import RBACService

router = APIRouter()

@router.get("", response_model=List[OrganisationResponse])
async def list_user_organisations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_svc = OrganisationService(db)
    orgs = await org_svc.get_user_organisations(current_user)
    return [OrganisationResponse(**o) for o in orgs]

@router.post("", response_model=OrganisationResponse, status_code=status.HTTP_201_CREATED)
async def create_organisation(
    payload: OrganisationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_svc = OrganisationService(db)
    org = await org_svc.create_organisation(
        name=payload.name,
        user=current_user,
        slug=payload.slug,
        description=payload.description,
        industry=payload.industry,
        website=payload.website,
        timezone_str=payload.timezone,
        locale=payload.locale,
        brand_identity=payload.brand_identity,
    )
    d = org.to_dict()
    d["user_role"] = "org_owner"
    return OrganisationResponse(**d)

@router.get("/active", response_model=OrganisationResponse)
async def get_active_organisation(
    tenant: TenantContext = Depends(get_tenant_context)
):
    d = tenant.organisation.to_dict()
    d["user_role"] = tenant.role.name
    return OrganisationResponse(**d)

@router.patch("/active", response_model=OrganisationResponse)
async def update_active_organisation(
    payload: OrganisationUpdate,
    tenant: TenantContext = Depends(require_permission("organisation.update")),
    db: AsyncSession = Depends(get_db)
):
    org_svc = OrganisationService(db)
    updated = await org_svc.update_organisation(
        org_id=tenant.organisation.id,
        updates=payload.model_dump(exclude_unset=True),
        actor=tenant.user,
    )
    d = updated.to_dict()
    d["user_role"] = tenant.role.name
    return OrganisationResponse(**d)

@router.get("/members", response_model=List[MemberResponse])
async def list_members(
    tenant: TenantContext = Depends(require_permission("member.view")),
    db: AsyncSession = Depends(get_db)
):
    org_svc = OrganisationService(db)
    members = await org_svc.list_members(tenant.organisation.id)
    return [MemberResponse(**m) for m in members]

@router.post("/members/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(
    payload: MemberInviteRequest,
    tenant: TenantContext = Depends(require_permission("member.invite")),
    db: AsyncSession = Depends(get_db)
):
    org_svc = OrganisationService(db)
    invitation = await org_svc.invite_member(
        org_id=tenant.organisation.id,
        email=payload.email,
        role_id=payload.role_id,
        inviter=tenant.user,
    )
    return {
        "message": f"Invitation dispatched to {payload.email}",
        "token": invitation.token,
    }

@router.delete("/members/{member_id}")
async def remove_member(
    member_id: str,
    tenant: TenantContext = Depends(require_permission("member.remove")),
    db: AsyncSession = Depends(get_db)
):
    org_svc = OrganisationService(db)
    await org_svc.remove_member(tenant.organisation.id, member_id, tenant.user)
    return {"message": "Member removed successfully."}

@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    tenant: TenantContext = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    rbac_svc = RBACService(db)
    roles = await rbac_svc.list_roles(tenant.organisation.id)
    return [
        RoleResponse(
            id=r.id,
            name=r.name,
            display_name=r.display_name,
            description=r.description,
            is_system=r.is_system,
            permissions=[rp.permission.name for rp in r.role_permissions if rp.permission],
        )
        for r in roles
    ]

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_role(
    payload: RoleCreate,
    tenant: TenantContext = Depends(require_permission("role.manage")),
    db: AsyncSession = Depends(get_db)
):
    rbac_svc = RBACService(db)
    role = await rbac_svc.create_custom_role(
        org_id=tenant.organisation.id,
        name=payload.name,
        display_name=payload.display_name,
        description=payload.description,
        permission_ids=payload.permission_ids,
        actor=tenant.user,
    )
    return RoleResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        is_system=role.is_system,
        permissions=[],
    )
