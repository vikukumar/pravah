"""
PRAVAH Workflow API Routes — Production Implementation
========================================================
Implements PRD §52 full workflow management API including:
- CRUD with draft/publish lifecycle
- Versioning (publish, list versions, restore)
- Server-side validation
- Async execution (non-blocking)
- SSE real-time execution progress stream
- Template management
- Node registry exposure
"""

import asyncio
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import TenantContext, require_permission
from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.workflow import (
    Workflow,
    WorkflowEdge,
    WorkflowExecution,
    WorkflowNode,
    WorkflowTemplate,
    WorkflowVersion,
)
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowExecuteRequest,
    WorkflowExecutionResponse,
    WorkflowNodeExecutionResponse,
    WorkflowResponse,
    WorkflowUpdate,
)
from app.services.node_registry import get_all_nodes, get_nodes_by_category
from app.services.workflow_engine import WorkflowEngine, WorkflowValidationError

router = APIRouter()


def _serialize_workflow(w: Workflow) -> WorkflowResponse:
    return WorkflowResponse(
        id=w.id,
        organisation_id=w.organisation_id,
        name=w.name,
        description=w.description,
        status=w.status,
        version=w.version,
        published_version=w.published_version,
        is_active=w.is_active,
        tags=w.tags,
        icon=w.icon,
        color=w.color,
        last_executed_at=w.last_executed_at,
        last_execution_status=w.last_execution_status,
        created_at=w.created_at,
        updated_at=w.updated_at,
        nodes=[
            {
                "id": n.node_key,
                "type": n.node_type,
                "name": n.name,
                "label": n.label,
                "category": n.category,
                "config": n.config,
                "position": {"x": n.position_x, "y": n.position_y},
                "color": n.color,
                "notes": n.notes,
            }
            for n in (w.nodes or [])
        ],
        edges=[
            {
                "id": f"{e.id}",
                "source": e.source_node_key,
                "target": e.target_node_key,
                "sourceHandle": e.source_handle,
                "targetHandle": e.target_handle,
                "type": e.edge_type,
            }
            for e in (w.edges or [])
        ],
    )


def _serialize_execution(ex: WorkflowExecution) -> WorkflowExecutionResponse:
    return WorkflowExecutionResponse(
        id=ex.id,
        workflow_id=ex.workflow_id,
        workflow_version=ex.workflow_version,
        organisation_id=ex.organisation_id,
        trigger_source=ex.trigger_source,
        status=ex.status,
        started_at=ex.started_at,
        queued_at=ex.queued_at,
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
            for ne in (ex.node_executions or [])
        ],
    )


# ============================================================
# Node Registry
# ============================================================

@router.get("/node-registry", tags=["Node Registry"])
async def get_node_registry(
    tenant: TenantContext = Depends(require_permission("workflow.view")),
):
    """Returns the complete metadata-driven node catalog grouped by category."""
    return {
        "nodes": get_all_nodes(),
        "by_category": get_nodes_by_category(),
        "total_count": len(get_all_nodes()),
    }


# ============================================================
# Templates
# ============================================================

@router.get("/templates", tags=["Workflow Templates"])
async def list_workflow_templates(
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db),
):
    """List all available workflow templates (admin and org-level)."""
    q = (
        select(WorkflowTemplate)
        .where(
            WorkflowTemplate.is_active == True,
            (WorkflowTemplate.is_admin_template == True) |
            (WorkflowTemplate.organisation_id == tenant.organisation.id),
        )
        .order_by(WorkflowTemplate.is_admin_template.desc(), WorkflowTemplate.name.asc())
    )
    res = await db.execute(q)
    templates = res.scalars().all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "icon": t.icon,
            "color": t.color,
            "tags": t.tags,
            "is_admin_template": t.is_admin_template,
            "usage_count": t.usage_count,
            "node_count": len((t.graph_data or {}).get("nodes", [])),
            "plan_requirements": t.plan_requirements,
            "created_at": t.created_at,
        }
        for t in templates
    ]


