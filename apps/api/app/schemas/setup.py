from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class SuperAdminSetup(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)
    confirm_password: str

class SystemConfigSetup(BaseModel):
    app_name: str = "PRAVAH"
    app_url: str = "http://localhost:3000"
    timezone: str = "UTC"
    locale: str = "en"
    currency: str = "USD"
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None

class SetupRequest(BaseModel):
    system: SystemConfigSetup
    super_admin: SuperAdminSetup

class SetupStatusResponse(BaseModel):
    is_initialized: bool
    app_name: str
    version: str
