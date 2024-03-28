"""
Pytest fixtures for actual tests.
"""

from typing import AsyncGenerator
import json
import asyncio
import pytest
from httpx import AsyncClient
from app.config import settings
from tests.data import apisix, keycloak

config = settings()

VAULT_HEADERS = {"X-Vault-Token": config.vault.token}
API6_HEADERS = {"Content-Type": "application/json", "X-API-KEY": config.apisix.admin_api_key}


@pytest.fixture(scope="session", autouse=True)
def anyio_backend() -> str:
    """
    Pytest fixture that sets the backend for AnyIO to 'asyncio' for the entire test session.

    ßThis fixture is automatically used (due to `autouse=True`) for all tests in the session.
    It ensures that AnyIO, a library for asynchronous I/O, uses the 'asyncio' library as its backend

    Returns:
        str: The name of the AnyIO backend to use.
    """
    return "asyncio"


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Yield an instance of httpx client for tests.
    """
    async with AsyncClient() as c:
        yield c


# ------- VAULT SETUP ---------
@pytest.fixture(scope="session", autouse=True)
async def vault_setup(client: AsyncClient) -> AsyncGenerator[None, None]:
    """
    Setup vault for tests.
    """
    # Setup vault
    # initiate the secret engine
    data = {
        "type": "kv",
    }
    url = f"{config.vault.url}/v1/sys/mounts/apisix-dev"
    await client.post(url, json=data, headers=VAULT_HEADERS)

    yield

    # Remove secret engine
    await client.delete(url, headers=VAULT_HEADERS)


# ------- APISIX SETUP ---------
@pytest.fixture(scope="session", autouse=True)
async def apisix_setup(client: AsyncClient) -> AsyncGenerator[None, None]:
    """
    Setup apisix for tests.
    """

    # Add secrets config for Vault

    url = f"{config.apisix.admin_url}/apisix/admin/secrets/vault/dev"
    data = {
        "uri": "http://vault:8200",
        "prefix": config.vault.base_path,
        "token": config.vault.token,
    }

    # Add some test routes
    routes_url = f"{config.apisix.admin_url}/apisix/admin/routes"
    routes = apisix.ROUTES

    await asyncio.gather(
        client.put(url, json=data, headers=API6_HEADERS),
        *[client.put(routes_url, json=route, headers=API6_HEADERS) for route in routes],
    )

    yield

    await asyncio.gather(
        client.delete(url, headers=API6_HEADERS), client.delete(routes_url, headers=API6_HEADERS)
    )


@pytest.fixture
async def clean_up_api6_consumers(client: AsyncClient) -> AsyncGenerator[None, None]:
    """
    Clean up API6 consumers after test is ran.
    """
    yield

    response = await client.get(
        f"{config.apisix.admin_url}/apisix/admin/consumers", headers=API6_HEADERS
    )
    data = response.json()
    if data["total"]:
        tasks = [
            client.delete(
                f"{config.apisix.admin_url}/apisix/admin/consumers/{user['value']['username']}",
                headers=API6_HEADERS,
            )
            for user in data["list"]
        ]
        await asyncio.gather(*tasks)


# ------- KEYCLOAK SETUP ---------
async def get_keycloak_admin_token(client: AsyncClient) -> str:
    """
    Pytest fixture that retrieves a admin user access token from Keycloak.

    This fixture makes a POST request to the Keycloak token endpoint
    with the client ID, username, and password.
    It then extracts the access token from the response and returns it.

    The access token can be used in other fixtures or tests
    to authenticate requests to APIs that use Keycloak for authentication.

    Returns:
        str: The access token for the user.
    """
    token_url = f"{config.keycloak.url}/realms/master/protocol/openid-connect/token"
    data = keycloak.KEYCLOAK_ADMIN_USER_TOKEN_DATA
    response = await client.post(token_url, data=data)
    access_token = response.json()["access_token"]
    assert isinstance(access_token, str), "access_token is not a string"
    return access_token


@pytest.fixture(scope="session", autouse=True)
async def keycloak_setup(client: AsyncClient) -> AsyncGenerator[None, None]:
    """
    Setup keycloak for tests.
    """
    # Setup keycloak
    admin_access_token = await get_keycloak_admin_token(client)

    auth_header = {
        "Authorization": f"Bearer {admin_access_token}",
    }
    with open("tests/data/realm-export.json", encoding="utf-8") as f:
        realm_json = json.load(f)

    await client.post(
        f"{config.keycloak.url}/admin/realms", json=realm_json, headers=auth_header
    )

    users = keycloak.KEYCLOAK_USERS

    user_url = f"{config.keycloak.url}/admin/realms/{config.keycloak.realm}/users"

    await asyncio.gather(*[client.post(user_url, json=user, headers=auth_header) for user in users])

    yield

    # Get test user's id and delete it
    admin_access_token = await get_keycloak_admin_token(client)

    id_responses = await asyncio.gather(
        *[
            client.get(f"{user_url}?username={user['username']}", headers=auth_header)
            for user in users
        ]
    )

    # user_id = r.json()[0]["id"]

    await asyncio.gather(
        *[
            client.delete(
                f"{user_url}/{response.json()[0]['id']}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            for response in id_responses
        ]
    )


@pytest.fixture
async def get_keycloak_user_token(client: AsyncClient) -> str:
    """
    Pytest fixture that retrieves a user access token from Keycloak.

    This fixture makes a POST request to the Keycloak token endpoint
    with the client ID, username, and password.
    It then extracts the access token from the response and returns it.

    The access token can be used in other fixtures or tests
    to authenticate requests to APIs that use Keycloak for authentication.

    Returns:
        str: The access token for the user.
    """
    token_url = (
        f"{config.keycloak.url}/realms/{config.keycloak.realm}"
        "/protocol/openid-connect/token"
    )
    data = {
        "client_id": "frontend",
        "username": keycloak.KEYCLOAK_USERS[0]["username"],
        "password": keycloak.KEYCLOAK_USERS[0]["credentials"][0]["value"],
        "grant_type": "password",
    }
    response = await client.post(token_url, data=data)
    access_token = response.json()["access_token"]
    assert isinstance(access_token, str), "access_token is not a string"
    return access_token


@pytest.fixture
async def get_keycloak_user_2_token_no_role(client: AsyncClient) -> str:
    """
    Pytest fixture that retrieves a user access token from Keycloak.

    This fixture makes a POST request to the Keycloak token endpoint
    with the client ID, username, and password.
    It then extracts the access token from the response and returns it.

    The access token can be used in other fixtures or tests
    to authenticate requests to APIs that use Keycloak for authentication.

    Returns:
        str: The access token for the user.
    """

    await remove_keycloak_realm_role_from_user(client)
    token_url = (
        f"{config.keycloak.url}/realms/{config.keycloak.realm}"
        "/protocol/openid-connect/token"
    )
    data = {
        "client_id": "frontend",
        "username": keycloak.KEYCLOAK_USERS[1]["username"],
        "password": keycloak.KEYCLOAK_USERS[1]["credentials"][0]["value"],
        "grant_type": "password",
    }
    response = await client.post(token_url, data=data)
    access_token = response.json()["access_token"]
    assert isinstance(access_token, str), "access_token is not a string"
    return access_token


async def remove_keycloak_realm_role_from_user(client: AsyncClient) -> None:
    """
    Asynchronously removes a realm role from a Keycloak user.

    This function first retrieves an admin access token from Keycloak,
    then uses that token to authenticate a GET request to the Keycloak users endpoint.
    It extracts the user ID from the response, then sends a DELETE request
    to the user's role mappings endpoint to remove the role.

    The role to be removed is defined within the function and is currently hardcoded.

    Note: This function assumes that the Keycloak server, realm,
    and user are all configured correctly.
    """
    admin_access_token = await get_keycloak_admin_token(client)

    auth_header = {
        "Authorization": f"Bearer {admin_access_token}",
    }
    user = keycloak.KEYCLOAK_USERS[1]

    user_url = f"{config.keycloak.url}/admin/realms/{config.keycloak.realm}/users"

    r = await client.get(f"{user_url}?username={user['username']}", headers=auth_header)

    user_id = r.json()[0]["id"]

    # Define the role to remove
    role = [{"id": "c8c93745-dbbd-49e8-af76-175bb2ca62a5", "name": "default-roles-test"}]

    # Delete the role from the user
    role_url = (
        f"{config.keycloak.url}/admin/realms/{config.keycloak.realm}/users"
        f"/{user_id}/role-mappings/realm"
    )

    await client.request("DELETE", role_url, json=role, headers=auth_header)
