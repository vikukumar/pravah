import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from app.core.database import BaseModel

class Workflow(BaseModel):
    __tablename__ = "workflows"

    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft", nullable=False) # draft, published, archived, disabled
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Store complete graph JSON snapshot for fast serialization
    graph_data = Column(JSON, nullable=False) # { nodes: [], edges: [] }
    
    last_executed_at = Column(DateTime(timezone=True), nullable=True)

    organisation = relationship("Organisation", back_populates="workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowNode(BaseModel):
    __tablename__ = "workflow_nodes"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    node_key = Column(String(100), nullable=False) # client node id
    name = Column(String(100), nullable=False)
    node_type = Column(String(100), nullable=False) # trigger_schedule, ai_generate_text, social_publish, etc.
    category = Column(String(50), nullable=False) # trigger, logic, ai, social, utility
    config = Column(JSON, nullable=False) # node configuration parameters
    position_x = Column(Integer, default=0, nullable=False)
    position_y = Column(Integer, default=0, nullable=False)

    workflow = relationship("Workflow", back_populates="nodes")

class WorkflowEdge(BaseModel):
    __tablename__ = "workflow_edges"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_key = Column(String(100), nullable=False)
    target_node_key = Column(String(100), nullable=False)
    source_handle = Column(String(100), nullable=True)
    target_handle = Column(String(100), nullable=True)
    condition = Column(String(255), nullable=True)

    workflow = relationship("Workflow", back_populates="edges")

class WorkflowExecution(BaseModel):
    __tablename__ = "workflow_executions"

    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    organisation_id = Column(String(36), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    trigger_source = Column(String(50), nullable=False) # manual, schedule, webhook, content_event
    status = Column(String(50), default="pending", nullable=False, index=True) # pending, running, completed, failed, cancelled
    
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_context = Column(JSON, nullable=True) # runtime state / outputs

    workflow = relationship("Workflow", back_populates="executions")
    node_executions = relationship("WorkflowNodeExecution", back_populates="execution", cascade="all, delete-orphan")

class WorkflowNodeExecution(BaseModel):
    __tablename__ = "workflow_node_executions"

    execution_id = Column(String(36), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    node_key = Column(String(100), nullable=False)
    node_name = Column(String(100), nullable=False)
    node_type = Column(String(100), nullable=False)
    
    status = Column(String(50), default="pending", nullable=False) # pending, running, success, failed, skipped
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    execution = relationship("WorkflowExecution", back_populates="node_executions")
