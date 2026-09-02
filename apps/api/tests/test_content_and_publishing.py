from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService
from app.services.organisation_service import OrganisationService
from app.services.social_service import SocialService

@pytest.mark.asyncio
async def test_content_lifecycle_and_publishing(client: AsyncClient, db_session: AsyncSession):
    auth_svc = AuthService(db_session)
    org_svc = OrganisationService(db_session)
    social_svc = SocialService(db_session)

    # Setup User & Org
    user = await auth_svc.register_user(
        email="publisher@pravah.app",
        password="PublisherPassword123!",
        first_name="Priya",
        auto_verify=True,
    )
    org = await org_svc.create_organisation(name="Priya Agency", user=user)
    tokens = await auth_svc.issue_tokens(user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Organisation-Id": org.id,
    }

    # Connect a social account (e.g. X / Twitter)
    await social_svc.connect_account_with_token(
        org_id=org.id,
        provider="x",
        account_id="x_priya_123",
        account_name="Priya Official",
        access_token="test_x_access_token",
        username="@priya_official",
        actor=user,
    )

    # 1. Create Draft Post
    post_payload = {
        "title": "Exciting Platform Milestone",
        "body": "We just published our quarterly product update! 🚀",
        "content_type": "text",
        "platforms": ["x"],
        "approval_required": True,
    }
    create_res = await client.post("/api/v1/content", json=post_payload, headers=headers)
    assert create_res.status_code == 201
    post_data = create_res.json()
    post_id = post_data["id"]
    assert post_data["status"] == "review"

    # 2. Approve Post
    approve_res = await client.post(
        f"/api/v1/content/{post_id}/approve",
        json={"action": "approve", "comments": "Looks ready for distribution."},
        headers=headers,
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # 3. Publish Now
    pub_res = await client.post(f"/api/v1/content/{post_id}/publish-now", headers=headers)
    assert pub_res.status_code == 200
    pub_data = pub_res.json()
    assert pub_data["status"] == "published"
    assert "x" in pub_data["published_results"]

    # 4. Test Best Posting Time Recommendation Endpoint
    rec_res = await client.get("/api/v1/ai/recommend-best-time?platform=x", headers=headers)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert "recommended_time" in rec_data
    assert "confidence_score" in rec_data
    assert "reason" in rec_data
