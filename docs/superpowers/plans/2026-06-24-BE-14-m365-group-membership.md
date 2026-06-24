# BE-14 M365 Group Membership Check — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restrict backend access to members of a configured M365 group by adding a `require_group_member` FastAPI dependency that wraps the existing `require_auth`, calls `POST /v1.0/users/{oid}/checkMemberObjects` via the existing Graph client, and caches results in memory with a 5-minute TTL.

**Architecture:** A new `group_auth.py` module owns the Graph call and in-memory cache. The existing `require_auth` dependency in `auth.py` is wrapped (not replaced) by a new `require_group_member` dependency. The `/chat` router switches to `require_group_member`. A new `GET /access` endpoint gives the frontend a dedicated probe. `ALLOWED_GROUP_ID` is added to `Settings` and the app fails fast on startup if it is missing.

**Tech Stack:** Python 3.13 · FastAPI · `msgraph-sdk` via existing `GraphAuthService` · `pydantic-settings` · `pytest` + `pytest-asyncio` · `httpx` (test client)

## Global Constraints

- Python 3.13, FastAPI ≥ 0.115, uv 0.6.x — do not alter `pyproject.toml` dependencies.
- No new third-party packages — use stdlib `time` for TTL, existing `msgraph-sdk` for Graph calls.
- All tests use `pytest-asyncio` with `asyncio_mode = "auto"` (already configured).
- `require_auth` is NOT modified — `require_group_member` calls it via `Depends`.
- Conventional commits with story ID: `feat(backend): ... (BE-14)`.
- Test doubles use `unittest.mock.patch` / `AsyncMock`, following existing test patterns.

---

### Task 1: Feature branch + `ALLOWED_GROUP_ID` config

**Files:**
- Modify: `apps/backend/src/app/config.py`
- Modify: `apps/backend/.env.example`
- Modify: `apps/backend/tests/test_config.py`

**Interfaces:**
- Produces: `Settings.allowed_group_id: str` — required field; pydantic raises `ValidationError` on startup if missing.

- [ ] **Step 1: Create feature branch**

```bash
git checkout -b feat/be-14-group-membership
```

- [ ] **Step 2: Write the failing test**

Open `apps/backend/tests/test_config.py` and add:

```python
def test_allowed_group_id_is_required():
    """Settings must reject an env without ALLOWED_GROUP_ID."""
    import os
    from unittest.mock import patch

    env_without_group = {k: v for k, v in os.environ.items() if k != "ALLOWED_GROUP_ID"}
    # Remove it from the environment and ensure validation fails
    with patch.dict(os.environ, env_without_group, clear=True):
        from pydantic import ValidationError

        # Force a fresh Settings instance (bypass lru_cache)
        from app.config import Settings

        with pytest.raises((ValidationError, Exception)):
            Settings(
                azure_tenant_id="t",
                azure_client_id="c",
                azure_client_secret="s",
                # allowed_group_id intentionally omitted
            )


def test_allowed_group_id_is_read_from_env():
    from app.config import Settings

    s = Settings(
        azure_tenant_id="t",
        azure_client_id="c",
        azure_client_secret="s",
        allowed_group_id="group-abc",
    )
    assert s.allowed_group_id == "group-abc"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd apps/backend && uv run pytest tests/test_config.py -k "allowed_group" -v
```

Expected: `FAILED` — `Settings` has no `allowed_group_id` field yet.

- [ ] **Step 4: Add `allowed_group_id` to Settings**

In `apps/backend/src/app/config.py`, add after `cors_origins`:

```python
    # Access control — Entra Object ID of the M365 group allowed to use the app
    allowed_group_id: str
```

- [ ] **Step 5: Add to `.env.example`**

Append to `apps/backend/.env.example`:

```
# Access control — Entra Object ID of the M365 group allowed to use the app
ALLOWED_GROUP_ID=
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd apps/backend && uv run pytest tests/test_config.py -k "allowed_group" -v
```

Expected: `2 passed`.

- [ ] **Step 7: Commit**

```bash
git add apps/backend/src/app/config.py apps/backend/.env.example apps/backend/tests/test_config.py
git commit -m "feat(backend): add ALLOWED_GROUP_ID to Settings (BE-14)"
```

---

### Task 2: `group_auth.py` — Graph check + TTL cache

**Files:**
- Create: `apps/backend/src/app/group_auth.py`
- Create: `apps/backend/tests/test_group_auth.py`

