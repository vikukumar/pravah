from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import TenantContext, require_permission
from app.core.database import get_db
from app.models.content import Content
from app.models.social import SocialAccount

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(
    days: int = Query(30, ge=7, le=365),
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns real analytics summary from actual content and publishing records.
    No fake or hardcoded data. If no data exists, returns zero-values with
    empty_state=True to signal the frontend to show an empty state.
    """
    org_id = tenant.organisation.id
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total published posts in period
    published_res = await db.execute(
        select(func.count(Content.id)).where(
            Content.organisation_id == org_id,
            Content.status == "published",
            Content.published_at >= since,
        )
    )
    published_count = published_res.scalar() or 0

    # Failed posts in period
    failed_res = await db.execute(
        select(func.count(Content.id)).where(
            Content.organisation_id == org_id,
            Content.status == "failed",
            Content.updated_at >= since,
        )
    )
    failed_count = failed_res.scalar() or 0

    # Total all-time published
    all_time_res = await db.execute(
        select(func.count(Content.id)).where(
            Content.organisation_id == org_id,
            Content.status == "published",
        )
    )
    all_time_count = all_time_res.scalar() or 0

    # Publishing by platform (from external_post_ids JSON keys)
    published_items_res = await db.execute(
        select(Content.platforms, Content.published_at).where(
            Content.organisation_id == org_id,
            Content.status == "published",
            Content.published_at >= since,
        )
    )
    published_items = published_items_res.all()

    platform_breakdown = {}
    for item in published_items:
        platforms = item.platforms or []
        for p in platforms:
            platform_breakdown[p] = platform_breakdown.get(p, 0) + 1

    # Connected accounts count
    acc_res = await db.execute(
        select(func.count(SocialAccount.id)).where(
            SocialAccount.organisation_id == org_id,
            SocialAccount.is_connected == True,
        )
    )
    connected_accounts = acc_res.scalar() or 0

    # Draft content awaiting action
    draft_res = await db.execute(
        select(func.count(Content.id)).where(
            Content.organisation_id == org_id,
            Content.status.in_(["draft", "review"]),
        )
    )
    draft_count = draft_res.scalar() or 0

    has_data = published_count > 0 or all_time_count > 0

    return {
        "period_days": days,
        "empty_state": not has_data,
        "published_this_period": published_count,
        "failed_this_period": failed_count,
        "all_time_published": all_time_count,
        "drafts_pending": draft_count,
        "connected_accounts": connected_accounts,
        "platform_breakdown": [
            {"platform": k, "posts": v}
            for k, v in sorted(platform_breakdown.items(), key=lambda x: x[1], reverse=True)
        ],
        "note": (
            "Analytics data is derived from your published content records. "
            "Social engagement metrics (impressions, likes, shares) require "
            "platform-specific analytics sync, which is coming in a future update."
        ) if has_data else (
            "No published content yet. Analytics will appear here once you start publishing."
        ),
    }
