from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class WorkflowNodeSchema(BaseModel):
    id: str
    type: str
    name: str
    category: str
    config: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})

class WorkflowEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    condition: Optional[str] = None

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    nodes: List[WorkflowNodeSchema] = Field(default_factory=list)
    edges: List[WorkflowEdgeSchema] = Field(default_factory=list)
    is_active: bool = True

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNodeSchema]] = None
    edges: Optional[List[WorkflowEdgeSchema]] = None
    status: Optional[str] = None # draft, published, archived, disabled
    is_active: Optional[bool] = None

class WorkflowResponse(BaseModel):
    id: str
    organisation_id: str
    name: str
    description: Optional[str]
    status: str
    version: int
    is_active: bool
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    last_executed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class WorkflowExecuteRequest(BaseModel):
    trigger_payload: Optional[Dict[str, Any]] = None

class WorkflowNodeExecutionResponse(BaseModel):
    node_key: str
    node_name: str
    node_type: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]

class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    organisation_id: str
    trigger_source: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    error_message: Optional[str]
    node_executions: List[WorkflowNodeExecutionResponse] = Field(default_factory=list)
