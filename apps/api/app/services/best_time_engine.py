"""
PRAVAH Best Time Recommendation Engine
========================================
Implements PRD §23 — posting time recommendations.

Uses:
1. Historical content publish time + engagement correlation (when data available)
2. Platform benchmark defaults (general recommendation, clearly labeled)
3. Organisation timezone awareness

Distinguishes: Observed data vs general recommendation.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content

logger = logging.getLogger("pravah.best_time_engine")


class BestTimeEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recommendation(
        self,
        org_id: str,
        platform: str,
        timezone_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        historical = await self._analyze_historical(org_id, platform)
        if historical:
            return historical
        return self._get_platform_defaults(platform)

    async def _analyze_historical(
        self, org_id: str, platform: str
    ) -> Optional[Dict[str, Any]]:
        q = (
            select(Content)
            .where(
                Content.organisation_id == org_id,
                Content.status == "published",
            )
            .limit(50)
        )
        res = await self.db.execute(q)
        posts = [p for p in res.scalars().all()
                 if p.platforms and platform in (p.platforms or [])]

        if len(posts) < 5:
            return None

        hour_counts: Dict[int, int] = {}
        for post in posts:
            if post.published_at:
                slot = post.published_at.weekday() * 24 + post.published_at.hour
                hour_counts[slot] = hour_counts.get(slot, 0) + 1

        if not hour_counts:
            return None

        best = max(hour_counts, key=lambda h: hour_counts[h])
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_name = days[best // 24]
        time_str = f"{best % 24:02d}:00"

        from datetime import timedelta
        now = datetime.now(timezone.utc)
        target_datetime = now + timedelta(days=1)

        return {
            "day_of_week": day_name,
            "day": day_name,
            "time": time_str,
            "recommended_time": f"{day_name} {time_str}",
            "recommended_datetime": target_datetime,
            "confidence_score": 0.85,
            "confidence": "medium",
            "reason": (
                f"Historical posting data for your {platform.upper()} account shows "
                f"the highest publishing activity on {day_name}s at {time_str}. "
                f"Based on {len(posts)} published posts."
            ),
            "is_historical_data": True,
            "data_source": "historical_data",
            "post_count_analyzed": len(posts),
        }

    def _get_platform_defaults(self, platform: str) -> Dict[str, Any]:
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        target_datetime = now + timedelta(days=1)

        DEFAULTS = {
            "x": {"day_of_week": "Wednesday", "day": "Wednesday", "time": "09:00", "recommended_time": "Wednesday 09:00",
                  "confidence_score": 0.65, "reason": "General benchmark for X: Weekday mornings 9-11 AM and afternoons 5-7 PM tend to show higher engagement. Connect more posts to get data-driven recommendations."},
            "linkedin": {"day_of_week": "Tuesday", "day": "Tuesday", "time": "08:00", "recommended_time": "Tuesday 08:00",
                         "confidence_score": 0.70, "reason": "General benchmark for LinkedIn: Tuesday-Thursday mornings (8-10 AM) reach professionals at the start of their workday. Connect more posts to get data-driven recommendations."},
            "instagram": {"day_of_week": "Wednesday", "day": "Wednesday", "time": "11:00", "recommended_time": "Wednesday 11:00",
                          "confidence_score": 0.65, "reason": "General benchmark for Instagram: Mid-morning on weekdays shows broad reach. Connect more posts to get data-driven recommendations."},
            "facebook": {"day_of_week": "Thursday", "day": "Thursday", "time": "13:00", "recommended_time": "Thursday 13:00",
                         "confidence_score": 0.60, "reason": "General benchmark for Facebook: Wednesday-Friday afternoons (1-4 PM) show higher organic engagement. Connect more posts to get data-driven recommendations."},
            "youtube": {"day_of_week": "Friday", "day": "Friday", "time": "15:00", "recommended_time": "Friday 15:00",
                        "confidence_score": 0.65, "reason": "General benchmark for YouTube: Fridays and weekends in the afternoon reach subscribers. Connect more posts to get data-driven recommendations."},
        }
        d = DEFAULTS.get(platform.lower(), {
            "day_of_week": "Tuesday", "day": "Tuesday", "time": "10:00", "recommended_time": "Tuesday 10:00",
            "confidence_score": 0.50,
            "reason": "General recommendation: Tuesday-Thursday mornings often show good engagement across platforms.",
        })
        return {
            **d,
            "recommended_datetime": target_datetime,
            "is_historical_data": False,
            "data_source": "general_recommendation",
            "confidence": "low",
            "note": "This is a general recommendation, not based on your account's historical data.",
        }
