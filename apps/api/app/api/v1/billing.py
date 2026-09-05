from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import TenantContext, require_permission
from app.core.database import get_db
from app.models.billing import Subscription
from app.schemas.billing import (
    ChangePlanRequest,
    CashfreeOrderCreateRequest,
    PlanFeatureSchema,
    PlanResponse,
    RazorpayOrderCreateRequest,
    RazorpayVerifyRequest,
    SubscriptionResponse,
    UsageMetricsResponse,
)
from app.services.billing_service import BillingService
from app.services.currency_service import CurrencyService

router = APIRouter()

@router.get("/exchange-rates")
async def get_exchange_rates():
    """Returns real-time currency exchange rates relative to base INR (Rupee)."""
    return await CurrencyService.get_exchange_rates()

@router.get("/plans", response_model=List[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db)):
    billing_svc = BillingService(db)
    plans = await billing_svc.list_plans()
    return [
        PlanResponse(
            id=p.id,
            name=p.name,
            slug=p.slug,
            description=p.description,
            price_monthly=p.price_monthly,
            price_yearly=p.price_yearly,
            currency=p.currency,
            is_free=p.is_free,
            is_active=p.is_active,
            trial_days=p.trial_days,
            features=PlanFeatureSchema(
                social_account_limit=p.features.social_account_limit,
                page_limit=p.features.page_limit,
                daily_post_limit=p.features.daily_post_limit,
                monthly_post_limit=p.features.monthly_post_limit,
                ai_token_limit_monthly=p.features.ai_token_limit_monthly,
                image_generation_limit_monthly=p.features.image_generation_limit_monthly,
                workflow_limit=p.features.workflow_limit,
                workflow_execution_limit_monthly=p.features.workflow_execution_limit_monthly,
                member_limit=p.features.member_limit,
                storage_limit_mb=p.features.storage_limit_mb,
                analytics_retention_days=p.features.analytics_retention_days,
                has_api_access=p.features.has_api_access,
                has_custom_providers=p.features.has_custom_providers,
                has_sso=p.features.has_sso,
                has_2fa=p.features.has_2fa,
                has_approval_workflows=p.features.has_approval_workflows,
                has_automation=p.features.has_automation,
                has_advanced_analytics=p.features.has_advanced_analytics,
            ) if p.features else PlanFeatureSchema(),
        )
        for p in plans
    ]

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_active_subscription(
    tenant: TenantContext = Depends(require_permission("billing.view")),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(Subscription.organisation_id == tenant.organisation.id)
    )
    res = await db.execute(query)
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found.")

    return SubscriptionResponse(
        id=sub.id,
        organisation_id=sub.organisation_id,
        plan_id=sub.plan_id,
        plan_name=sub.plan.name if sub.plan else "Free",
        status=sub.status,
        billing_period=sub.billing_period,
        current_period_start=sub.current_period_start,
        current_period_end=sub.current_period_end,
        trial_end=sub.trial_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        payment_gateway=sub.payment_gateway,
    )

@router.post("/change-plan", response_model=SubscriptionResponse)
async def change_subscription_plan(
    payload: ChangePlanRequest,
    tenant: TenantContext = Depends(require_permission("billing.manage")),
    db: AsyncSession = Depends(get_db)
):
    """
    Directly updates or switches the organisation's active subscription plan.
    Enables instant quota expansion.
    """
    billing_svc = BillingService(db)
    sub = await billing_svc.activate_plan(
        org_id=tenant.organisation.id,
        plan_id=payload.plan_id,
        billing_period=payload.billing_period,
        user=tenant.user,
    )
    res = await db.execute(
        select(Subscription).options(selectinload(Subscription.plan)).where(Subscription.id == sub.id)
    )
    updated_sub = res.scalar_one_or_none() or sub
    return SubscriptionResponse(
        id=updated_sub.id,
        organisation_id=updated_sub.organisation_id,
        plan_id=updated_sub.plan_id,
        plan_name=updated_sub.plan.name if updated_sub.plan else "Free",
        status=updated_sub.status,
        billing_period=updated_sub.billing_period,
        current_period_start=updated_sub.current_period_start,
        current_period_end=updated_sub.current_period_end,
        trial_end=updated_sub.trial_end,
        cancel_at_period_end=updated_sub.cancel_at_period_end,
        payment_gateway=updated_sub.payment_gateway,
    )

@router.get("/usage", response_model=UsageMetricsResponse)
async def get_usage(
    tenant: TenantContext = Depends(require_permission("billing.view")),
    db: AsyncSession = Depends(get_db)
):
    billing_svc = BillingService(db)
    metrics = await billing_svc.get_usage_metrics(tenant.organisation.id)
    return UsageMetricsResponse(**metrics)

@router.post("/razorpay/create-order")
async def create_razorpay_order(
    payload: RazorpayOrderCreateRequest,
    tenant: TenantContext = Depends(require_permission("billing.manage")),
    db: AsyncSession = Depends(get_db)
):
    billing_svc = BillingService(db)
    order_data = await billing_svc.create_razorpay_order(
        org_id=tenant.organisation.id,
        plan_id=payload.plan_id,
        billing_period=payload.billing_period,
        user=tenant.user,
    )
    return order_data

@router.post("/razorpay/verify")
async def verify_razorpay_order(
    payload: RazorpayVerifyRequest,
    tenant: TenantContext = Depends(require_permission("billing.manage")),
    db: AsyncSession = Depends(get_db)
):
    billing_svc = BillingService(db)
    sub = await billing_svc.verify_razorpay_payment(
        org_id=tenant.organisation.id,
        plan_id=payload.plan_id,
        billing_period=payload.billing_period,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
        user=tenant.user,
    )
    return {"message": "Payment verified and subscription activated successfully."}

@router.post("/cashfree/create-order")
async def create_cashfree_order(
    payload: CashfreeOrderCreateRequest,
    tenant: TenantContext = Depends(require_permission("billing.manage")),
    db: AsyncSession = Depends(get_db)
):
    billing_svc = BillingService(db)
    order_data = await billing_svc.create_cashfree_order(
        org_id=tenant.organisation.id,
        plan_id=payload.plan_id,
        billing_period=payload.billing_period,
        user=tenant.user,
    )
    return order_data
