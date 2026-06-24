from __future__ import annotations

import logging

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def validate_entra_token(token: str, tenant_id: str, client_id: str) -> dict:
    """Validate an Entra ID JWT and return its decoded claims.

    Raises jwt.PyJWTError on any validation failure.
    """
    jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    jwks_client = jwt.PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=[client_id, f"api://{client_id}"],
        issuer=[
            f"https://login.microsoftonline.com/{tenant_id}/v2.0",
            f"https://sts.windows.net/{tenant_id}/",
        ],
    )


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> dict:
    """FastAPI dependency — validates the Entra ID bearer token.

    Returns the decoded JWT claims on success.
    Raises HTTP 401 for missing, expired, or invalid tokens.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    settings = get_settings()
    try:
        return validate_entra_token(
            credentials.credentials,
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
        )
    except Exception:
        logger.exception("Token validation failed")
        raise HTTPException(status_code=401, detail="Unauthorized")


async def require_group_member(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> dict:
    """FastAPI dependency — validates token AND checks for the required app role.

    Entra injects a `roles` claim listing app roles assigned to the user (directly
    or via group). No Graph API call is needed.

    Returns decoded JWT claims on success.
    Raises HTTP 401 for invalid/missing token.
    Raises HTTP 403 if the required app role is absent from the token.
    """
    claims = await require_auth(credentials)
    settings = get_settings()
    if settings.allowed_role not in claims.get("roles", []):
        raise HTTPException(status_code=403, detail="Forbidden")
    return claims
