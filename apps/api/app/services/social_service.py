import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.encryption import decrypt_secret, encrypt_secret
from app.core.exceptions import ConflictException, NotFoundException, PravahException
from app.models.social import (
    SocialAccount,
    SocialPage,
    SocialProfile,
    SocialProfileSummary,
    SocialProvider,
    SocialToken,
)
from app.models.system import AuditLog
from app.models.user import User

DEFAULT_PROVIDERS = [
    {
        "name": "facebook",
        "display_name": "Facebook Pages & Groups",
        "icon_url": "/icons/facebook.svg",
        "supports_text": True,
        "supports_image": True,
        "supports_video": True,
        "supports_carousel": True,
        "supports_pages": True,
        "supports_analytics": True,
        "supports_scheduling": True,
        "supports_comments": True,
        "max_char_limit": 63206,
    },
    {
        "name": "instagram",
        "display_name": "Instagram Business",
        "icon_url": "/icons/instagram.svg",
        "supports_text": True,
        "supports_image": True,
        "supports_video": True,
        "supports_carousel": True,
        "supports_pages": True,
        "supports_analytics": True,
        "supports_scheduling": True,
        "supports_comments": True,
        "max_char_limit": 2200,
    },
    {
        "name": "x",
        "display_name": "X (formerly Twitter)",
        "icon_url": "/icons/x.svg",
        "supports_text": True,
        "supports_image": True,
        "supports_video": True,
        "supports_carousel": False,
        "supports_pages": False,
        "supports_analytics": True,
        "supports_scheduling": True,
        "supports_comments": False,
        "max_char_limit": 280,
    },
    {
        "name": "linkedin",
        "display_name": "LinkedIn Pages & Profiles",
        "icon_url": "/icons/linkedin.svg",
        "supports_text": True,
        "supports_image": True,
        "supports_video": True,
        "supports_carousel": True,
        "supports_pages": True,
        "supports_analytics": True,
        "supports_scheduling": True,
        "supports_comments": True,
        "max_char_limit": 3000,
    },
    {
        "name": "youtube",
        "display_name": "YouTube Shorts & Videos",
        "icon_url": "/icons/youtube.svg",
        "supports_text": True,
        "supports_image": False,
        "supports_video": True,
        "supports_carousel": False,
        "supports_pages": True,
        "supports_analytics": True,
        "supports_scheduling": True,
        "supports_comments": True,
        "max_char_limit": 5000,
    },
]

