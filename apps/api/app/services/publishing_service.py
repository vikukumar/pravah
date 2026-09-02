import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.encryption import decrypt_secret
from app.core.exceptions import PravahException
from app.models.content import Content, ContentSchedule
from app.models.organisation import Organisation
from app.models.social import SocialAccount, SocialPage, SocialToken
from app.models.system import AuditLog, Notification
from app.models.user import User

logger = logging.getLogger("pravah.publishing")


class PublishingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def publish_content_now(
        self,
        org_id: str,
        content_id: str,
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        # 1. Load Organisation and check emergency stop
        org_res = await self.db.execute(select(Organisation).where(Organisation.id == org_id))
        org = org_res.scalar_one_or_none()
        if not org or not org.is_active:
            raise PravahException(detail="Organisation is inactive or not found", error_code="ORG_INACTIVE")

        if org.publishing_paused or org.automation_disabled:
            raise PravahException(
                detail="Publishing is paused under emergency controls. Please unpause in Organisation Settings.",
                error_code="PUBLISHING_PAUSED"
            )

        # 2. Load Content
        query = select(Content).where(Content.id == content_id, Content.organisation_id == org_id)
        res = await self.db.execute(query)
        content = res.scalar_one_or_none()
        if not content:
            raise PravahException(detail="Content item not found", error_code="CONTENT_NOT_FOUND")

        # 3. Mark status as publishing
        content.status = "publishing"
        await self.db.commit()

        # 4. Dispatch to each target platform
        published_results = {}
        errors = []

        for platform in content.platforms:
            platform_str = str(platform).lower()
            try:
                acc_query = (
                    select(SocialAccount)
                    .options(selectinload(SocialAccount.tokens), selectinload(SocialAccount.pages))
                    .where(
                        SocialAccount.organisation_id == org_id,
                        SocialAccount.provider == platform_str,
                        SocialAccount.is_connected == True,
                    )
                )
                acc_res = await self.db.execute(acc_query)
                account = acc_res.scalar_one_or_none()

                if not account:
                    errors.append(f"No connected {platform_str.capitalize()} account found for this organisation.")
                    continue

                token_obj = account.tokens[0] if account.tokens else None
                if not token_obj or not token_obj.is_valid:
                    errors.append(f"Social token for {account.account_name} is expired or invalid. Please reconnect.")
                    continue

                access_token = decrypt_secret(token_obj.access_token_encrypted)

                # Real Platform API Dispatch
                post_id = await self._dispatch_to_platform(
                    platform=platform_str,
                    access_token=access_token,
                    account=account,
                    body=content.body,
                    media_urls=content.media_urls,
                )
                published_results[platform_str] = post_id

            except PravahException:
                raise
            except Exception as ex:
                logger.error(f"Publishing error on {platform_str}: {str(ex)}")
                errors.append(f"{platform_str.capitalize()}: {str(ex)}")

        # 5. Persist final results
        if published_results:
            content.status = "published"
            content.published_at = datetime.now(timezone.utc)
            content.external_post_ids = published_results
            if errors:
                content.error_message = "; ".join(errors)
        else:
            content.status = "failed"
            content.error_message = "; ".join(errors) if errors else "No platform could be published to."

        # Update schedule if present
        sched_query = select(ContentSchedule).where(ContentSchedule.content_id == content.id)
        sched_res = await self.db.execute(sched_query)
        sched = sched_res.scalar_one_or_none()
        if sched:
            sched.is_published = (content.status == "published")
            sched.last_attempt_at = datetime.now(timezone.utc)
            sched.attempts += 1

        # Audit
        audit = AuditLog(
            actor_id=actor.id if actor else None,
            actor_email=actor.email if actor else "system",
            organisation_id=org_id,
            action="content.published" if content.status == "published" else "content.publish_failed",
            target_type="content",
            target_id=content.id,
            result="success" if content.status == "published" else "failure",
            details={"published_results": published_results, "errors": errors},
        )
        self.db.add(audit)

        if content.created_by_id:
            notif = Notification(
                user_id=content.created_by_id,
                organisation_id=org_id,
                title="Post Published Successfully" if content.status == "published" else "Publishing Failed",
                message=f"Post '{content.title or content.body[:30]}' was {content.status}.",
                notification_type="success" if content.status == "published" else "error",
                category="publishing",
                action_url=f"/dashboard/content/{content.id}",
            )
            self.db.add(notif)

        await self.db.commit()
        await self.db.refresh(content)

        return {
            "content_id": content.id,
            "status": content.status,
            "published_results": published_results,
            "errors": errors,
        }

    async def _dispatch_to_platform(
        self,
        platform: str,
        access_token: str,
        account: SocialAccount,
        body: str,
        media_urls: Optional[List[str]] = None,
    ) -> str:
        """
        Calls the official provider API with real access_token.
        Raises PravahException if the API call fails.
        Never returns fake post IDs.
        """
        if platform == "x":
            return await self._publish_to_x(access_token, body, media_urls)

        elif platform == "facebook":
            return await self._publish_to_facebook(access_token, account, body, media_urls)

        elif platform == "linkedin":
            return await self._publish_to_linkedin(access_token, account, body, media_urls)

        elif platform == "instagram":
            return await self._publish_to_instagram(access_token, account, body, media_urls)

        elif platform == "youtube":
            raise PravahException(
                detail="YouTube video publishing requires a video file URL. Text-only YouTube posts are not supported.",
                error_code="YOUTUBE_VIDEO_REQUIRED"
            )

        else:
            raise PravahException(
                detail=f"Unsupported publishing platform: {platform}",
                error_code="UNSUPPORTED_PLATFORM"
            )

    async def _publish_to_x(self, access_token: str, body: str, media_urls: Optional[List[str]]) -> str:
        """Publishes to X (Twitter) using API v2."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.twitter.com/2/tweets",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={"text": body[:280]},
            )

        if resp.status_code == 201:
            data = resp.json()
            post_id = data.get("data", {}).get("id")
            if post_id:
                return post_id
            raise PravahException(detail="X API returned 201 but no tweet ID.", error_code="X_PUBLISH_ERROR")

        elif resp.status_code == 401:
            raise PravahException(
                detail="X authentication failed. Token expired or revoked. Please reconnect your X account.",
                error_code="X_AUTH_ERROR"
            )
        elif resp.status_code == 403:
            raise PravahException(
                detail=f"X API permission error: {resp.text[:200]}",
                error_code="X_PERMISSION_ERROR"
            )
        elif resp.status_code == 429:
            raise PravahException(
                detail="X API rate limit exceeded. Please try again later.",
                error_code="X_RATE_LIMITED"
            )
        else:
            raise PravahException(
                detail=f"X API error {resp.status_code}: {resp.text[:200]}",
                error_code="X_PUBLISH_ERROR"
            )

    async def _publish_to_facebook(
        self,
        access_token: str,
        account: SocialAccount,
        body: str,
        media_urls: Optional[List[str]],
    ) -> str:
        """Publishes to Facebook Page using Graph API."""
        target_page = account.pages[0] if account.pages else None
        if target_page and target_page.access_token_encrypted:
            from app.core.encryption import decrypt_secret as ds
            page_token = ds(target_page.access_token_encrypted)
            page_id = target_page.page_id
        else:
            page_token = access_token
            page_id = account.account_id

        payload = {"message": body}
        if media_urls and len(media_urls) > 0:
            payload["url"] = media_urls[0]

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"https://graph.facebook.com/v19.0/{page_id}/feed",
                params={"access_token": page_token},
                json=payload,
            )

        if resp.status_code == 200:
            data = resp.json()
            post_id = data.get("id")
            if post_id:
                return post_id
            raise PravahException(detail="Facebook API returned 200 but no post ID.", error_code="FB_PUBLISH_ERROR")
        elif resp.status_code == 190:
            raise PravahException(
                detail="Facebook access token expired. Please reconnect your Facebook account.",
                error_code="FB_TOKEN_EXPIRED"
            )
        else:
            error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = error_data.get("error", {}).get("message", resp.text[:200])
            raise PravahException(
                detail=f"Facebook API error {resp.status_code}: {error_msg}",
                error_code="FB_PUBLISH_ERROR"
            )

    async def _publish_to_linkedin(
        self,
        access_token: str,
        account: SocialAccount,
        body: str,
        media_urls: Optional[List[str]],
    ) -> str:
        """Publishes to LinkedIn using UGC Posts API."""
        # First get the member URN
        async with httpx.AsyncClient(timeout=15.0) as client:
            me_resp = await client.get(
                "https://api.linkedin.com/v2/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )

        if me_resp.status_code != 200:
            raise PravahException(
                detail=f"LinkedIn profile fetch failed: {me_resp.status_code}. Please reconnect.",
                error_code="LI_AUTH_ERROR"
            )

        person_id = me_resp.json().get("id", account.account_id)
        author_urn = f"urn:li:person:{person_id}"

        post_body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": body[:3000]},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
                json=post_body,
            )

        if resp.status_code == 201:
            post_urn = resp.headers.get("x-restli-id", "")
            if post_urn:
                return post_urn
            raise PravahException(detail="LinkedIn returned 201 but no post URN.", error_code="LI_PUBLISH_ERROR")
        elif resp.status_code == 401:
            raise PravahException(
                detail="LinkedIn token expired or invalid. Please reconnect your LinkedIn account.",
                error_code="LI_AUTH_ERROR"
            )
        else:
            raise PravahException(
                detail=f"LinkedIn API error {resp.status_code}: {resp.text[:200]}",
                error_code="LI_PUBLISH_ERROR"
            )

    async def _publish_to_instagram(
        self,
        access_token: str,
        account: SocialAccount,
        body: str,
        media_urls: Optional[List[str]],
    ) -> str:
        """
        Publishes to Instagram using Content Publishing API.
        Instagram requires a media URL (image or video) — text-only posts not supported.
        """
        if not media_urls or len(media_urls) == 0:
            raise PravahException(
                detail="Instagram requires an image or video URL. Text-only posts are not supported on Instagram.",
                error_code="IG_MEDIA_REQUIRED"
            )

        # Get Instagram Business Account ID via Facebook Graph
        target_page = account.pages[0] if account.pages else None
        if not target_page:
            raise PravahException(
                detail="No Instagram Business account linked. Connect a Facebook Page with an Instagram Business Account.",
                error_code="IG_NO_BUSINESS_ACCOUNT"
            )

        ig_account_id = target_page.page_id
        page_token = access_token
        if target_page.access_token_encrypted:
            from app.core.encryption import decrypt_secret as ds
            page_token = ds(target_page.access_token_encrypted)

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Create media container
            container_resp = await client.post(
                f"https://graph.facebook.com/v19.0/{ig_account_id}/media",
                params={
                    "access_token": page_token,
                    "image_url": media_urls[0],
                    "caption": body[:2200],
                },
            )

        if container_resp.status_code != 200:
            raise PravahException(
                detail=f"Instagram media container creation failed: {container_resp.text[:200]}",
                error_code="IG_CONTAINER_ERROR"
            )

        container_id = container_resp.json().get("id")
        if not container_id:
            raise PravahException(detail="Instagram returned no media container ID.", error_code="IG_CONTAINER_ERROR")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 2: Publish the container
            pub_resp = await client.post(
                f"https://graph.facebook.com/v19.0/{ig_account_id}/media_publish",
                params={
                    "access_token": page_token,
                    "creation_id": container_id,
                },
            )

        if pub_resp.status_code == 200:
            media_id = pub_resp.json().get("id")
            if media_id:
                return media_id
            raise PravahException(detail="Instagram publish returned no media ID.", error_code="IG_PUBLISH_ERROR")
        else:
            raise PravahException(
                detail=f"Instagram publishing failed: {pub_resp.text[:200]}",
                error_code="IG_PUBLISH_ERROR"
            )
