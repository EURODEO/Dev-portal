"""
API key route handlers
"""

from http import HTTPStatus
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from httpx import AsyncClient, HTTPError
from app.config import settings, logger
from app.dependencies.jwt_token import validate_token, AccessToken
from app.dependencies.http_client import get_http_client
from app.services import vault, apisix
from app.utils.uuid import remove_dashes

router = APIRouter()

config = settings()


# For now just refactor the existing endpoint as is
# Either naming this route differently or creating routes for routes and apikey
@router.get("/getapikey")
async def get_api_key(
    token: AccessToken = Depends(validate_token),
    client: AsyncClient = Depends(get_http_client),
) -> JSONResponse:
    """
    Retrieve the API key for a user.

    This function retrieves the user's API key from Vault and APISix.
    If the user does not exist in Vault, it saves the user to Vault.
    If the user does not exist in APISix, it creates the user in APISix.

    Args:
        token (AccessToken): The access token of the user.
        client (AsyncClient): The HTTP client to use for making requests.

    Returns:
        JSONResponse: A response containing the user's API key
                      and the routes that require key authentication.

    Raises:
        HTTPException: If there is an error getting user info from APISix or Vault,
                       or if there is an error saving the user to Vault or APISix.
    """
    uuid = token.sub
    uuid_not_dashes = remove_dashes(uuid)

    try:
        vault_user, apisix_user = await asyncio.gather(
            vault.get_user_info_from_vault(client, uuid_not_dashes),
            apisix.get_apisix_consumer(client, uuid_not_dashes),
        )
    except HTTPError as e:
        logger.exception("Error getting user info from APISix or Vault, error: %s", e)
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail="APISix and or Vault service error"
        ) from e

    if not vault_user:
        logger.debug("User not found in vault --> Saving user to vault")
        try:
            vault_user = await vault.save_user_to_vault(client, uuid_not_dashes)
        except HTTPError as e:
            logger.error("Error saving user to Vault: %s", e)
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail="Vault service error"
            ) from e

    if not apisix_user:
        logger.debug("User not found in apisix --> Creating user to apisix")
        try:
            await apisix.create_apisix_consumer(client, uuid_not_dashes)
        except HTTPError as e:
            logger.exception("Error saving user to APISIX: %s", e)
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="APISix service error",
            ) from e

    api_key = vault_user.auth_key

    logger.debug("retrieving all the routes that requires key authentication")
    routes = await apisix.get_routes(client)

    return JSONResponse(status_code=200, content={"apiKey": api_key, **routes.model_dump()})


@router.delete("/apikey")
async def delete_user(
    token: AccessToken = Depends(validate_token),
    client: AsyncClient = Depends(get_http_client),
) -> JSONResponse:
    """
    Delete a user from both Vault and APISix.

    This function first retrieves the user's information from both Vault and APISix.
    If the user exists in Vault, it deletes the user from Vault.
    If the user exists in APISix, it deletes the user from APISix.

    Args:
        token (AccessToken): The access token of the user to be deleted.
        client (AsyncClient): The HTTP client to use for making requests.

    Returns:
        JSONResponse: A response indicating whether the deletion was successful.

    Raises:
        HTTPException: If there is an error getting user info from APISix or Vault,
                       or if there is an error deleting the user from Vault or APISix.
    """
    uuid = token.sub
    uuid_not_dashes = remove_dashes(uuid)

    try:
        vault_user, apisix_user = await asyncio.gather(
            vault.get_user_info_from_vault(client, uuid_not_dashes),
            apisix.get_apisix_consumer(client, uuid_not_dashes),
        )
    except HTTPException as e:
        logger.exception("Error getting user info from APISix or Vault, error: %s", e)
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail="APISix and or Vault service error"
        ) from e

    if vault_user:
        logger.debug("User found from vault --> Deleting user from Vault")
        try:
            await vault.delete_user_from_vault(client, uuid_not_dashes)
        except HTTPException as e:
            logger.exception("Error deleting user from Vault: %s", e)
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail="Vault service error"
            ) from e

    if apisix_user:
        logger.debug("User not found in apisix --> Deleting user from APISix")
        try:
            await apisix.delete_apisix_consumer(client, uuid_not_dashes)
        except HTTPException as e:
            logger.exception("Error deleting user from APISix: %s", e)
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="APISix service error",
            ) from e

    return JSONResponse(status_code=200, content="OK")
