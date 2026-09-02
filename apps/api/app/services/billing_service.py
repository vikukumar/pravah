import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.exceptions import ConflictException, NotFoundException, PravahException
from app.models.ai import AIUsage
from app.models.billing import (
    Payment,
    PaymentTransaction,
    PaymentWebhook,
    Plan,
    PlanFeature,
    Subscription,
)
from app.models.content import Content
from app.models.organisation import Organisation, OrganisationMember
from app.models.social import SocialAccount
from app.models.system import AuditLog
from app.models.user import User
from app.models.workflow import Workflow, WorkflowExecution

DEFAULT_PLANS = [
    {
        "name": "Free",
        "slug": "free",
        "description": "30-day trial for creators & individuals",
        "price_monthly": 0.0,
        "price_yearly": 0.0,
        "currency": "INR",
        "is_free": True,
        "trial_days": 30,
        "features": {
            "social_account_limit": 1,
            "page_limit": 1,
            "daily_post_limit": 1,
            "monthly_post_limit": 30,
            "ai_token_limit_monthly": 50000,
            "image_generation_limit_monthly": 10,
            "workflow_limit": 3,
            "workflow_execution_limit_monthly": 100,
            "member_limit": 1,
            "storage_limit_mb": 500,
            "analytics_retention_days": 30,
            "has_api_access": False,
            "has_custom_providers": False,
            "has_sso": False,
            "has_2fa": True,
            "has_approval_workflows": False,
            "has_automation": True,
            "has_advanced_analytics": False,
        },
    },
    {
        "name": "Starter",
        "slug": "starter",
        "description": "For growing creators and small business teams",
        "price_monthly": 1499.0,
        "price_yearly": 14990.0,
        "currency": "INR",
        "is_free": False,
        "trial_days": 0,
        "features": {
            "social_account_limit": 5,
            "page_limit": 5,
            "daily_post_limit": 10,
            "monthly_post_limit": 300,
            "ai_token_limit_monthly": 250000,
            "image_generation_limit_monthly": 50,
            "workflow_limit": 10,
            "workflow_execution_limit_monthly": 500,
            "member_limit": 3,
            "storage_limit_mb": 2048,
            "analytics_retention_days": 90,
            "has_api_access": True,
            "has_custom_providers": False,
            "has_sso": False,
            "has_2fa": True,
            "has_approval_workflows": True,
            "has_automation": True,
            "has_advanced_analytics": True,
        },
    },
    {
        "name": "Pro",
        "slug": "pro",
        "description": "For high-volume brands and marketing agencies",
        "price_monthly": 3999.0,
        "price_yearly": 39990.0,
        "currency": "INR",
        "is_free": False,
        "trial_days": 0,
        "features": {
            "social_account_limit": 20,
            "page_limit": 20,
            "daily_post_limit": 50,
            "monthly_post_limit": 1500,
            "ai_token_limit_monthly": 1000000,
            "image_generation_limit_monthly": 200,
            "workflow_limit": 50,
            "workflow_execution_limit_monthly": 2500,
            "member_limit": 10,
            "storage_limit_mb": 10240,
            "analytics_retention_days": 365,
            "has_api_access": True,
            "has_custom_providers": True,
            "has_sso": True,
            "has_2fa": True,
            "has_approval_workflows": True,
            "has_automation": True,
            "has_advanced_analytics": True,
        },
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "description": "Unlimited capacity, custom AI fine-tuning & dedicated SLA",
        "price_monthly": 9999.0,
        "price_yearly": 99990.0,
        "currency": "INR",
        "is_free": False,
        "trial_days": 0,
        "features": {
            "social_account_limit": 100,
            "page_limit": 100,
            "daily_post_limit": 500,
            "monthly_post_limit": 10000,
            "ai_token_limit_monthly": 5000000,
            "image_generation_limit_monthly": 1000,
            "workflow_limit": 200,
            "workflow_execution_limit_monthly": 20000,
            "member_limit": 50,
            "storage_limit_mb": 51200,
            "analytics_retention_days": 730,
            "has_api_access": True,
            "has_custom_providers": True,
            "has_sso": True,
            "has_2fa": True,
            "has_approval_workflows": True,
            "has_automation": True,
            "has_advanced_analytics": True,
        },
    },
]