**Interfaces:**
- Consumes: `GraphAuthService.get_client() -> GraphServiceClient` (existing, `apps/backend/src/app/services/graph_auth.py`)
- Produces:
  - `GroupMembershipCache` — class with `get(oid) -> bool | None`, `set(oid, result) -> None`
  - `check_group_membership(oid: str, group_id: str, auth_service: GraphAuthService) -> bool`
  - `_cache: GroupMembershipCache` — module-level singleton used by the FastAPI dependency

The Graph call is `POST /v1.0/users/{oid}/checkMemberObjects` with body `{"ids": [group_id]}`. Returns a list of group IDs the user is a member of — the user is in the group if `group_id` is in that list.

- [ ] **Step 1: Write the failing tests**

Create `apps/backend/tests/test_group_auth.py`:

```python
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── Cache unit tests ──────────────────────────────────────────────────────────


def test_cache_miss_returns_none():
    from app.group_auth import GroupMembershipCache

    cache = GroupMembershipCache(ttl_seconds=300)
    assert cache.get("unknown-oid") is None


def test_cache_hit_returns_stored_value():
    from app.group_auth import GroupMembershipCache

    cache = GroupMembershipCache(ttl_seconds=300)
    cache.set("oid-1", True)
    assert cache.get("oid-1") is True


def test_cache_stores_false():
    from app.group_auth import GroupMembershipCache

    cache = GroupMembershipCache(ttl_seconds=300)
    cache.set("oid-2", False)
    assert cache.get("oid-2") is False


def test_cache_entry_expires_after_ttl():
    from app.group_auth import GroupMembershipCache

    cache = GroupMembershipCache(ttl_seconds=1)
    cache.set("oid-3", True)

    # Advance time past TTL
    with patch("app.group_auth.time") as mock_time:
        mock_time.time.return_value = time.time() + 2
        assert cache.get("oid-3") is None


# ── check_group_membership unit tests ────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_group_membership_returns_true_when_member():
    from app.group_auth import check_group_membership
    from app.services.graph_auth import GraphAuthService

    auth = MagicMock(spec=GraphAuthService)
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.value = ["group-abc"]
    mock_client.users.by_user_id.return_value.check_member_objects.post = AsyncMock(
        return_value=mock_response
    )
    auth.get_client.return_value = mock_client

    result = await check_group_membership("oid-1", "group-abc", auth)
    assert result is True


@pytest.mark.asyncio
async def test_check_group_membership_returns_false_when_not_member():
    from app.group_auth import check_group_membership
    from app.services.graph_auth import GraphAuthService

    auth = MagicMock(spec=GraphAuthService)
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.value = []
    mock_client.users.by_user_id.return_value.check_member_objects.post = AsyncMock(
        return_value=mock_response
    )
    auth.get_client.return_value = mock_client

    result = await check_group_membership("oid-1", "group-abc", auth)
    assert result is False


@pytest.mark.asyncio
async def test_check_group_membership_raises_on_graph_error():
    from app.group_auth import check_group_membership
    from app.services.graph_auth import GraphAuthService

    auth = MagicMock(spec=GraphAuthService)
    mock_client = MagicMock()
    mock_client.users.by_user_id.return_value.check_member_objects.post = AsyncMock(
        side_effect=Exception("Graph API unavailable")
    )
    auth.get_client.return_value = mock_client

    with pytest.raises(Exception, match="Graph API unavailable"):
        await check_group_membership("oid-1", "group-abc", auth)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd apps/backend && uv run pytest tests/test_group_auth.py -v
```

Expected: `ImportError` — `group_auth` module doesn't exist yet.

- [ ] **Step 3: Write the implementation**

Create `apps/backend/src/app/group_auth.py`:

```python
from __future__ import annotations

import time

from msgraph.generated.users.item.check_member_objects.check_member_objects_post_request_body import (
    CheckMemberObjectsPostRequestBody,
)

from app.services.graph_auth import GraphAuthService

# Module-level cache singleton — shared across requests
_cache: GroupMembershipCache


class GroupMembershipCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[bool, float]] = {}

    def get(self, oid: str) -> bool | None:
        entry = self._store.get(oid)
        if entry is None:
            return None
        result, expiry = entry
        if time.time() >= expiry:
            del self._store[oid]
            return None
        return result

    def set(self, oid: str, result: bool) -> None:
        self._store[oid] = (result, time.time() + self._ttl)


_cache = GroupMembershipCache(ttl_seconds=300)


async def check_group_membership(
    oid: str,
    group_id: str,
    auth_service: GraphAuthService,
) -> bool:
    """Call Graph checkMemberObjects and return True if oid is in group_id.

    Raises on any Graph error — callers should handle and return 503.
    """
    client = auth_service.get_client()
    body = CheckMemberObjectsPostRequestBody(ids=[group_id])
    response = await client.users.by_user_id(oid).check_member_objects.post(body)
    return group_id in (response.value or [])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd apps/backend && uv run pytest tests/test_group_auth.py -v
```

