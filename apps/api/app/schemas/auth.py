from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)
    confirm_password: str
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = None
    last_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    otp_code: Optional[str] = None
    two_factor_code: Optional[str] = None
    remember_me: bool = False

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    requires_two_factor: bool = False
    requires_verification: bool = False

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    code: str
    otp_type: str = "verify_email" # verify_email, login, reset_password

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)
    confirm_password: str

class MagicLinkRequest(BaseModel):
    email: EmailStr

class MagicLinkVerifyRequest(BaseModel):
    token: str

class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code_url: str
    otpauth_url: str
    recovery_codes: List[str]

class TwoFactorVerifyRequest(BaseModel):
    code: str

class SessionResponse(BaseModel):
    id: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[str]
    created_at: datetime
    last_activity_at: datetime
    is_current: bool = False