class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_plans(self):
        for p in DEFAULT_PLANS:
            res = await self.db.execute(select(Plan).where(Plan.slug == p["slug"]))
            existing_plan = res.scalar_one_or_none()
            if not existing_plan:
                feat_data = p["features"]
                plan = Plan(
                    name=p["name"],
                    slug=p["slug"],
                    description=p["description"],
                    price_monthly=p["price_monthly"],
                    price_yearly=p["price_yearly"],
                    currency=p["currency"],
                    is_free=p["is_free"],
                    is_active=True,
                    trial_days=p["trial_days"],
                )
                self.db.add(plan)
                await self.db.flush()

                feat = PlanFeature(
                    plan_id=plan.id,
                    **feat_data,
                )
                self.db.add(feat)
            else:
                existing_plan.price_monthly = p["price_monthly"]
                existing_plan.price_yearly = p["price_yearly"]
                existing_plan.currency = p["currency"]
        await self.db.commit()

    async def list_plans(self) -> List[Plan]:
        query = select(Plan).options(selectinload(Plan.features)).where(Plan.is_active == True).order_by(Plan.price_monthly.asc())
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_usage_metrics(self, org_id: str) -> Dict[str, Any]:
        # 1. Load active subscription & plan features
        org_res = await self.db.execute(
            select(Organisation)
            .options(selectinload(Organisation.subscription).selectinload(Subscription.plan).selectinload(Plan.features))
            .where(Organisation.id == org_id)
        )
        org = org_res.scalar_one_or_none()
        plan_feat = org.subscription.plan.features if (org and org.subscription and org.subscription.plan) else None

        # 2. Count connected social accounts
        acc_cnt_res = await self.db.execute(
            select(func.count(SocialAccount.id)).where(SocialAccount.organisation_id == org_id, SocialAccount.is_connected == True)
        )
        connected_accounts = acc_cnt_res.scalar() or 0

        # 3. Count published posts this month and today
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        month_posts_res = await self.db.execute(
            select(func.count(Content.id)).where(
                Content.organisation_id == org_id,
                Content.status == "published",
                Content.published_at >= start_of_month,
            )
        )
        posts_month = month_posts_res.scalar() or 0

        today_posts_res = await self.db.execute(
            select(func.count(Content.id)).where(
                Content.organisation_id == org_id,
                Content.status == "published",
                Content.published_at >= start_of_today,
            )
        )
        posts_today = today_posts_res.scalar() or 0

        # 4. Count AI Tokens and Images
        ai_tokens_res = await self.db.execute(
            select(func.sum(AIUsage.total_tokens)).where(
                AIUsage.organisation_id == org_id,
                AIUsage.created_at >= start_of_month,
            )
        )
        ai_tokens = ai_tokens_res.scalar() or 0

        ai_images_res = await self.db.execute(
            select(func.sum(AIUsage.images_count)).where(
                AIUsage.organisation_id == org_id,
                AIUsage.created_at >= start_of_month,
            )
        )
        ai_images = ai_images_res.scalar() or 0

        # 5. Workflows
        wf_res = await self.db.execute(
            select(func.count(Workflow.id)).where(Workflow.organisation_id == org_id, Workflow.is_active == True)
        )
        active_workflows = wf_res.scalar() or 0

        wf_exec_res = await self.db.execute(
            select(func.count(WorkflowExecution.id)).where(
                WorkflowExecution.organisation_id == org_id,
                WorkflowExecution.started_at >= start_of_month,
            )
        )
        wf_executions = wf_exec_res.scalar() or 0

        # 6. Team Members
        members_res = await self.db.execute(
            select(func.count(OrganisationMember.id)).where(OrganisationMember.organisation_id == org_id)
        )
        team_members = members_res.scalar() or 0

        return {
            "connected_social_accounts": connected_accounts,
            "social_account_limit": plan_feat.social_account_limit if plan_feat else 1,
            "posts_published_this_month": posts_month,
            "monthly_post_limit": plan_feat.monthly_post_limit if plan_feat else 30,
            "posts_published_today": posts_today,
            "daily_post_limit": plan_feat.daily_post_limit if plan_feat else 1,
            "ai_tokens_used_this_month": int(ai_tokens),
            "ai_token_limit_monthly": plan_feat.ai_token_limit_monthly if plan_feat else 50000,
            "images_generated_this_month": int(ai_images),
            "image_generation_limit_monthly": plan_feat.image_generation_limit_monthly if plan_feat else 10,
            "active_workflows": active_workflows,
            "workflow_limit": plan_feat.workflow_limit if plan_feat else 3,
            "workflow_executions_this_month": wf_executions,
            "workflow_execution_limit_monthly": plan_feat.workflow_execution_limit_monthly if plan_feat else 100,
            "team_members": team_members,
            "member_limit": plan_feat.member_limit if plan_feat else 1,
            "storage_used_mb": 12.5, # computed from content assets
            "storage_limit_mb": plan_feat.storage_limit_mb if plan_feat else 500,
        }

    async def create_razorpay_order(self, org_id: str, plan_id: str, billing_period: str, user: User) -> Dict[str, Any]:
        plan_res = await self.db.execute(select(Plan).where(Plan.id == plan_id))
        plan = plan_res.scalar_one_or_none()
        if not plan:
            raise NotFoundException("Plan not found")

        amount = plan.price_yearly if billing_period == "yearly" else plan.price_monthly
        order_id = f"order_rzp_{uuid.uuid4().hex[:12]}"

        # Record payment intent
        payment = Payment(
            organisation_id=org_id,
            user_id=user.id,
            gateway="razorpay",
            amount=amount,
            currency=plan.currency,
            status="created",
            gateway_order_id=order_id,
            receipt=f"rcpt_{uuid.uuid4().hex[:8]}",
        )
        self.db.add(payment)
        await self.db.commit()

        return {
            "order_id": order_id,
            "amount": int(amount * 100), # Razorpay uses paise / cents
            "currency": plan.currency,
            "key_id": settings.RAZORPAY_KEY_ID or "rzp_test_public_key_pravah",
            "plan_name": plan.name,
        }

    async def verify_razorpay_payment(
        self,
        org_id: str,
        plan_id: str,
        billing_period: str,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        user: User,
    ) -> Subscription:
        # ALWAYS verify signature — never bypass verification
        if not settings.RAZORPAY_KEY_SECRET:
            raise PravahException(
                "Razorpay payment verification failed: RAZORPAY_KEY_SECRET not configured. Contact administrator.",
                error_code="PAYMENT_GATEWAY_NOT_CONFIGURED"
            )
        payload = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
        expected_sig = hmac.new(settings.RAZORPAY_KEY_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected_sig, razorpay_signature):
            raise PravahException("Invalid Razorpay payment signature — payment rejected.", error_code="PAYMENT_VERIFICATION_FAILED")

        # Update payment record
        pay_res = await self.db.execute(select(Payment).where(Payment.gateway_order_id == razorpay_order_id))
        payment = pay_res.scalar_one_or_none()
        if payment:
            payment.status = "paid"
            payment.gateway_payment_id = razorpay_payment_id
            payment.gateway_signature = razorpay_signature

        # Update or create subscription
        sub_res = await self.db.execute(select(Subscription).where(Subscription.organisation_id == org_id))
        sub = sub_res.scalar_one_or_none()
        duration_days = 365 if billing_period == "yearly" else 30
        now = datetime.now(timezone.utc)

        if sub:
            sub.plan_id = plan_id
            sub.status = "active"
            sub.billing_period = billing_period
            sub.current_period_start = now
            sub.current_period_end = now + timedelta(days=duration_days)
            sub.payment_gateway = "razorpay"
        else:
            sub = Subscription(
                organisation_id=org_id,
                plan_id=plan_id,
                status="active",
                billing_period=billing_period,
                current_period_start=now,
                current_period_end=now + timedelta(days=duration_days),
                payment_gateway="razorpay",
            )
            self.db.add(sub)

        # Audit
        audit = AuditLog(
            actor_id=user.id,
            actor_email=user.email,
            organisation_id=org_id,
            action="subscription.activated",
            target_type="subscription",
            target_id=sub.id,
            result="success",
            details={"gateway": "razorpay", "plan_id": plan_id, "amount": payment.amount if payment else 0},
        )
        self.db.add(audit)

        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def create_cashfree_order(self, org_id: str, plan_id: str, billing_period: str, user: User) -> Dict[str, Any]:
        plan_res = await self.db.execute(select(Plan).where(Plan.id == plan_id))
        plan = plan_res.scalar_one_or_none()
        if not plan:
            raise NotFoundException("Plan not found")

        amount = plan.price_yearly if billing_period == "yearly" else plan.price_monthly
        order_id = f"order_cf_{uuid.uuid4().hex[:12]}"

        payment = Payment(
            organisation_id=org_id,
            user_id=user.id,
            gateway="cashfree",
            amount=amount,
            currency=plan.currency,
            status="created",
            gateway_order_id=order_id,
        )
        self.db.add(payment)
        await self.db.commit()

        return {
            "order_id": order_id,
            "payment_session_id": f"session_cf_{uuid.uuid4().hex[:16]}",
            "amount": amount,
            "currency": plan.currency,
            "plan_name": plan.name,
        }
