import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService

@pytest.mark.asyncio
async def test_setup_flow_and_super_admin(client: AsyncClient, db_session: AsyncSession):
    # 1. Check status before setup
    res = await client.get("/api/v1/setup/status")
    assert res.status_code == 200
    assert res.json()["is_initialized"] is False

    # 2. Perform setup
    setup_payload = {
        "system": {
            "app_name": "PRAVAH Platform",
            "app_url": "http://localhost:3000",
            "timezone": "UTC",
            "locale": "en",
            "currency": "USD",
        },
        "super_admin": {
            "first_name": "Vikram",
            "last_name": "Sharma",
            "email": "admin@pravah.app",
            "password": "SuperSecretPassword123!",
            "confirm_password": "SuperSecretPassword123!",
        },
    }
    init_res = await client.post("/api/v1/setup/initialize", json=setup_payload)
    assert init_res.status_code == 201
    data = init_res.json()
    assert "tokens" in data
    assert "access_token" in data["tokens"]
    assert data["tokens"]["user"]["isSuperAdmin"] is True

    # 3. Verify status after setup is now initialized
    status_res = await client.get("/api/v1/setup/status")
    assert status_res.status_code == 200
    assert status_res.json()["is_initialized"] is True

    # 4. Repeated setup must fail with Conflict (409)
    dup_res = await client.post("/api/v1/setup/initialize", json=setup_payload)
    assert dup_res.status_code == 409

@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient, db_session: AsyncSession):
    # Register regular user
    reg_payload = {
        "email": "creator@pravah.app",
        "first_name": "Pooja",
        "last_name": "Verma",
        "password": "CreatorPassword123!",
        "confirm_password": "CreatorPassword123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "tokens" in reg_data
    assert "organisation_id" in reg_data

    # Login with valid credentials
    login_payload = {
        "email": "creator@pravah.app",
        "password": "CreatorPassword123!",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == "creator@pravah.app"

    # Login with invalid password must fail (401)
    bad_login = await client.post("/api/v1/auth/login", json={"email": "creator@pravah.app", "password": "WrongPassword!"})
    assert bad_login.status_code == 401
