from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import TenantContext, get_tenant_context, require_permission
from app.core.database import get_db
from app.schemas.content import (
    CampaignCreate,
    CampaignResponse,
    ContentApprovalRequest,
    ContentCreate,
    ContentResponse,
    ContentUpdate,
)
from app.services.content_service import ContentService
from app.services.publishing_service import PublishingService

router = APIRouter()

@router.get("", response_model=List[ContentResponse])
async def list_content(
    status_filter: Optional[str] = Query(None, alias="status"),
    campaign_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db)
):
    content_svc = ContentService(db)
    items = await content_svc.list_content(
        org_id=tenant.organisation.id,
        status_filter=status_filter,
        campaign_id=campaign_id,
        limit=limit,
        offset=offset,
    )
    res = []
    for item in items:
        d = item.to_dict()
        d["scheduled_at"] = item.schedule.scheduled_for if item.schedule else None
        res.append(ContentResponse(**d))
    return res

@router.post("", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    payload: ContentCreate,
    tenant: TenantContext = Depends(require_permission("content.create")),
    db: AsyncSession = Depends(get_db)
):
    content_svc = ContentService(db)
    item = await content_svc.create_content(
        org_id=tenant.organisation.id,
        user=tenant.user,
        title=payload.title,
        body=payload.body,
        content_type=payload.content_type,
        platforms=payload.platforms,
        account_ids=payload.account_ids,
        page_ids=payload.page_ids,
        media_urls=payload.media_urls,
        campaign_id=payload.campaign_id,
        scheduled_at=payload.scheduled_at,
        approval_required=payload.approval_required,
        ai_provider_id=payload.ai_provider_id,
        ai_model=payload.ai_model,
        ai_prompt=payload.ai_prompt,
    )
    d = item.to_dict()
    d["scheduled_at"] = payload.scheduled_at
    return ContentResponse(**d)

@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    payload: ContentUpdate,
    tenant: TenantContext = Depends(require_permission("content.update")),
    db: AsyncSession = Depends(get_db)
):
    content_svc = ContentService(db)
    item = await content_svc.update_content(
        org_id=tenant.organisation.id,
        content_id=content_id,
        user=tenant.user,
        updates=payload.model_dump(exclude_unset=True),
    )
    d = item.to_dict()
    d["scheduled_at"] = payload.scheduled_at
    return ContentResponse(**d)

@router.post("/{content_id}/approve", response_model=ContentResponse)
async def approve_or_reject(
    content_id: str,
    payload: ContentApprovalRequest,
    tenant: TenantContext = Depends(require_permission("content.approve")),
    db: AsyncSession = Depends(get_db)
):
    content_svc = ContentService(db)
    item = await content_svc.approve_or_reject_content(
        org_id=tenant.organisation.id,
        content_id=content_id,
        reviewer=tenant.user,
        action=payload.action,
        comments=payload.comments,
    )
    d = item.to_dict()
    d["scheduled_at"] = None
    return ContentResponse(**d)

@router.post("/{content_id}/publish-now")
async def publish_content_now(
    content_id: str,
    tenant: TenantContext = Depends(require_permission("content.publish")),
    db: AsyncSession = Depends(get_db)
):
    pub_svc = PublishingService(db)
    result = await pub_svc.publish_content_now(
        org_id=tenant.organisation.id,
        content_id=content_id,
        actor=tenant.user,
    )
    return result

@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    tenant: TenantContext = Depends(require_permission("content.delete")),
    db: AsyncSession = Depends(get_db)
):
    content_svc = ContentService(db)
    await content_svc.delete_content(tenant.organisation.id, content_id, tenant.user)
    return {"message": "Content deleted successfully."}

@router.get("/calendar")
async def get_calendar(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    tenant: TenantContext = Depends(require_permission("content.view")),
    db: AsyncSession = Depends(get_db)
):
    start_dt = start or datetime(2026, 1, 1, tzinfo=timezone.utc)
    end_dt = end or datetime(2027, 1, 1, tzinfo=timezone.utc)
    content_svc = ContentService(db)
    events = await content_svc.list_calendar_content(tenant.organisation.id, start_dt, end_dt)
    return events
