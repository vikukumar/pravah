import pyotp
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.encryption import decrypt_secret, encrypt_secret
from app.core.exceptions import ConflictException, NotFoundException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    generate_random_token,
    generate_recovery_codes,
    get_password_hash,
    verify_password,
)
from app.models.system import AuditLog, NotificationPreference
from app.models.user import (
    OTP,
    RecoveryCode,
    Session,
    TwoFactorCredential,
    User,
    UserCredential,
    VerificationToken,
)

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        middle_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        is_super_admin: bool = False,
        auto_verify: bool = False,
    ) -> User:
        # Check if email exists
        existing = await self.db.execute(select(User).where(User.email == email.lower().strip()))
        if existing.scalar_one_or_none():
            raise ConflictException("A user with this email address already exists.")

        user = User(
            email=email.lower().strip(),
            phone=phone,
            first_name=first_name.strip(),
            middle_name=middle_name.strip() if middle_name else None,
            last_name=last_name.strip() if last_name else None,
            is_super_admin=is_super_admin,
            is_active=True,
            is_verified=auto_verify,
            two_factor_enabled=False,
        )
        self.db.add(user)
        await self.db.flush()

        credential = UserCredential(
            user_id=user.id,
            password_hash=get_password_hash(password),
            is_active=True,
        )
        self.db.add(credential)

        # Default notification preferences
        notif_pref = NotificationPreference(
            user_id=user.id,
            email_publishing_success=True,
            email_publishing_failure=True,
            email_content_approval=True,
            email_workflow_failure=True,
            email_security_alerts=True,
            email_billing_updates=True,
            in_app_all=True,
        )
        self.db.add(notif_pref)

        # Audit log
        audit = AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            action="user.registered",
            target_type="user",
            target_id=user.id,
            result="success",
            details={"is_super_admin": is_super_admin, "auto_verify": auto_verify},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[Dict[str, Any]]]:
        query = (
            select(User)
            .options(selectinload(User.credentials), selectinload(User.two_factor))
            .where(User.email == email.lower().strip())
        )
        res = await self.db.execute(query)
        user = res.scalar_one_or_none()

        if not user:
            # Audit failed login
            audit = AuditLog(
                actor_email=email,
                action="user.login_failed",
                target_type="user",
                ip_address=ip_address,
                user_agent=user_agent,
                result="failure",
                details={"reason": "User not found"},
            )
            self.db.add(audit)
            await self.db.commit()
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Your account is disabled. Please contact support.")

        # Check password against active credentials
        valid_password = False
        for cred in user.credentials:
            if cred.is_active and verify_password(password, cred.password_hash):
                valid_password = True
                break

        if not valid_password:
            audit = AuditLog(
                actor_id=user.id,
                actor_email=user.email,
                action="user.login_failed",
                target_type="user",
                target_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                result="failure",
                details={"reason": "Invalid password"},
            )
            self.db.add(audit)
            await self.db.commit()
            raise UnauthorizedException("Invalid email or password")

        # Check if 2FA is required
        if user.two_factor_enabled:
            return user, {"requires_two_factor": True}

        # Check if email verification is required
        if not user.is_verified and not user.is_super_admin:
            return user, {"requires_verification": True}

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        
        # Create session
        session_token = generate_random_token(48)
        session = Session(
            user_id=user.id,
            token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
            is_revoked=False,
            last_activity_at=datetime.now(timezone.utc),
        )
        self.db.add(session)

        # Audit successful login
        audit = AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            action="user.login_success",
            target_type="user",
            target_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            result="success",
        )
        self.db.add(audit)
        await self.db.commit()

        return user, None

    async def issue_tokens(self, user: User) -> Dict[str, Any]:
        access_token = create_access_token(
            subject=user.id,
            extra_claims={"email": user.email, "is_super_admin": user.is_super_admin}
        )
        refresh_token = create_refresh_token(subject=user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "firstName": user.first_name,
                "middleName": user.middle_name,
                "lastName": user.last_name,
                "avatarUrl": user.avatar_url,
                "isSuperAdmin": user.is_super_admin,
                "isActive": user.is_active,
                "isVerified": user.is_verified,
                "twoFactorEnabled": user.two_factor_enabled,
            },
        }

    async def generate_email_otp(self, user: User, otp_type: str = "verify_email") -> str:
        code = generate_otp(6)
        otp = OTP(
            user_id=user.id,
            code=code,
            otp_type=otp_type,
            attempts=0,
            max_attempts=5,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
            is_used=False,
        )
        self.db.add(otp)
        await self.db.commit()
        return code

    async def verify_otp(self, email: str, code: str, otp_type: str = "verify_email") -> User:
        user_res = await self.db.execute(select(User).where(User.email == email.lower().strip()))
        user = user_res.scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")

        otp_query = (
            select(OTP)
            .where(
                OTP.user_id == user.id,
                OTP.otp_type == otp_type,
                OTP.is_used == False,
                OTP.expires_at >= datetime.now(timezone.utc),
            )
            .order_by(OTP.created_at.desc())
        )
        res = await self.db.execute(otp_query)
        otp = res.scalars().first()

        if not otp:
            raise UnauthorizedException("Invalid or expired OTP code")

        if otp.attempts >= otp.max_attempts:
            raise UnauthorizedException("Maximum OTP verification attempts exceeded")

        otp.attempts += 1

        if otp.code != code.strip():
            await self.db.commit()
            raise UnauthorizedException("Incorrect OTP code")

        otp.is_used = True
        if otp_type == "verify_email":
            user.is_verified = True

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def setup_two_factor(self, user: User) -> Dict[str, Any]:
        secret = pyotp.random_base32()
        otpauth_url = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name=settings.PROJECT_NAME
        )

        # Generate QR code data URL (or return otpauth_url)
        encrypted_secret = encrypt_secret(secret)
        
        # Save or update TwoFactorCredential
        existing = await self.db.execute(select(TwoFactorCredential).where(TwoFactorCredential.user_id == user.id))
        tfa = existing.scalar_one_or_none()
        if not tfa:
            tfa = TwoFactorCredential(
                user_id=user.id,
                secret_encrypted=encrypted_secret,
                is_verified=False,
            )
            self.db.add(tfa)
        else:
            tfa.secret_encrypted = encrypted_secret
            tfa.is_verified = False

        # Generate recovery codes
        raw_codes = generate_recovery_codes(8)
        # Clear previous unused recovery codes
        await self.db.execute(delete(RecoveryCode).where(RecoveryCode.user_id == user.id))
        for c in raw_codes:
            rc = RecoveryCode(
                user_id=user.id,
                code_hash=get_password_hash(c),
                is_used=False,
            )
            self.db.add(rc)

        await self.db.commit()

        return {
            "secret": secret,
            "otpauth_url": otpauth_url,
            "qr_code_url": f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={otpauth_url}",
            "recovery_codes": raw_codes,
        }

    async def verify_and_enable_two_factor(self, user: User, code: str) -> bool:
        tfa_res = await self.db.execute(select(TwoFactorCredential).where(TwoFactorCredential.user_id == user.id))
        tfa = tfa_res.scalar_one_or_none()
        if not tfa:
            raise NotFoundException("Two-factor authentication has not been initialized.")

        secret = decrypt_secret(tfa.secret_encrypted)
        totp = pyotp.TOTP(secret)
        if not totp.verify(code.strip(), valid_window=1):
            raise UnauthorizedException("Invalid TOTP verification code")

        tfa.is_verified = True
        user.two_factor_enabled = True
        
        audit = AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            action="user.2fa_enabled",
            target_type="user",
            target_id=user.id,
            result="success",
        )
        self.db.add(audit)
        await self.db.commit()
        return True

    async def verify_two_factor_login(self, user: User, code: str) -> bool:
        tfa_res = await self.db.execute(select(TwoFactorCredential).where(TwoFactorCredential.user_id == user.id))
        tfa = tfa_res.scalar_one_or_none()
        if not tfa or not tfa.is_verified:
            return True

        secret = decrypt_secret(tfa.secret_encrypted)
        totp = pyotp.TOTP(secret)
        if totp.verify(code.strip(), valid_window=1):
            return True

        # Check recovery codes
        rc_res = await self.db.execute(select(RecoveryCode).where(RecoveryCode.user_id == user.id, RecoveryCode.is_used == False))
        recovery_codes = rc_res.scalars().all()
        for rc in recovery_codes:
            if verify_password(code.strip(), rc.code_hash):
                rc.is_used = True
                rc.used_at = datetime.now(timezone.utc)
                await self.db.commit()
                return True

        raise UnauthorizedException("Invalid two-factor code or recovery code")

    async def create_password_reset_token(self, email: str) -> str:
        user_res = await self.db.execute(select(User).where(User.email == email.lower().strip()))
        user = user_res.scalar_one_or_none()
        if not user:
            # Silent return to prevent enumeration
            return ""

        token_str = generate_random_token(48)
        token = VerificationToken(
            user_id=user.id,
            token=token_str,
            token_type="password_reset",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS),
            is_used=False,
        )
        self.db.add(token)
        await self.db.commit()
        return token_str

    async def reset_password(self, token_str: str, new_password: str) -> User:
        query = (
            select(VerificationToken)
            .where(
                VerificationToken.token == token_str,
                VerificationToken.token_type == "password_reset",
                VerificationToken.is_used == False,
                VerificationToken.expires_at >= datetime.now(timezone.utc),
            )
        )
        res = await self.db.execute(query)
        token = res.scalar_one_or_none()
        if not token:
            raise UnauthorizedException("Invalid or expired password reset link")

        user_res = await self.db.execute(select(User).options(selectinload(User.credentials)).where(User.id == token.user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")

        # Update or create active credential
        for cred in user.credentials:
            cred.is_active = False

        new_cred = UserCredential(
            user_id=user.id,
            password_hash=get_password_hash(new_password),
            is_active=True,
        )
        self.db.add(new_cred)
        token.is_used = True

        # Revoke all existing sessions for security
        await self.db.execute(
            update(Session).where(Session.user_id == user.id).values(is_revoked=True)
        )

        audit = AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            action="user.password_reset",
            target_type="user",
            target_id=user.id,
            result="success",
        )
        self.db.add(audit)
        await self.db.commit()
        return user

    async def get_user_sessions(self, user_id: str) -> List[Session]:
        query = (
            select(Session)
            .where(Session.user_id == user_id, Session.is_revoked == False)
            .order_by(Session.last_activity_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def revoke_session(self, user_id: str, session_id: str):
        query = (
            update(Session)
            .where(Session.id == session_id, Session.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.execute(query)
        await self.db.commit()

    async def revoke_all_sessions(self, user_id: str):
        query = (
            update(Session)
            .where(Session.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.db.execute(query)
        await self.db.commit()
