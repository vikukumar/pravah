from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import TenantContext, require_permission
from app.core.database import get_db
from app.models.system import AuditLog

router = APIRouter()


def _campaign_to_dict(c) -> Dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "objective": c.objective,
        "status": c.status,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "post_count": 0,
    }


@router.get("")
async def list_campaigns(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db),
):
    from app.models.content import Campaign
    query = (
        select(Campaign)
        .where(Campaign.organisation_id == tenant.organisation.id)
        .order_by(Campaign.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(query)
    campaigns = res.scalars().all()

    result = []
    for c in campaigns:
        d = _campaign_to_dict(c)
        # Count real content items
        from app.models.content import Content
        count_res = await db.execute(
            select(func.count(Content.id)).where(
                Content.campaign_id == c.id,
                Content.organisation_id == tenant.organisation.id,
            )
        )
        d["post_count"] = count_res.scalar() or 0
        result.append(d)

    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: Dict[str, Any],
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db),
):
    from app.models.content import Campaign
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Campaign name is required.")

    campaign = Campaign(
        organisation_id=tenant.organisation.id,
        name=name,
        description=payload.get("description"),
        objective=payload.get("objective", "Brand Awareness"),
        status="active",
        start_date=datetime.now(timezone.utc),
        owner_id=tenant.user.id,
    )
    db.add(campaign)

    audit = AuditLog(
        actor_id=tenant.user.id,
        actor_email=tenant.user.email,
        organisation_id=tenant.organisation.id,
        action="campaign.created",
        target_type="campaign",
        result="success",
        details={"name": name, "objective": campaign.objective},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(campaign)
    return _campaign_to_dict(campaign)


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    payload: Dict[str, Any],
    tenant: TenantContext = Depends(require_permission("content.update")),
    db: AsyncSession = Depends(get_db),
):
    from app.models.content import Campaign
    res = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.organisation_id == tenant.organisation.id,
        )
    )
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    if "name" in payload and payload["name"]:
        campaign.name = payload["name"].strip()
    if "description" in payload:
        campaign.description = payload["description"]
    if "objective" in payload:
        campaign.objective = payload["objective"]
    if "status" in payload:
        campaign.status = payload["status"]
    if "end_date" in payload and payload["end_date"]:
        campaign.end_date = datetime.fromisoformat(payload["end_date"])

    await db.commit()
    await db.refresh(campaign)
    return _campaign_to_dict(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    tenant: TenantContext = Depends(require_permission("content.delete")),
    db: AsyncSession = Depends(get_db),
):
    from app.models.content import Campaign
    res = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.organisation_id == tenant.organisation.id,
        )
    )
    campaign = res.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    await db.delete(campaign)
    await db.commit()
