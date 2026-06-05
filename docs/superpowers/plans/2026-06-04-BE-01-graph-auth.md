# BE-01 Graph Auth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a settings module and a Graph auth service so the backend can acquire a Microsoft Graph token via client-credentials and verify it with a real Graph call.

**Architecture:** `pydantic-settings` reads credentials from `.env`; `GraphAuthService` wraps `azure-identity`'s `ClientSecretCredential` and returns a `GraphServiceClient`. A standalone verification script runs the full auth flow end-to-end against a real tenant. Unit tests mock the credential so CI never needs real secrets.

**Tech Stack:** Python 3.13 · pydantic-settings · azure-identity · msgraph-sdk · pytest · uv

**Story:** BE-01
**Working directory:** `apps/backend/` inside repo root `/Users/fiqriismail/Projects/Arctellis/group-one-rtp`

---

## Prerequisites — Manual Azure steps

These must be done in the Azure Portal (or Azure CLI) before the verification script can pass. They cannot be automated.

1. **Create an Entra ID app registration**
   - Azure Portal → Entra ID → App registrations → New registration
   - Name: `group-one-rtp-backend` (or similar)
   - Account type: single-tenant (this org only)
   - No redirect URI needed (daemon app)

2. **Create a client secret**
   - Certificates & secrets → New client secret
   - Copy the secret value immediately — it is only shown once
   - Add to `apps/backend/.env`:
     ```
     AZURE_TENANT_ID=<Directory (tenant) ID from Overview>
     AZURE_CLIENT_ID=<Application (client) ID from Overview>
     AZURE_CLIENT_SECRET=<the secret value you just copied>
     ```

3. **Grant Graph permissions**
   - API permissions → Add permission → Microsoft Graph → Application permissions
   - Add `Sites.Selected` (preferred — scoped to one site) **or** `Sites.Read.All`
   - Click **Grant admin consent**
   - Status column must show green ✓ for both permissions

4. **If using `Sites.Selected` — grant access to the specific site**
   - This requires a Graph API call (Portal does not support it):
     ```bash
     # Get the site ID first (replace <tenant> and <site>):
     curl -H "Authorization: Bearer <token>" \
       "https://graph.microsoft.com/v1.0/sites/<tenant>.sharepoint.com:/sites/<site>"
     # Then grant the app read access to that site:
     curl -X POST -H "Authorization: Bearer <token>" \
       -H "Content-Type: application/json" \
       -d '{"roles":["read"],"grantedToIdentities":[{"application":{"id":"<AZURE_CLIENT_ID>"}}]}' \
       "https://graph.microsoft.com/v1.0/sites/<site-id>/permissions"
     ```
   - Alternatively, use `Sites.Read.All` for the initial dev/test phase and scope down later.

Once these steps are done, fill in `apps/backend/.env` and proceed with the tasks below.

---

## File Map

```
apps/backend/
├── src/app/
│   ├── config.py               ← pydantic-settings model + get_settings()
│   └── services/
│       ├── __init__.py
│       └── graph_auth.py       ← GraphAuthService (credential + client)
├── scripts/
│   └── verify_graph_auth.py    ← standalone integration harness
└── tests/
    ├── test_config.py          ← unit tests for settings loading
    └── test_graph_auth.py      ← unit tests for GraphAuthService (mocked)
```

---

## Task 1: Git branch

**Files:** none

- [ ] **Step 1.1: Create and switch to the feature branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git checkout -b feature/BE-01-graph-auth
```

Expected: `Switched to a new branch 'feature/BE-01-graph-auth'`

---

## Task 2: Settings module (TDD)

**Files:**
- Create: `apps/backend/src/app/config.py`
- Create: `apps/backend/tests/test_config.py`

- [ ] **Step 2.1: Write the failing tests first**

Create `apps/backend/tests/test_config.py`:

```python
import pytest
from pydantic import ValidationError


def test_settings_loads_required_fields():
    from app.config import Settings

    s = Settings(
        azure_tenant_id="tenant-123",
        azure_client_id="client-456",
        azure_client_secret="secret-789",
    )
    assert s.azure_tenant_id == "tenant-123"
    assert s.azure_client_id == "client-456"
    assert s.azure_client_secret == "secret-789"


def test_settings_defaults():
    from app.config import Settings

    s = Settings(
        azure_tenant_id="t",
        azure_client_id="c",
        azure_client_secret="s",
    )
    assert s.cache_ttl_seconds == 60
    assert s.list_row_threshold == 1000
    assert s.azure_openai_deployment == "gpt-4o"


def test_settings_missing_tenant_id_raises():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(azure_client_id="c", azure_client_secret="s")


