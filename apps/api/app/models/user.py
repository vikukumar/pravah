import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True, index=True)
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    is_super_admin = Column(Boolean, default=False, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    credentials = relationship("UserCredential", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    memberships = relationship("OrganisationMember", back_populates="user", cascade="all, delete-orphan")
    two_factor = relationship("TwoFactorCredential", back_populates="user", uselist=False, cascade="all, delete-orphan")
    recovery_codes = relationship("RecoveryCode", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserCredential(BaseModel):
    __tablename__ = "user_credentials"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="credentials")

class Session(BaseModel):
    __tablename__ = "sessions"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_info = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="sessions")

class VerificationToken(BaseModel):
    __tablename__ = "verification_tokens"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    token_type = Column(String(50), nullable=False) # email_verify, password_reset, magic_link
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

class OTP(BaseModel):
    __tablename__ = "otps"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(10), nullable=False, index=True)
    otp_type = Column(String(50), nullable=False) # login, verify_email, verify_phone, reset_password
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

class TwoFactorCredential(BaseModel):
    __tablename__ = "two_factor_credentials"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    secret_encrypted = Column(Text, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    backup_phone = Column(String(50), nullable=True)

    user = relationship("User", back_populates="two_factor")

class RecoveryCode(BaseModel):
    __tablename__ = "recovery_codes"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="recovery_codes")

class SSOProvider(BaseModel):
    __tablename__ = "sso_providers"

    name = Column(String(100), unique=True, nullable=False) # google, github, microsoft, oidc
    display_name = Column(String(100), nullable=False)
    client_id = Column(String(255), nullable=False)
    client_secret_encrypted = Column(Text, nullable=False)
    discovery_url = Column(String(500), nullable=True)
    authorization_url = Column(String(500), nullable=True)
    token_url = Column(String(500), nullable=True)
    userinfo_url = Column(String(500), nullable=True)
    is_enabled = Column(Boolean, default=False, nullable=False)
