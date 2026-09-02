from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.system import Notification, NotificationPreference
from app.models.user import User

router = APIRouter()

@router.get("")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    res = await db.execute(query)
    notifs = res.scalars().all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "notification_type": n.notification_type,
            "category": n.category,
            "action_url": n.action_url,
            "is_read": n.is_read,
            "created_at": n.created_at,
        }
        for n in notifs
    ]

@router.post("/{notification_id}/mark-read")
async def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await db.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    return {"message": "Notification marked as read."}

@router.post("/mark-all-read")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    return {"message": "All notifications marked as read."}
