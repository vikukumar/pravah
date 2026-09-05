"""
PRAVAH Social Posts Sync Service
Fetches recent posts from each connected social platform and caches them in the DB.
Cached posts are used to provide AI context for style-matched content generation.

Rate-limit policy:
  - Per-account re-fetch is throttled to once every 6 hours max.
  - Each platform returns up to 25 recent posts per sync.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.encryption import decrypt_secret
from app.core.exceptions import NotFoundException, PravahException
from app.models.social import SocialAccount, SocialPostHistory, SocialToken

logger = logging.getLogger("pravah.social_posts")

# Minimum hours between re-fetches per account to respect platform rate limits
RATE_LIMIT_HOURS = 6
MAX_POSTS_PER_SYNC = 25


class SocialPostsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────────────────────────────
    # Main sync entry point
    # ──────────────────────────────────────────────────────────────────────

    async def sync_posts(self, org_id: str, account_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Fetch and cache recent posts from the platform.
        Returns: {"synced": int, "skipped": bool, "reason": str}
        """
        query = select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.organisation_id == org_id,
            SocialAccount.is_deleted.is_(False),
        )
        result = await self.db.execute(query)
        account = result.scalar_one_or_none()
        if not account:
            raise NotFoundException("Social account not found")

        if not account.is_connected:
            return {"synced": 0, "skipped": True, "reason": "Account is disconnected"}

        # Rate-limit check: skip if fetched recently
        if not force:
            latest_post_query = (
                select(SocialPostHistory.fetched_at)
                .where(SocialPostHistory.social_account_id == account_id)
                .order_by(SocialPostHistory.fetched_at.desc())
                .limit(1)
            )
            latest_result = await self.db.execute(latest_post_query)
            latest_fetch = latest_result.scalar_one_or_none()
            if latest_fetch:
                age_hours = (datetime.now(timezone.utc) - latest_fetch).total_seconds() / 3600
                if age_hours < RATE_LIMIT_HOURS:
                    return {
                        "synced": 0,
                        "skipped": True,
                        "reason": f"Last synced {age_hours:.1f}h ago. Will sync again after {RATE_LIMIT_HOURS}h.",
                        "next_sync_in_hours": round(RATE_LIMIT_HOURS - age_hours, 1),
                    }

        # Get valid access token
        token = await self._get_valid_token(account_id)
        if not token:
            return {"synced": 0, "skipped": True, "reason": "No valid access token found"}

        access_token = decrypt_secret(token.access_token_encrypted)
        provider = account.provider

        # Platform-specific fetch
        posts = []
        try:
            if provider in ("facebook",):
                posts = await self._fetch_facebook_posts(access_token, account.account_id)
            elif provider == "instagram":
                posts = await self._fetch_instagram_posts(access_token, account.account_id)
            elif provider == "x":
                posts = await self._fetch_x_posts(access_token, account.account_id)
            elif provider == "linkedin":
                posts = await self._fetch_linkedin_posts(access_token, account.account_id)
            elif provider == "youtube":
                posts = await self._fetch_youtube_posts(access_token, account.account_id)
            else:
                return {"synced": 0, "skipped": True, "reason": f"Post fetch not supported for {provider}"}
        except Exception as e:
            logger.warning(f"Post fetch failed for account {account_id} ({provider}): {e}")
            return {"synced": 0, "skipped": False, "reason": f"Platform API error: {str(e)}"}

        # Upsert posts into DB
        synced = 0
        now = datetime.now(timezone.utc)
        for post_data in posts[:MAX_POSTS_PER_SYNC]:
            external_post_id = post_data.get("external_post_id")
            if not external_post_id:
                continue

            # Check if already exists
            existing_q = select(SocialPostHistory).where(
                SocialPostHistory.social_account_id == account_id,
                SocialPostHistory.external_post_id == external_post_id,
            )
            existing_r = await self.db.execute(existing_q)
            existing = existing_r.scalar_one_or_none()

            if existing:
                # Update engagement counts
                existing.likes_count = post_data.get("likes_count", existing.likes_count)
                existing.shares_count = post_data.get("shares_count", existing.shares_count)
                existing.comments_count = post_data.get("comments_count", existing.comments_count)
                existing.views_count = post_data.get("views_count", existing.views_count)
                existing.fetched_at = now
            else:
                post_record = SocialPostHistory(
                    social_account_id=account_id,
                    organisation_id=org_id,
                    platform=provider,
                    external_post_id=external_post_id,
                    body=post_data.get("body"),
                    media_urls=post_data.get("media_urls", []),
                    post_url=post_data.get("post_url"),
                    posted_at=post_data.get("posted_at"),
                    likes_count=post_data.get("likes_count", 0),
                    shares_count=post_data.get("shares_count", 0),
                    comments_count=post_data.get("comments_count", 0),
                    views_count=post_data.get("views_count", 0),
                    hashtags=post_data.get("hashtags", []),
                    raw_data=post_data.get("raw_data"),
                    fetched_at=now,
                )
                self.db.add(post_record)
                synced += 1

        await self.db.commit()
        logger.info(f"Synced {synced} new posts for account {account_id} ({provider})")
        return {"synced": synced, "skipped": False, "total_cached": len(posts), "reason": "OK"}

    async def get_cached_posts(
        self, org_id: str, account_id: str, limit: int = 25
    ) -> List[SocialPostHistory]:
        """Return cached posts for an account, newest first."""
        query = (
            select(SocialPostHistory)
            .where(
                SocialPostHistory.social_account_id == account_id,
                SocialPostHistory.organisation_id == org_id,
            )
            .order_by(SocialPostHistory.posted_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_style_context(self, org_id: str, account_ids: List[str], limit: int = 10) -> str:
        """
        Return a formatted string of recent posts for use as AI context.
        This lets the AI match the user's writing style and tone.
        """
        all_posts = []
        for account_id in account_ids:
            posts = await self.get_cached_posts(org_id, account_id, limit=limit)
            all_posts.extend(posts)

        if not all_posts:
            return ""

        # Sort by date and take most recent
        all_posts.sort(key=lambda p: p.posted_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        sample = all_posts[:limit]

        lines = ["### Previous Posts (Use as style/voice reference):\n"]
        for i, post in enumerate(sample, 1):
            if post.body:
                lines.append(f"{i}. [{post.platform.upper()}] {post.body[:300]}")
                if post.hashtags:
                    lines.append(f"   Hashtags: {' '.join(post.hashtags[:5])}")
                lines.append("")

        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────────────
    # Platform-specific fetchers
    # ──────────────────────────────────────────────────────────────────────

    async def _get_valid_token(self, account_id: str) -> Optional[SocialToken]:
        query = (
            select(SocialToken)
            .where(
                SocialToken.social_account_id == account_id,
                SocialToken.is_valid.is_(True),
            )
            .order_by(SocialToken.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _fetch_facebook_posts(self, access_token: str, fb_user_id: str) -> List[Dict]:
        """Fetch from Facebook Graph API /me/posts"""
        url = f"https://graph.facebook.com/v19.0/{fb_user_id}/posts"
        params = {
            "access_token": access_token,
            "fields": "id,message,story,created_time,permalink_url,likes.summary(true),shares,comments.summary(true)",
            "limit": MAX_POSTS_PER_SYNC,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                logger.warning(f"Facebook posts fetch failed: {resp.status_code} {resp.text[:200]}")
                return []
            data = resp.json().get("data", [])

        posts = []
        for item in data:
            posts.append({
                "external_post_id": item.get("id"),
                "body": item.get("message") or item.get("story"),
                "post_url": item.get("permalink_url"),
                "posted_at": self._parse_dt(item.get("created_time")),
                "likes_count": item.get("likes", {}).get("summary", {}).get("total_count", 0),
                "shares_count": item.get("shares", {}).get("count", 0),
                "comments_count": item.get("comments", {}).get("summary", {}).get("total_count", 0),
                "hashtags": self._extract_hashtags(item.get("message", "")),
                "raw_data": item,
            })
        return posts

    async def _fetch_instagram_posts(self, access_token: str, ig_account_id: str) -> List[Dict]:
        """Fetch from Instagram Graph API /media"""
        url = f"https://graph.facebook.com/v19.0/{ig_account_id}/media"
        params = {
            "access_token": access_token,
            "fields": "id,caption,media_url,permalink,timestamp,like_count,comments_count,media_type",
            "limit": MAX_POSTS_PER_SYNC,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []
            data = resp.json().get("data", [])

        posts = []
        for item in data:
            posts.append({
                "external_post_id": item.get("id"),
                "body": item.get("caption"),
                "media_urls": [item["media_url"]] if item.get("media_url") else [],
                "post_url": item.get("permalink"),
                "posted_at": self._parse_dt(item.get("timestamp")),
                "likes_count": item.get("like_count", 0),
                "comments_count": item.get("comments_count", 0),
                "hashtags": self._extract_hashtags(item.get("caption", "")),
                "raw_data": item,
            })
        return posts

    async def _fetch_x_posts(self, access_token: str, twitter_user_id: str) -> List[Dict]:
        """Fetch from Twitter v2 /users/:id/tweets"""
        url = f"https://api.twitter.com/2/users/{twitter_user_id}/tweets"
        params = {
            "max_results": min(MAX_POSTS_PER_SYNC, 10),  # Twitter free tier max
            "tweet.fields": "created_at,public_metrics,entities",
            "expansions": "attachments.media_keys",
            "media.fields": "url,preview_image_url",
        }
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"X/Twitter posts fetch failed: {resp.status_code}")
                return []
            data = resp.json()

        posts = []
        for tweet in data.get("data", []):
            metrics = tweet.get("public_metrics", {})
            posts.append({
                "external_post_id": tweet.get("id"),
                "body": tweet.get("text"),
                "post_url": f"https://twitter.com/i/web/status/{tweet.get('id')}",
                "posted_at": self._parse_dt(tweet.get("created_at")),
                "likes_count": metrics.get("like_count", 0),
                "shares_count": metrics.get("retweet_count", 0),
                "comments_count": metrics.get("reply_count", 0),
                "views_count": metrics.get("impression_count", 0),
                "hashtags": [t["tag"] for t in tweet.get("entities", {}).get("hashtags", [])],
                "raw_data": tweet,
            })
        return posts

    async def _fetch_linkedin_posts(self, access_token: str, linkedin_person_id: str) -> List[Dict]:
        """Fetch from LinkedIn ugcPosts"""
        url = "https://api.linkedin.com/v2/ugcPosts"
        params = {
            "q": "authors",
            "authors": f"List(urn:li:person:{linkedin_person_id})",
            "count": MAX_POSTS_PER_SYNC,
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": "202311",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                return []
            data = resp.json().get("elements", [])

        posts = []
        for item in data:
            content = item.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {})
            text = content.get("shareCommentary", {}).get("text", "")
            posts.append({
                "external_post_id": item.get("id"),
                "body": text,
                "posted_at": self._parse_dt_ms(item.get("firstPublishedAt")),
                "hashtags": self._extract_hashtags(text),
                "raw_data": item,
            })
        return posts

    async def _fetch_youtube_posts(self, access_token: str, channel_owner_id: str) -> List[Dict]:
        """Fetch from YouTube Data API uploads playlist"""
        # First get channel ID
        channels_url = "https://www.googleapis.com/youtube/v3/channels"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            ch_resp = await client.get(channels_url, params={"part": "contentDetails", "mine": "true"}, headers=headers)
            if ch_resp.status_code != 200:
                return []
            channels = ch_resp.json().get("items", [])
            if not channels:
                return []

            uploads_playlist = channels[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
            if not uploads_playlist:
                return []

            # Fetch uploads
            pl_url = "https://www.googleapis.com/youtube/v3/playlistItems"
            pl_resp = await client.get(pl_url, params={
                "part": "snippet",
                "playlistId": uploads_playlist,
                "maxResults": MAX_POSTS_PER_SYNC,
            }, headers=headers)
            if pl_resp.status_code != 200:
                return []
            items = pl_resp.json().get("items", [])

        posts = []
        for item in items:
            snippet = item.get("snippet", {})
            posts.append({
                "external_post_id": snippet.get("resourceId", {}).get("videoId"),
                "body": f"{snippet.get('title', '')} — {snippet.get('description', '')[:300]}",
                "post_url": f"https://www.youtube.com/watch?v={snippet.get('resourceId', {}).get('videoId')}",
                "media_urls": [snippet.get("thumbnails", {}).get("high", {}).get("url", "")],
                "posted_at": self._parse_dt(snippet.get("publishedAt")),
                "hashtags": self._extract_hashtags(snippet.get("description", "")),
                "raw_data": snippet,
            })
        return posts

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _parse_dt(self, dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def _parse_dt_ms(self, ms: Optional[int]) -> Optional[datetime]:
        if not ms:
            return None
        try:
            return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        except Exception:
            return None

    def _extract_hashtags(self, text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r"#(\w+)", text)
