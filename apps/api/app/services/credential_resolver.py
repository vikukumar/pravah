"""
PRAVAH Credential Resolver
============================
Implements the three-tier credential resolution chain for all integrations:

  Priority 1: DB (SystemSetting / admin-configured via UI)
  Priority 2: Environment variable (from .env / deployment secret)
  Priority 3: Disabled (raises PravahException with clear admin guidance)

Used by:
- Payment gateways: Razorpay, Cashfree
- Social OAuth: X, Facebook, Instagram, LinkedIn, YouTube
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import decrypt_string
from app.core.exceptions import PravahException
from app.models.system import SystemSetting

logger = logging.getLogger("pravah.credential_resolver")


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "x" * len(value)
    return value[:4] + ("x" * (len(value) - 8)) + value[-4:]


@dataclass
class RazorpayCredentials:
    key_id: str
    key_secret: str
    webhook_secret: Optional[str] = None
    source: str = "env"


@dataclass
class CashfreeCredentials:
    app_id: str
    secret_key: str
    environment: str = "TEST"
    source: str = "env"


@dataclass
class SocialOAuthCredentials:
    client_id: str
    client_secret: str
    redirect_uri: str
    is_enabled: bool = True
    source: str = "env"


class CredentialResolver:
    """
    Resolves integration credentials: DB -> EnvVar -> Disabled.
    DB always wins over env vars, allowing admin UI overrides without redeployment.
    """

    DB_KEY_PAYMENT = "payment_gateway_config"
    DB_KEY_SOCIAL  = "social_oauth_credentials"

    _SOCIAL_ENV_MAP = {
        "facebook":  ("FACEBOOK_CLIENT_ID",  "FACEBOOK_CLIENT_SECRET"),
        "instagram": ("FACEBOOK_CLIENT_ID",  "FACEBOOK_CLIENT_SECRET"),
        "x":         ("X_CLIENT_ID",         "X_CLIENT_SECRET"),
        "linkedin":  ("LINKEDIN_CLIENT_ID",  "LINKEDIN_CLIENT_SECRET"),
        "youtube":   ("YOUTUBE_CLIENT_ID",   "YOUTUBE_CLIENT_SECRET"),
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._payment_cache: Optional[Dict[str, Any]] = None
        self._social_cache: Optional[Dict[str, Any]] = None

    async def _load_payment_db(self) -> Dict[str, Any]:
        if self._payment_cache is not None:
            return self._payment_cache
        res = await self.db.execute(
            select(SystemSetting).where(SystemSetting.key == self.DB_KEY_PAYMENT)
        )
        s = res.scalar_one_or_none()
        self._payment_cache = (s.value if s and isinstance(s.value, dict) else {})
        return self._payment_cache

    async def _load_social_db(self) -> Dict[str, Any]:
        if self._social_cache is not None:
            return self._social_cache
        res = await self.db.execute(
            select(SystemSetting).where(SystemSetting.key == self.DB_KEY_SOCIAL)
        )
        s = res.scalar_one_or_none()
        self._social_cache = (s.value if s and isinstance(s.value, dict) else {})
        return self._social_cache

    # ------------------------------------------------------------------
    # Razorpay
    # ------------------------------------------------------------------
    async def get_razorpay(self) -> RazorpayCredentials:
        db_cfg = await self._load_payment_db()
        rzp = db_cfg.get("razorpay", {})

        key_id = rzp.get("key_id", "").strip()
        key_secret = ""
        if rzp.get("key_secret_encrypted"):
            try:
                key_secret = decrypt_string(rzp["key_secret_encrypted"])
            except Exception:
                logger.warning("Failed to decrypt Razorpay key_secret from DB")

        webhook_secret = None
        if rzp.get("webhook_secret_encrypted"):
            try:
                webhook_secret = decrypt_string(rzp["webhook_secret_encrypted"])
            except Exception:
                pass

        if key_id and key_secret:
            return RazorpayCredentials(key_id=key_id, key_secret=key_secret,
                                       webhook_secret=webhook_secret, source="db")

        # Env fallback
        env_id  = settings.RAZORPAY_KEY_ID or ""
        env_sec = settings.RAZORPAY_KEY_SECRET or ""
        if env_id and env_sec:
            return RazorpayCredentials(key_id=env_id, key_secret=env_sec,
                                       webhook_secret=settings.RAZORPAY_WEBHOOK_SECRET or None,
                                       source="env")

        raise PravahException(
            detail="Razorpay is not configured. Set RAZORPAY_KEY_ID + RAZORPAY_KEY_SECRET in .env, or configure in Admin -> Payment Gateways.",
            error_code="RAZORPAY_NOT_CONFIGURED",
        )

    async def get_razorpay_status(self) -> Dict[str, Any]:
        db_cfg = await self._load_payment_db()
        rzp = db_cfg.get("razorpay", {})
        has_db  = bool(rzp.get("key_id") and rzp.get("key_secret_encrypted"))
        has_env = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)

        if has_db:
            return {"gateway": "razorpay", "enabled": True, "source": "db",
                    "key_id_masked": _mask(rzp.get("key_id", "")),
                    "has_webhook_secret": bool(rzp.get("webhook_secret_encrypted")),
                    "environment": rzp.get("environment", "live")}
        if has_env:
            return {"gateway": "razorpay", "enabled": True, "source": "env",
                    "key_id_masked": _mask(settings.RAZORPAY_KEY_ID or ""),
                    "has_webhook_secret": bool(settings.RAZORPAY_WEBHOOK_SECRET),
                    "environment": "live"}
        return {"gateway": "razorpay", "enabled": False, "source": "disabled",
                "key_id_masked": "", "has_webhook_secret": False, "environment": "live"}

    # ------------------------------------------------------------------
    # Cashfree
    # ------------------------------------------------------------------
    async def get_cashfree(self) -> CashfreeCredentials:
        db_cfg = await self._load_payment_db()
        cf = db_cfg.get("cashfree", {})

        app_id = cf.get("app_id", "").strip()
        secret_key = ""
        if cf.get("secret_key_encrypted"):
            try:
                secret_key = decrypt_string(cf["secret_key_encrypted"])
            except Exception:
                logger.warning("Failed to decrypt Cashfree secret from DB")

        environment = cf.get("environment", "TEST")

        if app_id and secret_key:
            return CashfreeCredentials(app_id=app_id, secret_key=secret_key,
                                       environment=environment, source="db")

        env_id  = settings.CASHFREE_APP_ID or ""
        env_sec = settings.CASHFREE_SECRET_KEY or ""
        if env_id and env_sec:
            return CashfreeCredentials(app_id=env_id, secret_key=env_sec,
                                       environment=settings.CASHFREE_ENV or "TEST",
                                       source="env")

        raise PravahException(
            detail="Cashfree is not configured. Set CASHFREE_APP_ID + CASHFREE_SECRET_KEY in .env, or configure in Admin -> Payment Gateways.",
            error_code="CASHFREE_NOT_CONFIGURED",
        )

    async def get_cashfree_status(self) -> Dict[str, Any]:
        db_cfg = await self._load_payment_db()
        cf = db_cfg.get("cashfree", {})
        has_db  = bool(cf.get("app_id") and cf.get("secret_key_encrypted"))
        has_env = bool(settings.CASHFREE_APP_ID and settings.CASHFREE_SECRET_KEY)

        if has_db:
            return {"gateway": "cashfree", "enabled": True, "source": "db",
                    "app_id_masked": _mask(cf.get("app_id", "")),
                    "environment": cf.get("environment", "TEST")}
        if has_env:
            return {"gateway": "cashfree", "enabled": True, "source": "env",
                    "app_id_masked": _mask(settings.CASHFREE_APP_ID or ""),
                    "environment": settings.CASHFREE_ENV or "TEST"}
        return {"gateway": "cashfree", "enabled": False, "source": "disabled",
                "app_id_masked": "", "environment": "TEST"}

    # ------------------------------------------------------------------
    # Social OAuth
    # ------------------------------------------------------------------
    async def get_social(self, provider: str, redirect_uri: str = "") -> SocialOAuthCredentials:
        provider = provider.lower().strip()
        db_creds = await self._load_social_db()
        p = db_creds.get(provider, {})

        client_id = p.get("client_id", "").strip()
        client_secret = ""
        if p.get("client_secret_encrypted"):
            try:
                client_secret = decrypt_string(p["client_secret_encrypted"])
            except Exception:
                logger.warning("Failed to decrypt %s client_secret from DB", provider)

        is_enabled = p.get("is_enabled", True)
        db_redirect = p.get("redirect_uri", redirect_uri)

        if client_id and client_secret:
            if not is_enabled:
                raise PravahException(
                    detail=f"{provider.capitalize()} integration is disabled by the administrator.",
                    error_code="SOCIAL_PROVIDER_DISABLED",
                )
            return SocialOAuthCredentials(client_id=client_id, client_secret=client_secret,
                                          redirect_uri=db_redirect or redirect_uri,
                                          is_enabled=True, source="db")

        # Env fallback
        env_map = self._SOCIAL_ENV_MAP.get(provider)
        if env_map:
            env_client_id  = getattr(settings, env_map[0], None) or ""
            env_client_sec = getattr(settings, env_map[1], None) or ""
            if env_client_id and env_client_sec:
                return SocialOAuthCredentials(client_id=env_client_id, client_secret=env_client_sec,
                                              redirect_uri=redirect_uri, is_enabled=True, source="env")

        id_var, _ = self._SOCIAL_ENV_MAP.get(provider, ("?_CLIENT_ID", "?_CLIENT_SECRET"))
        raise PravahException(
            detail=(
                f"OAuth credentials for {provider} are not configured. "
                f"Set {id_var} and its secret in your .env file, "
                f"or configure in Admin -> Social Integrations."
            ),
            error_code="SOCIAL_NOT_CONFIGURED",
        )

    async def get_social_status(self) -> Dict[str, Any]:
        db_creds = await self._load_social_db()
        results = {}
        for provider, (env_id_key, env_sec_key) in self._SOCIAL_ENV_MAP.items():
            if provider == "instagram":
                continue
            p = db_creds.get(provider, {})
            has_db  = bool(p.get("client_id") and p.get("client_secret_encrypted"))
            has_env = bool(getattr(settings, env_id_key, None) and
                           getattr(settings, env_sec_key, None))
            if has_db:
                results[provider] = {"enabled": True, "source": "db", "is_enabled": p.get("is_enabled", True),
                                     "client_id_masked": _mask(p.get("client_id", "")),
                                     "redirect_uri": p.get("redirect_uri", "")}
            elif has_env:
                results[provider] = {"enabled": True, "source": "env", "is_enabled": True,
                                     "client_id_masked": _mask(getattr(settings, env_id_key, "") or ""),
                                     "redirect_uri": ""}
            else:
                results[provider] = {"enabled": False, "source": "disabled", "is_enabled": False,
                                     "client_id_masked": "", "redirect_uri": ""}
        return results

    async def get_all_status(self) -> Dict[str, Any]:
        return {
            "razorpay": await self.get_razorpay_status(),
            "cashfree":  await self.get_cashfree_status(),
            "social":    await self.get_social_status(),
        }
