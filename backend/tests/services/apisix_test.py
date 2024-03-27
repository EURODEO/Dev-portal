from typing import Callable
import pytest
from httpx import HTTPStatusError
from httpx import AsyncClient
from app.config import settings, APISixInstanceSettings
from app.services.apisix import (
    create_apisix_consumer,
    get_apisix_consumer,
    get_routes,
    delete_apisix_consumer,
)

config = settings()

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_api6_user_not_found(
    client: AsyncClient, clean_up_api6_consumers: Callable, apisix_instance: APISixInstanceSettings
) -> None:
    identifier = "testuser"
    response = await get_apisix_consumer(client, apisix_instance, identifier)
    assert response is None


async def test_create_api6_consumer_success(
    client: AsyncClient, clean_up_api6_consumers: Callable, apisix_instance: APISixInstanceSettings
) -> None:
    identifier = "supermario"
    response = await create_apisix_consumer(client, apisix_instance, identifier)
    assert response.username == identifier


async def test_delete_api6_consumer_success(
    client: AsyncClient, apisix_instance: APISixInstanceSettings
) -> None:
    identifier = "supermario"
    response = await create_apisix_consumer(client, apisix_instance, identifier)
    assert response.username == identifier

    await delete_apisix_consumer(client, apisix_instance, identifier)


async def test_delete_api6_user_not_found_should_raise_error(
    client: AsyncClient, apisix_instance: APISixInstanceSettings
) -> None:
    identifier = "testuser"
    with pytest.raises(HTTPStatusError):
        await delete_apisix_consumer(client, apisix_instance, identifier)


async def test_get_api6_routes(
    client: AsyncClient, apisix_instance: APISixInstanceSettings
) -> None:
    # Routes are created in conftest.py in setup_apisix()
    # Current implementation does not list routes that does not have key-auth plugin defined
    response = await get_routes(client, apisix_instance)
    assert len(response.routes) == 2
    assert f"{apisix_instance.gateway_url}/foo" in response.routes
    assert f"{apisix_instance.gateway_url}/bar" in response.routes
