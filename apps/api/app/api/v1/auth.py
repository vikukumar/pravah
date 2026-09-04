from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import PravahException
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    OTPVerifyRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    TwoFactorSetupResponse,
    TwoFactorVerifyRequest,
)
from app.services.auth_service import AuthService
from app.services.organisation_service import OrganisationService

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise PravahException("Passwords do not match")

    auth_svc = AuthService(db)
    org_svc = OrganisationService(db)

    user = await auth_svc.register_user(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        phone=payload.phone,
        auto_verify=False,
    )

    # Automatically create user's first personal workspace
    org = await org_svc.create_organisation(
        name=f"{user.first_name}'s Brand",
        user=user,
    )

    # Generate initial email verification OTP
    otp_code = await auth_svc.generate_email_otp(user, otp_type="verify_email")

    tokens = await auth_svc.issue_tokens(user)
    return {
        "message": "User registered successfully. Please verify your email with the OTP sent.",
        "tokens": tokens,
        "organisation_id": org.id,
        "debug_otp": otp_code if settings.DEBUG else None,
    }

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    auth_svc = AuthService(db)
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")

    user, auth_state = await auth_svc.authenticate_user(
        email=payload.email,
        password=payload.password,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    if auth_state and auth_state.get("requires_two_factor"):
        if not payload.two_factor_code:
            return TokenResponse(
                access_token="",
                refresh_token="",
                expires_in=0,
                user={"id": user.id, "email": user.email},
                requires_two_factor=True,
            )
        # Verify 2FA code
        await auth_svc.verify_two_factor_login(user, payload.two_factor_code)

    tokens = await auth_svc.issue_tokens(user)

    # Set secure HttpOnly cookie for session
    response.set_cookie(
        key="pravah_token",
        value=tokens["access_token"],
        httponly=True,
        secure=(settings.ENVIRONMENT == "production"),
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=tokens["expires_in"],
        user=tokens["user"],
    )

@router.post("/verify-otp")
async def verify_otp(payload: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    auth_svc = AuthService(db)
    user = await auth_svc.verify_otp(payload.email, payload.code, payload.otp_type)
    tokens = await auth_svc.issue_tokens(user)
    return {
        "message": "Verification successful.",
        "tokens": tokens,
    }

@router.post("/resend-otp")
async def resend_otp(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    auth_svc = AuthService(db)
    # Check user
    from sqlalchemy import select
    res = await db.execute(select(User).where(User.email == payload.email.lower().strip()))
    user = res.scalar_one_or_none()
    if user:
        otp_code = await auth_svc.generate_email_otp(user, otp_type="verify_email")
        return {
            "message": "OTP resent successfully.",
            "debug_otp": otp_code if settings.DEBUG else None,
        }
    return {"message": "If this email is registered, an OTP has been sent."}

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    auth_svc = AuthService(db)
    token = await auth_svc.create_password_reset_token(payload.email)
    return {
        "message": "If your email is registered, a password reset link has been dispatched.",
        "reset_token": token if settings.DEBUG else None,
    }

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise PravahException("Passwords do not match")
    auth_svc = AuthService(db)
    user = await auth_svc.reset_password(payload.token, payload.password)
    return {"message": "Password reset successfully. Please login with your new password."}

@router.get("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_svc = AuthService(db)
    data = await auth_svc.setup_two_factor(current_user)
    return TwoFactorSetupResponse(**data)

@router.post("/2fa/verify")
async def verify_two_factor(
    payload: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_svc = AuthService(db)
    await auth_svc.verify_and_enable_two_factor(current_user, payload.code)
    return {"message": "Two-factor authentication successfully enabled."}

@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_svc = AuthService(db)
    sessions = await auth_svc.get_user_sessions(current_user.id)
    return [
        {
            "id": s.id,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "device_info": s.device_info,
            "created_at": s.created_at,
            "last_activity_at": s.last_activity_at,
        }
        for s in sessions
    ]

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_svc = AuthService(db)
    await auth_svc.revoke_session(current_user.id, session_id)
    return {"message": "Session revoked."}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="pravah_token")
    return {"message": "Logged out successfully."}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "firstName": current_user.first_name,
        "middleName": current_user.middle_name,
        "lastName": current_user.last_name,
        "phone": current_user.phone,
        "avatarUrl": current_user.avatar_url,
        "isSuperAdmin": current_user.is_super_admin,
        "isActive": current_user.is_active,
        "isVerified": current_user.is_verified,
        "twoFactorEnabled": current_user.two_factor_enabled,
        "createdAt": current_user.created_at,
    }
