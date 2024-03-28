"""
Service for interacting with the APISIX API.
"""

from httpx import AsyncClient
from app.config import settings
from app.dependencies.http_client import http_request
from app.models.apisix import APISixConsumer, APISixRoutes

config = settings()

HEADERS = {"Content-Type": "application/json", "X-API-KEY": config.apisix.admin_api_key}


def create_consumer(identifier: str) -> APISixConsumer:
    """
    Create a consumer dictionary for APISIX.

    Args:
        identifier (str): The identifier for the consumer.

    Returns:
        APISixConsumer: A dictionary representing the consumer.
    """
    return APISixConsumer(
        username=identifier,
        plugins={
            "key-auth": {"key": f"{config.apisix.key_path}{identifier}/{config.apisix.key_name}"}
        },
    )


async def create_apisix_consumer(client: AsyncClient, identifier: str) -> APISixConsumer:
    """
    Create a consumer in APISIX.

    Args:
        client (AsyncClient): The HTTP client to use for making the request.
        identifier (str): The identifier for the consumer.

    Returns:
        APISixConsumer: A dictionary representing the created consumer.
    """
    apisix_consumer = create_consumer(identifier)
    await http_request(
        client,
        "PUT",
        f"{config.apisix.admin_url}/apisix/admin/consumers",
        headers=HEADERS,
        data=create_consumer(identifier).model_dump(),
    )
    return apisix_consumer


async def get_apisix_consumer(client: AsyncClient, identifier: str) -> APISixConsumer | None:
    """
    Retrieve a consumer from APISIX.

    Args:
        client (AsyncClient): The HTTP client to use for making the request.
        identifier (str): The identifier for the consumer.

    Returns:
        APISixConsumer: A dictionary representing the consumer if found, None otherwise.
    """
    response = await http_request(
        client,
        "GET",
        f"{config.apisix.admin_url}/apisix/admin/consumers/{identifier}",
        headers=HEADERS,
        valid_status_codes=(200, 404),
    )
    # response = make_request("GET", f"consumers/{username}", accepted_status_codes=[200, 404])
    # {'key': '/apisix/consumers/foobar',
    #'value': {'create_time': 1710165806, 'plugins':
    # {'key-auth': {'key': '$secret://vault/dev/foobar/key-auth'}},
    # 'username': 'foobar', 'update_time': 1710232230}}
    data = response.json()
    return APISixConsumer(**data["value"]) if response.status_code in {200, 201} else None


async def get_routes(client: AsyncClient) -> APISixRoutes:
    """
    Retrieve a list of key-auth routes from APISIX.

    Args:
        client (AsyncClient): The HTTP client to use for making the request.

    Returns:
        list[str]: A list of routes.
    """
    response = await http_request(
        client, "GET", f"{config.apisix.admin_url}/apisix/admin/routes", headers=HEADERS
    )
    routes = response.json().get("list", [])
    # {'total': 1,
    #'list': [{'value':
    # {'update_time': 1710230570, 'plugins':
    # {'key-auth': {'hide_credentials': False, 'query': 'apikey', 'header': 'apikey'},
    #'proxy-rewrite': {'use_real_request_uri_unsafe': False, 'uri': '/'}},
    #'priority': 0, 'uri': '/foo', 'create_time': 1710225526, 'upstream':
    # {'type': 'roundrobin', 'pass_host': 'pass', 'nodes': {'httpbin.org:80': 1},
    #'hash_on': 'vars', 'scheme': 'http'}, 'status': 1, 'id': 'foo'},
    #'createdIndex': 101, 'key': '/apisix/routes/foo', 'modifiedIndex': 128}]}
    return APISixRoutes(routes=routes)


async def delete_apisix_consumer(client: AsyncClient, identifier: str) -> None:
    """
    Delete a consumer from APISIX.

    Args:
        client (AsyncClient): The HTTP client to use for making the request.
        identifier (str): The identifier for the consumer.
    """
    await http_request(
        client,
        "DELETE",
        f"{config.apisix.admin_url}/apisix/admin/consumers/{identifier}",
        headers=HEADERS,
    )
