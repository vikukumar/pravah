from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkflowNodeSchema(BaseModel):
    id: str
    type: str
    name: str
    category: str
    config: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 100, "y": 100})
    label: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None

    def model_dump(self, **kwargs):
        d = super().model_dump(**kwargs)
        return d


class WorkflowEdgeSchema(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    condition: Optional[str] = None
    type: Optional[str] = "default"


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNodeSchema]] = Field(default_factory=list)
    edges: Optional[List[WorkflowEdgeSchema]] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNodeSchema]] = None
    edges: Optional[List[WorkflowEdgeSchema]] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: str
    organisation_id: str
    name: str
    description: Optional[str] = None
    status: str
    version: int
    published_version: Optional[int] = None
    is_active: bool
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    tags: Optional[List[str]] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    last_executed_at: Optional[datetime] = None
    last_execution_status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WorkflowExecuteRequest(BaseModel):
    trigger_payload: Optional[Dict[str, Any]] = None
    trigger_source: Optional[str] = "manual"


class WorkflowNodeExecutionResponse(BaseModel):
    node_key: str
    node_name: str
    node_type: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    workflow_version: Optional[int] = None
    organisation_id: str
    trigger_source: str
    status: str
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    node_executions: List[WorkflowNodeExecutionResponse] = Field(default_factory=list)
