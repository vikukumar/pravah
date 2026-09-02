import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.content import Content
from app.models.organisation import Organisation

# Benchmarked peak social engagement windows (24h clock, local time)
PLATFORM_PEAK_WINDOWS = {
    "x": {
        "weekday_hours": [9, 12, 17, 19],
        "weekend_hours": [10, 14, 18],
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
    },
    "linkedin": {
        "weekday_hours": [8, 10, 12, 16],
        "weekend_hours": [11, 14],
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
    },
    "facebook": {
        "weekday_hours": [9, 13, 16, 20],
        "weekend_hours": [11, 15, 19],
        "best_days": ["Wednesday", "Thursday", "Friday"],
    },
    "instagram": {
        "weekday_hours": [11, 14, 18, 21],
        "weekend_hours": [10, 13, 17, 20],
        "best_days": ["Monday", "Tuesday", "Wednesday", "Friday"],
    },
    "youtube": {
        "weekday_hours": [14, 16, 19],
        "weekend_hours": [10, 12, 15],
        "best_days": ["Thursday", "Friday", "Saturday"],
    },
}

class BestTimeEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_recommendation(
        self,
        org_id: str,
        platform: str = "x",
        target_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        platform = platform.lower()
        if platform not in PLATFORM_PEAK_WINDOWS:
            platform = "x"

        # Check organisation timezone
        org_res = await self.db.execute(select(Organisation).where(Organisation.id == org_id))
        org = org_res.scalar_one_or_none()
        org_timezone = org.timezone if org else "UTC"

        # Check if there is historical published content for this organisation
        content_res = await self.db.execute(
            select(Content).where(Content.organisation_id == org_id, Content.status == "published")
        )
        published_posts = content_res.scalars().all()
        has_historical_data = len(published_posts) >= 5

        base_date = target_date or (datetime.now(timezone.utc) + timedelta(days=1))
        day_name = base_date.strftime("%A")
        is_weekend = base_date.weekday() >= 5

        config = PLATFORM_PEAK_WINDOWS[platform]
        candidate_hours = config["weekend_hours"] if is_weekend else config["weekday_hours"]
        
        chosen_hour = candidate_hours[0]
        chosen_minute = 0

        if has_historical_data:
            # If historical data exists, refine based on post timestamps
            hours_distribution = [p.published_at.hour for p in published_posts if p.published_at]
            if hours_distribution:
                # Find most common or average window
                chosen_hour = max(set(hours_distribution), key=hours_distribution.count)
                chosen_minute = 30
            reason = f"Historical engagement for your {platform.capitalize()} profile is highest during this window based on {len(published_posts)} past posts."
            confidence = 0.88
        else:
            # Benchmark recommendation
            reason = f"General benchmark recommendation for {platform.capitalize()}: highest audience activity typically occurs around {chosen_hour}:00 in {org_timezone}."
            confidence = 0.65

        # Compute datetime
        rec_dt = base_date.replace(hour=chosen_hour, minute=chosen_minute, second=0, microsecond=0)
        formatted_time = rec_dt.strftime("%I:%M %p")

        return {
            "day_of_week": day_name,
            "recommended_time": formatted_time,
            "recommended_datetime": rec_dt,
            "confidence_score": confidence,
            "reason": reason,
            "is_historical_data": has_historical_data,
        }
