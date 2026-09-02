import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService
from app.services.organisation_service import OrganisationService

@pytest.mark.asyncio
async def test_billing_plans_and_cms_pages(client: AsyncClient, db_session: AsyncSession):
    auth_svc = AuthService(db_session)
    org_svc = OrganisationService(db_session)

    user = await auth_svc.register_user(
        email="billing_tester@pravah.app",
        password="BillingPassword123!",
        first_name="Karan",
        auto_verify=True,
    )
    org = await org_svc.create_organisation(name="Karan Studio", user=user)
    tokens = await auth_svc.issue_tokens(user)
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Organisation-Id": org.id,
    }

    # 1. Fetch public plans
    plans_res = await client.get("/api/v1/billing/plans")
    assert plans_res.status_code == 200
    plans = plans_res.json()
    assert len(plans) >= 3
    free_plan = next(p for p in plans if p["is_free"] is True)
    assert free_plan["features"]["social_account_limit"] == 1

    # 2. Fetch organisation active subscription & usage
    sub_res = await client.get("/api/v1/billing/subscription", headers=headers)
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["status"] == "active"

    usage_res = await client.get("/api/v1/billing/usage", headers=headers)
    assert usage_res.status_code == 200
    usage_data = usage_res.json()
    assert "connected_social_accounts" in usage_data
    assert "posts_published_this_month" in usage_data

    # 3. Create Razorpay order
    starter_plan = next(p for p in plans if p["slug"] == "starter")
    rzp_res = await client.post(
        "/api/v1/billing/razorpay/create-order",
        json={"plan_id": starter_plan["id"], "billing_period": "monthly"},
        headers=headers,
    )
    assert rzp_res.status_code == 200
    rzp_data = rzp_res.json()
    assert "order_id" in rzp_data
    assert rzp_data["amount"] == int(starter_plan["price_monthly"] * 100)

    # 4. Verify CMS Dynamic Page (e.g. Terms)
    cms_res = await client.get("/api/v1/cms/pages/terms")
    assert cms_res.status_code == 200
    page_data = cms_res.json()
    assert page_data["slug"] == "terms"
    assert len(page_data["blocks"]) >= 2
    assert page_data["seo"]["meta_title"] is not None

    # 5. Submit Dynamic Contact Form
    form_res = await client.post(
        "/api/v1/cms/forms/submit",
        json={
            "form_name": "contact_us",
            "data": {
                "name": "Karan Tester",
                "email": "karan@example.com",
                "company": "Karan Studio",
                "message": "Interested in enterprise social automation.",
            },
        },
    )
    assert form_res.status_code == 201
    assert "submission_id" in form_res.json()
