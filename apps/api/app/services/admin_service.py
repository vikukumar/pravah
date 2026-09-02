from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai import AIUsage
from app.models.billing import Payment, Subscription
from app.models.content import Content
from app.models.organisation import Organisation
from app.models.system import AuditLog, FeatureFlag, SystemSetting
from app.models.user import User
from app.models.workflow import WorkflowExecution

class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_platform_metrics(self) -> Dict[str, Any]:
        users_count_res = await self.db.execute(select(func.count(User.id)))
        total_users = users_count_res.scalar() or 0

        active_users_res = await self.db.execute(select(func.count(User.id)).where(User.is_active == True))
        active_users = active_users_res.scalar() or 0

        orgs_count_res = await self.db.execute(select(func.count(Organisation.id)))
        total_orgs = orgs_count_res.scalar() or 0

        subs_count_res = await self.db.execute(select(func.count(Subscription.id)).where(Subscription.status == "active"))
        active_subs = subs_count_res.scalar() or 0

        revenue_res = await self.db.execute(select(func.sum(Payment.amount)).where(Payment.status == "paid"))
        total_rev = revenue_res.scalar() or 0.0

        posts_res = await self.db.execute(select(func.count(Content.id)).where(Content.status == "published"))
        published_posts = posts_res.scalar() or 0

        wf_exec_res = await self.db.execute(select(func.count(WorkflowExecution.id)))
        wf_executions = wf_exec_res.scalar() or 0

        tokens_res = await self.db.execute(select(func.sum(AIUsage.total_tokens)))
        total_tokens = tokens_res.scalar() or 0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_organisations": total_orgs,
            "active_subscriptions": active_subs,
            "total_revenue_usd": float(total_rev),
            "total_published_posts": published_posts,
            "total_workflow_executions": wf_executions,
            "total_ai_tokens_consumed": int(total_tokens),
            "system_health": "operational",
        }

    async def list_audit_logs(
        self,
        org_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        if org_id:
            query = query.where(AuditLog.organisation_id == org_id)
        if action:
            query = query.where(AuditLog.action.ilike(f"%{action}%"))

        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_feature_flags(self) -> List[FeatureFlag]:
        res = await self.db.execute(select(FeatureFlag).order_by(FeatureFlag.key.asc()))
        return list(res.scalars().all())

    async def set_feature_flag(
        self,
        key: str,
        name: str,
        is_enabled_globally: bool = True,
        description: Optional[str] = None,
    ) -> FeatureFlag:
        res = await self.db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
        flag = res.scalar_one_or_none()
        if not flag:
            flag = FeatureFlag(
                key=key,
                name=name,
                description=description,
                is_enabled_globally=is_enabled_globally,
            )
            self.db.add(flag)
        else:
            flag.name = name
            flag.is_enabled_globally = is_enabled_globally
            if description:
                flag.description = description

        await self.db.commit()
        await self.db.refresh(flag)
        return flag

    async def get_system_settings(self, public_only: bool = False) -> Dict[str, Any]:
        query = select(SystemSetting)
        if public_only:
            query = query.where(SystemSetting.is_public == True)
        res = await self.db.execute(query)
        settings_list = res.scalars().all()
        return {s.key: s.value for s in settings_list}

    async def set_system_setting(self, key: str, value: Any, is_public: bool = False, description: Optional[str] = None):
        res = await self.db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = res.scalar_one_or_none()
        if not setting:
            setting = SystemSetting(key=key, value=value, is_public=is_public, description=description)
            self.db.add(setting)
        else:
            setting.value = value
            setting.is_public = is_public
            if description:
                setting.description = description

        await self.db.commit()

    async def toggle_platform_emergency_stop(self, pause_all_publishing: bool, actor: User):
        await self.db.execute(
            update(Organisation).values(publishing_paused=pause_all_publishing)
        )
        audit = AuditLog(
            actor_id=actor.id,
            actor_email=actor.email,
            action="admin.emergency_stop_toggled",
            target_type="system",
            result="success",
            details={"publishing_paused": pause_all_publishing},
        )
        self.db.add(audit)
        await self.db.commit()
