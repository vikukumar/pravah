from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import ConflictException
from app.models.organisation import Permission, Role, RolePermission
from app.models.user import User

DEFAULT_PERMISSIONS = [
    # Organisation
    ("organisation.view", "organisation", "View organisation settings and details"),
    ("organisation.update", "organisation", "Update organisation configuration and branding"),
    ("organisation.delete", "organisation", "Delete organisation"),
    
    # Members & Roles
    ("member.view", "member", "View organisation team members"),
    ("member.invite", "member", "Invite new members"),
    ("member.remove", "member", "Remove organisation members"),
    ("role.manage", "role", "Create and assign custom roles"),
    
    # Social Accounts
    ("social.view", "social", "View connected social accounts and pages"),
    ("social.connect", "social", "Connect new social media accounts"),
    ("social.disconnect", "social", "Disconnect social media accounts"),
    ("social.sync", "social", "Trigger manual profile intelligence synchronization"),
    
    # Content & Calendar
    ("content.view", "content", "View content, drafts, and calendar items"),
    ("content.create", "content", "Create posts and drafts"),
    ("content.update", "content", "Edit existing content and schedules"),
    ("content.delete", "content", "Delete content items"),
    ("content.approve", "content", "Approve or reject content reviews"),
    ("content.publish", "content", "Publish posts immediately to social networks"),
    
    # AI Studio
    ("ai.generate_text", "ai", "Generate AI social media content"),
    ("ai.generate_image", "ai", "Generate AI images"),
    ("ai.custom_provider", "ai", "Configure custom AI providers"),
    
    # Workflows
    ("workflow.view", "workflow", "View visual automation workflows"),
    ("workflow.create", "workflow", "Create and edit automation workflows"),
    ("workflow.edit", "workflow", "Edit existing automation workflows"),
    ("workflow.execute", "workflow", "Execute automation workflows"),
    ("workflow.publish", "workflow", "Publish workflows to production"),
    ("workflow.delete", "workflow", "Delete automation workflows"),
    
    # Campaigns & Media
    ("campaign.manage", "campaign", "Create and manage marketing campaigns"),
    ("media.manage", "media", "Upload, search, and delete media library assets"),
    
    # Analytics
    ("analytics.view", "analytics", "View post, account, and campaign analytics"),
    ("analytics.export", "analytics", "Export analytical reports"),
    
    # Billing
    ("billing.view", "billing", "View active plan and invoice history"),
    ("billing.manage", "billing", "Upgrade, downgrade, and manage payment methods"),
    
    # Settings & Audit
    ("settings.manage", "settings", "Manage organisation security and integration settings"),
    ("audit.view", "audit", "View organisation audit logs"),
]

class RBACService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_system_permissions_and_roles(self):
        # Seed permissions
        for perm_name, module, desc in DEFAULT_PERMISSIONS:
            res = await self.db.execute(select(Permission).where(Permission.name == perm_name))
            if not res.scalar_one_or_none():
                perm = Permission(name=perm_name, module=module, description=desc)
                self.db.add(perm)
        await self.db.flush()

        # Load all permissions
        all_perms_res = await self.db.execute(select(Permission))
        all_perms = {p.name: p for p in all_perms_res.scalars().all()}

        # Seed standard system roles
        roles_spec = [
            ("super_admin", "Super Administrator", "Full platform access across all organisations", list(all_perms.keys())),
            ("org_owner", "Organisation Owner", "Unrestricted access within organisation", list(all_perms.keys())),
            ("org_admin", "Organisation Admin", "Manage members, billing, content and settings", [
                k for k in all_perms.keys() if k != "organisation.delete"
            ]),
            ("manager", "Content Manager", "Create, edit, approve, schedule, and publish content", [
                "social.view", "social.connect", "social.disconnect", "social.sync",
                "content.view", "content.create", "content.update", "content.delete",
                "content.approve", "content.publish",
                "ai.generate_text", "ai.generate_image", "ai.custom_provider",
                "workflow.view", "workflow.create", "workflow.edit", "workflow.execute",
                "workflow.publish", "workflow.delete",
                "campaign.manage", "media.manage",
                "analytics.view", "analytics.export",
                "billing.view", "audit.view",
            ]),
            ("editor", "Editor", "Create and edit drafts requiring approval", [
                "social.view", "content.view", "content.create", "content.update",
                "ai.generate_text", "ai.generate_image", "media.manage", "analytics.view"
            ]),
            ("publisher", "Publisher", "Approve and publish approved content", [
                "social.view", "content.view", "content.approve", "content.publish", "analytics.view"
            ]),
            ("analyst", "Analyst", "Read-only access to analytics, posts, and reports", [
                "social.view", "content.view", "analytics.view", "analytics.export"
            ]),
            ("user", "Team Member", "Basic read access", [
                "social.view", "content.view", "media.manage"
            ]),
        ]

        for role_name, display_name, desc, perm_names in roles_spec:
            role_res = await self.db.execute(
                select(Role).where(Role.name == role_name, Role.organisation_id == None)
            )
            role = role_res.scalar_one_or_none()
            if not role:
                role = Role(
                    name=role_name,
                    display_name=display_name,
                    description=desc,
                    is_system=True,
                )
                self.db.add(role)
                await self.db.flush()

                # Add RolePermissions
                for pname in perm_names:
                    if pname in all_perms:
                        rp = RolePermission(role_id=role.id, permission_id=all_perms[pname].id)
                        self.db.add(rp)

        await self.db.commit()

    async def list_permissions(self) -> List[Permission]:
        res = await self.db.execute(select(Permission).order_by(Permission.module.asc()))
        return list(res.scalars().all())

    async def list_roles(self, org_id: Optional[str] = None) -> List[Role]:
        query = (
            select(Role)
            .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
            .where((Role.organisation_id == org_id) | (Role.organisation_id == None))
            .order_by(Role.is_system.desc(), Role.name.asc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create_custom_role(
        self,
        org_id: str,
        name: str,
        display_name: str,
        description: Optional[str],
        permission_ids: List[str],
        actor: User
    ) -> Role:
        existing = await self.db.execute(
            select(Role).where(Role.organisation_id == org_id, Role.name == name)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("A role with this name already exists in this organisation.")

        role = Role(
            organisation_id=org_id,
            name=name.lower().replace(" ", "_"),
            display_name=display_name,
            description=description,
            is_system=False,
        )
        self.db.add(role)
        await self.db.flush()

        for pid in permission_ids:
            rp = RolePermission(role_id=role.id, permission_id=pid)
            self.db.add(rp)

        await self.db.commit()
        await self.db.refresh(role)
        return role
