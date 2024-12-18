"""
API key route handlers
"""

from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from httpx import AsyncClient
from app.config import settings, logger
from app.dependencies.jwt_token import validate_token
from app.dependencies.http_client import get_http_client
from app.services import apikey
from app.models.request import AccessToken, User
from app.models.response import GetAPIKey, MessageResponse
from app.exceptions import APISIXError, VaultError

router = APIRouter()

config = settings()


# For now just refactor the existing endpoint as is
# Either naming this route differently or creating routes for routes and apikey
@router.get("/apikey", response_model=GetAPIKey)
async def get_api_key(
    token: AccessToken = Depends(validate_token),
    client: AsyncClient = Depends(get_http_client),
) -> GetAPIKey:
    """
    Retrieve the API key for a user.

    This function retrieves the user's API key from Vault and APISIX.
    If the user does not exist in Vault, it saves the user to Vault.
    If the user does not exist in APISIX, it creates the user in APISIX.

    Args:
        token (AccessToken): The access token of the user.
        client (AsyncClient): The HTTP client to use for making requests.

    Returns:
        GetAPIKey: A response containing the user's API key.

    Raises:
        HTTPException: If there is an error getting user info from APISIX or Vault,
                       or if there is an error saving the user to Vault or APISIX.
    """
    user = User(id=token.sub, groups=token.groups)

    vault_user = None

    logger.debug("Got request to retrieve API key for user '%s'", user.id)

    try:
        vault_users, apisix_users = await apikey.get_user_from_vault_and_apisix_instances(
            client, user.id
        )

        if None in vault_users or None in apisix_users:
            logger.debug(
                "User '%s' not found in all Vault and/or APISIX instances --> Upserting user",
                user.id,
            )
            vault_user = await apikey.create_user_to_vault_and_apisixes(
                client, user, vault_users, apisix_users
            )

    except (VaultError, APISIXError) as e:
        raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail=str(e)) from e

    # Use the created API key
    # Or grab the first existing one since user's API key is same regardless the instance
    api_key = (
        vault_user.auth_key if vault_user else next(user for user in vault_users if user).auth_key
    )

    return GetAPIKey(apiKey=api_key)


@router.delete("/apikey", response_model=MessageResponse)
async def delete_user(
    token: AccessToken = Depends(validate_token),
    client: AsyncClient = Depends(get_http_client),
) -> MessageResponse:
    """
    Delete a user from both Vault and APISIX.

    This function first retrieves the user's information from both Vault and APISIX.
    If the user exists in Vault, it deletes the user from Vault.
    If the user exists in APISIX, it deletes the user from APISIX.

    Args:
        token (AccessToken): The access token of the user to be deleted.
        client (AsyncClient): The HTTP client to use for making requests.

    Returns:
        MessageResponse: A response indicating whether the deletion was successful.

    Raises:
        HTTPException: If there is an error getting user info from APISIX or Vault,
                       or if there is an error deleting the user from Vault or APISIX.
    """
    user = User(id=token.sub, groups=token.groups)

    logger.debug("Got request to delete API key for user '%s'", user.id)

    try:
        vault_users, apisix_users = await apikey.get_user_from_vault_and_apisix_instances(
            client, user.id
        )
        if any(vault_users) or any(apisix_users):
            logger.debug("User '%s' found in Vault and/or APISIX --> Deleting user", user.id)
            await apikey.delete_user_from_vault_and_apisixes(
                client, user, vault_users, apisix_users
            )

    except (VaultError, APISIXError) as e:
        raise HTTPException(status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail=str(e)) from e

    return MessageResponse(message="OK")
