from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class OrganisationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = None
    description: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    timezone: str = "UTC"
    locale: str = "en"
    brand_identity: Optional[Dict[str, Any]] = None

class OrganisationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    brand_identity: Optional[Dict[str, Any]] = None
    publishing_paused: Optional[bool] = None
    workflows_paused: Optional[bool] = None
    automation_disabled: Optional[bool] = None

class OrganisationResponse(BaseModel):
    id: str
    name: str
    slug: str
    logo_url: Optional[str]
    description: Optional[str]
    website: Optional[str]
    industry: Optional[str]
    timezone: str
    locale: str
    is_active: bool
    brand_identity: Optional[Dict[str, Any]]
    publishing_paused: bool
    workflows_paused: bool
    automation_disabled: bool
    user_role: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MemberInviteRequest(BaseModel):
    email: EmailStr
    role_id: str

class MemberResponse(BaseModel):
    id: str
    organisation_id: str
    user_id: str
    role_id: str
    role_name: str
    is_active: bool
    first_name: str
    last_name: Optional[str]
    email: str
    avatar_url: Optional[str]
    created_at: datetime

class RoleCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    permission_ids: List[str]

class RoleResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    is_system: bool
    permissions: List[str]

class PermissionResponse(BaseModel):
    id: str
    name: str
    module: str
    description: Optional[str]

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    member_count: int = 0
