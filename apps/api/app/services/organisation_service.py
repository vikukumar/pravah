import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import generate_random_token
from app.models.billing import Plan, Subscription
from app.models.organisation import (
    Organisation,
    OrganisationInvitation,
    OrganisationMember,
    Role,
)
from app.models.system import AuditLog
from app.models.user import User

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

class OrganisationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_organisation(
        self,
        name: str,
        user: User,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        industry: Optional[str] = None,
        website: Optional[str] = None,
        timezone_str: str = "UTC",
        locale: str = "en",
        brand_identity: Optional[Dict[str, Any]] = None,
    ) -> Organisation:
        org_slug = slugify(slug or name)
        # Check uniqueness of slug
        existing = await self.db.execute(select(Organisation).where(Organisation.slug == org_slug))
        if existing.scalar_one_or_none():
            org_slug = f"{org_slug}-{uuid.uuid4().hex[:6]}"

        org = Organisation(
            name=name.strip(),
            slug=org_slug,
            description=description,
            industry=industry,
            website=website,
            timezone=timezone_str,
            locale=locale,
            brand_identity=brand_identity or {},
            is_active=True,
        )
        self.db.add(org)
        await self.db.flush()

        # Find or create Org Owner Role
        role_res = await self.db.execute(
            select(Role).where(Role.name == "org_owner", Role.organisation_id == None)
        )
        owner_role = role_res.scalar_one_or_none()
        if not owner_role:
            owner_role = Role(
                name="org_owner",
                display_name="Organisation Owner",
                description="Unrestricted control of organisation resources",
                is_system=True,
            )
            self.db.add(owner_role)
            await self.db.flush()

        # Assign user as Org Owner
        member = OrganisationMember(
            organisation_id=org.id,
            user_id=user.id,
            role_id=owner_role.id,
            is_active=True,
        )
        self.db.add(member)

        # Attach default Free plan or initial plan
        free_plan_res = await self.db.execute(select(Plan).where(Plan.is_free == True))
        free_plan = free_plan_res.scalar_one_or_none()
        if free_plan:
            subscription = Subscription(
                organisation_id=org.id,
                plan_id=free_plan.id,
                status="active",
                billing_period="monthly",
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc) + timedelta(days=free_plan.trial_days or 30),
                trial_end=datetime.now(timezone.utc) + timedelta(days=free_plan.trial_days or 30),
            )
            self.db.add(subscription)

        # Audit
        audit = AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            organisation_id=org.id,
            action="organisation.created",
            target_type="organisation",
            target_id=org.id,
            result="success",
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def get_user_organisations(self, user: User) -> List[Dict[str, Any]]:
        query = (
            select(OrganisationMember)
            .options(selectinload(OrganisationMember.organisation), selectinload(OrganisationMember.role))
            .where(OrganisationMember.user_id == user.id, OrganisationMember.is_active == True)
        )
        res = await self.db.execute(query)
        memberships = res.scalars().all()
        
        result = []
        for m in memberships:
            if m.organisation and m.organisation.is_active:
                d = m.organisation.to_dict()
                d["user_role"] = m.role.name if m.role else "user"
                result.append(d)
                
        # If super admin, also include all other active organisations
        if user.is_super_admin:
            existing_ids = {m.organisation_id for m in memberships}
            all_orgs_query = select(Organisation).where(Organisation.is_active == True)
            all_res = await self.db.execute(all_orgs_query)
            all_orgs = all_res.scalars().all()
            for org in all_orgs:
                if org.id not in existing_ids:
                    d = org.to_dict()
                    d["user_role"] = "super_admin"
                    result.append(d)
                    
        return result

    async def update_organisation(
        self,
        org_id: str,
        updates: Dict[str, Any],
        actor: User
    ) -> Organisation:
        query = select(Organisation).where(Organisation.id == org_id)
        res = await self.db.execute(query)
        org = res.scalar_one_or_none()
        if not org:
            raise NotFoundException("Organisation not found")

        for key, val in updates.items():
            if hasattr(org, key) and val is not None:
                setattr(org, key, val)

        audit = AuditLog(
            actor_id=actor.id,
            actor_email=actor.email,
            organisation_id=org.id,
            action="organisation.updated",
            target_type="organisation",
            target_id=org.id,
            result="success",
            details={k: str(v) for k, v in updates.items() if v is not None},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(org)
        return org

    async def invite_member(
        self,
        org_id: str,
        email: str,
        role_id: str,
        inviter: User
    ) -> OrganisationInvitation:
        # Check if user is already a member
        user_query = (
            select(User)
            .join(OrganisationMember, OrganisationMember.user_id == User.id)
            .where(OrganisationMember.organisation_id == org_id, User.email == email.lower().strip())
        )
        existing_member = await self.db.execute(user_query)
        if existing_member.scalar_one_or_none():
            raise ConflictException("User is already a member of this organisation.")

        token = generate_random_token(48)
        invitation = OrganisationInvitation(
            organisation_id=org_id,
            email=email.lower().strip(),
            role_id=role_id,
            token=token,
            inviter_id=inviter.id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_accepted=False,
        )
        self.db.add(invitation)

        audit = AuditLog(
            actor_id=inviter.id,
            actor_email=inviter.email,
            organisation_id=org_id,
            action="member.invited",
            target_type="invitation",
            result="success",
            details={"email": email, "role_id": role_id},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(invitation)
        return invitation

    async def accept_invitation(self, token: str, user: User) -> OrganisationMember:
        query = (
            select(OrganisationInvitation)
            .where(
                OrganisationInvitation.token == token,
                OrganisationInvitation.is_accepted == False,
                OrganisationInvitation.expires_at >= datetime.now(timezone.utc),
            )
        )
        res = await self.db.execute(query)
        invitation = res.scalar_one_or_none()
        if not invitation:
            raise NotFoundException("Invalid or expired invitation link")

        member = OrganisationMember(
            organisation_id=invitation.organisation_id,
            user_id=user.id,
            role_id=invitation.role_id,
            is_active=True,
        )
        self.db.add(member)
        invitation.is_accepted = True

        audit = AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            organisation_id=invitation.organisation_id,
            action="invitation.accepted",
            target_type="organisation_member",
            result="success",
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def list_members(self, org_id: str) -> List[Dict[str, Any]]:
        query = (
            select(OrganisationMember)
            .options(selectinload(OrganisationMember.user), selectinload(OrganisationMember.role))
            .where(OrganisationMember.organisation_id == org_id)
        )
        res = await self.db.execute(query)
        members = res.scalars().all()

        return [
            {
                "id": m.id,
                "organisation_id": m.organisation_id,
                "user_id": m.user_id,
                "role_id": m.role_id,
                "role_name": m.role.name if m.role else "user",
                "is_active": m.is_active,
                "first_name": m.user.first_name,
                "last_name": m.user.last_name,
                "email": m.user.email,
                "avatar_url": m.user.avatar_url,
                "created_at": m.created_at,
            }
            for m in members
        ]

    async def remove_member(self, org_id: str, member_id: str, actor: User):
        query = select(OrganisationMember).where(OrganisationMember.id == member_id, OrganisationMember.organisation_id == org_id)
        res = await self.db.execute(query)
        member = res.scalar_one_or_none()
        if not member:
            raise NotFoundException("Member not found")

        await self.db.delete(member)
        audit = AuditLog(
            actor_id=actor.id,
            actor_email=actor.email,
            organisation_id=org_id,
            action="member.removed",
            target_type="organisation_member",
            target_id=member_id,
            result="success",
        )
        self.db.add(audit)
        await self.db.commit()
