"""
PRAVAH Workflow Database Models
==================================
Implements PRD §52, §105 — complete workflow persistence including
versioning, variables, secret references, templates, and run locks.
"""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import BaseModel


class Workflow(BaseModel):
    """Master workflow definition belonging to an organisation."""
    __tablename__ = "workflows"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # status: draft | published | archived | disabled
    status = Column(String(50), default="draft", nullable=False, index=True)
    # version: current draft version number (increments on each publish)
    version = Column(Integer, default=1, nullable=False)
    # published_version: the last published version number (execution always runs this)
    published_version = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)

    # Complete graph snapshot for fast serialization (draft state)
    graph_data = Column(JSON, nullable=False, default=dict)

    # Metadata
    tags = Column(JSON, nullable=True)          # List of string tags
    icon = Column(String(100), nullable=True)   # Lucide icon name
    color = Column(String(20), nullable=True)   # Hex color
    notes = Column(Text, nullable=True)          # Admin/user notes

    # Approval config
    requires_approval = Column(Boolean, default=False, nullable=False)
    approval_mode = Column(String(50), default="auto", nullable=False)  # auto | approval_required

    last_executed_at = Column(DateTime(timezone=True), nullable=True)
    last_execution_status = Column(String(50), nullable=True)

    # Relationships
    organisation = relationship("Organisation", back_populates="workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    versions = relationship("WorkflowVersion", back_populates="workflow", cascade="all, delete-orphan")
    variables = relationship("WorkflowVariable", back_populates="workflow", cascade="all, delete-orphan")
    secret_references = relationship("WorkflowSecretReference", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowVersion(BaseModel):
    """
    Immutable snapshot of a published workflow version.
    Executions always run against a specific published version.
    Editing a published workflow creates a new draft, not a modification of the version.
    """
    __tablename__ = "workflow_versions"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    published_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Immutable snapshot of the graph at publish time
    graph_snapshot = Column(JSON, nullable=False)  # {nodes: [], edges: []}
    variables_snapshot = Column(JSON, nullable=True)

    published_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)  # Optional publish message / changelog entry

    workflow = relationship("Workflow", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("workflow_id", "version_number", name="uq_workflow_version"),
    )


class WorkflowNode(BaseModel):
    """Individual node in a workflow graph."""
    __tablename__ = "workflow_nodes"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    node_key = Column(String(100), nullable=False)   # Client-assigned node ID (unique within workflow)
    name = Column(String(200), nullable=False)
    node_type = Column(String(100), nullable=False)  # Must match a NODE_REGISTRY key
    category = Column(String(50), nullable=False)    # trigger | logic | ai | social | utility | data | time | content
    config = Column(JSON, nullable=False, default=dict)
    position_x = Column(Float, default=250.0, nullable=False)
    position_y = Column(Float, default=100.0, nullable=False)
    # Visual customization
    label = Column(String(200), nullable=True)       # User-provided display label
    color = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)

    workflow = relationship("Workflow", back_populates="nodes")


class WorkflowEdge(BaseModel):
    """Connection between two nodes in a workflow graph."""
    __tablename__ = "workflow_edges"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_key = Column(String(100), nullable=False)
    target_node_key = Column(String(100), nullable=False)
    source_handle = Column(String(100), nullable=True)  # e.g. "true", "false", "case_1"
    target_handle = Column(String(100), nullable=True)
    condition = Column(String(255), nullable=True)
    # Visual
    edge_type = Column(String(50), default="default", nullable=True)  # default | step | smooth

    workflow = relationship("Workflow", back_populates="edges")


class WorkflowVariable(BaseModel):
    """Workflow-level variable definitions (referenced via {{vars.NAME}})."""
    __tablename__ = "workflow_variables"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    label = Column(String(200), nullable=True)
    # value_type: text | number | boolean | json | secret_ref
    value_type = Column(String(50), default="text", nullable=False)
    default_value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    is_secret_ref = Column(Boolean, default=False, nullable=False)

    workflow = relationship("Workflow", back_populates="variables")

    __table_args__ = (
        UniqueConstraint("workflow_id", "key", name="uq_workflow_variable_key"),
    )


class WorkflowSecretReference(BaseModel):
    """
    Named secret reference for use in node configuration.
    Nodes reference secrets as {{secret:REF_NAME}} — never as raw values.
    The actual secret value is stored encrypted and resolved at execution time only.
    """
    __tablename__ = "workflow_secret_references"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    ref_name = Column(String(100), nullable=False)     # Reference name used in node config
    description = Column(Text, nullable=True)
    encrypted_value = Column(Text, nullable=True)      # Fernet-encrypted secret value
    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    workflow = relationship("Workflow", back_populates="secret_references")

    __table_args__ = (
        UniqueConstraint("workflow_id", "ref_name", name="uq_workflow_secret_ref"),
    )


class WorkflowExecution(BaseModel):
    """
    Record of a single workflow execution run.
    Each execution is associated with the specific workflow version that ran.
    """
    __tablename__ = "workflow_executions"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_version = Column(Integer, nullable=True)   # Which version was executed
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # trigger_source: manual | schedule | webhook | content_event | campaign_event | approval_event
    trigger_source = Column(String(50), nullable=False, default="manual")
    trigger_payload = Column(JSON, nullable=True)

    # Status state machine: queued → running → completed | failed | cancelled | timed_out
    status = Column(String(50), default="queued", nullable=False, index=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    queued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    # execution_context: runtime outputs keyed by node_key (secrets redacted)
    execution_context = Column(JSON, nullable=True)

    workflow = relationship("Workflow", back_populates="executions")
    node_executions = relationship("WorkflowNodeExecution", back_populates="execution", cascade="all, delete-orphan")


class WorkflowNodeExecution(BaseModel):
    """Execution record for a single node within a workflow execution."""
    __tablename__ = "workflow_node_executions"

    execution_id = Column(String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    node_key = Column(String(100), nullable=False)
    node_name = Column(String(200), nullable=False)
    node_type = Column(String(100), nullable=False)

    # status: queued | running | success | failed | skipped | retrying
    status = Column(String(50), default="queued", nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Secrets are NEVER stored in input_data or output_data (redacted before persist)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    execution = relationship("WorkflowExecution", back_populates="node_executions")


class WorkflowTemplate(BaseModel):
    """
    Reusable workflow templates (admin-created or user-saved).
    Templates are copied into the organisation context when used — never shared directly.
    """
    __tablename__ = "workflow_templates"

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # e.g. "publishing", "analytics", "engagement"
    icon = Column(String(100), nullable=True)
    color = Column(String(20), nullable=True)
    tags = Column(JSON, nullable=True)

    # Complete workflow graph definition
    graph_data = Column(JSON, nullable=False, default=dict)

    is_active = Column(Boolean, default=True, nullable=False)
    is_admin_template = Column(Boolean, default=False, nullable=False)  # Platform-level vs user-saved
    # Plan-gated availability
    plan_requirements = Column(JSON, nullable=True)  # List of required plan features

    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="SET NULL"), nullable=True)
    # usage_count: tracks how many times this template has been used (informational)
    usage_count = Column(Integer, default=0, nullable=False)


class WorkflowRunLock(BaseModel):
    """
    Idempotency lock to prevent concurrent duplicate execution of the same workflow.
    Automatically expires to prevent deadlocks.
    """
    __tablename__ = "workflow_run_locks"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    execution_id = Column(String(36), nullable=False)
    idempotency_key = Column(String(255), nullable=False, unique=True)
    locked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_released = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_workflow_run_lock_key"),
    )
