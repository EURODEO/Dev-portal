"""
JWT Token dependency
"""

from http import HTTPStatus
from jose import jwt, JWTError, ExpiredSignatureError
from pydantic import ValidationError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from httpx import AsyncClient
from app.config import settings, logger
from app.dependencies.http_client import get_http_client, http_request
from app.models.access_token import AccessToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="tokenUrl")

config = settings()


async def get_jwk(client: AsyncClient, token: str) -> dict[str, str]:
    """
    Retrieve the JSON Web Key (JWK) from a Keycloak server.

    Retrieves the JWK from given server that corresponds to the Key ID (kid) in the JWT header.
    The JWK is used to verify the signature of the JWT.

    Parameters:
    token (str): The JWT as a string.

    Returns:
    dict: The JWK as a dictionary. If no matching JWK is found, an empty dictionary is returned.
    """

    header = jwt.get_unverified_header(token)
    jwks_url = (
        f"{config.keycloak.url}/realms/{config.keycloak.realm}" "/protocol/openid-connect/certs"
    )
    try:
        response = await http_request(client, "GET", jwks_url)
        jwks: dict[str, list[dict[str, str]]] = response.json()
        for key in jwks["keys"]:
            if key["kid"] == header["kid"]:
                return key
        return {}
    except Exception as e:
        logger.exception("Fetching JWK error: %s", e)
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE, detail="Keycloak service error"
        ) from e


async def validate_token(
    token: str = Depends(oauth2_scheme), client: AsyncClient = Depends(get_http_client)
) -> AccessToken:
    """
    Validate and decode given token
    """
    if not token or token == "undefined":  # nosec
        logger.exception("Token has not been provided")
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Token has not been provided"
        )
    try:
        jwk = await get_jwk(client, token)
        payload = jwt.decode(token, jwk, algorithms=["RS256"], audience="account")
        return AccessToken(**payload)
    except ExpiredSignatureError as e:
        logger.exception("JWT Token has expired: %s", e)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Token signature has expired"
        ) from e
    except JWTError as e:
        logger.exception("JW Token validation failed with error: %s", e)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Token validation failed"
        ) from e
    except ValidationError as e:
        logger.exception("User does not have valid ADMIN role")
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="User does not have valid ADMIN role"
        ) from e
