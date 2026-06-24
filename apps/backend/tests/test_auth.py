from unittest.mock import AsyncMock, patch

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
async def test_require_group_member_passes_when_role_present():
    from app.auth import require_group_member

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good.token")
    claims = {"sub": "user-123", "roles": ["App.Access"]}

    with patch("app.auth.require_auth", new=AsyncMock(return_value=claims)), \
         patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_role = "App.Access"
        result = await require_group_member(credentials=creds)

    assert result == claims


@pytest.mark.asyncio
async def test_require_group_member_raises_403_when_role_absent():
    from app.auth import require_group_member

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good.token")
    claims = {"sub": "user-123", "roles": []}

    with patch("app.auth.require_auth", new=AsyncMock(return_value=claims)), \
         patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_role = "App.Access"
        with pytest.raises(HTTPException) as exc_info:
            await require_group_member(credentials=creds)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_require_group_member_raises_403_when_no_roles_claim():
    from app.auth import require_group_member

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good.token")
    claims = {"sub": "user-123"}

    with patch("app.auth.require_auth", new=AsyncMock(return_value=claims)), \
         patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_role = "App.Access"
        with pytest.raises(HTTPException) as exc_info:
            await require_group_member(credentials=creds)

    assert exc_info.value.status_code == 403