Expected: `7 passed`.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/src/app/group_auth.py apps/backend/tests/test_group_auth.py
git commit -m "feat(backend): add group_auth module with Graph check and TTL cache (BE-14)"
```

---

### Task 3: `require_group_member` dependency + `GET /access` endpoint

**Files:**
- Modify: `apps/backend/src/app/auth.py`
- Modify: `apps/backend/src/app/main.py`
- Modify: `apps/backend/src/app/routers/chat.py`
- Modify: `apps/backend/tests/test_auth.py`
- Modify: `apps/backend/tests/test_health.py`
- Modify: `apps/backend/tests/test_chat.py`

**Interfaces:**
- Consumes: `require_auth(credentials) -> dict` (existing), `_cache: GroupMembershipCache` (Task 2), `check_group_membership(oid, group_id, auth_service) -> bool` (Task 2), `get_settings() -> Settings` (existing)
- Produces:
  - `require_group_member(credentials, request) -> dict` — FastAPI dependency; returns claims dict; raises `401` or `403`
  - `GET /access` — returns `{"access": "granted"}` for group members

- [ ] **Step 1: Write the failing tests for `require_group_member`**

Append to `apps/backend/tests/test_auth.py`:

```python
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
    from app.services.graph_auth import GraphAuthService

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good.token")
    claims = {"sub": "user-123", "oid": "oid-abc"}

    with patch("app.auth.require_auth", return_value=claims), \
         patch("app.auth.check_group_membership", new=AsyncMock(return_value=False)), \
         patch("app.auth._get_auth_service", return_value=MagicMock(spec=GraphAuthService)), \
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
    from app.services.graph_auth import GraphAuthService

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="good.token")
    claims = {"sub": "user-123", "oid": "oid-abc"}

    with patch("app.auth.require_auth", return_value=claims), \
         patch("app.auth.check_group_membership", new=AsyncMock(side_effect=Exception("Graph down"))), \
         patch("app.auth._get_auth_service", return_value=MagicMock(spec=GraphAuthService)), \
         patch("app.auth.get_settings") as mock_settings:
        mock_settings.return_value.allowed_group_id = "group-xyz"
        with pytest.raises(HTTPException) as exc_info:
            await require_group_member(credentials=creds)

    assert exc_info.value.status_code == 503
```

Write the failing tests for `GET /access` by appending to `apps/backend/tests/test_health.py`:

```python
# ── GET /access ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_access_returns_200_for_group_member():
    from unittest.mock import patch
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd apps/backend && uv run pytest tests/test_auth.py -k "group_member" tests/test_health.py -k "access" -v
```

Expected: `ImportError` or `AttributeError` — `require_group_member` and `_get_auth_service` don't exist yet.

- [ ] **Step 3: Add `require_group_member` and `_get_auth_service` to `auth.py`**

In `apps/backend/src/app/auth.py`, add at the top of the file (after existing imports):

```python
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
```

Then append `require_group_member` to `auth.py`:

```python
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
```

- [ ] **Step 4: Store `auth_service` on `app.state` in `main.py`**

`require_group_member` needs `GraphAuthService` on `app.state`. Update the lifespan in `apps/backend/src/app/main.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not hasattr(app.state, "agent"):
        settings = get_settings()
        auth = GraphAuthService(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )
        service = await create_sharepoint_service(auth_service=auth, settings=settings)
        app.state.agent = build_agent(service, settings)
        app.state.auth_service = auth   # ← add this line
    yield
```

Also add the `GET /access` endpoint in `main.py` (after the `GET /health` endpoint):

```python
from app.auth import require_group_member

@app.get("/access")
async def access_check(claims: dict = Depends(require_group_member)) -> dict[str, str]:
    return {"access": "granted"}
```

- [ ] **Step 5: Update `/chat` router to use `require_group_member`**

In `apps/backend/src/app/routers/chat.py`, change line 12 and 14:

```python
from app.auth import require_group_member   # was: require_auth

router = APIRouter(dependencies=[Depends(require_group_member)])   # was: require_auth
```

- [ ] **Step 6: Fix the existing chat tests to override the new dependency**

In `apps/backend/tests/test_chat.py`, find the section that overrides `require_auth` (around line 94) and update it to also override `require_group_member`:

```python
from app.auth import require_auth, require_group_member

