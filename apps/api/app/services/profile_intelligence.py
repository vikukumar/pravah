"""
PRAVAH Social Profile Intelligence Pipeline
=============================================
Implements PRD §1, §6, §18 — automatic AI analysis of connected social accounts.

Flow:
  Connect Social Account
    → Retrieve permitted profile metadata
    → Retrieve historical content (if API permits)
    → AI-synthesize brand/audience/tone summary
    → Persist versioned SocialProfileSummary

The pipeline clearly distinguishes:
  - Observed provider data (from API)
  - AI-derived interpretation
  - General recommendation (no sufficient data)
  - User-configured preference
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social import SocialAccount, SocialProfileSummary, SocialToken
from app.core.encryption import decrypt_secret

logger = logging.getLogger("pravah.profile_intelligence")

# Platform capability matrix — per PRD §2
PLATFORM_CAPABILITIES = {
    "x": {
        "supports_text": True, "supports_image": True, "supports_video": True,
        "supports_carousel": False, "supports_link": True, "supports_story": False,
        "supports_reel": False, "supports_short_video": False, "supports_long_video": False,
        "supports_poll": True, "supports_thread": True, "supports_scheduling": True,
        "supports_analytics": True, "supports_pages": False, "supports_mentions": True,
        "supports_hashtags": True, "character_limits": {"text": 280},
        "media_limits": {"images": 4, "video_seconds": 140},
        "api_constraints": ["rate_limit_15_min", "oauth2_bearer"],
    },
    "instagram": {
        "supports_text": True, "supports_image": True, "supports_video": True,
        "supports_carousel": True, "supports_link": False, "supports_story": True,
        "supports_reel": True, "supports_short_video": True, "supports_long_video": False,
        "supports_poll": False, "supports_thread": False, "supports_scheduling": True,
        "supports_analytics": True, "supports_pages": True, "supports_mentions": True,
        "supports_hashtags": True, "character_limits": {"caption": 2200},
        "media_limits": {"carousel_images": 10, "video_seconds": 60},
        "api_constraints": ["requires_business_account", "requires_facebook_page"],
    },
    "facebook": {
        "supports_text": True, "supports_image": True, "supports_video": True,
        "supports_carousel": True, "supports_link": True, "supports_story": True,
        "supports_reel": True, "supports_short_video": True, "supports_long_video": True,
        "supports_poll": True, "supports_thread": False, "supports_scheduling": True,
        "supports_analytics": True, "supports_pages": True, "supports_mentions": True,
        "supports_hashtags": True, "character_limits": {"post": 63206},
        "media_limits": {"images": 10, "video_mb": 4096},
        "api_constraints": ["requires_page_access_token", "graph_api_v19"],
    },
    "linkedin": {
        "supports_text": True, "supports_image": True, "supports_video": True,
        "supports_carousel": True, "supports_link": True, "supports_story": False,
        "supports_reel": False, "supports_short_video": False, "supports_long_video": True,
        "supports_poll": True, "supports_thread": False, "supports_scheduling": True,
        "supports_analytics": True, "supports_pages": True, "supports_mentions": True,
        "supports_hashtags": True, "character_limits": {"post": 3000, "article_title": 100},
        "media_limits": {"images": 9, "video_mb": 200},
        "api_constraints": ["oauth2_3_legged", "member_token_required"],
    },
    "youtube": {
        "supports_text": True, "supports_image": False, "supports_video": True,
        "supports_carousel": False, "supports_link": True, "supports_story": False,
        "supports_reel": False, "supports_short_video": True, "supports_long_video": True,
        "supports_poll": True, "supports_thread": False, "supports_scheduling": True,
        "supports_analytics": True, "supports_pages": True, "supports_mentions": False,
        "supports_hashtags": True, "character_limits": {"title": 100, "description": 5000},
        "media_limits": {"max_file_gb": 256, "short_seconds": 60},
        "api_constraints": ["youtube_data_api_v3", "oauth2_required"],
    },
}

# Suggested content formats per platform — per PRD §3
PLATFORM_CONTENT_FORMATS = {
    "x": ["short_text", "thread", "image_post", "video_post", "poll"],
    "instagram": ["feed_image", "carousel", "reel", "story", "video_post"],
    "facebook": ["feed_post", "image_post", "link_post", "video", "reel", "poll", "story"],
    "linkedin": ["professional_text", "image_post", "document", "video", "poll", "article"],
    "youtube": ["long_video", "short_video", "community_post"],
}


class ProfileIntelligencePipeline:
    """
    Automated social account intelligence pipeline.
    Runs asynchronously after account connection to build AI profile summary.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run(self, account_id: str, org_id: str) -> Optional[SocialProfileSummary]:
        """
        Execute the full intelligence pipeline for a social account.

        Returns the persisted SocialProfileSummary or None if account not found.
        """
        # Load account with tokens
        from sqlalchemy.orm import selectinload
        q = (
            select(SocialAccount)
            .options(selectinload(SocialAccount.tokens), selectinload(SocialAccount.pages))
            .where(SocialAccount.id == account_id, SocialAccount.organisation_id == org_id)
        )
        res = await self.db.execute(q)
        account = res.scalar_one_or_none()

        if not account:
            logger.warning("ProfileIntelligence: account %s not found for org %s", account_id, org_id)
            return None

        logger.info(
            "ProfileIntelligence: running pipeline for account=%s platform=%s",
            account_id, account.provider
        )

        # Update account sync status
        account.sync_status = "syncing"
        await self.db.commit()

        try:
            # Step 1: Collect observed data from account metadata
            observed_data = self._collect_observed_data(account)

            # Step 2: Get platform capabilities
            capabilities = PLATFORM_CAPABILITIES.get(account.provider.lower(), {})
            content_formats = PLATFORM_CONTENT_FORMATS.get(account.provider.lower(), ["text"])

            # Step 3: Retrieve live profile data if token available
            live_profile = {}
            if account.tokens:
                token_obj = account.tokens[0]
                if token_obj and token_obj.is_valid:
                    try:
                        access_token = decrypt_secret(token_obj.access_token_encrypted)
                        live_profile = await self._fetch_live_profile(
                            account.provider, access_token, account.account_id
                        )
                    except Exception as e:
                        logger.warning("ProfileIntelligence: live fetch failed: %s", e)

            # Step 4: Merge observed + live data
            profile_data = {**observed_data, **live_profile}

            # Step 5: AI-synthesize brand intelligence
            ai_summary = await self._synthesize_with_ai(account, profile_data, capabilities)

            # Step 6: Build structured profile summary
            summary_data = {
                "brand": {
                    "name": account.account_name or profile_data.get("name", ""),
                    "handle": account.username or profile_data.get("username", ""),
                    "description": profile_data.get("bio", account.bio or ""),
                    "url": profile_data.get("url", ""),
                    "profile_image": profile_data.get("profile_image_url", account.avatar_url or ""),
                },
                "business": {
                    "category": profile_data.get("category", ""),
                    "follower_count": profile_data.get("followers_count", account.followers_count or 0),
                    "following_count": profile_data.get("following_count", 0),
                    "post_count": profile_data.get("post_count", 0),
                },
                "platform": {
                    "name": account.provider,
                    "capabilities": capabilities,
                    "supported_formats": content_formats,
                    "account_type": profile_data.get("account_type", account.account_type or "business"),
                },
                "audience": ai_summary.get("audience", {}),
                "tone": ai_summary.get("tone", {"description": "professional", "confidence": "low"}),
                "voice": ai_summary.get("voice", {"keywords": [], "style": "neutral"}),
                "topics": ai_summary.get("topics", []),
                "content_types": ai_summary.get("content_types", ["Educational", "Informational"]),
                "keywords": ai_summary.get("keywords", []),
                "hashtags": ai_summary.get("hashtags", []),
                "posting_patterns": ai_summary.get("posting_patterns", {}),
                "best_times": ai_summary.get("best_times", []),
                "successful_formats": ai_summary.get("successful_formats", content_formats[:2]),
                "content_constraints": [
                    f"Max {capabilities.get('character_limits', {}).get('text', 'N/A')} characters"
                    if "character_limits" in capabilities else ""
                ],
                "data_quality": {
                    "observed_provider_data": True,
                    "ai_derived": True,
                    "has_historical_data": False,
                    "confidence": "medium" if live_profile else "low",
                    "note": (
                        "Profile intelligence is AI-derived from account metadata. "
                        "Accuracy improves as historical content data becomes available."
                    ) if not live_profile else "Profile intelligence is based on observed API data.",
                },
                "last_analysis_at": datetime.now(timezone.utc).isoformat(),
            }

            # Step 7: Persist / update SocialProfileSummary
            existing_q = await self.db.execute(
                select(SocialProfileSummary).where(
                    SocialProfileSummary.social_account_id == account.id
                )
            )
            existing = existing_q.scalar_one_or_none()

            if existing:
                existing.summary_data = summary_data
                existing.version = (existing.version or 1) + 1
                existing.analyzed_at = datetime.now(timezone.utc)
                profile_summary = existing
            else:
                profile_summary = SocialProfileSummary(
                    social_account_id=account.id,
                    organisation_id=org_id,
                    summary_data=summary_data,
                    version=1,
                    analyzed_at=datetime.now(timezone.utc),
                )
                self.db.add(profile_summary)

            # Update account sync status to ready
            account.sync_status = "synced"
            account.last_synced_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(profile_summary)

            logger.info(
                "ProfileIntelligence: pipeline completed for account=%s summary_version=%s",
                account_id, profile_summary.version
            )
            return profile_summary

        except Exception as e:
            logger.error("ProfileIntelligence: pipeline failed for account=%s: %s", account_id, e)
            account.sync_status = "sync_failed"
            await self.db.commit()
            return None

    def _collect_observed_data(self, account: SocialAccount) -> Dict[str, Any]:
        """Collect directly observed data from the account model (no AI inference)."""
        return {
            "name": account.account_name or "",
            "username": account.username or "",
            "bio": account.bio or "",
            "avatar_url": account.avatar_url or "",
            "followers_count": account.followers_count or 0,
            "platform": account.provider,
            "account_type": account.account_type or "personal",
            "data_source": "observed_provider_data",
        }

    async def _fetch_live_profile(
        self, platform: str, access_token: str, account_id: str
    ) -> Dict[str, Any]:
        """
        Attempt to retrieve real-time profile data from the platform's API.
        Returns empty dict if not available or token is invalid.
        NOTE: Actual API calls only work with real developer credentials.
        """
        live_data: Dict[str, Any] = {}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if platform == "x":
                    resp = await client.get(
                        f"https://api.twitter.com/2/users/me",
                        headers={"Authorization": f"Bearer {access_token}"},
                        params={"user.fields": "name,username,description,public_metrics,profile_image_url"},
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        metrics = data.get("public_metrics", {})
                        live_data = {
                            "name": data.get("name", ""),
                            "username": data.get("username", ""),
                            "bio": data.get("description", ""),
                            "profile_image_url": data.get("profile_image_url", ""),
                            "followers_count": metrics.get("followers_count", 0),
                            "following_count": metrics.get("following_count", 0),
                            "post_count": metrics.get("tweet_count", 0),
                            "data_source": "observed_provider_data",
                        }

                elif platform == "linkedin":
                    resp = await client.get(
                        "https://api.linkedin.com/v2/me",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        live_data = {
                            "name": f"{data.get('localizedFirstName', '')} {data.get('localizedLastName', '')}".strip(),
                            "data_source": "observed_provider_data",
                        }

                elif platform == "instagram":
                    resp = await client.get(
                        f"https://graph.instagram.com/me",
                        params={"fields": "id,name,biography,followers_count,media_count,profile_picture_url",
                                "access_token": access_token},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        live_data = {
                            "name": data.get("name", ""),
                            "bio": data.get("biography", ""),
                            "followers_count": data.get("followers_count", 0),
                            "post_count": data.get("media_count", 0),
                            "profile_image_url": data.get("profile_picture_url", ""),
                            "data_source": "observed_provider_data",
                        }

        except Exception as e:
            logger.debug("ProfileIntelligence: live profile fetch skipped for %s: %s", platform, e)

        return live_data

    async def _synthesize_with_ai(
        self,
        account: SocialAccount,
        profile_data: Dict[str, Any],
        capabilities: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Use configured AI provider to synthesize brand intelligence from profile data.
        Falls back to heuristic defaults if no AI provider is configured.

        IMPORTANT: Clearly marks all AI-derived fields as such.
        """
        platform = account.provider
        name = profile_data.get("name", account.account_name or "Unknown")
        bio = profile_data.get("bio", "")
        followers = profile_data.get("followers_count", 0)

        # Heuristic defaults — used when AI provider not available or call fails
        heuristic = {
            "audience": {
                "description": "AI inference unavailable — using general defaults",
                "data_source": "general_recommendation",
                "size": "unknown" if not followers else (
                    "nano" if followers < 1000 else
                    "micro" if followers < 50000 else
                    "macro" if followers < 500000 else "mega"
                ),
            },
            "tone": {
                "description": "professional",
                "data_source": "ai_derived",
                "confidence": "low",
                "note": "Based on minimal available profile data",
            },
            "voice": {"keywords": [], "style": "neutral"},
            "topics": [],
            "content_types": ["Educational", "Informational", "Promotional"],
            "keywords": bio.split()[:10] if bio else [],
            "hashtags": [f"#{platform}", f"#{name.replace(' ', '').lower()[:15]}"] if name else [],
            "posting_patterns": {
                "data_source": "general_recommendation",
                "note": "No historical data available. Using platform best-practice defaults.",
            },
            "best_times": _get_default_best_times(platform),
            "successful_formats": PLATFORM_CONTENT_FORMATS.get(platform, ["text"])[:2],
        }

        # Attempt real AI synthesis if we have a bio to work with
        if bio and len(bio) > 20:
            try:
                from app.services.provider_resolver import ProviderResolver
                resolver = ProviderResolver(self.db)
                provider = await resolver.resolve(
                    capability="text",
                    org_id=account.organisation_id,
                )

                ai_prompt = (
                    f"Analyse this social media profile and extract structured intelligence.\n\n"
                    f"Platform: {platform}\n"
                    f"Account Name: {name}\n"
                    f"Biography: {bio}\n"
                    f"Followers: {followers}\n\n"
                    f"Extract: target audience, communication tone, brand voice keywords, "
                    f"likely topics, hashtag strategy. Respond as JSON with keys: "
                    f"audience_description, tone, voice_keywords, topics, hashtags. "
                    f"Keep it concise and practical."
                )

                import httpx as _httpx
                async with _httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        f"{provider.base_uri.rstrip('/')}/chat/completions",
                        headers={"Authorization": f"Bearer {provider.api_key}",
                                 "HTTP-Referer": "https://pravah.app",
                                 "X-Title": "PRAVAH Profile Intelligence"},
                        json={
                            "model": provider.model,
                            "messages": [{"role": "user", "content": ai_prompt}],
                            "temperature": 0.3,
                            "max_tokens": 400,
                        },
                    )
                    if resp.status_code == 200:
                        import json
                        content = resp.json()["choices"][0]["message"]["content"]
                        # Attempt to parse JSON from AI response
                        try:
                            # Strip markdown code fences if present
                            clean = content.strip().strip("```json").strip("```").strip()
                            ai_data = json.loads(clean)
                            heuristic["tone"]["description"] = ai_data.get("tone", "professional")
                            heuristic["tone"]["data_source"] = "ai_derived"
                            heuristic["tone"]["confidence"] = "medium"
                            heuristic["voice"]["keywords"] = ai_data.get("voice_keywords", [])[:10]
                            heuristic["topics"] = ai_data.get("topics", [])[:8]
                            heuristic["hashtags"] = (
                                ai_data.get("hashtags", [])[:15] or heuristic["hashtags"]
                            )
                            heuristic["audience"]["description"] = ai_data.get("audience_description", "General audience")
                            heuristic["audience"]["data_source"] = "ai_derived"
                            logger.info("ProfileIntelligence: AI synthesis completed for account=%s", account.id)
                        except json.JSONDecodeError:
                            logger.debug("ProfileIntelligence: AI response not JSON parseable, using heuristics")

            except Exception as e:
                logger.debug("ProfileIntelligence: AI synthesis failed, using heuristics: %s", e)

        return heuristic


def _get_default_best_times(platform: str) -> list:
    """Return general recommended posting times per PRD best-practice benchmarks."""
    DEFAULTS = {
        "x": [
            {"day": "Tuesday", "time": "09:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Wednesday", "time": "12:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Thursday", "time": "17:00", "timezone": "local", "source": "general_recommendation"},
        ],
        "linkedin": [
            {"day": "Tuesday", "time": "08:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Wednesday", "time": "10:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Thursday", "time": "12:00", "timezone": "local", "source": "general_recommendation"},
        ],
        "instagram": [
            {"day": "Monday", "time": "11:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Wednesday", "time": "14:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Friday", "time": "18:00", "timezone": "local", "source": "general_recommendation"},
        ],
        "facebook": [
            {"day": "Wednesday", "time": "13:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Thursday", "time": "16:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Friday", "time": "20:00", "timezone": "local", "source": "general_recommendation"},
        ],
        "youtube": [
            {"day": "Thursday", "time": "14:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Friday", "time": "16:00", "timezone": "local", "source": "general_recommendation"},
            {"day": "Saturday", "time": "10:00", "timezone": "local", "source": "general_recommendation"},
        ],
    }
    return DEFAULTS.get(platform.lower(), [
        {"day": "Tuesday", "time": "10:00", "timezone": "local", "source": "general_recommendation"}
    ])