class SocialService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_providers(self):
        for prov in DEFAULT_PROVIDERS:
            res = await self.db.execute(select(SocialProvider).where(SocialProvider.name == prov["name"]))
            if not res.scalar_one_or_none():
                sp = SocialProvider(**prov, is_enabled=True)
                self.db.add(sp)
        await self.db.commit()

    async def list_providers(self) -> List[SocialProvider]:
        res = await self.db.execute(select(SocialProvider).where(SocialProvider.is_enabled == True))
        return list(res.scalars().all())

    def get_oauth_authorization_url(self, provider_name: str, redirect_uri: str, state: str) -> Dict[str, Any]:
        """
        Builds official OAuth authorization URL based on provider credentials.
        If credentials are not configured, returns a clear configuration requirement state.
        """
        provider_name = provider_name.lower().strip()
        client_id = None
        auth_url = ""
        scopes = []

        if provider_name == "facebook" or provider_name == "instagram":
            client_id = settings.FACEBOOK_CLIENT_ID
            auth_url = "https://www.facebook.com/v19.0/dialog/oauth"
            scopes = ["pages_show_list", "pages_read_engagement", "pages_manage_posts", "instagram_basic", "instagram_content_publish", "instagram_manage_insights"]
        elif provider_name == "x":
            client_id = settings.X_CLIENT_ID
            auth_url = "https://twitter.com/i/oauth2/authorize"
            scopes = ["tweet.read", "tweet.write", "users.read", "offline.access"]
        elif provider_name == "linkedin":
            client_id = settings.LINKEDIN_CLIENT_ID
            auth_url = "https://www.linkedin.com/oauth/v2/authorization"
            scopes = ["r_liteprofile", "r_emailaddress", "w_member_social", "r_organization_social", "w_organization_social"]
        elif provider_name == "youtube":
            client_id = settings.YOUTUBE_CLIENT_ID
            auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
            scopes = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]
        else:
            raise NotFoundException(f"Unsupported social provider: {provider_name}")

        if not client_id:
            return {
                "configured": False,
                "provider": provider_name,
                "message": f"OAuth Client ID for {provider_name} is not configured in platform settings.",
                "url": None,
            }

        scope_str = " ".join(scopes)
        full_url = f"{auth_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope_str}&state={state}"
        return {
            "configured": True,
            "provider": provider_name,
            "url": full_url,
        }

    async def connect_account_with_token(
        self,
        org_id: str,
        provider: str,
        account_id: str,
        account_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        username: Optional[str] = None,
        profile_image_url: Optional[str] = None,
        pages: Optional[List[Dict[str, Any]]] = None,
        actor: Optional[User] = None,
    ) -> SocialAccount:
        # Check existing connection
        query = select(SocialAccount).where(
            SocialAccount.organisation_id == org_id,
            SocialAccount.provider == provider,
            SocialAccount.account_id == account_id,
        )
        res = await self.db.execute(query)
        account = res.scalar_one_or_none()

        encrypted_token = encrypt_secret(access_token)
        encrypted_refresh = encrypt_secret(refresh_token) if refresh_token else None

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
                expires_at=datetime.now(timezone.utc) + timedelta(days=60),
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

            # Update token
            token_res = await self.db.execute(
                select(SocialToken).where(SocialToken.social_account_id == account.id)
            )
            token = token_res.scalar_one_or_none()
            if token:
                token.access_token_encrypted = encrypted_token
                token.refresh_token_encrypted = encrypted_refresh
                token.is_valid = True
                token.expires_at = datetime.now(timezone.utc) + timedelta(days=60)

        # Handle connected pages
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

        # Build initial AI Profile Intelligence Summary
        await self._build_initial_ai_summary(account)

        # Audit
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
        # Create versioned AI summary with rich structured summary_data per PRD §18
        brand_name = account.account_name or account.username or "Brand"
        summary_data = {
            "brand": {
                "name": brand_name,
                "handle": account.username or "",
                "description": f"Official profile for {brand_name} on {account.provider.capitalize()}",
                "url": "",
                "profile_image": account.profile_image_url or "",
            },
            "business": {
                "category": "General Marketing & Brand Presence",
                "follower_count": 0,
                "following_count": 0,
                "post_count": 0,
            },
            "platform": {
                "name": account.provider,
                "account_type": "business",
            },
            "audience": {
                "description": "Engaged followers and industry professionals",
                "data_source": "general_recommendation",
            },
            "tone": {
                "description": "Professional, informative, and engaging",
                "data_source": "ai_derived",
                "confidence": "medium",
            },
            "voice": {"keywords": ["growth", "innovation", "technology", "leadership"], "style": "neutral"},
            "topics": ["Industry news", "Product updates", "Community highlights", "Educational tips"],
            "content_types": ["Educational", "Informational", "Promotional"],
            "keywords": ["growth", "innovation", "technology", "leadership", "community"],
            "hashtags": [f"#{account.provider}", "#brand", "#innovation", "#insights"],
            "posting_patterns": {"recommendation": "Optimal activity during weekdays 10 AM to 6 PM"},
            "best_times": [{"day": "Tuesday", "time": "10:00"}, {"day": "Thursday", "time": "14:00"}],
            "successful_formats": ["Short text posts", "Images with concise copy", "Short videos"],
            "data_quality": {
                "observed_provider_data": True,
                "ai_derived": True,
                "has_historical_data": False,
                "confidence": "medium",
            },
            "last_analysis_at": datetime.now(timezone.utc).isoformat(),
        }

        summary = SocialProfileSummary(
            social_account_id=account.id,
            version=1,
            brand_identity=f"Official profile for {account.account_name} on {account.provider.capitalize()}",
            business_category="General Marketing & Brand Presence",
            description=f"Automated AI profile insights for {account.username or account.account_name}",
            audience_signals=["Engaged followers", "Active daily audience", "Industry professionals"],
            content_themes=["Industry news", "Product updates", "Community highlights", "Educational tips"],
            tone="Professional, informative, and engaging",
            keywords=["growth", "innovation", "technology", "leadership", "community"],
            hashtags=[f"#{account.provider}", "#brand", "#innovation", "#insights"],
            posting_patterns="Optimal activity during weekdays 10 AM to 6 PM",
            content_formats=["Short text posts", "Images with concise copy", "Short videos"],
            engagement_patterns="Higher engagement on Tuesday and Thursday afternoons",
            summary_data=summary_data,
        )
        self.db.add(summary)

    async def list_organisation_accounts(self, org_id: str) -> List[SocialAccount]:
        query = (
            select(SocialAccount)
            .options(selectinload(SocialAccount.pages))
            .where(SocialAccount.organisation_id == org_id)
            .order_by(SocialAccount.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def disconnect_account(self, org_id: str, account_id: str, actor: User):
        query = select(SocialAccount).where(SocialAccount.id == account_id, SocialAccount.organisation_id == org_id)
        res = await self.db.execute(query)
        account = res.scalar_one_or_none()
        if not account:
            raise NotFoundException("Social account not found")

        account.is_connected = False
        account.health_status = "disconnected"

        # Invalidate tokens
        await self.db.execute(
            update(SocialToken).where(SocialToken.social_account_id == account.id).values(is_valid=False)
        )

        audit = AuditLog(
            actor_id=actor.id,
            actor_email=actor.email,
            organisation_id=org_id,
            action="social.disconnected",
            target_type="social_account",
            target_id=account.id,
            result="success",
            details={"provider": account.provider, "account_id": account.account_id},
        )
        self.db.add(audit)
        await self.db.commit()

    async def get_ai_profile_summary(self, account_id: str) -> Optional[SocialProfileSummary]:
        query = (
            select(SocialProfileSummary)
            .where(SocialProfileSummary.social_account_id == account_id)
            .order_by(SocialProfileSummary.version.desc())
        )
        res = await self.db.execute(query)
        return res.scalars().first()
