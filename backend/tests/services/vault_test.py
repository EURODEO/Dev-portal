from datetime import datetime, timezone
import pytest
from freezegun import freeze_time
from httpx import AsyncClient
from app.services import vault
from app.config import settings

config = settings()

# This is the same as using the @pytest.mark.anyio on all test functions in the module
pytestmark = pytest.mark.anyio


async def test_vault_user_not_found_wont_raise_exception(client: AsyncClient) -> None:
    # Vault returns 404 if user is not found which is not error in this context
    identifier = "testuser"
    response = await vault.get_user_info_from_vault(client, identifier)
    assert response is None


@freeze_time("2021-01-01 00:00:00")
async def test_vault_user_creation_success(client: AsyncClient) -> None:
    identifier = "supermario"
    apikey = vault.generate_api_key(identifier)

    await vault.save_user_to_vault(client, identifier)
    response = await vault.get_user_info_from_vault(client, identifier)

    assert response is not None
    assert response.model_dump() == {
        "auth_key": apikey,
        "date": datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M:%S"),
    }


async def test_user_deletion_success(client: AsyncClient) -> None:
    identifier = "User-not-exists"

    await vault.save_user_to_vault(client, identifier)
    await vault.delete_user_from_vault(client, identifier)
    response = await vault.get_user_info_from_vault(client, identifier)

    assert response is None