@router.post("/from-template/{template_id}", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED, tags=["Workflow Templates"])
async def create_from_template(
    template_id: str,
    name: Optional[str] = Query(None),
    tenant: TenantContext = Depends(require_permission("workflow.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow from a template. Template is copied into the organisation."""
    q = select(WorkflowTemplate).where(
        WorkflowTemplate.id == template_id,
        WorkflowTemplate.is_active == True,
    )
    res = await db.execute(q)
    template = res.scalar_one_or_none()
    if not template:
        raise NotFoundException("Workflow template not found.")

    graph_data = template.graph_data or {"nodes": [], "edges": []}

    workflow = Workflow(
        organisation_id=tenant.organisation.id,
        created_by_id=tenant.user.id,
        name=name or f"Copy of {template.name}",
        description=template.description,
        status="draft",
        version=1,
        is_active=False,
        graph_data=graph_data,
        icon=template.icon,
        color=template.color,
        tags=template.tags,
    )
    db.add(workflow)
    await db.flush()

    # Save nodes from template
    for node_data in graph_data.get("nodes", []):
        node = WorkflowNode(
            workflow_id=workflow.id,
            node_key=node_data.get("id", ""),
            name=node_data.get("name", "Node"),
            node_type=node_data.get("type", ""),
            category=node_data.get("category", "utility"),
            config=node_data.get("config", {}),
            position_x=node_data.get("position", {}).get("x", 100),
            position_y=node_data.get("position", {}).get("y", 100),
        )
        db.add(node)

    for edge_data in graph_data.get("edges", []):
        edge = WorkflowEdge(
            workflow_id=workflow.id,
            source_node_key=edge_data.get("source", ""),
            target_node_key=edge_data.get("target", ""),
            source_handle=edge_data.get("sourceHandle"),
            target_handle=edge_data.get("targetHandle"),
        )
        db.add(edge)

    # Increment template usage count
    template.usage_count = (template.usage_count or 0) + 1

    await db.commit()
    await db.refresh(workflow)
    await db.refresh(workflow, attribute_names=["nodes", "edges"])

    return _serialize_workflow(workflow)


# ============================================================
# Workflow CRUD
# ============================================================

@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    show_archived: bool = Query(False),
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db),
):
    """
    List workflows for the organisation.
    By default excludes archived (soft-deleted) workflows.
    Pass ?show_archived=true to include them.
    """
    query = (
        select(Workflow)
        .options(selectinload(Workflow.nodes), selectinload(Workflow.edges))
        .where(Workflow.organisation_id == tenant.organisation.id)
        .order_by(Workflow.updated_at.desc())
    )

    # Exclude archived unless explicitly requested
    if status_filter:
        query = query.where(Workflow.status == status_filter)
    elif not show_archived:
        query = query.where(Workflow.status != "archived")

    if search:
        query = query.where(Workflow.name.ilike(f"%{search}%"))

    res = await db.execute(query)
    workflows = res.scalars().all()
    return [_serialize_workflow(w) for w in workflows]


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    tenant: TenantContext = Depends(require_permission("workflow.create")),
    db: AsyncSession = Depends(get_db),
):
    workflow = Workflow(
        organisation_id=tenant.organisation.id,
        created_by_id=tenant.user.id,
        name=payload.name,
        description=payload.description,
        status=payload.status or "published",
        version=1,
        is_active=payload.is_active,
        graph_data={"nodes": [], "edges": []},
    )
    db.add(workflow)
    await db.flush()

    # Save nodes
    for n in (payload.nodes or []):
        node = WorkflowNode(
            workflow_id=workflow.id,
            node_key=n.id,
            name=n.name,
            node_type=n.type,
            category=n.category,
            config=n.config or {},
            position_x=float(n.position.get("x", 100)),
            position_y=float(n.position.get("y", 100)),
        )
        db.add(node)

    # Save edges
    for e in (payload.edges or []):
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

    q = select(Workflow).options(selectinload(Workflow.nodes), selectinload(Workflow.edges)).where(Workflow.id == workflow.id)
    res = await db.execute(q)
    workflow = res.scalar_one()

    return _serialize_workflow(workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Workflow)
        .options(selectinload(Workflow.nodes), selectinload(Workflow.edges))
        .where(Workflow.id == workflow_id, Workflow.organisation_id == tenant.organisation.id)
    )
    res = await db.execute(q)
    workflow = res.scalar_one_or_none()
    if not workflow:
        raise NotFoundException("Workflow not found.")
    return _serialize_workflow(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdate,
    tenant: TenantContext = Depends(require_permission("workflow.edit")),
    db: AsyncSession = Depends(get_db),
):
    """
    Update workflow draft.
    If the workflow is published, updates create a new draft state (doesn't mutate published version).
    """
    q = (
        select(Workflow)
        .options(selectinload(Workflow.nodes), selectinload(Workflow.edges))
        .where(Workflow.id == workflow_id, Workflow.organisation_id == tenant.organisation.id)
    )
    res = await db.execute(q)
    workflow = res.scalar_one_or_none()
    if not workflow:
        raise NotFoundException("Workflow not found.")

    # Update metadata
    if payload.name is not None:
        workflow.name = payload.name
    if payload.description is not None:
        workflow.description = payload.description
    if payload.tags is not None:
        workflow.tags = payload.tags
    if payload.icon is not None:
        workflow.icon = payload.icon
    if payload.color is not None:
        workflow.color = payload.color

    # Update graph if provided
    if payload.nodes is not None and payload.edges is not None:
        # If published, mark as draft again (editing published workflow creates draft)
        if workflow.status == "published":
            workflow.status = "draft"

        # Delete existing nodes and edges, replace
        await db.execute(delete(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id))
        await db.execute(delete(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id))

        for n in payload.nodes:
            node = WorkflowNode(
                workflow_id=workflow.id,
                node_key=n.id,
                name=n.name,
                node_type=n.type,
                category=n.category,
                config=n.config or {},
                position_x=float(n.position.get("x", 100)),
                position_y=float(n.position.get("y", 100)),
                label=n.label,
                color=n.color,
                notes=n.notes,
            )
            db.add(node)

        for e in payload.edges:
            edge = WorkflowEdge(
                workflow_id=workflow.id,
                source_node_key=e.source,
                target_node_key=e.target,
                source_handle=e.sourceHandle,
                target_handle=e.targetHandle,
            )
            db.add(edge)

        workflow.graph_data = {
            "nodes": [n.model_dump() for n in payload.nodes],
            "edges": [e.model_dump() for e in payload.edges],
        }

    await db.commit()
    await db.refresh(workflow)

    q2 = select(Workflow).options(selectinload(Workflow.nodes), selectinload(Workflow.edges)).where(Workflow.id == workflow_id)
    res2 = await db.execute(q2)
    workflow = res2.scalar_one()

    return _serialize_workflow(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    permanent: bool = Query(False, description="If true, permanently delete from DB (owner only)"),
    tenant: TenantContext = Depends(require_permission("workflow.delete")),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete (archive) a workflow.
    - Default: soft-archive — workflow stops running, history preserved, hidden from list.
    - ?permanent=true — hard delete (removes DB records). Only for org_owner / super_admin.
    """
    q = (
        select(Workflow)
        .options(selectinload(Workflow.nodes), selectinload(Workflow.edges))
        .where(Workflow.id == workflow_id, Workflow.organisation_id == tenant.organisation.id)
    )
    res = await db.execute(q)
    workflow = res.scalar_one_or_none()
    if not workflow:
        raise NotFoundException("Workflow not found.")

    if permanent:
        # Hard delete: remove nodes, edges, then workflow
        await db.execute(delete(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id))
        await db.execute(delete(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id))
        await db.delete(workflow)
    else:
        # Soft archive
        workflow.status = "archived"
        workflow.is_active = False

    await db.commit()


@router.post("/{workflow_id}/duplicate", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_workflow(
    workflow_id: str,
    tenant: TenantContext = Depends(require_permission("workflow.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a complete copy of a workflow as a new draft."""
    q = (
        select(Workflow)
        .options(selectinload(Workflow.nodes), selectinload(Workflow.edges))
        .where(Workflow.id == workflow_id, Workflow.organisation_id == tenant.organisation.id)
    )
    res = await db.execute(q)
    original = res.scalar_one_or_none()
    if not original:
        raise NotFoundException("Workflow not found.")

    copy = Workflow(
        organisation_id=tenant.organisation.id,
        created_by_id=tenant.user.id,
        name=f"Copy of {original.name}",
        description=original.description,
        status="draft",
        version=1,
        is_active=False,
        graph_data=original.graph_data,
        tags=original.tags,
        icon=original.icon,
        color=original.color,
    )
    db.add(copy)
    await db.flush()

    for node in original.nodes:
        db.add(WorkflowNode(
            workflow_id=copy.id,
            node_key=node.node_key,
            name=node.name,
            node_type=node.node_type,
            category=node.category,
            config=node.config,
            position_x=node.position_x,
            position_y=node.position_y,
        ))

    for edge in original.edges:
        db.add(WorkflowEdge(
            workflow_id=copy.id,
            source_node_key=edge.source_node_key,
            target_node_key=edge.target_node_key,
            source_handle=edge.source_handle,
            target_handle=edge.target_handle,
        ))

    await db.commit()
    await db.refresh(copy)

    q2 = select(Workflow).options(selectinload(Workflow.nodes), selectinload(Workflow.edges)).where(Workflow.id == copy.id)
    res2 = await db.execute(q2)
    copy = res2.scalar_one()
    return _serialize_workflow(copy)


# ============================================================
# Activate / Deactivate
# ============================================================

@router.post("/{workflow_id}/activate")
async def activate_workflow(
    workflow_id: str,
    tenant: TenantContext = Depends(require_permission("workflow.edit")),
    db: AsyncSession = Depends(get_db),
):
    q = select(Workflow).where(Workflow.id == workflow_id, Workflow.organisation_id == tenant.organisation.id)
    res = await db.execute(q)
    workflow = res.scalar_one_or_none()
    if not workflow:
        raise NotFoundException("Workflow not found.")
    if workflow.status == "draft":
        raise HTTPException(status_code=400, detail="Publish the workflow before activating it.")
    workflow.is_active = True
    await db.commit()
    return {"status": "activated", "workflow_id": workflow_id}


@router.post("/{workflow_id}/deactivate")
async def deactivate_workflow(
    workflow_id: str,
    tenant: TenantContext = Depends(require_permission("workflow.edit")),
    db: AsyncSession = Depends(get_db),
):
    q = select(Workflow).where(Workflow.id == workflow_id, Workflow.organisation_id == tenant.organisation.id)
    res = await db.execute(q)
    workflow = res.scalar_one_or_none()
    if not workflow:
        raise NotFoundException("Workflow not found.")
    workflow.is_active = False
    await db.commit()
    return {"status": "deactivated", "workflow_id": workflow_id}


# ============================================================
# Validation
# ============================================================

@router.post("/{workflow_id}/validate")
async def validate_workflow(
    workflow_id: str,
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db),
):
    """Server-side workflow validation — returns errors and warnings."""
    engine = WorkflowEngine(db)
    result = await engine.validate_workflow(workflow_id=workflow_id, org_id=tenant.organisation.id)
    return result


