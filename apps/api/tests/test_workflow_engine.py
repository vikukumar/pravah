import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService
from app.services.organisation_service import OrganisationService

@pytest.mark.asyncio
async def test_workflow_creation_and_execution(client: AsyncClient, db_session: AsyncSession):
    auth_svc = AuthService(db_session)
    org_svc = OrganisationService(db_session)

    user = await auth_svc.register_user(
        email="automator@pravah.app",
        password="AutomatorPassword123!",
        first_name="Anil",
        auto_verify=True,
    )
    org = await org_svc.create_organisation(name="Anil Automations", user=user)
    tokens = await auth_svc.issue_tokens(user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Organisation-Id": org.id,
    }

    # 1. Create a DAG workflow: Trigger -> AI Generate Text -> Social Publish
    workflow_payload = {
        "name": "Daily AI News Broadcast",
        "description": "Automatically generates daily brand post and publishes to X",
        "is_active": True,
        "nodes": [
            {
                "id": "node-1",
                "type": "trigger_manual",
                "name": "Manual Launch Trigger",
                "category": "trigger",
                "config": {},
                "position": {"x": 100, "y": 100},
            },
            {
                "id": "node-2",
                "type": "ai_generate_text",
                "name": "Generate Innovation Post",
                "category": "ai",
                "config": {"topic": "AI Automation in SaaS", "platform": "x"},
                "position": {"x": 300, "y": 100},
            },
            {
                "id": "node-3",
                "type": "social_publish",
                "name": "Publish to X",
                "category": "social",
                "config": {"platform": "x"},
                "position": {"x": 500, "y": 100},
            },
        ],
        "edges": [
            {
                "id": "e1-2",
                "source": "node-1",
                "target": "node-2",
            },
            {
                "id": "e2-3",
                "source": "node-2",
                "target": "node-3",
            },
        ],
    }

    create_res = await client.post("/api/v1/workflows", json=workflow_payload, headers=headers)
    assert create_res.status_code == 201
    wf_data = create_res.json()
    wf_id = wf_data["id"]
    assert len(wf_data["nodes"]) == 3

    # 2. Execute Workflow
    exec_res = await client.post(
        f"/api/v1/workflows/{wf_id}/execute",
        json={"trigger_payload": {"source": "test_runner"}},
        headers=headers,
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "completed"
    assert len(exec_data["node_executions"]) == 3
    assert exec_data["node_executions"][0]["status"] == "success"
    assert exec_data["node_executions"][1]["status"] == "success"
    assert exec_data["node_executions"][2]["status"] == "success"

    # 3. List Execution History
    history_res = await client.get(f"/api/v1/workflows/{wf_id}/executions", headers=headers)
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 1
