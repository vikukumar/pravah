import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.encryption import encrypt_secret
from app.core.exceptions import NotFoundException, PravahException
from app.services.credential_resolver import CredentialResolver
from app.models.social import (
    SocialAccount,
    SocialPage,
    SocialProfileSummary,
    SocialProvider,
    SocialToken,
)
from app.models.system import AuditLog, SystemSetting
from app.models.user import User

# Provider OAuth endpoint configuration
PROVIDER_OAUTH_CONFIG = {
    "facebook": {
        "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v19.0/oauth/access_token",
        "profile_url": "https://graph.facebook.com/v19.0/me?fields=id,name,picture",
        "scopes": [
            "pages_show_list", "pages_read_engagement", "pages_manage_posts",
            "instagram_basic", "instagram_content_publish", "instagram_manage_insights",
            "public_profile"
        ],
    },
    "instagram": {
        "auth_url": "https://www.facebook.com/v19.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v19.0/oauth/access_token",
        "profile_url": "https://graph.facebook.com/v19.0/me?fields=id,name,picture",
        "scopes": [
            "pages_show_list", "pages_read_engagement",
            "instagram_basic", "instagram_content_publish", "instagram_manage_insights",
        ],
    },
    "x": {
        "auth_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "profile_url": "https://api.twitter.com/2/users/me",
        "scopes": ["tweet.read", "tweet.write", "users.read", "offline.access"],
        "code_challenge_method": "S256",
    },
    "linkedin": {
        "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "profile_url": "https://api.linkedin.com/v2/me",
        "scopes": [
            "r_liteprofile", "r_emailaddress", "w_member_social",
            "r_organization_social", "w_organization_social"
        ],
    },
    "youtube": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "profile_url": "https://www.googleapis.com/oauth2/v3/userinfo",
        "scopes": [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
            "openid", "profile", "email"
        ],
        "access_type": "offline",
        "prompt": "consent",
    },
}

DEFAULT_PROVIDERS = [
    {"name": "facebook", "display_name": "Facebook Pages & Groups", "icon_url": "/icons/facebook.svg",
     "supports_text": True, "supports_image": True, "supports_video": True, "supports_carousel": True,
     "supports_pages": True, "supports_analytics": True, "supports_scheduling": True, "supports_comments": True, "max_char_limit": 63206},
    {"name": "instagram", "display_name": "Instagram Business", "icon_url": "/icons/instagram.svg",
     "supports_text": True, "supports_image": True, "supports_video": True, "supports_carousel": True,
     "supports_pages": True, "supports_analytics": True, "supports_scheduling": True, "supports_comments": True, "max_char_limit": 2200},
    {"name": "x", "display_name": "X (formerly Twitter)", "icon_url": "/icons/x.svg",
     "supports_text": True, "supports_image": True, "supports_video": True, "supports_carousel": False,
     "supports_pages": False, "supports_analytics": True, "supports_scheduling": True, "supports_comments": False, "max_char_limit": 280},
    {"name": "linkedin", "display_name": "LinkedIn Pages & Profiles", "icon_url": "/icons/linkedin.svg",
     "supports_text": True, "supports_image": True, "supports_video": True, "supports_carousel": True,
     "supports_pages": True, "supports_analytics": True, "supports_scheduling": True, "supports_comments": True, "max_char_limit": 3000},
    {"name": "youtube", "display_name": "YouTube Shorts & Videos", "icon_url": "/icons/youtube.svg",
     "supports_text": True, "supports_image": False, "supports_video": True, "supports_carousel": False,
     "supports_pages": True, "supports_analytics": True, "supports_scheduling": True, "supports_comments": True, "max_char_limit": 5000},
]


