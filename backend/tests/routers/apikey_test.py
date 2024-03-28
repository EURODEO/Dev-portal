"""
Tests for getapikey route
"""

from typing import Callable, cast
from datetime import datetime, timedelta, timezone
import pytest
from freezegun import freeze_time
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings

pytestmark = pytest.mark.anyio

config = settings()

BASE_URL = f"http://localhost:{config.server.port}"


async def test_get_api_key_without_token_fails() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=cast(Callable, app)), base_url=BASE_URL
    ) as ac:
        response = await ac.get("/getapikey")

    assert response.status_code == 401
    data = response.json()

    assert data == {"message": "Not authenticated"}


async def test_get_api_key_with_invalid_token_fails(get_keycloak_user_token: Callable) -> None:
    # Remove the last character from the token to make it invalid
    token = cast(str, get_keycloak_user_token)
    modified_token = token[:-1]
    async with AsyncClient(
        transport=ASGITransport(app=cast(Callable, app)), base_url=BASE_URL
    ) as ac:
        response = await ac.get("/getapikey", headers={"Authorization": f"Bearer {modified_token}"})

    assert response.status_code == 401
    data = response.json()

    assert data == {"message": "Token validation failed"}


# Manipulate time six minutes in the future
@freeze_time(datetime.now(timezone.utc) + timedelta(minutes=6))
async def test_get_api_key_with_expired_token_fails(get_keycloak_user_token: Callable) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=cast(Callable, app)), base_url=BASE_URL
    ) as ac:
        response = await ac.get(
            "/getapikey", headers={"Authorization": f"Bearer {get_keycloak_user_token}"}
        )

    assert response.status_code == 401
    data = response.json()

    assert data == {"message": "Token signature has expired"}


async def test_get_api_key_with_invalid_role_fails(
    get_keycloak_user_2_token_no_role: Callable,
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=cast(Callable, app)), base_url=BASE_URL
    ) as ac:
        response = await ac.get(
            "/getapikey", headers={"Authorization": f"Bearer {get_keycloak_user_2_token_no_role}"}
        )

    assert response.status_code == 403
    data = response.json()

    assert data == {"message": "User does not have valid ADMIN role"}


async def test_get_api_key_for_new_user_succeeds(get_keycloak_user_token: Callable) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=cast(Callable, app)), base_url=BASE_URL
    ) as ac:
        response = await ac.get(
            "/getapikey", headers={"Authorization": f"Bearer {get_keycloak_user_token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "apiKey" in data
    assert len(data["routes"]) == 2


async def test_get_api_key_for_existing_user_succeeds(get_keycloak_user_token: Callable) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=cast(Callable, app)), base_url=BASE_URL
    ) as ac:
        await ac.get("/getapikey", headers={"Authorization": f"Bearer {get_keycloak_user_token}"})
        response = await ac.get(
            "/getapikey", headers={"Authorization": f"Bearer {get_keycloak_user_token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "apiKey" in data
    assert len(data["routes"]) == 2


async def test_delete_api_key_succeeds(get_keycloak_user_token) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=cast(Callable, app)), base_url=BASE_URL
    ) as ac:
        response = await ac.delete(
            "/apikey", headers={"Authorization": f"Bearer {get_keycloak_user_token}"}
        )

    assert response.status_code == 200
    assert response.json() == "OK"
