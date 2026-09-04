from typing import Callable, List, Optional
from fastapi import Cookie, Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security import decode_token
from app.models.billing import Plan, Subscription
from app.models.organisation import Organisation, OrganisationMember, Role, RolePermission
from app.models.user import User

security_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    token_cookie: Optional[str] = Cookie(default=None, alias="pravah_token"),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = None
    if auth_header and auth_header.credentials:
        token = auth_header.credentials
    elif token_cookie:
        token = token_cookie
        
    if not token:
        raise UnauthorizedException("Authentication token missing")
        
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedException("Invalid or expired authentication token")
        
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Malformed token payload")
        
    query = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise UnauthorizedException("User not found or inactive")
        
    return user

async def get_current_active_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_super_admin:
        raise ForbiddenException("Super administrator access required")
    return current_user

class TenantContext:
    def __init__(
        self,
        user: User,
        organisation: Organisation,
        member: OrganisationMember,
        role: Role,
        permissions: List[str],
        subscription: Optional[Subscription] = None
    ):
        self.user = user
        self.organisation = organisation
        self.member = member
        self.role = role
        self.permissions = permissions
        self.subscription = subscription

    def has_permission(self, permission_name: str) -> bool:
        if self.user.is_super_admin or self.role.name in ["org_owner", "super_admin"]:
            return True
        return permission_name in self.permissions

async def get_tenant_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    org_id_header: Optional[str] = Header(None, alias="X-Organisation-Id"),
    org_id_query: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> TenantContext:
    org_id = org_id_header or org_id_query
    
    # If no org header is passed, check if user has a membership and pick the first active one
    if not org_id:
        member_query = (
            select(OrganisationMember)
            .where(OrganisationMember.user_id == current_user.id, OrganisationMember.is_active == True)
            .order_by(OrganisationMember.created_at.asc())
        )
        res = await db.execute(member_query)
        first_member = res.scalars().first()
        if first_member:
            org_id = first_member.organisation_id
        else:
            # If user is super admin and no org exists, allow virtual or raise error
            if current_user.is_super_admin:
                # Find any organization or raise
                all_orgs_query = select(Organisation).limit(1)
                all_orgs_res = await db.execute(all_orgs_query)
                first_org = all_orgs_res.scalar_one_or_none()
                if first_org:
                    org_id = first_org.id
                    
    if not org_id:
        raise NotFoundException("No active organisation context found. Please select or create an organisation.")

    # Validate Organisation existence and active status
    org_query = (
        select(Organisation)
        .options(selectinload(Organisation.subscription).selectinload(Subscription.plan).selectinload(Plan.features))
        .where(Organisation.id == org_id, Organisation.is_active == True)
    )
    org_res = await db.execute(org_query)
    organisation = org_res.scalar_one_or_none()
    
    if not organisation:
        raise NotFoundException("Organisation not found or inactive")
        
    # Validate membership
    member_query = (
        select(OrganisationMember)
        .options(
            selectinload(OrganisationMember.role)
            .selectinload(Role.role_permissions)
            .selectinload(RolePermission.permission)
        )
        .where(
            OrganisationMember.organisation_id == org_id,
            OrganisationMember.user_id == current_user.id,
            OrganisationMember.is_active == True
        )
    )
    member_res = await db.execute(member_query)
    member = member_res.scalar_one_or_none()
    
    if not member and not current_user.is_super_admin:
        raise ForbiddenException("You do not have access to this organisation")
        
    # If super admin without membership, assign synthetic super admin role
    if not member and current_user.is_super_admin:
        # Create virtual role/permissions
        role = Role(name="super_admin", display_name="Super Administrator", is_system=True)
        permissions = ["*"]
        return TenantContext(
            user=current_user,
            organisation=organisation,
            member=None, # type: ignore
            role=role,
            permissions=permissions,
            subscription=organisation.subscription
        )
        
    role = member.role
    permissions = [rp.permission.name for rp in role.role_permissions if rp.permission]
    
    return TenantContext(
        user=current_user,
        organisation=organisation,
        member=member,
        role=role,
        permissions=permissions,
        subscription=organisation.subscription
    )

def require_permission(permission_name: str) -> Callable:
    async def permission_checker(
        tenant: TenantContext = Depends(get_tenant_context)
    ) -> TenantContext:
        if not tenant.has_permission(permission_name):
            raise ForbiddenException(f"Permission denied: Requires '{permission_name}'")
        return tenant
    return permission_checker