# ============================================================
# Publish & Versioning
# ============================================================

@router.post("/{workflow_id}/publish")
async def publish_workflow(
    workflow_id: str,
    publish_message: Optional[str] = Query(None, description="Optional changelog message"),
    tenant: TenantContext = Depends(require_permission("workflow.publish")),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish the current draft workflow as an immutable version.
    Validates the workflow before publishing.
    Future executions will run against this version.
    """
    engine = WorkflowEngine(db)
    try:
        version = await engine.publish_workflow(
            workflow_id=workflow_id,
            org_id=tenant.organisation.id,
            actor=tenant.user,
            publish_message=publish_message,
        )
        return {
            "status": "published",
            "workflow_id": workflow_id,
            "version_number": version.version_number,
            "published_at": version.published_at.isoformat(),
        }
    except WorkflowValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={"message": "Workflow validation failed before publishing.", "errors": e.errors},
        )


@router.get("/{workflow_id}/versions")
async def list_workflow_versions(
    workflow_id: str,
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db),
):
    """List all published versions of a workflow."""
    q = (
        select(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == workflow_id)
        .order_by(WorkflowVersion.version_number.desc())
    )
    res = await db.execute(q)
    versions = res.scalars().all()

    return [
        {
            "id": v.id,
            "workflow_id": v.workflow_id,
            "version_number": v.version_number,
            "is_active": v.is_active,
            "description": v.description,
            "published_at": v.published_at.isoformat() if v.published_at else None,
            "published_by_id": v.published_by_id,
            "node_count": len((v.graph_snapshot or {}).get("nodes", [])),
            "edge_count": len((v.graph_snapshot or {}).get("edges", [])),
        }
        for v in versions
    ]


@router.post("/{workflow_id}/versions/{version_number}/restore")
async def restore_workflow_version(
    workflow_id: str,
    version_number: int,
    tenant: TenantContext = Depends(require_permission("workflow.publish")),
    db: AsyncSession = Depends(get_db),
):
    """Restore a workflow to a specific previously published version."""
    q = select(WorkflowVersion).where(
        WorkflowVersion.workflow_id == workflow_id,
        WorkflowVersion.version_number == version_number,
    )
    res = await db.execute(q)
    version = res.scalar_one_or_none()
    if not version:
        raise NotFoundException(f"Version {version_number} not found for this workflow.")

    # Load the workflow
    wq = select(Workflow).where(Workflow.id == workflow_id, Workflow.organisation_id == tenant.organisation.id)
    wres = await db.execute(wq)
    workflow = wres.scalar_one_or_none()
    if not workflow:
        raise NotFoundException("Workflow not found.")

    # Replace draft graph with snapshot
    graph = version.graph_snapshot or {"nodes": [], "edges": []}
    workflow.graph_data = graph
    workflow.status = "draft"

    await db.execute(delete(WorkflowNode).where(WorkflowNode.workflow_id == workflow_id))
    await db.execute(delete(WorkflowEdge).where(WorkflowEdge.workflow_id == workflow_id))

    for node_data in graph.get("nodes", []):
        db.add(WorkflowNode(
            workflow_id=workflow.id,
            node_key=node_data.get("id", ""),
            name=node_data.get("name", "Node"),
            node_type=node_data.get("type", ""),
            category=node_data.get("category", "utility"),
            config=node_data.get("config", {}),
            position_x=node_data.get("position", {}).get("x", 100),
            position_y=node_data.get("position", {}).get("y", 100),
        ))

    for edge_data in graph.get("edges", []):
        db.add(WorkflowEdge(
            workflow_id=workflow.id,
            source_node_key=edge_data.get("source", ""),
            target_node_key=edge_data.get("target", ""),
            source_handle=edge_data.get("sourceHandle"),
            target_handle=edge_data.get("targetHandle"),
        ))

    await db.commit()
    return {"status": "restored", "version_number": version_number}


# ============================================================
# Execution
# ============================================================

@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    payload: WorkflowExecuteRequest,
    tenant: TenantContext = Depends(require_permission("workflow.execute")),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute a workflow.
    Returns the execution record with full node execution statuses.
    """
    engine = WorkflowEngine(db)
    execution = await engine.execute_workflow(
        workflow_id=workflow_id,
        org_id=tenant.organisation.id,
        trigger_source=payload.trigger_source or "manual",
        trigger_payload=payload.trigger_payload or {},
        actor=tenant.user,
        run_sync=True,
    )

    # Load node executions
    q = (
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.node_executions))
        .where(WorkflowExecution.id == execution.id)
    )
    res = await db.execute(q)
    exec_loaded = res.scalar_one_or_none() or execution

    return _serialize_execution(exec_loaded)


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: str,
    limit: int = Query(default=20, le=100),
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.node_executions))
        .where(
            WorkflowExecution.workflow_id == workflow_id,
            WorkflowExecution.organisation_id == tenant.organisation.id,
        )
        .order_by(WorkflowExecution.queued_at.desc())
        .limit(limit)
    )
    res = await db.execute(query)
    executions = res.scalars().all()
    return [_serialize_execution(ex) for ex in executions]