def test_settings_missing_client_id_raises():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(azure_tenant_id="t", azure_client_secret="s")


def test_settings_missing_client_secret_raises():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(azure_tenant_id="t", azure_client_id="c")


def test_get_settings_returns_settings_instance():
    from app.config import Settings, get_settings

    get_settings.cache_clear()
    import os
    os.environ.setdefault("AZURE_TENANT_ID", "t")
    os.environ.setdefault("AZURE_CLIENT_ID", "c")
    os.environ.setdefault("AZURE_CLIENT_SECRET", "s")
    result = get_settings()
    assert isinstance(result, Settings)
    get_settings.cache_clear()
```

- [ ] **Step 2.2: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_config.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.config'`

- [ ] **Step 2.3: Implement the settings module**

Create `apps/backend/src/app/config.py`:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Entra ID — required, no defaults
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"

    # SharePoint / Microsoft Graph
    sharepoint_site_url: str = ""
    sharepoint_list_id: str = ""

    # Cache and retrieval
    cache_ttl_seconds: int = 60
    list_row_threshold: int = 1000


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 2.4: Run tests — verify they PASS**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_config.py -v
```

Expected:
```
PASSED tests/test_config.py::test_settings_loads_required_fields
PASSED tests/test_config.py::test_settings_defaults
PASSED tests/test_config.py::test_settings_missing_tenant_id_raises
PASSED tests/test_config.py::test_settings_missing_client_id_raises
PASSED tests/test_config.py::test_settings_missing_client_secret_raises
PASSED tests/test_config.py::test_get_settings_returns_settings_instance
6 passed
```

- [ ] **Step 2.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/config.py apps/backend/tests/test_config.py
git commit -m "feat(backend): add pydantic-settings config module (BE-01)"
```

---

## Task 3: GraphAuthService (TDD with mocks)

**Files:**
- Create: `apps/backend/src/app/services/__init__.py`
- Create: `apps/backend/src/app/services/graph_auth.py`
- Create: `apps/backend/tests/test_graph_auth.py`

- [ ] **Step 3.1: Write the failing tests first**

Create `apps/backend/tests/test_graph_auth.py`:

```python
from unittest.mock import MagicMock, patch


def test_graph_auth_service_creates_client_secret_credential():
    with patch("app.services.graph_auth.ClientSecretCredential") as mock_cred_cls:
        from app.services.graph_auth import GraphAuthService

        GraphAuthService(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="secret-789",
        )
        mock_cred_cls.assert_called_once_with(
            tenant_id="tenant-123",
            client_id="client-456",
            client_secret="secret-789",
        )


def test_graph_auth_service_get_credential_returns_credential():
    with patch("app.services.graph_auth.ClientSecretCredential") as mock_cred_cls:
        from app.services.graph_auth import GraphAuthService

        service = GraphAuthService("t", "c", "s")
        credential = service.get_credential()
        assert credential is mock_cred_cls.return_value


def test_graph_auth_service_get_client_returns_graph_service_client():
    with patch("app.services.graph_auth.ClientSecretCredential"), patch(
        "app.services.graph_auth.GraphServiceClient"
    ) as mock_graph_cls:
        from app.services.graph_auth import GraphAuthService

        service = GraphAuthService("t", "c", "s")
        client = service.get_client()
        mock_graph_cls.assert_called_once()
        assert client is mock_graph_cls.return_value


def test_graph_auth_service_get_client_passes_credential():
    with patch(
        "app.services.graph_auth.ClientSecretCredential"
    ) as mock_cred_cls, patch(
        "app.services.graph_auth.GraphServiceClient"
    ) as mock_graph_cls:
        from app.services.graph_auth import GraphAuthService

        service = GraphAuthService("t", "c", "s")
        service.get_client()
        mock_graph_cls.assert_called_once_with(credentials=mock_cred_cls.return_value)
```

- [ ] **Step 3.2: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_graph_auth.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.services'`

- [ ] **Step 3.3: Create the services package init**

Create `apps/backend/src/app/services/__init__.py` as an empty file.

- [ ] **Step 3.4: Implement GraphAuthService**

Create `apps/backend/src/app/services/graph_auth.py`:

```python
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient


class GraphAuthService:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str) -> None:
        self._credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )

    def get_credential(self) -> ClientSecretCredential:
        return self._credential

    def get_client(self) -> GraphServiceClient:
        return GraphServiceClient(credentials=self._credential)
```

