import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel

class Organisation(BaseModel):
    __tablename__ = "organisations"

    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    logo_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True)
    timezone = Column(String(100), default="UTC", nullable=False)
    locale = Column(String(20), default="en", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Stored brand profile and content guidelines (AI context)
    brand_identity = Column(JSON, nullable=True)
    
    # Emergency controls
    publishing_paused = Column(Boolean, default=False, nullable=False)
    workflows_paused = Column(Boolean, default=False, nullable=False)
    automation_disabled = Column(Boolean, default=False, nullable=False)

    # Relationships
    members = relationship("OrganisationMember", back_populates="organisation", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="organisation", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="organisation", cascade="all, delete-orphan")
    social_accounts = relationship("SocialAccount", back_populates="organisation", cascade="all, delete-orphan")
    content_items = relationship("Content", back_populates="organisation", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="organisation", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="organisation", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="organisation", uselist=False, cascade="all, delete-orphan")
    invitations = relationship("OrganisationInvitation", back_populates="organisation", cascade="all, delete-orphan")
    dashboard_layouts = relationship("Dashboard", back_populates="organisation", cascade="all, delete-orphan")

class OrganisationMember(BaseModel):
    __tablename__ = "organisation_members"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    organisation = relationship("Organisation", back_populates="members")
    user = relationship("User", back_populates="memberships")
    role = relationship("Role")
    team = relationship("Team", back_populates="members")

    __table_args__ = (
        Index("ix_org_member_unique", "organisation_id", "user_id", unique=True),
    )

class Team(BaseModel):
    __tablename__ = "teams"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    organisation = relationship("Organisation", back_populates="teams")
    members = relationship("OrganisationMember", back_populates="team")

class Role(BaseModel):
    __tablename__ = "roles"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=True, index=True) # Null for system/platform roles
    name = Column(String(100), nullable=False) # e.g. super_admin, org_owner, manager, editor, publisher, analyst
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)

    organisation = relationship("Organisation", back_populates="roles")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

class Permission(BaseModel):
    __tablename__ = "permissions"

    name = Column(String(100), unique=True, index=True, nullable=False) # e.g. content.create, content.publish
    module = Column(String(50), nullable=False, index=True) # content, social, workflow, billing, admin
    description = Column(Text, nullable=True)

    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

class RolePermission(BaseModel):
    __tablename__ = "role_permissions"

    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    __table_args__ = (
        Index("ix_role_permission_unique", "role_id", "permission_id", unique=True),
    )

class OrganisationInvitation(BaseModel):
    __tablename__ = "organisation_invitations"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    inviter_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_accepted = Column(Boolean, default=False, nullable=False)

    organisation = relationship("Organisation", back_populates="invitations")
