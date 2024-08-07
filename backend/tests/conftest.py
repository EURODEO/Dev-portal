"""
Pytest fixtures for actual tests.
"""

from typing import AsyncGenerator, Any
import json
import asyncio
import pytest
from httpx import AsyncClient
from app.config import settings, APISixInstanceSettings
from tests.data import apisix, keycloak

config = settings()

VAULT_HEADERS = {"X-Vault-Token": config.vault.token}


def get_apisix_headers(instance: APISixInstanceSettings) -> dict[str, str]:
    """ """
    return {"Content-Type": "application/json", "X-API-KEY": instance.admin_api_key}


def get_realm_group_id_by_name(group_name: str) -> str:
    """
    Get the group ID of a realm group by its name.

    Args:
        name (str): The name of the realm group.

    Returns:
        str: The group ID of the realm group.
    """
    with open("tests/data/realm-export.json", encoding="utf-8") as f:
        realm_json = json.load(f)

    for group in realm_json["groups"]:
        if group["name"] == group_name:
            return group["id"]
    raise ValueError(f'Group "{group_name}" not found in the realm export data.')


@pytest.fixture(scope="session", autouse=True)
def anyio_backend() -> str:
    """
    Pytest fixture that sets the backend for AnyIO to 'asyncio' for the entire test session.

    This fixture is automatically used (due to `autouse=True`) for all tests in the session.
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
    data = {
        "uri": "http://vault:8200",  # use the docker network since this is for apisix
        "prefix": config.vault.base_path,
        "token": config.vault.token,
    }

    # Add consumer group

    group_data = {
        "plugins": {},
        "id": "EUMETNET_USER",
    }

    # Add some test routes
    routes = apisix.ROUTES

    secret_requests = [
        client.put(
            f"{instance.admin_url}/apisix/admin/secrets/vault/dev",
            json=data,
            headers=get_apisix_headers(instance),
        )
        for instance in config.apisix.instances
    ]

    consumer_group_requests = [
        client.put(
            f"{instance.admin_url}/apisix/admin/consumer_groups",
            json=group_data,
            headers=get_apisix_headers(instance),
        )
        for instance in config.apisix.instances
    ]

    routes_requests = [
        client.put(
            f"{instance.admin_url}/apisix/admin/routes",
            json=route,
            headers=get_apisix_headers(instance),
        )
        for route in routes
        for instance in config.apisix.instances
    ]

    await asyncio.gather(
        *secret_requests,
        *consumer_group_requests,
        *routes_requests,
    )

    yield

    # Clean up created resources
    await asyncio.gather(
        *[
            client.delete(
                f"{instance.admin_url}/apisix/admin/secrets/vault/dev",
                headers=get_apisix_headers(instance),
            )
            for instance in config.apisix.instances
        ],
        *[
            client.delete(
                f"{instance.admin_url}/apisix/admin/routes", headers=get_apisix_headers(instance)
            )
            for instance in config.apisix.instances
        ],
        *[
            client.delete(
                f"{instance.admin_url}/apisix/admin/consumer_groups/{group_data['id']}",
                headers=get_apisix_headers(instance),
            )
            for instance in config.apisix.instances
        ],
    )


@pytest.fixture
async def clean_up_api6_consumers(client: AsyncClient) -> AsyncGenerator[None, None]:
    """
    Clean up API6 consumers after test is ran.
    """
    yield

    consumer_responses = await asyncio.gather(
        *[
            client.get(
                f"{instance.admin_url}/apisix/admin/consumers", headers=get_apisix_headers(instance)
            )
            for instance in config.apisix.instances
        ]
    )

    delete_tasks = []

    for response, instance in zip(consumer_responses, config.apisix.instances):
        data = response.json()
        if data["total"]:
            delete_tasks.extend(
                [
                    client.delete(
                        f"{instance.admin_url}/apisix/admin/consumers/{user['value']['username']}",
                        headers=get_apisix_headers(instance),
                    )
                    for user in data["list"]
                ]
            )
    await asyncio.gather(*delete_tasks)


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

    await client.post(f"{config.keycloak.url}/admin/realms", json=realm_json, headers=auth_header)

    users = keycloak.KEYCLOAK_USERS

    user_url = f"{config.keycloak.url}/admin/realms/{config.keycloak.realm}/users"

    await asyncio.gather(
        *[
            client.post(user_url, json=user, headers=auth_header)
            for user in users
            if "skip_init_creation" not in user
        ]
    )

    yield

    # Get test user's id and delete it
    admin_access_token = await get_keycloak_admin_token(client)

    kc_users = await client.get(user_url, headers=auth_header)

    user_ids_to_delete = [
        kc_user["id"]
        for kc_user in kc_users.json()
        if kc_user["username"] in [user["username"] for user in users]
    ]

    await asyncio.gather(
        *[
            client.delete(
                f"{user_url}/{id}",
                headers={"Authorization": f"Bearer {admin_access_token}"},
            )
            for id in user_ids_to_delete
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
        f"{config.keycloak.url}/realms/{config.keycloak.realm}" "/protocol/openid-connect/token"
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
async def get_keycloak_user_2_token_no_groups(client: AsyncClient) -> str:
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

    await remove_keycloak_user_from_group(client)
    token_url = (
        f"{config.keycloak.url}/realms/{config.keycloak.realm}" "/protocol/openid-connect/token"
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


@pytest.fixture
async def get_keycloak_realm_admin_token(client: AsyncClient) -> str:
    """
    Pytest fixture that retrieves a admin user's access token from Keycloak.

    Adds user to the realm group "ADMIN" before retrieving the token.

    The access token can be used in other fixtures or tests
    to authenticate requests to APIs that use Keycloak for authentication.

    Returns:
        str: The access token for the admin user.
    """

    await add_keycloak_user_to_group(client)

    token_url = (
        f"{config.keycloak.url}/realms/{config.keycloak.realm}" "/protocol/openid-connect/token"
    )
    data = {
        "client_id": "frontend",
        "username": keycloak.KEYCLOAK_USERS[2]["username"],
        "password": keycloak.KEYCLOAK_USERS[2]["credentials"][0]["value"],
        "grant_type": "password",
    }
    response = await client.post(token_url, data=data)
    access_token = response.json()["access_token"]
    assert isinstance(access_token, str), "access_token is not a string"
    return access_token


async def remove_keycloak_user_from_group(client: AsyncClient) -> None:
    """
    Asynchronously removes a Keycloak user from a group.

    This function first retrieves an admin access token from Keycloak,
    then uses that token to authenticate a GET request to the Keycloak users endpoint.
    It extracts the user ID from the response, then sends a DELETE request
    to the user's groups endpoint to remove the user from the group.

    The group to be removed from is defined within the function and is currently hardcoded.

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

    # Define the group ID to remove the user from
    group_id = get_realm_group_id_by_name("USER")

    # Remove the user from the group
    group_url = (
        f"{config.keycloak.url}/admin/realms/{config.keycloak.realm}/users"
        f"/{user_id}/groups/{group_id}"
    )

    await client.request("DELETE", group_url, headers=auth_header)


