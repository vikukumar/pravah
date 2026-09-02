from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.api.deps import TenantContext, get_tenant_context, require_permission
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.workflow import (
    Workflow,
    WorkflowEdge,
    WorkflowExecution,
    WorkflowNode,
    WorkflowNodeExecution,
)
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    WorkflowNodeExecutionResponse,
    WorkflowResponse,
    WorkflowUpdate,
)
from app.services.workflow_engine import WorkflowEngine

router = APIRouter()

@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Workflow)
        .options(selectinload(Workflow.nodes), selectinload(Workflow.edges))
        .where(Workflow.organisation_id == tenant.organisation.id)
        .order_by(Workflow.created_at.desc())
    )
    res = await db.execute(query)
    workflows = res.scalars().all()
    return [
        WorkflowResponse(
            id=w.id,
            organisation_id=w.organisation_id,
            name=w.name,
            description=w.description,
            status=w.status,
            version=w.version,
            is_active=w.is_active,
            nodes=[
                {
                    "id": n.node_key,
                    "type": n.node_type,
                    "name": n.name,
                    "category": n.category,
                    "config": n.config,
                    "position": {"x": n.position_x, "y": n.position_y},
                }
                for n in w.nodes
            ],
            edges=[
                {
                    "id": f"{e.source_node_key}-{e.target_node_key}",
                    "source": e.source_node_key,
                    "target": e.target_node_key,
                    "sourceHandle": e.source_handle,
                    "targetHandle": e.target_handle,
                }
                for e in w.edges
            ],
            last_executed_at=w.last_executed_at,
            created_at=w.created_at,
            updated_at=w.updated_at,
        )
        for w in workflows
    ]

@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    tenant: TenantContext = Depends(require_permission("workflow.create")),
    db: AsyncSession = Depends(get_db)
):
    workflow = Workflow(
        organisation_id=tenant.organisation.id,
        created_by_id=tenant.user.id,
        name=payload.name,
        description=payload.description,
        status="published",
        version=1,
        is_active=payload.is_active,
        graph_data={
            "nodes": [n.model_dump() for n in payload.nodes],
            "edges": [e.model_dump() for e in payload.edges],
        },
    )
    db.add(workflow)
    await db.flush()

    # Save nodes
    for n in payload.nodes:
        node = WorkflowNode(
            workflow_id=workflow.id,
            node_key=n.id,
            name=n.name,
            node_type=n.type,
            category=n.category,
            config=n.config,
            position_x=int(n.position.get("x", 0)),
            position_y=int(n.position.get("y", 0)),
        )
        db.add(node)

    # Save edges
    for e in payload.edges:
        edge = WorkflowEdge(
            workflow_id=workflow.id,
            source_node_key=e.source,
            target_node_key=e.target,
            source_handle=e.sourceHandle,
            target_handle=e.targetHandle,
        )
        db.add(edge)

    await db.commit()
    await db.refresh(workflow)

    return WorkflowResponse(
        id=workflow.id,
        organisation_id=workflow.organisation_id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status,
        version=workflow.version,
        is_active=workflow.is_active,
        nodes=[n.model_dump() for n in payload.nodes],
        edges=[e.model_dump() for e in payload.edges],
        last_executed_at=None,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )

@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    payload: WorkflowExecuteRequest,
    tenant: TenantContext = Depends(require_permission("workflow.execute")),
    db: AsyncSession = Depends(get_db)
):
    engine = WorkflowEngine(db)
    execution = await engine.execute_workflow(
        workflow_id=workflow_id,
        org_id=tenant.organisation.id,
        trigger_source="manual",
        trigger_payload=payload.trigger_payload,
        actor=tenant.user,
    )

    # Load node executions
    node_execs_res = await db.execute(
        select(WorkflowNodeExecution).where(WorkflowNodeExecution.execution_id == execution.id)
    )
    node_execs = node_execs_res.scalars().all()

    return WorkflowExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        organisation_id=execution.organisation_id,
        trigger_source=execution.trigger_source,
        status=execution.status,
        started_at=execution.started_at,
        finished_at=execution.finished_at,
        duration_ms=execution.duration_ms,
        error_message=execution.error_message,
        node_executions=[
            WorkflowNodeExecutionResponse(
                node_key=ne.node_key,
                node_name=ne.node_name,
                node_type=ne.node_type,
                status=ne.status,
                started_at=ne.started_at,
                finished_at=ne.finished_at,
                duration_ms=ne.duration_ms,
                output_data=ne.output_data,
                error_message=ne.error_message,
            )
            for ne in node_execs
        ],
    )

@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: str,
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.node_executions))
        .where(
            WorkflowExecution.workflow_id == workflow_id,
            WorkflowExecution.organisation_id == tenant.organisation.id,
        )
        .order_by(WorkflowExecution.started_at.desc())
        .limit(20)
    )
    res = await db.execute(query)
    executions = res.scalars().all()

    return [
        WorkflowExecutionResponse(
            id=ex.id,
            workflow_id=ex.workflow_id,
            organisation_id=ex.organisation_id,
            trigger_source=ex.trigger_source,
            status=ex.status,
            started_at=ex.started_at,
            finished_at=ex.finished_at,
            duration_ms=ex.duration_ms,
            error_message=ex.error_message,
            node_executions=[
                WorkflowNodeExecutionResponse(
                    node_key=ne.node_key,
                    node_name=ne.node_name,
                    node_type=ne.node_type,
                    status=ne.status,
                    started_at=ne.started_at,
                    finished_at=ne.finished_at,
                    duration_ms=ne.duration_ms,
                    output_data=ne.output_data,
                    error_message=ne.error_message,
                )
                for ne in ex.node_executions
            ],
        )
        for ex in executions
    ]
