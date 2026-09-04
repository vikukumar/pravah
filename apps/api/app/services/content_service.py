import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import NotFoundException
from app.models.content import (
    Content,
    ContentApproval,
    ContentSchedule,
    ContentVersion,
)
from app.models.system import AuditLog, Notification
from app.models.user import User

def compute_fingerprint(text: str, media_urls: Optional[List[str]] = None) -> str:
    norm = text.lower().strip()
    if media_urls:
        norm += "".join(sorted(media_urls))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

class ContentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_content(
        self,
        org_id: str,
        user: User,
        body: str,
        platforms: List[str],
        title: Optional[str] = None,
        content_type: str = "text",
        account_ids: Optional[List[str]] = None,
        page_ids: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        campaign_id: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        approval_required: bool = False,
        ai_provider_id: Optional[str] = None,
        ai_model: Optional[str] = None,
        ai_prompt: Optional[str] = None,
    ) -> Content:
        fingerprint = compute_fingerprint(body, media_urls)

        # Initial status
        initial_status = "draft"
        if scheduled_at and not approval_required:
            initial_status = "scheduled"
        elif approval_required:
            initial_status = "review"

        content = Content(
            organisation_id=org_id,
            campaign_id=campaign_id,
            created_by_id=user.id,
            title=title,
            body=body,
            content_type=content_type,
            status=initial_status,
            platforms=platforms,
            account_ids=account_ids or [],
            page_ids=page_ids or [],
            media_urls=media_urls or [],
            approval_required=approval_required,
            ai_provider_id=ai_provider_id,
            ai_model=ai_model,
            ai_prompt=ai_prompt,
            content_fingerprint=fingerprint,
            version=1,
        )
        self.db.add(content)
        await self.db.flush()

        # Create version 1 record
        v1 = ContentVersion(
            content_id=content.id,
            version_number=1,
            title=title,
            body=body,
            media_urls=media_urls or [],
            edited_by_id=user.id,
            change_summary="Initial creation",
        )
        self.db.add(v1)

        # If scheduled, create ContentSchedule
        if scheduled_at:
            sched = ContentSchedule(
                content_id=content.id,
                organisation_id=org_id,
                scheduled_for=scheduled_at,
                idempotency_key=str(uuid.uuid4()),
                is_published=False,
            )
            self.db.add(sched)

        # Audit
        audit = AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            organisation_id=org_id,
            action="content.created",
            target_type="content",
            target_id=content.id,
            result="success",
            details={"status": initial_status, "platforms": platforms},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def update_content(
        self,
        org_id: str,
        content_id: str,
        user: User,
        updates: Dict[str, Any],
        change_summary: str = "Updated content",
    ) -> Content:
        query = select(Content).where(Content.id == content_id, Content.organisation_id == org_id)
        res = await self.db.execute(query)
        content = res.scalar_one_or_none()
        if not content:
            raise NotFoundException("Content not found")

        content.version += 1
        for key, val in updates.items():
            if hasattr(content, key) and val is not None:
                setattr(content, key, val)

        if "body" in updates or "media_urls" in updates:
            content.content_fingerprint = compute_fingerprint(
                content.body,
                content.media_urls
            )

        # Add version snapshot
        version_rec = ContentVersion(
            content_id=content.id,
            version_number=content.version,
            title=content.title,
            body=content.body,
            media_urls=content.media_urls,
            edited_by_id=user.id,
            change_summary=change_summary,
        )
        self.db.add(version_rec)

        # Update schedule if scheduled_at is provided
        if "scheduled_at" in updates:
            sched_val = updates["scheduled_at"]
            sched_query = select(ContentSchedule).where(ContentSchedule.content_id == content.id)
            sched_res = await self.db.execute(sched_query)
            existing_sched = sched_res.scalar_one_or_none()

            if sched_val:
                if existing_sched:
                    existing_sched.scheduled_for = sched_val
                    existing_sched.is_published = False
                else:
                    new_sched = ContentSchedule(
                        content_id=content.id,
                        organisation_id=org_id,
                        scheduled_for=sched_val,
                        idempotency_key=str(uuid.uuid4()),
                        is_published=False,
                    )
                    self.db.add(new_sched)
                if not content.approval_required:
                    content.status = "scheduled"
            elif existing_sched:
                await self.db.delete(existing_sched)
                if content.status == "scheduled":
                    content.status = "draft"

        audit = AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            organisation_id=org_id,
            action="content.updated",
            target_type="content",
            target_id=content.id,
            result="success",
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def approve_or_reject_content(
        self,
        org_id: str,
        content_id: str,
        reviewer: User,
        action: str,
        comments: Optional[str] = None,
    ) -> Content:
        query = select(Content).where(Content.id == content_id, Content.organisation_id == org_id)
        res = await self.db.execute(query)
        content = res.scalar_one_or_none()
        if not content:
            raise NotFoundException("Content not found")

        approval = ContentApproval(
            content_id=content.id,
            reviewer_id=reviewer.id,
            action=action,
            comments=comments,
        )
        self.db.add(approval)

        if action == "approve":
            content.status = "approved"
            content.current_approver_id = reviewer.id
            # If it has a schedule, move to scheduled
            sched_query = select(ContentSchedule).where(ContentSchedule.content_id == content.id)
            sched_res = await self.db.execute(sched_query)
            if sched_res.scalar_one_or_none():
                content.status = "scheduled"
        elif action == "reject":
            content.status = "rejected"
        elif action == "changes_requested":
            content.status = "draft"

        # Create in-app notification for content creator
        if content.created_by_id:
            notif = Notification(
                user_id=content.created_by_id,
                organisation_id=org_id,
                title=f"Content {action.capitalize()}",
                message=f"Your post '{content.title or content.body[:30]}' was {action} by {reviewer.first_name}.",
                notification_type="info" if action == "approve" else "warning",
                category="approval",
                action_url=f"/dashboard/content/{content.id}",
            )
            self.db.add(notif)

        audit = AuditLog(
            actor_id=reviewer.id,
            actor_email=reviewer.email,
            organisation_id=org_id,
            action=f"content.{action}",
            target_type="content",
            target_id=content.id,
            result="success",
            details={"comments": comments},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def list_content(
        self,
        org_id: str,
        status_filter: Optional[str] = None,
        campaign_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Content]:
        query = (
            select(Content)
            .options(selectinload(Content.schedule))
            .where(Content.organisation_id == org_id)
            .order_by(Content.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status_filter and status_filter != "all":
            query = query.where(Content.status == status_filter)
        if campaign_id:
            query = query.where(Content.campaign_id == campaign_id)

        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_calendar_content(
        self,
        org_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        query = (
            select(Content, ContentSchedule)
            .join(ContentSchedule, ContentSchedule.content_id == Content.id)
            .where(
                Content.organisation_id == org_id,
                ContentSchedule.scheduled_for >= start_date,
                ContentSchedule.scheduled_for <= end_date,
            )
            .order_by(ContentSchedule.scheduled_for.asc())
        )
        res = await self.db.execute(query)
        items = res.all()

        calendar_events = []
        for content, sched in items:
            calendar_events.append({
                "id": content.id,
                "title": content.title or content.body[:40] + "...",
                "body": content.body,
                "platforms": content.platforms,
                "status": content.status,
                "scheduled_at": sched.scheduled_for,
                "is_published": sched.is_published,
                "media_urls": content.media_urls,
            })
        return calendar_events

    async def delete_content(self, org_id: str, content_id: str, actor: User):
        query = select(Content).where(Content.id == content_id, Content.organisation_id == org_id)
        res = await self.db.execute(query)
        content = res.scalar_one_or_none()
        if not content:
            raise NotFoundException("Content not found")

        await self.db.delete(content)
        audit = AuditLog(
            actor_id=actor.id,
            actor_email=actor.email,
            organisation_id=org_id,
            action="content.deleted",
            target_type="content",
            target_id=content_id,
            result="success",
        )
        self.db.add(audit)
        await self.db.commit()
