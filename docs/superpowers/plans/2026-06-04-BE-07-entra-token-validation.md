# BE-07 Entra Token Validation Middleware Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate the end-user's Entra ID bearer token on every protected request so that only authenticated organisation members can reach the `/chat` endpoint.

**Architecture:** `auth.py` exposes `validate_entra_token(token, tenant_id, client_id) -> dict` (thin PyJWT wrapper) and a FastAPI dependency `require_auth` that extracts the `Authorization: Bearer` header, calls `validate_entra_token`, and raises HTTP 401 on any failure. `require_auth` is attached at the router level in `chat.py` so all `/chat` routes are protected automatically. Tests patch `validate_entra_token` to avoid real Entra HTTP calls; existing chat tests get a fixture that bypasses auth via `dependency_overrides`.

**Tech Stack:** Python 3.13 · `PyJWT>=2.8` (`PyJWKClient`, `jwt.decode`) · FastAPI `HTTPBearer` · pytest-asyncio · uv

**Story:** BE-07
**Working directory:** `apps/backend/` inside repo root `/Users/fiqriismail/Projects/Arctellis/group-one-rtp`

**Existing context:**
- `src/app/config.py` — `Settings` with `azure_tenant_id: str`, `azure_client_id: str`
- `src/app/main.py` — FastAPI app with `/health` (unprotected) and lifespan
- `src/app/routers/chat.py` — `POST /chat` router, currently no auth
- `tests/test_chat.py` — 10 existing tests, all pass without auth
- `PyJWT==2.13.0` installed (transitive dep) — `PyJWKClient`, `jwt.decode`, `jwt.PyJWTError` all available

---

## File Map

```
apps/backend/
├── pyproject.toml             ← add PyJWT[crypto]>=2.8 explicitly
├── src/app/
│   ├── auth.py                ← validate_entra_token + require_auth (create)
│   └── routers/
│       └── chat.py            ← add require_auth to router dependencies (modify)
└── tests/
    ├── test_auth.py           ← 6 new tests for auth logic + endpoint protection (create)
    └── test_chat.py           ← add override_auth autouse fixture (modify)
```

---

## Task 1: Git branch + pin PyJWT

- [ ] **Step 1.1: Create feature branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git checkout -b feature/BE-07-entra-token-validation
```

Expected: `Switched to a new branch 'feature/BE-07-entra-token-validation'`

- [ ] **Step 1.2: Add PyJWT to `apps/backend/pyproject.toml`**

In `[project] dependencies`, add after `pydantic-settings`:

```toml
    "PyJWT[crypto]>=2.8",
```

- [ ] **Step 1.3: Sync and verify**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv sync --all-extras
uv run python -c "from jwt import PyJWKClient; print('OK')"
```

Expected: `OK`

- [ ] **Step 1.4: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/pyproject.toml
git commit -m "chore(backend): add PyJWT as explicit dependency (BE-07)"
```

---

## Task 2: `auth.py` — token validation + `require_auth` dependency (TDD)

**Files:**
- Create: `apps/backend/src/app/auth.py`
- Create: `apps/backend/tests/test_auth.py`

- [ ] **Step 2.1: Write failing tests**

Create `apps/backend/tests/test_auth.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import AsyncClient, ASGITransport


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
```

- [ ] **Step 2.2: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_auth.py::test_require_auth_no_credentials_raises_401 -v
```

Expected: `ModuleNotFoundError: No module named 'app.auth'`

- [ ] **Step 2.3: Create `apps/backend/src/app/auth.py`**

```python
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
    jwks_url = (
        f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    )
    jwks_client = jwt.PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=client_id,
        issuer=f"https://login.microsoftonline.com/{tenant_id}/v2.0",
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
```

- [ ] **Step 2.4: Run tests — verify all 6 pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_auth.py -v
```

Expected: 6 passed.

**Note:** `test_chat_without_auth_header_returns_401` and `test_chat_with_invalid_token_returns_401` may still FAIL at this step because `require_auth` is not yet wired to the chat router. That is expected — they will pass after Task 3.

- [ ] **Step 2.5: Commit the auth module**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/auth.py apps/backend/tests/test_auth.py
git commit -m "feat(backend): add Entra ID token validation and require_auth dependency (BE-07)"
```

