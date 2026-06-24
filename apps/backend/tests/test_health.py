import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient


def test_health_returns_200():
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_status_ok():
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


# ── GET /access ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_access_returns_200_for_group_member():
    from app.auth import require_group_member
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        app.dependency_overrides[require_group_member] = lambda: {"oid": "oid-abc"}
        try:
            response = await client.get("/access", headers={"Authorization": "Bearer tok"})
        finally:
            app.dependency_overrides.pop(require_group_member, None)

    assert response.status_code == 200
    assert response.json() == {"access": "granted"}


@pytest.mark.asyncio
async def test_access_returns_403_for_non_member():
    from fastapi import HTTPException
    from app.auth import require_group_member
    from app.main import app

    async def deny():
        raise HTTPException(status_code=403, detail="Forbidden")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        app.dependency_overrides[require_group_member] = deny
        try:
            response = await client.get("/access", headers={"Authorization": "Bearer tok"})
        finally:
            app.dependency_overrides.pop(require_group_member, None)

    assert response.status_code == 403
