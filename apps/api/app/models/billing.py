import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel

class Plan(BaseModel):
    __tablename__ = "plans"

    name = Column(String(100), unique=True, index=True, nullable=False) # Free, Starter, Pro, Agency, Enterprise
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price_monthly = Column(Float, default=0.0, nullable=False)
    price_yearly = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    is_free = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    trial_days = Column(Integer, default=30, nullable=False)
    
    # Razorpay and Cashfree plan mapping IDs
    razorpay_plan_id_monthly = Column(String(100), nullable=True)
    razorpay_plan_id_yearly = Column(String(100), nullable=True)
    cashfree_plan_id_monthly = Column(String(100), nullable=True)
    cashfree_plan_id_yearly = Column(String(100), nullable=True)

    features = relationship("PlanFeature", back_populates="plan", uselist=False, cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="plan")

class PlanFeature(BaseModel):
    __tablename__ = "plan_features"

    plan_id = Column(String(36), ForeignKey("plans.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # Quantitative Quota Limits (0 or negative may denote unlimited or restricted)
    social_account_limit = Column(Integer, default=1, nullable=False)
    page_limit = Column(Integer, default=1, nullable=False)
    daily_post_limit = Column(Integer, default=1, nullable=False)
    monthly_post_limit = Column(Integer, default=30, nullable=False)
    ai_token_limit_monthly = Column(Integer, default=50000, nullable=False)
    image_generation_limit_monthly = Column(Integer, default=10, nullable=False)
    workflow_limit = Column(Integer, default=3, nullable=False)
    workflow_execution_limit_monthly = Column(Integer, default=100, nullable=False)
    member_limit = Column(Integer, default=1, nullable=False)
    storage_limit_mb = Column(Integer, default=500, nullable=False)
    analytics_retention_days = Column(Integer, default=30, nullable=False)
    
    # Feature Flags
    has_api_access = Column(Boolean, default=False, nullable=False)
    has_custom_providers = Column(Boolean, default=False, nullable=False)
    has_sso = Column(Boolean, default=False, nullable=False)
    has_2fa = Column(Boolean, default=True, nullable=False)
    has_approval_workflows = Column(Boolean, default=False, nullable=False)
    has_automation = Column(Boolean, default=True, nullable=False)
    has_advanced_analytics = Column(Boolean, default=False, nullable=False)

    plan = relationship("Plan", back_populates="features")

class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    status = Column(String(50), default="active", nullable=False, index=True) 
    # trial, active, past_due, grace_period, cancelled, expired, suspended
    
    billing_period = Column(String(20), default="monthly", nullable=False) # monthly, yearly
    current_period_start = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    
    payment_gateway = Column(String(50), nullable=True) # razorpay, cashfree
    external_subscription_id = Column(String(255), nullable=True, index=True)
    external_customer_id = Column(String(255), nullable=True)

    organisation = relationship("Organisation", back_populates="subscription")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")

class Payment(BaseModel):
    __tablename__ = "payments"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    gateway = Column(String(50), nullable=False) # razorpay, cashfree
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    
    status = Column(String(50), default="created", nullable=False, index=True)
    # created, pending, paid, failed, cancelled, refunded, partially_refunded, expired
    
    gateway_order_id = Column(String(255), nullable=True, index=True)
    gateway_payment_id = Column(String(255), nullable=True, index=True)
    gateway_signature = Column(String(500), nullable=True)
    
    receipt = Column(String(100), nullable=True)
    error_code = Column(String(100), nullable=True)
    error_description = Column(Text, nullable=True)

    subscription = relationship("Subscription", back_populates="payments")
    transactions = relationship("PaymentTransaction", back_populates="payment", cascade="all, delete-orphan")

class PaymentTransaction(BaseModel):
    __tablename__ = "payment_transactions"

    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False) # order_created, payment_captured, payment_failed, refund_issued
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    raw_payload = Column(JSON, nullable=True)

    payment = relationship("Payment", back_populates="transactions")

class PaymentWebhook(BaseModel):
    __tablename__ = "payment_webhooks"

    gateway = Column(String(50), nullable=False, index=True) # razorpay, cashfree
    event_type = Column(String(100), nullable=False)
    event_id = Column(String(255), unique=True, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
