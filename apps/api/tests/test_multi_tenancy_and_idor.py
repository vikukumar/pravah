import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService
from app.services.content_service import ContentService
from app.services.organisation_service import OrganisationService

@pytest.mark.asyncio
async def test_tenant_isolation_and_idor_prevention(client: AsyncClient, db_session: AsyncSession):
    auth_svc = AuthService(db_session)
    org_svc = OrganisationService(db_session)
    content_svc = ContentService(db_session)

    # 1. Create User A and Org A
    user_a = await auth_svc.register_user(
        email="tenant_a@pravah.app",
        password="PasswordA123!",
        first_name="Alice",
        auto_verify=True,
    )
    org_a = await org_svc.create_organisation(name="Org A Inc", user=user_a)
    tokens_a = await auth_svc.issue_tokens(user_a)
    headers_a = {
        "Authorization": f"Bearer {tokens_a['access_token']}",
        "X-Organisation-Id": org_a.id,
    }

    # 2. Create User B and Org B
    user_b = await auth_svc.register_user(
        email="tenant_b@pravah.app",
        password="PasswordB123!",
        first_name="Bob",
        auto_verify=True,
    )
    org_b = await org_svc.create_organisation(name="Org B Inc", user=user_b)
    tokens_b = await auth_svc.issue_tokens(user_b)
    headers_b = {
        "Authorization": f"Bearer {tokens_b['access_token']}",
        "X-Organisation-Id": org_b.id,
    }

    # 3. Create Content in Org A
    content_a = await content_svc.create_content(
        org_id=org_a.id,
        user=user_a,
        title="Org A Confidential Post",
        body="Sensitive business update for Org A.",
        platforms=["x"],
    )

    # 4. User B attempts to access Org A's content list while specifying Org A in Header (Cross-tenant IDOR attack)
    bad_headers_b = {
        "Authorization": f"Bearer {tokens_b['access_token']}",
        "X-Organisation-Id": org_a.id, # Attempt to access Org A
    }
    attack_res = await client.get("/api/v1/content", headers=bad_headers_b)
    # Must be 403 Forbidden because User B has no membership in Org A
    assert attack_res.status_code == 403

    # 5. User B in their own Org B context requests content
    res_b = await client.get("/api/v1/content", headers=headers_b)
    assert res_b.status_code == 200
    items_b = res_b.json()
    assert len(items_b) == 0 # None of Org A's posts appear in Org B

    # 6. User B attempts to delete Org A's post by ID
    del_attack = await client.delete(f"/api/v1/content/{content_a.id}", headers=headers_b)
    assert del_attack.status_code in [403, 404]

    # 7. Verify Org A's post is still intact
    res_a = await client.get("/api/v1/content", headers=headers_a)
    assert res_a.status_code == 200
    assert len(res_a.json()) == 1
    assert res_a.json()[0]["id"] == content_a.id
