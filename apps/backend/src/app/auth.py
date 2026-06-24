from __future__ import annotations

import logging

import jwt
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.group_auth import _cache, check_group_membership
from app.services.graph_auth import GraphAuthService

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


def _get_auth_service(request: Request) -> GraphAuthService:
    """Return the GraphAuthService stored on app state by the lifespan."""
    return request.app.state.auth_service


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
    request: Request = None,
) -> dict:
    """FastAPI dependency — validates token AND checks M365 group membership.

    Returns decoded JWT claims on success.
    Raises HTTP 401 for invalid/missing token.
    Raises HTTP 403 if the user is not in the configured group.
    Raises HTTP 503 if the Graph membership check fails.
    """
    claims = await require_auth(credentials)
    oid = claims.get("oid", "")
    settings = get_settings()
    group_id = settings.allowed_group_id

    cached = _cache.get(oid)
    if cached is True:
        return claims
    if cached is False:
        raise HTTPException(status_code=403, detail="Forbidden")

    auth_service = _get_auth_service(request)
    try:
        is_member = await check_group_membership(oid, group_id, auth_service)
    except Exception:
        logger.exception("Group membership check failed for oid=%s", oid)
        raise HTTPException(status_code=503, detail="Service Unavailable")

    _cache.set(oid, is_member)
    if not is_member:
        raise HTTPException(status_code=403, detail="Forbidden")
    return claims