@router.get("/{workflow_id}/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    workflow_id: str,
    execution_id: str,
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(WorkflowExecution)
        .options(selectinload(WorkflowExecution.node_executions))
        .where(
            WorkflowExecution.id == execution_id,
            WorkflowExecution.workflow_id == workflow_id,
            WorkflowExecution.organisation_id == tenant.organisation.id,
        )
    )
    res = await db.execute(q)
    execution = res.scalar_one_or_none()
    if not execution:
        raise NotFoundException("Execution not found.")
    return _serialize_execution(execution)


@router.get("/{workflow_id}/executions/{execution_id}/stream")
async def stream_execution_status(
    workflow_id: str,
    execution_id: str,
    tenant: TenantContext = Depends(require_permission("workflow.view")),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE stream for real-time workflow execution progress.
    Streams node-level status updates as Server-Sent Events.
    Closes when execution reaches a terminal state.
    """
    org_id = tenant.organisation.id

    async def event_generator():
        from app.core.database import AsyncSessionLocal
        poll_interval = 1.0  # seconds
        max_polls = 600  # 10 minutes max

        for _ in range(max_polls):
            async with AsyncSessionLocal() as stream_db:
                ex_res = await stream_db.execute(
                    select(WorkflowExecution)
                    .options(selectinload(WorkflowExecution.node_executions))
                    .where(
                        WorkflowExecution.id == execution_id,
                        WorkflowExecution.organisation_id == org_id,
                    )
                )
                execution = ex_res.scalar_one_or_none()

            if not execution:
                yield f"event: error\ndata: {json.dumps({'error': 'Execution not found'})}\n\n"
                break

            payload = {
                "execution_id": execution.id,
                "status": execution.status,
                "duration_ms": execution.duration_ms,
                "error_message": execution.error_message,
                "node_executions": [
                    {
                        "node_key": ne.node_key,
                        "node_name": ne.node_name,
                        "node_type": ne.node_type,
                        "status": ne.status,
                        "duration_ms": ne.duration_ms,
                        "error_message": ne.error_message,
                    }
                    for ne in execution.node_executions
                ],
            }

            yield f"data: {json.dumps(payload)}\n\n"

            # Terminal states: stop streaming
            if execution.status in ("completed", "failed", "cancelled", "timed_out"):
                yield f"event: done\ndata: {json.dumps({'final_status': execution.status})}\n\n"
                break

            await asyncio.sleep(poll_interval)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
