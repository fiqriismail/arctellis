from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import ASGITransport, AsyncClient

# ── require_auth unit tests ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_auth_no_credentials_raises_401():
    from app.auth import require_auth

    with pytest.raises(HTTPException) as exc_info:
        await require_auth(credentials=None)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_auth_invalid_token_raises_401():
    import jwt

    from app.auth import require_auth

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token")

    with patch("app.auth.validate_entra_token", side_effect=jwt.PyJWTError("bad")):
        with pytest.raises(HTTPException) as exc_info:
            await require_auth(credentials=creds)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_auth_valid_token_returns_claims():
    from app.auth import require_auth

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good.token")
    expected = {"sub": "user-123", "name": "Alice"}

    with patch("app.auth.validate_entra_token", return_value=expected):
        result = await require_auth(credentials=creds)

    assert result == expected


# ── endpoint protection ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_requires_no_auth():
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_without_auth_header_returns_401():
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/chat", json={"question": "hi", "session_id": "x"}
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_with_invalid_token_returns_401():
    import jwt

    from app.main import app

    with patch("app.auth.validate_entra_token", side_effect=jwt.PyJWTError("bad")):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/chat",
                json={"question": "hi", "session_id": "x"},
                headers={"Authorization": "Bearer bad.token.here"},
            )

    assert response.status_code == 401


# ── require_group_member unit tests ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_require_group_member_passes_for_group_member():
    from fastapi.security import HTTPAuthorizationCredentials
    from unittest.mock import AsyncMock, patch, MagicMock

    from app.auth import require_group_member
    from app.services.graph_auth import GraphAuthService

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good.token")
    claims = {"sub": "user-123", "oid": "oid-abc"}

    with patch("app.auth.require_auth", return_value=claims), \
         patch("app.auth.check_group_membership", new=AsyncMock(return_value=True)), \
         patch("app.auth._get_auth_service", return_value=MagicMock(spec=GraphAuthService)), \
         patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_group_id = "group-xyz"
        result = await require_group_member(credentials=creds)

    assert result == claims


@pytest.mark.asyncio
async def test_require_group_member_raises_403_for_non_member():
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials
    from unittest.mock import AsyncMock, patch, MagicMock

    from app.auth import require_group_member
    from app.group_auth import GroupMembershipCache
    from app.services.graph_auth import GraphAuthService

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good.token")
    claims = {"sub": "user-123", "oid": "oid-abc"}
    fresh_cache = GroupMembershipCache()

    with patch("app.auth.require_auth", return_value=claims), \
         patch("app.auth.check_group_membership", new=AsyncMock(return_value=False)), \
         patch("app.auth._get_auth_service", return_value=MagicMock(spec=GraphAuthService)), \
         patch("app.auth._cache", fresh_cache), \
         patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_group_id = "group-xyz"
        with pytest.raises(HTTPException) as exc_info:
            await require_group_member(credentials=creds)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_group_member_raises_503_on_graph_failure():
    from fastapi import HTTPException
    from fastapi.security import HTTPAuthorizationCredentials
    from unittest.mock import AsyncMock, patch, MagicMock

    from app.auth import require_group_member
    from app.group_auth import GroupMembershipCache
    from app.services.graph_auth import GraphAuthService

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good.token")
    claims = {"sub": "user-123", "oid": "oid-abc"}
    fresh_cache = GroupMembershipCache()

    with patch("app.auth.require_auth", return_value=claims), \
         patch("app.auth.check_group_membership", new=AsyncMock(side_effect=Exception("Graph down"))), \
         patch("app.auth._get_auth_service", return_value=MagicMock(spec=GraphAuthService)), \
         patch("app.auth._cache", fresh_cache), \
         patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_group_id = "group-xyz"
        with pytest.raises(HTTPException) as exc_info:
            await require_group_member(credentials=creds)

    assert exc_info.value.status_code == 503