async def add_keycloak_user_to_group(client: AsyncClient) -> None:
    """
    Asynchronously adds a Keycloak user to a group.

    This function first retrieves an admin access token from Keycloak,
    then uses that token to authenticate a GET request to the Keycloak users endpoint.
    It extracts the user ID from the response, then sends a PUT request
    to the user's groups endpoint to add the user to the group.

    The group to be added to is defined within the function and is currently hardcoded.

    Note: This function assumes that the Keycloak server, realm,
    and user are all configured correctly.
    """
    admin_access_token = await get_keycloak_admin_token(client)

    auth_header = {
        "Authorization": f"Bearer {admin_access_token}",
    }

    user = keycloak.KEYCLOAK_USERS[2]

    user_url = f"{config.keycloak.url}/admin/realms/{config.keycloak.realm}/users"

    r = await client.get(f"{user_url}?username={user['username']}", headers=auth_header)

    user_id = r.json()[0]["id"]

    # Define the group ID to add the user to
    group_id = get_realm_group_id_by_name("ADMIN")

    # Add the user to the group
    group_url = (
        f"{config.keycloak.url}/admin/realms/{config.keycloak.realm}/users"
        f"/{user_id}/groups/{group_id}"
    )

    await client.request("PUT", group_url, headers=auth_header)