# Override both — chat router now uses require_group_member
app.dependency_overrides[require_auth] = lambda: {"sub": "test-user", "oid": "oid-test"}
app.dependency_overrides[require_group_member] = lambda: {"sub": "test-user", "oid": "oid-test"}
```

And in the teardown / cleanup section, add:

```python
app.dependency_overrides.pop(require_group_member, None)
```

- [ ] **Step 7: Run all backend tests**

```bash
cd apps/backend && uv run pytest -v
```

Expected: all tests pass. If `test_config.py` fails because `ALLOWED_GROUP_ID` is missing in the test environment, add a fallback in conftest or set it:

```bash
cd apps/backend && ALLOWED_GROUP_ID=test-group uv run pytest -v
```

- [ ] **Step 8: Commit**

```bash
git add apps/backend/src/app/auth.py \
        apps/backend/src/app/main.py \
        apps/backend/src/app/routers/chat.py \
        apps/backend/tests/test_auth.py \
        apps/backend/tests/test_health.py \
        apps/backend/tests/test_chat.py
git commit -m "feat(backend): add require_group_member dependency and GET /access endpoint (BE-14)"
```

---

### Task 4: Document `GroupMember.Read.All` permission

**Files:**
- Modify: `docs/guides/azure-entra-id-setup.md`

- [ ] **Step 1: Add the Graph permission to the setup guide**

Open `docs/guides/azure-entra-id-setup.md` and add a section documenting that the app registration requires `GroupMember.Read.All` as an Application permission with admin consent:

Find the existing Graph permissions section and add:

```markdown
### Additional permission for BE-14 — M365 Group Membership Check

Add the following **Application** permission (not Delegated) to the app registration and grant admin consent:

| Permission | Type | Purpose |
|---|---|---|
| `GroupMember.Read.All` | Application | Allows the backend to call `POST /v1.0/users/{oid}/checkMemberObjects` to verify group membership |

Also add `ALLOWED_GROUP_ID=<entra-object-id-of-m365-group>` to the backend `.env` (or Key Vault secret in production).
```

- [ ] **Step 2: Commit**

```bash
git add docs/guides/azure-entra-id-setup.md
git commit -m "docs: document GroupMember.Read.All permission for BE-14 (BE-14)"
```

---

### Task 5: Mark story done and update brain

**Files:**
- Modify: `brain/stories/backend/BE-14 M365 Group Membership Check.md`
- Modify: `brain/stories/backend/Story Board - Backend.md`
- Modify: `brain/stories/daily-updates/2026-06-24.md`

- [ ] **Step 1: Mark story done**

In `brain/stories/backend/BE-14 M365 Group Membership Check.md`, change:

```
tag: todo
```
to:
```
tag: done
```

And tick all acceptance criteria checkboxes.

- [ ] **Step 2: Update Story Board**

In `brain/stories/backend/Story Board - Backend.md`, change the BE-14 row from `todo` to `done`.

- [ ] **Step 3: Append daily note**

In `brain/stories/daily-updates/2026-06-24.md`, append:

```markdown
- Completed [BE-14] M365 Group Membership Check — added group_auth.py with Graph checkMemberObjects call and 5-min TTL cache; require_group_member dependency wraps require_auth; GET /access endpoint added; /chat router updated.
```

- [ ] **Step 4: Commit and push**

```bash
git add brain/
git commit -m "chore(brain): mark BE-14 done"
git push -u origin feat/be-14-group-membership
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Covered by |
|---|---|
| `ALLOWED_GROUP_ID` added to Settings; fails to start if missing | Task 1 |
| `GroupMember.Read.All` documented in setup guide | Task 4 |
| `group_auth.py` implements `check_group_membership(oid)` via `checkMemberObjects` | Task 2 |
| In-memory cache per `oid` with 5-minute TTL | Task 2 (`GroupMembershipCache`) |
| `require_group_member` wraps `require_auth`; returns 401/403 | Task 3 |
| `GET /access` returns 200 for members, 403 for non-members | Task 3 |
| `/chat` router updated to use `require_group_member` | Task 3, Step 5 |
| Tests: cache hit/miss | Task 2 |
| Tests: member → 200 | Task 3 |
| Tests: non-member → 403 | Task 3 |
| Tests: Graph failure → 503 | Task 3 |

**Placeholder scan:** No TBD, TODO, or "similar to Task N" patterns found.

**Type consistency:**
- `check_group_membership(oid: str, group_id: str, auth_service: GraphAuthService) -> bool` — defined Task 2, consumed Task 3. ✓
- `_cache: GroupMembershipCache` — defined Task 2, imported in `auth.py` Task 3. ✓
- `_get_auth_service(request: Request) -> GraphAuthService` — defined and used in Task 3. ✓
- `require_group_member` — defined Task 3, imported in `chat.py` Task 3 Step 5, tested Task 3. ✓
