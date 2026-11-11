import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(async_client: AsyncClient):
    # 1. Register new contractor
    register_payload = {
        "email": "new_contractor@apex.com",
        "password": "SecurePassword2026!",
        "full_name": "Marcus Vance",
        "role": "DEMOLITION_CONTRACTOR",
        "company_name": "Apex Demolition Group",
        "phone_number": "+1 (312) 555-0100",
    }
    reg_response = await async_client.post("/api/v1/auth/register", json=register_payload)
    assert reg_response.status_code == 201
    user_data = reg_response.json()
    assert user_data["email"] == "new_contractor@apex.com"
    assert "hashed_password" not in user_data

    # 2. Prevent duplicate email registration
    dup_response = await async_client.post("/api/v1/auth/register", json=register_payload)
    assert dup_response.status_code == 400

    # 3. Login with credentials via OAuth2 form
    login_data = {
        "username": "new_contractor@apex.com",
        "password": "SecurePassword2026!",
    }
    login_response = await async_client.post("/api/v1/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_info = login_response.json()
    assert "access_token" in token_info
    assert token_info["token_type"] == "bearer"

    token = token_info["access_token"]

    # 4. Access protected /auth/me
    me_response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "new_contractor@apex.com"


@pytest.mark.asyncio
async def test_invalid_login_credentials(async_client: AsyncClient):
    login_data = {
        "username": "non_existent@apex.com",
        "password": "WrongPassword123!",
    }
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401