---

## Task 3: Apply `require_auth` to chat router + update test_chat.py

**Files:**
- Modify: `apps/backend/src/app/routers/chat.py`
- Modify: `apps/backend/tests/test_chat.py`

- [ ] **Step 3.1: Add `require_auth` to the chat router**

Read `apps/backend/src/app/routers/chat.py`. Find the line:

```python
router = APIRouter()
```

Replace it with:

```python
from app.auth import require_auth

router = APIRouter(dependencies=[Depends(require_auth)])
```

Also add `Depends` to the imports from fastapi if it's not already imported at the top. The full imports section should start with:

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from app.auth import require_auth
from app.session import append_to_history, get_history
```

And the router definition:

```python
router = APIRouter(dependencies=[Depends(require_auth)])
```

- [ ] **Step 3.2: Run test_auth.py — verify all 6 now pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_auth.py -v
```

Expected: 6 passed.

- [ ] **Step 3.3: Run test_chat.py — expect the existing 10 tests to FAIL (auth now required)**

```bash
uv run pytest tests/test_chat.py -v 2>&1 | grep -E "PASSED|FAILED"
```

Expected: endpoint tests return 401 instead of 200 — the 5 async endpoint tests FAIL.

- [ ] **Step 3.4: Add `override_auth` fixture to test_chat.py**

Open `apps/backend/tests/test_chat.py`. Find the comment line `# ── /chat endpoint ──` (or similar). Add a new autouse fixture **before** the endpoint tests section. Insert the following block right after the `reset_sessions` fixture:

```python
@pytest.fixture(autouse=True)
def override_auth():
    from app.main import app
    from app.auth import require_auth

    app.dependency_overrides[require_auth] = lambda: {"sub": "test-user"}
    yield
    app.dependency_overrides.pop(require_auth, None)
```

- [ ] **Step 3.5: Run full test suite — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

Expected: all tests pass (101 existing + 6 new = 107 passed).

- [ ] **Step 3.6: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/routers/chat.py apps/backend/tests/test_chat.py
git commit -m "feat(backend): apply require_auth to chat router (BE-07)"
```

---

## Task 4: Ruff lint + push

- [ ] **Step 4.1: Run ruff**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Fix any issues:

```bash
uv run ruff format src/ tests/
uv run ruff check --fix src/ tests/
```

- [ ] **Step 4.2: Commit fixes if any**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/ apps/backend/tests/
git diff --staged --quiet || git commit -m "style(backend): ruff formatting (BE-07)"
```

- [ ] **Step 4.3: Final test run**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

All tests must pass.

- [ ] **Step 4.4: Push**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git push -u origin feature/BE-07-entra-token-validation
```

---

## Self-Review

**Spec coverage:**

| Acceptance criterion | Task |
|---|---|
| Backend validates Entra ID bearer token on every request (NFR-8) | Tasks 2–3: `require_auth` attached to chat router |
| Unauthenticated/invalid requests rejected with 401 (D-2) | Task 2: `HTTPBearer(auto_error=False)` + manual 401; tests verify it |
| Token validation (issuer/audience/signature/expiry) correct | Task 2: `validate_entra_token` — PyJWT validates all four |
| Applied as middleware/dependency across protected routes incl. `/chat` | Task 3: `APIRouter(dependencies=[Depends(require_auth)])` |
| No secrets or data returned to unauthenticated callers (NFR-2) | Task 2: HTTPException 401 returned before any handler logic runs |
| `/health` unprotected (implied — health checks must work) | Task 2: `test_health_requires_no_auth` verifies 200 without token |

**Placeholder scan:** None found.

**Type consistency:**
- `validate_entra_token(token: str, tenant_id: str, client_id: str) -> dict` — consistent across Task 2 implementation, Task 2 tests (patched), and Task 3 `require_auth` call.
- `require_auth(credentials: HTTPAuthorizationCredentials | None = Security(_bearer)) -> dict` — consistent across Task 2 implementation and all test patches/overrides.
- `app.dependency_overrides[require_auth] = lambda: {"sub": "test-user"}` — consistent between Task 3 fixture and Task 2 test mock pattern.
