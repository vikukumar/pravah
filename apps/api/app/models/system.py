from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel

class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organisation_id = Column(String(36), nullable=True, index=True)
    
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="info", nullable=False) # info, success, warning, error, security
    category = Column(String(50), nullable=False) # publishing, approval, workflow, billing, security, token_expired
    
    action_url = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="notifications")

class NotificationPreference(BaseModel):
    __tablename__ = "notification_preferences"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    email_publishing_success = Column(Boolean, default=True, nullable=False)
    email_publishing_failure = Column(Boolean, default=True, nullable=False)
    email_content_approval = Column(Boolean, default=True, nullable=False)
    email_workflow_failure = Column(Boolean, default=True, nullable=False)
    email_security_alerts = Column(Boolean, default=True, nullable=False)
    email_billing_updates = Column(Boolean, default=True, nullable=False)
    
    in_app_all = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="notification_preferences")

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    actor_id = Column(String(36), nullable=True, index=True) # user_id or system
    actor_email = Column(String(255), nullable=True)
    organisation_id = Column(String(36), nullable=True, index=True)
    
    action = Column(String(100), nullable=False, index=True) 
    # user.login, user.failed_login, content.published, workflow.executed, plan.changed, etc.
    target_type = Column(String(100), nullable=True) # content, organisation, role, user, billing, workflow
    target_id = Column(String(36), nullable=True)
    
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    result = Column(String(50), default="success", nullable=False) # success, failure, denied
    details = Column(JSON, nullable=True) # sanitized metadata

class Dashboard(BaseModel):
    __tablename__ = "dashboards"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(100), default="Default Overview", nullable=False)
    is_default = Column(Boolean, default=True, nullable=False)
    layout_data = Column(JSON, nullable=False) # array of widget positions and sizes

    organisation = relationship("Organisation", back_populates="dashboard_layouts")
    widgets = relationship("DashboardWidget", back_populates="dashboard", cascade="all, delete-orphan")

class DashboardWidget(BaseModel):
    __tablename__ = "dashboard_widgets"

    dashboard_id = Column(String(36), ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False, index=True)
    widget_type = Column(String(100), nullable=False) # post_metrics, scheduled_posts, engagement_chart, ai_recommendations, plan_usage
    title = Column(String(100), nullable=False)
    grid_x = Column(Integer, default=0, nullable=False)
    grid_y = Column(Integer, default=0, nullable=False)
    grid_w = Column(Integer, default=4, nullable=False)
    grid_h = Column(Integer, default=3, nullable=False)
    config = Column(JSON, nullable=True)

    dashboard = relationship("Dashboard", back_populates="widgets")

class SystemSetting(BaseModel):
    __tablename__ = "system_settings"

    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False) # Exposed to frontend without auth
    is_encrypted = Column(Boolean, default=False, nullable=False)

class FeatureFlag(BaseModel):
    __tablename__ = "feature_flags"

    key = Column(String(100), unique=True, index=True, nullable=False) # e.g. "ai_image_gen", "custom_sso", "advanced_analytics"
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_enabled_globally = Column(Boolean, default=True, nullable=False)
    allowed_plans = Column(JSON, nullable=True) # list of plan slugs
    allowed_organisations = Column(JSON, nullable=True) # list of org ids
    allowed_users = Column(JSON, nullable=True) # list of user ids

class Webhook(BaseModel):
    __tablename__ = "webhooks"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    target_url = Column(String(500), nullable=False)
    secret_encrypted = Column(Text, nullable=False)
    events = Column(JSON, nullable=False) # list of subscribed event types
    is_active = Column(Boolean, default=True, nullable=False)

class Job(BaseModel):
    __tablename__ = "jobs"

    organisation_id = Column(String(36), nullable=True, index=True)
    job_type = Column(String(100), nullable=False, index=True) # publish_content, sync_social, run_workflow, send_email
    status = Column(String(50), default="pending", nullable=False, index=True) # pending, queued, running, completed, failed, cancelled
    payload = Column(JSON, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    retries = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    error_message = Column(Text, nullable=True)

    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")

class JobExecution(BaseModel):
    __tablename__ = "job_executions"

    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False) # success, failed
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error = Column(Text, nullable=True)

    job = relationship("Job", back_populates="executions")