- [ ] **Step 3.5: Run tests — verify they PASS**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_graph_auth.py -v
```

Expected:
```
PASSED tests/test_graph_auth.py::test_graph_auth_service_creates_client_secret_credential
PASSED tests/test_graph_auth.py::test_graph_auth_service_get_credential_returns_credential
PASSED tests/test_graph_auth.py::test_graph_auth_service_get_client_returns_graph_service_client
PASSED tests/test_graph_auth.py::test_graph_auth_service_get_client_passes_credential
4 passed
```

- [ ] **Step 3.6: Run the full test suite to confirm nothing broke**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

Expected: all tests pass (health + config + graph_auth).

- [ ] **Step 3.7: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/ apps/backend/tests/test_graph_auth.py
git commit -m "feat(backend): add GraphAuthService with client-credentials flow (BE-01)"
```

---

## Task 4: Verification script

**Files:**
- Create: `apps/backend/scripts/__init__.py` (empty — makes scripts importable by uv)
- Create: `apps/backend/scripts/verify_graph_auth.py`

This script is **not** a pytest test — it is an integration harness that runs against a real Azure tenant. It requires a populated `.env` file with valid credentials.

- [ ] **Step 4.1: Create the scripts directory**

```bash
mkdir -p /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend/scripts
touch /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend/scripts/__init__.py
```

- [ ] **Step 4.2: Create the verification script**

Create `apps/backend/scripts/verify_graph_auth.py`:

```python
"""
Verification script for BE-01 — Graph auth.

Run from apps/backend/:
    uv run python scripts/verify_graph_auth.py

Requires a populated .env with:
    AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
Optionally:
    SHAREPOINT_SITE_URL  (enables a live Graph site lookup)
"""

import asyncio
import sys
from urllib.parse import urlparse

from app.config import Settings
from app.services.graph_auth import GraphAuthService


async def verify() -> None:
    settings = Settings()  # reads .env in cwd

    print("=== BE-01 Graph Auth Verification ===\n")

    # Step 1: acquire a token
    print("1. Acquiring Graph token via client-credentials...")
    service = GraphAuthService(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )
    credential = service.get_credential()
    token = credential.get_token("https://graph.microsoft.com/.default")

    if not token.token:
        print("   FAIL — token is empty")
        sys.exit(1)

    print(f"   OK — token acquired (expires: {token.expires_on})\n")

    # Step 2: make a real Graph call if site URL is configured
    if settings.sharepoint_site_url:
        print(f"2. Verifying Graph access to: {settings.sharepoint_site_url}")
        parsed = urlparse(settings.sharepoint_site_url)
        hostname = parsed.netloc
        site_path = parsed.path.rstrip("/")

        client = service.get_client()
        try:
            site = await client.sites.by_site_id(f"{hostname}:{site_path}").get()
            print(f"   OK — site accessible: {site.display_name}\n")
        except Exception as exc:
            print(f"   FAIL — Graph call raised: {exc}")
            sys.exit(1)
    else:
        print("2. SHAREPOINT_SITE_URL not set — skipping live Graph site lookup")
        print("   (Set it in .env to test the full permissions grant)\n")

    print("=== Verification complete — Graph auth is working ===")


if __name__ == "__main__":
    asyncio.run(verify())
```

- [ ] **Step 4.3: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/scripts/
git commit -m "feat(backend): add Graph auth verification script (BE-01)"
```

---

## Task 5: Ruff lint gate

**Files:** none new

- [ ] **Step 5.1: Run ruff**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run ruff check src/ tests/ scripts/
uv run ruff format --check src/ tests/ scripts/
```

If any issues:
```bash
uv run ruff format src/ tests/ scripts/
uv run ruff check --fix src/ tests/ scripts/
```

Re-run both checks to confirm clean.

- [ ] **Step 5.2: Commit any fixes**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/ apps/backend/tests/ apps/backend/scripts/
git commit -m "style(backend): ruff formatting (BE-01)" --allow-empty
```

---

## Task 6: Push branch

- [ ] **Step 6.1: Push to origin**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git push -u origin feature/BE-01-graph-auth
```

---

## Self-Review

**Spec coverage:**

| Acceptance criterion | Task |
|---|---|
| Entra app registration with client secret | Prerequisites (manual) |
| Graph permission granted with admin consent | Prerequisites (manual) |
| Backend acquires Graph token via client-credentials | Task 3 (GraphAuthService) |
| Verification script confirms token + Graph call | Task 4 |
| Credentials from config (env / .env) | Task 2 (Settings) |

**Placeholder scan:** none found — all steps have complete code.

**Type consistency:** `GraphAuthService.__init__` takes `(tenant_id, client_id, client_secret)` as `str` — consistent across Task 3 tests and Task 4 verification script. `get_settings()` returns `Settings` — consistent with Task 4 usage.