class SocialService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_providers(self):
        """Seed provider definitions. Disabled by default -- admin must configure credentials."""
        for prov in DEFAULT_PROVIDERS:
            res = await self.db.execute(select(SocialProvider).where(SocialProvider.name == prov["name"]))
            if not res.scalar_one_or_none():
                sp = SocialProvider(**prov, is_enabled=False)
                self.db.add(sp)
        await self.db.commit()

    async def list_providers(self) -> List[SocialProvider]:
        """Returns all provider definitions for admin view."""
        res = await self.db.execute(select(SocialProvider))
        return list(res.scalars().all())

    async def get_available_providers(self) -> List[Dict[str, Any]]:
        """
        Returns providers available for user connection.
        Priority chain: DB credentials -> env vars -> disabled.
        A provider is surfaced only when credentials resolve successfully.
        """
        cred_resolver = CredentialResolver(self.db)
        social_status = await cred_resolver.get_social_status()

        # instagram shares facebook credentials
        if social_status.get("facebook", {}).get("enabled"):
            social_status["instagram"] = social_status["facebook"]

        all_providers_res = await self.db.execute(
            select(SocialProvider).where(SocialProvider.is_enabled == True)
        )
        enabled_providers = list(all_providers_res.scalars().all())

        available = []
        for prov in enabled_providers:
            prov_status = social_status.get(prov.name, {})
            if not prov_status.get("enabled") or not prov_status.get("is_enabled", True):
                continue
            available.append({
                "id": prov.id,
                "name": prov.name,
                "display_name": prov.display_name,
                "icon_url": prov.icon_url,
                "is_enabled": True,
                "configured": True,
                "credential_source": prov_status.get("source", "db"),
                "supports_text": prov.supports_text,
                "supports_image": prov.supports_image,
                "supports_video": prov.supports_video,
                "supports_carousel": prov.supports_carousel,
                "supports_pages": prov.supports_pages,
                "supports_analytics": prov.supports_analytics,
                "supports_scheduling": prov.supports_scheduling,
                "supports_comments": prov.supports_comments,
                "max_char_limit": prov.max_char_limit,
            })
        return available

    async def get_provider_credential_status(self) -> List[Dict[str, Any]]:
        """For admin: returns all providers with their credential configuration status (DB + env)."""
        cred_resolver = CredentialResolver(self.db)
        social_status = await cred_resolver.get_social_status()
        all_providers_res = await self.db.execute(select(SocialProvider))
        all_providers = list(all_providers_res.scalars().all())

        results = []
        for prov in all_providers:
            # instagram shares facebook credentials
            status_key = "facebook" if prov.name == "instagram" else prov.name
            prov_status = social_status.get(status_key, {})
            is_enabled = prov_status.get("is_enabled", False)
            has_creds = prov_status.get("enabled", False)

            if has_creds and is_enabled:
                config_status = "ready"
            elif has_creds:
                config_status = "configured_disabled"
            else:
                config_status = "not_configured"

            results.append({
                "id": prov.id,
                "name": prov.name,
                "display_name": prov.display_name,
                "icon_url": prov.icon_url,
                "is_enabled": prov.is_enabled,
                "configuration_status": config_status,
                "has_client_id": has_creds,
                "has_client_secret": has_creds,
                "credential_source": prov_status.get("source", "disabled"),
                "redirect_uri": prov_status.get("redirect_uri", ""),
                "supports_text": prov.supports_text,
                "supports_image": prov.supports_image,
                "supports_video": prov.supports_video,
                "supports_pages": prov.supports_pages,
                "supports_analytics": prov.supports_analytics,
            })
        return results

    async def generate_oauth_state(self, provider: str, org_id: str, user_id: str, redirect_uri: str) -> str:
        """Generate a secure CSRF state token for OAuth, stored in DB temporarily."""
        state = secrets.token_urlsafe(32)
        state_data = {
            "state": state,
            "provider": provider,
            "org_id": org_id,
            "user_id": user_id,
            "redirect_uri": redirect_uri,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        setting_key = f"oauth_state_{state}"
        res = await self.db.execute(select(SystemSetting).where(SystemSetting.key == setting_key))
        existing = res.scalar_one_or_none()
        if not existing:
            s = SystemSetting(key=setting_key, value=state_data, is_public=False, description="OAuth CSRF state token")
            self.db.add(s)
        else:
            existing.value = state_data
        await self.db.commit()
        return state

    async def validate_and_consume_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Validates and consumes OAuth state (one-time use, 10-minute expiry)."""
        setting_key = f"oauth_state_{state}"
        res = await self.db.execute(select(SystemSetting).where(SystemSetting.key == setting_key))
        setting = res.scalar_one_or_none()
        if not setting or not setting.value:
            return None

        state_data = setting.value
        await self.db.delete(setting)
        await self.db.commit()

        created_at_str = state_data.get("created_at", "")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str)
                if datetime.now(timezone.utc) - created_at > timedelta(minutes=10):
                    return None
            except Exception:
                return None

        if state_data.get("state") != state:
            return None

        return state_data

    async def get_oauth_authorization_url(
        self,
        provider_name: str,
        redirect_uri: str,
        org_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Builds real OAuth authorization URL using DB->env priority chain for credentials."""
        provider_name = provider_name.lower().strip()

        if provider_name not in PROVIDER_OAUTH_CONFIG:
            raise NotFoundException(f"Unsupported social provider: {provider_name}")

        oauth_config = PROVIDER_OAUTH_CONFIG[provider_name]

        # Resolve credentials via priority chain
        cred_resolver = CredentialResolver(self.db)
        try:
            creds = await cred_resolver.get_social(provider_name, redirect_uri)
        except PravahException as exc:
            return {
                "configured": False,
                "provider": provider_name,
                "message": exc.detail,
                "authorization_url": None,
                "state": None,
            }

        state = await self.generate_oauth_state(provider_name, org_id, user_id, redirect_uri)

        params = {
            "client_id": creds.client_id,
            "redirect_uri": creds.redirect_uri or redirect_uri,
            "response_type": "code",
            "scope": " ".join(oauth_config["scopes"]),
            "state": state,
        }

        if provider_name == "youtube":
            params["access_type"] = oauth_config.get("access_type", "offline")
            params["prompt"] = oauth_config.get("prompt", "consent")

        full_url = f"{oauth_config['auth_url']}?{urlencode(params)}"

        return {
            "configured": True,
            "provider": provider_name,
            "authorization_url": full_url,
            "state": state,
            "scopes": oauth_config["scopes"],
            "credential_source": creds.source,
        }

    async def exchange_oauth_code(
        self,
        provider_name: str,
        code: str,
        redirect_uri: str,
    ) -> Dict[str, Any]:
        """Exchanges OAuth authorization code for real access + refresh tokens. Uses DB->env chain."""
        if provider_name not in PROVIDER_OAUTH_CONFIG:
            raise PravahException(detail=f"Unsupported provider: {provider_name}", error_code="UNSUPPORTED_PROVIDER")

        oauth_config = PROVIDER_OAUTH_CONFIG[provider_name]

        # Resolve via priority chain
        cred_resolver = CredentialResolver(self.db)
        creds = await cred_resolver.get_social(provider_name, redirect_uri)  # raises if not configured

        token_url = oauth_config["token_url"]

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                if provider_name == "x":
                    import base64
                    basic = base64.b64encode(f"{creds.client_id}:{creds.client_secret}".encode()).decode()
                    resp = await client.post(
                        token_url,
                        headers={
                            "Authorization": f"Basic {basic}",
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                        data={
                            "grant_type": "authorization_code",
                            "code": code,
                            "redirect_uri": redirect_uri,
                            "code_verifier": "challenge",
                        },
                    )
                else:
                    resp = await client.post(
                        token_url,
                        data={
                            "client_id": creds.client_id,
                            "client_secret": creds.client_secret,
                            "code": code,
                            "redirect_uri": redirect_uri,
                            "grant_type": "authorization_code",
                        },
                    )

                if resp.status_code not in (200, 201):
                    raise PravahException(
                        detail=f"Token exchange failed for {provider_name}: {resp.text[:300]}",
                        error_code="OAUTH_TOKEN_EXCHANGE_FAILED"
                    )

                data = resp.json()
                return {
                    "access_token": data.get("access_token", ""),
                    "refresh_token": data.get("refresh_token"),
                    "expires_in": data.get("expires_in", 3600),
                    "scope": data.get("scope", ""),
                    "token_type": data.get("token_type", "Bearer"),
                }

            except httpx.ConnectError as e:
                raise PravahException(
                    detail=f"Could not connect to {provider_name} token endpoint: {str(e)}",
                    error_code="PROVIDER_CONNECT_ERROR"
                )

    async def fetch_provider_profile(self, provider_name: str, access_token: str) -> Dict[str, Any]:
        """Fetches real user profile from provider API using the access token."""
        if provider_name not in PROVIDER_OAUTH_CONFIG:
            return {}

        oauth_config = PROVIDER_OAUTH_CONFIG[provider_name]
        profile_url = oauth_config.get("profile_url", "")

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                if provider_name == "x":
                    resp = await client.get(
                        profile_url,
                        headers={"Authorization": f"Bearer {access_token}"},
                        params={"user.fields": "id,name,username,profile_image_url,public_metrics"},
                    )
                    if resp.status_code == 200:
                        d = resp.json().get("data", {})
                        return {
                            "id": d.get("id", ""),
                            "name": d.get("name", ""),
                            "username": f"@{d.get('username', '')}",
                            "profile_image_url": d.get("profile_image_url", ""),
                            "followers_count": d.get("public_metrics", {}).get("followers_count", 0),
                        }
                elif provider_name in ("facebook", "instagram"):
                    resp = await client.get(profile_url, params={"access_token": access_token})
                    if resp.status_code == 200:
                        d = resp.json()
                        return {
                            "id": d.get("id", ""),
                            "name": d.get("name", ""),
                            "username": d.get("username", ""),
                            "profile_image_url": d.get("picture", {}).get("data", {}).get("url", ""),
                        }
                elif provider_name == "linkedin":
                    resp = await client.get(profile_url, headers={"Authorization": f"Bearer {access_token}"})
                    if resp.status_code == 200:
                        d = resp.json()
                        first = d.get("localizedFirstName", "")
                        last = d.get("localizedLastName", "")
                        return {
                            "id": d.get("id", ""),
                            "name": f"{first} {last}".strip(),
                            "username": "",
                            "profile_image_url": "",
                        }
                elif provider_name == "youtube":
                    resp = await client.get(profile_url, headers={"Authorization": f"Bearer {access_token}"})
                    if resp.status_code == 200:
                        d = resp.json()
                        return {
                            "id": d.get("sub", ""),
                            "name": d.get("name", ""),
                            "username": d.get("email", ""),
                            "profile_image_url": d.get("picture", ""),
                        }
            except Exception:
                pass

        return {}

    async def connect_account_with_token(
        self,
        org_id: str,
        provider: str,
        account_id: str,
        account_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        token_expires_in: int = 3600,
        username: Optional[str] = None,
        profile_image_url: Optional[str] = None,
        pages: Optional[List[Dict[str, Any]]] = None,
        actor: Optional[User] = None,
    ) -> SocialAccount:
        query = select(SocialAccount).where(
            SocialAccount.organisation_id == org_id,
            SocialAccount.provider == provider,
            SocialAccount.account_id == account_id,
        )
        res = await self.db.execute(query)
        account = res.scalar_one_or_none()

        encrypted_token = encrypt_secret(access_token)
        encrypted_refresh = encrypt_secret(refresh_token) if refresh_token else None
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_expires_in)

        if not account:
            account = SocialAccount(
                organisation_id=org_id,
                provider=provider,
                account_id=account_id,
                account_name=account_name,
                username=username,
                profile_image_url=profile_image_url,
                is_connected=True,
                health_status="healthy",
                last_sync_at=datetime.now(timezone.utc),
            )
            self.db.add(account)
            await self.db.flush()

            token = SocialToken(
                social_account_id=account.id,
                access_token_encrypted=encrypted_token,
                refresh_token_encrypted=encrypted_refresh,
                expires_at=expires_at,
                is_valid=True,
            )
            self.db.add(token)
        else:
            account.account_name = account_name
            account.username = username or account.username
            account.profile_image_url = profile_image_url or account.profile_image_url
            account.is_connected = True
            account.health_status = "healthy"
            account.last_sync_at = datetime.now(timezone.utc)

            token_res = await self.db.execute(
                select(SocialToken).where(SocialToken.social_account_id == account.id)
            )
            token = token_res.scalar_one_or_none()
            if token:
                token.access_token_encrypted = encrypted_token
                token.refresh_token_encrypted = encrypted_refresh
                token.is_valid = True
                token.expires_at = expires_at

        if pages:
            for p in pages:
                page_query = select(SocialPage).where(
                    SocialPage.social_account_id == account.id,
                    SocialPage.page_id == p.get("id"),
                )
                page_res = await self.db.execute(page_query)
                page = page_res.scalar_one_or_none()
                page_token_enc = encrypt_secret(p.get("access_token", "")) if p.get("access_token") else None
                if not page:
                    page = SocialPage(
                        social_account_id=account.id,
                        organisation_id=org_id,
                        platform=provider,
                        page_id=p.get("id"),
                        name=p.get("name", "Page"),
                        username=p.get("username"),
                        page_url=p.get("url"),
                        profile_image_url=p.get("image_url"),
                        access_token_encrypted=page_token_enc,
                        is_connected=True,
                        health_status="healthy",
                        last_sync_at=datetime.now(timezone.utc),
                    )
                    self.db.add(page)
                else:
                    page.name = p.get("name", page.name)
                    page.is_connected = True
                    if page_token_enc:
                        page.access_token_encrypted = page_token_enc

        await self._build_initial_ai_summary(account)

        audit = AuditLog(
            actor_id=actor.id if actor else None,
            actor_email=actor.email if actor else None,
            organisation_id=org_id,
            action="social.connected",
            target_type="social_account",
            target_id=account.id,
            result="success",
            details={"provider": provider, "account_id": account_id, "account_name": account_name},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(account)
        return account

    async def _build_initial_ai_summary(self, account: SocialAccount):
        """Create initial AI profile summary with real (empty) baseline data."""
        sum_res = await self.db.execute(
            select(SocialProfileSummary).where(SocialProfileSummary.social_account_id == account.id)
        )
        if sum_res.scalar_one_or_none():
            return  # Already exists

        brand_name = account.account_name or account.username or "Brand"
        now = datetime.now(timezone.utc)

        summary_data = {
            "brand": {"name": brand_name, "handle": account.username or "", "profile_image": account.profile_image_url or ""},
            "business": {"category": "General", "follower_count": 0, "following_count": 0, "post_count": 0},
            "platform": {"name": account.provider, "account_type": "business"},
            "audience": {"description": "Awaiting analytics data from provider.", "data_source": "pending"},
            "tone": {"description": "Awaiting AI analysis.", "data_source": "pending", "confidence": "none"},
            "voice": {"keywords": [], "style": "neutral"},
            "topics": [], "content_types": [], "keywords": [], "hashtags": [],
            "posting_patterns": {"recommendation": "Connect account and post content to generate insights."},
            "best_times": [], "successful_formats": [],
            "data_quality": {
                "observed_provider_data": False, "ai_derived": False,
                "has_historical_data": False, "confidence": "none"
            },
            "last_analysis_at": now.isoformat(),
        }

        summary = SocialProfileSummary(
            social_account_id=account.id,
            version=1,
            brand_identity=f"Official profile for {account.account_name} on {account.provider.capitalize()}",
            business_category="General Marketing & Brand Presence",
            description=f"Initial profile baseline. Full analysis pending content history.",
            audience_signals=[],
            content_themes=[],
            tone="",
            keywords=[],
            hashtags=[],
            posting_patterns="Post content to generate real pattern analysis.",
            content_formats=[],
            engagement_patterns="No engagement data available yet.",
            summary_data=summary_data,
        )
        self.db.add(summary)

    async def list_organisation_accounts(self, org_id: str, include_deleted: bool = False) -> List[SocialAccount]:
        query = (
            select(SocialAccount)
            .options(selectinload(SocialAccount.pages))
            .where(SocialAccount.organisation_id == org_id)
        )
        if not include_deleted:
            query = query.where(SocialAccount.is_deleted.is_(False))
        query = query.order_by(SocialAccount.created_at.desc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def disconnect_account(self, org_id: str, account_id: str, actor: User):
        query = select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.organisation_id == org_id,
            SocialAccount.is_deleted.is_(False),
        )
        res = await self.db.execute(query)
        account = res.scalar_one_or_none()
        if not account:
            raise NotFoundException("Social account not found")

        account.is_connected = False
        account.health_status = "disconnected"
        await self.db.execute(update(SocialToken).where(SocialToken.social_account_id == account.id).values(is_valid=False))

        audit = AuditLog(
            actor_id=actor.id, actor_email=actor.email, organisation_id=org_id,
            action="social.disconnected", target_type="social_account", target_id=account.id,
            result="success", details={"provider": account.provider, "account_id": account.account_id},
        )
        self.db.add(audit)
        await self.db.commit()

    async def soft_delete_account(
        self, org_id: str, account_id: str, actor: User, reason: str = "User requested removal"
    ):
        """
        Soft-delete: marks account as deleted so it is hidden from all UI lists.
        The record and all history stays in the DB permanently for audit purposes.
        Tokens are invalidated. The account cannot be reconnected under the same record—
        a new OAuth flow will create a fresh SocialAccount row.
        """
        query = select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.organisation_id == org_id,
        )
        res = await self.db.execute(query)
        account = res.scalar_one_or_none()
        if not account:
            raise NotFoundException("Social account not found")

        account.is_connected = False
        account.is_deleted = True
        account.deleted_at = datetime.now(timezone.utc)
        account.health_status = "removed"
        account.disconnect_reason = reason

        # Invalidate all tokens
        await self.db.execute(
            update(SocialToken)
            .where(SocialToken.social_account_id == account.id)
            .values(is_valid=False)
        )

        audit = AuditLog(
            actor_id=actor.id, actor_email=actor.email, organisation_id=org_id,
            action="social.removed", target_type="social_account", target_id=account.id,
            result="success",
            details={
                "provider": account.provider,
                "account_id": account.account_id,
                "account_name": account.account_name,
                "reason": reason,
            },
        )
        self.db.add(audit)
        await self.db.commit()

    async def get_account_history(self, org_id: str) -> List[SocialAccount]:
        """
        Returns ALL accounts for an org including soft-deleted ones.
        Used in the UI 'Connection History' view.
        """
        return await self.list_organisation_accounts(org_id, include_deleted=True)

    async def get_ai_profile_summary(self, account_id: str) -> Optional[SocialProfileSummary]:
        query = (
            select(SocialProfileSummary)
            .where(SocialProfileSummary.social_account_id == account_id)
            .order_by(SocialProfileSummary.version.desc())
        )
        res = await self.db.execute(query)
        return res.scalars().first()
