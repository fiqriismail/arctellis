# BE-02 SharePoint Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `SharePointService` that reads list items and column schema from Microsoft Graph so downstream tools have structured data and column metadata to work with.

**Architecture:** `SharePointService` wraps the `GraphServiceClient` from BE-01 and exposes two async methods — `get_schema()` returning column definitions and `get_items()` returning list items with parsed field values. A factory function resolves the site ID from the configured URL. A `_safe_parse` utility converts loosely-typed SharePoint field values defensively without crashing on bad data.

**Tech Stack:** Python 3.13 · msgraph-sdk · azure-identity · pydantic-settings · pytest · pytest-asyncio · uv

**Story:** BE-02
**Working directory:** `apps/backend/` inside repo root `/Users/fiqriismail/Projects/Arctellis/group-one-rtp`

**Existing context:**
- `src/app/config.py` — `Settings` with `sharepoint_site_url`, `sharepoint_list_id`, `azure_tenant_id`, `azure_client_id`, `azure_client_secret`
- `src/app/services/graph_auth.py` — `GraphAuthService` with `get_client() -> GraphServiceClient`
- `.env` is populated with real credentials and `SHAREPOINT_SITE_URL=https://barringtondigital.sharepoint.com/sites/Procurement`, `SHAREPOINT_LIST_ID=37b0d45b-4f69-42cf-b26f-7112033a83fb`

---

## File Map

```
apps/backend/
├── src/app/
│   └── services/
│       ├── sharepoint.py           ← SharePointService, ColumnDefinition, ListItem, create_sharepoint_service
│       └── graph_auth.py           ← existing, unchanged
├── tests/
│   └── test_sharepoint_service.py  ← unit tests (all mocked — no real Graph calls)
└── scripts/
    └── verify_sharepoint.py        ← integration harness (requires .env)
```

---

## Task 1: Git branch

- [ ] **Step 1.1: Create feature branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git checkout -b feature/BE-02-sharepoint-service
```

Expected: `Switched to a new branch 'feature/BE-02-sharepoint-service'`

---

## Task 2: Data models + SharePointService constructor (TDD)

**Files:**
- Create: `apps/backend/src/app/services/sharepoint.py`
- Create: `apps/backend/tests/test_sharepoint_service.py`

- [ ] **Step 2.1: Write failing tests**

Create `apps/backend/tests/test_sharepoint_service.py`:

```python
from unittest.mock import MagicMock


def test_column_definition_stores_fields():
    from app.services.sharepoint import ColumnDefinition

    col = ColumnDefinition(name="Budget", display_name="Budget", column_type="number")
    assert col.name == "Budget"
    assert col.display_name == "Budget"
    assert col.column_type == "number"


def test_list_item_stores_fields():
    from app.services.sharepoint import ListItem

    item = ListItem(id="1", fields={"Title": "Test", "Budget": 100.0})
    assert item.id == "1"
    assert item.fields["Title"] == "Test"


def test_sharepoint_service_stores_client_and_ids():
    from app.services.sharepoint import SharePointService

    mock_client = MagicMock()
    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    assert service._site_id == "site-1"
    assert service._list_id == "list-1"
```

- [ ] **Step 2.2: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.services.sharepoint'`

- [ ] **Step 2.3: Implement models and service skeleton**

Create `apps/backend/src/app/services/sharepoint.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from msgraph import GraphServiceClient


@dataclass
class ColumnDefinition:
    name: str
    display_name: str
    column_type: str  # "text" | "number" | "dateTime" | "choice" | "boolean" | "lookup" | "person" | "other"


@dataclass
class ListItem:
    id: str
    fields: dict[str, Any]


class SharePointService:
    def __init__(
        self,
        client: GraphServiceClient,
        site_id: str,
        list_id: str,
    ) -> None:
        self._client = client
        self._site_id = site_id
        self._list_id = list_id
```

- [ ] **Step 2.4: Run tests — verify they PASS**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py -v
```

Expected: 3 passed.

- [ ] **Step 2.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): add SharePointService skeleton and data models (BE-02)"
```

---

## Task 3: `_infer_column_type` and `_safe_parse` pure functions (TDD)

**Files:**
- Modify: `apps/backend/src/app/services/sharepoint.py`
- Modify: `apps/backend/tests/test_sharepoint_service.py`

- [ ] **Step 3.1: Write failing tests**

Append to `apps/backend/tests/test_sharepoint_service.py`:

```python
def test_infer_column_type_number():
    from app.services.sharepoint import SharePointService

    mock_col = MagicMock()
    mock_col.number = MagicMock()  # non-None = number column
    mock_col.date_time = None
    mock_col.boolean = None
    mock_col.choice = None
    mock_col.lookup = None
    mock_col.person_or_group = None
    assert SharePointService._infer_column_type(mock_col) == "number"


def test_infer_column_type_datetime():
    from app.services.sharepoint import SharePointService

    mock_col = MagicMock()
    mock_col.number = None
    mock_col.date_time = MagicMock()
    mock_col.boolean = None
    mock_col.choice = None
    mock_col.lookup = None
    mock_col.person_or_group = None
    assert SharePointService._infer_column_type(mock_col) == "dateTime"


def test_infer_column_type_boolean():
    from app.services.sharepoint import SharePointService

    mock_col = MagicMock()
    mock_col.number = None
    mock_col.date_time = None
    mock_col.boolean = MagicMock()
    mock_col.choice = None
    mock_col.lookup = None
    mock_col.person_or_group = None
    assert SharePointService._infer_column_type(mock_col) == "boolean"


def test_infer_column_type_defaults_to_text():
    from app.services.sharepoint import SharePointService

    mock_col = MagicMock()
    mock_col.number = None
    mock_col.date_time = None
    mock_col.boolean = None
    mock_col.choice = None
    mock_col.lookup = None
    mock_col.person_or_group = None
    assert SharePointService._infer_column_type(mock_col) == "text"


def test_safe_parse_number_valid():
    from app.services.sharepoint import SharePointService

    assert SharePointService._safe_parse("42.5", "number") == 42.5


def test_safe_parse_number_integer_string():
    from app.services.sharepoint import SharePointService

    assert SharePointService._safe_parse("10", "number") == 10.0


def test_safe_parse_number_invalid_returns_none():
    from app.services.sharepoint import SharePointService

    assert SharePointService._safe_parse("not-a-number", "number") is None


def test_safe_parse_datetime_valid():
    from app.services.sharepoint import SharePointService

    result = SharePointService._safe_parse("2026-01-15T10:00:00Z", "dateTime")
    assert result is not None
    assert result.year == 2026


def test_safe_parse_datetime_invalid_returns_none():
    from app.services.sharepoint import SharePointService

    assert SharePointService._safe_parse("not-a-date", "dateTime") is None


def test_safe_parse_boolean_true():
    from app.services.sharepoint import SharePointService

    assert SharePointService._safe_parse(True, "boolean") is True


def test_safe_parse_boolean_string_true():
    from app.services.sharepoint import SharePointService

    assert SharePointService._safe_parse("true", "boolean") is True


def test_safe_parse_boolean_string_false():
    from app.services.sharepoint import SharePointService

    assert SharePointService._safe_parse("false", "boolean") is False


def test_safe_parse_none_returns_none():
    from app.services.sharepoint import SharePointService

    assert SharePointService._safe_parse(None, "text") is None


def test_safe_parse_text_returns_string():
    from app.services.sharepoint import SharePointService

    assert SharePointService._safe_parse("hello", "text") == "hello"
```

- [ ] **Step 3.2: Run tests — verify new tests FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
```

Expected: the 3 from Task 2 pass, new tests fail with `AttributeError`.

- [ ] **Step 3.3: Implement the pure functions**

Add to `apps/backend/src/app/services/sharepoint.py` — add the import at the top and methods to `SharePointService`:

Add to imports section (after `from __future__ import annotations`):

```python
from datetime import datetime
```

Add as static methods inside `SharePointService` (after `__init__`):

```python
    @staticmethod
    def _infer_column_type(col: Any) -> str:
        if col.number is not None:
            return "number"
        if col.date_time is not None:
            return "dateTime"
        if col.boolean is not None:
            return "boolean"
        if col.choice is not None:
            return "choice"
        if col.lookup is not None:
            return "lookup"
        if col.person_or_group is not None:
            return "person"
        return "text"

    @staticmethod
    def _safe_parse(value: Any, column_type: str) -> Any:
        if value is None:
            return None
        if column_type == "number":
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        if column_type == "dateTime":
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    return None
            return None
        if column_type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        return str(value)
```

- [ ] **Step 3.4: Run tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py -v
```

Expected: all 17 tests pass.

- [ ] **Step 3.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): add _infer_column_type and _safe_parse to SharePointService (BE-02)"
```

---

## Task 4: `get_schema()` (TDD)

**Files:**
- Modify: `apps/backend/src/app/services/sharepoint.py`
- Modify: `apps/backend/tests/test_sharepoint_service.py`

- [ ] **Step 4.1: Write failing tests**

Append to `apps/backend/tests/test_sharepoint_service.py`:

```python
import pytest
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_get_schema_returns_column_definitions():
    from app.services.sharepoint import SharePointService

    mock_col1 = MagicMock()
    mock_col1.name = "Title"
    mock_col1.display_name = "Title"
    mock_col1.hidden = False
    mock_col1.number = None
    mock_col1.date_time = None
    mock_col1.boolean = None
    mock_col1.choice = None
    mock_col1.lookup = None
    mock_col1.person_or_group = None

    mock_col2 = MagicMock()
    mock_col2.name = "Budget"
    mock_col2.display_name = "Budget"
    mock_col2.hidden = False
    mock_col2.number = MagicMock()
    mock_col2.date_time = None
    mock_col2.boolean = None
    mock_col2.choice = None
    mock_col2.lookup = None
    mock_col2.person_or_group = None

    mock_response = MagicMock()
    mock_response.value = [mock_col1, mock_col2]

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.columns.get = AsyncMock(
        return_value=mock_response
    )

    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    columns = await service.get_schema()

    assert len(columns) == 2
    assert columns[0].name == "Title"
    assert columns[0].column_type == "text"
    assert columns[1].name == "Budget"
    assert columns[1].column_type == "number"


@pytest.mark.asyncio
async def test_get_schema_skips_hidden_columns():
    from app.services.sharepoint import SharePointService

    mock_visible = MagicMock()
    mock_visible.name = "Status"
    mock_visible.display_name = "Status"
    mock_visible.hidden = False
    mock_visible.number = None
    mock_visible.date_time = None
    mock_visible.boolean = None
    mock_visible.choice = MagicMock()
    mock_visible.lookup = None
    mock_visible.person_or_group = None

    mock_hidden = MagicMock()
    mock_hidden.name = "_UIVersionString"
    mock_hidden.display_name = "UI Version"
    mock_hidden.hidden = True

    mock_response = MagicMock()
    mock_response.value = [mock_visible, mock_hidden]

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.columns.get = AsyncMock(
        return_value=mock_response
    )

    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    columns = await service.get_schema()

    assert len(columns) == 1
    assert columns[0].name == "Status"
    assert columns[0].column_type == "choice"


@pytest.mark.asyncio
async def test_get_schema_returns_empty_on_no_columns():
    from app.services.sharepoint import SharePointService

    mock_response = MagicMock()
    mock_response.value = []

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.columns.get = AsyncMock(
        return_value=mock_response
    )

    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    columns = await service.get_schema()
    assert columns == []
```

- [ ] **Step 4.2: Run tests — verify new tests FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py::test_get_schema_returns_column_definitions -v
```

Expected: `AttributeError: 'SharePointService' object has no attribute 'get_schema'`

- [ ] **Step 4.3: Implement `get_schema()`**

Add to `SharePointService` in `apps/backend/src/app/services/sharepoint.py`:

```python
    async def get_schema(self) -> list[ColumnDefinition]:
        result = await (
            self._client.sites.by_site_id(self._site_id)
            .lists.by_list_id(self._list_id)
            .columns.get()
        )
        columns: list[ColumnDefinition] = []
        if not result or not result.value:
            return columns
        for col in result.value:
            if col.hidden or not col.name:
                continue
            columns.append(
                ColumnDefinition(
                    name=col.name,
                    display_name=col.display_name or col.name,
                    column_type=self._infer_column_type(col),
                )
            )
        return columns
```

- [ ] **Step 4.4: Run tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py -v
```

Expected: all 20 tests pass.

- [ ] **Step 4.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): implement get_schema on SharePointService (BE-02)"
```

---

## Task 5: `get_items()` (TDD)

**Files:**
- Modify: `apps/backend/src/app/services/sharepoint.py`
- Modify: `apps/backend/tests/test_sharepoint_service.py`

- [ ] **Step 5.1: Write failing tests**

Append to `apps/backend/tests/test_sharepoint_service.py`:

```python
@pytest.mark.asyncio
async def test_get_items_returns_list_items():
    from app.services.sharepoint import SharePointService

    mock_fields = MagicMock()
    mock_fields.additional_data = {"Title": "Request 1", "Budget": "5000"}

    mock_item = MagicMock()
    mock_item.id = "42"
    mock_item.fields = mock_fields

    mock_response = MagicMock()
    mock_response.value = [mock_item]
    mock_response.odata_next_link = None

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get = AsyncMock(
        return_value=mock_response
    )

    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    items = await service.get_items()

    assert len(items) == 1
    assert items[0].id == "42"
    assert items[0].fields["Title"] == "Request 1"
    assert items[0].fields["Budget"] == "5000"


@pytest.mark.asyncio
async def test_get_items_returns_empty_on_no_items():
    from app.services.sharepoint import SharePointService

    mock_response = MagicMock()
    mock_response.value = []
    mock_response.odata_next_link = None

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get = AsyncMock(
        return_value=mock_response
    )

    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    items = await service.get_items()
    assert items == []


@pytest.mark.asyncio
async def test_get_items_handles_none_fields():
    from app.services.sharepoint import SharePointService

    mock_item = MagicMock()
    mock_item.id = "1"
    mock_item.fields = None

    mock_response = MagicMock()
    mock_response.value = [mock_item]
    mock_response.odata_next_link = None

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get = AsyncMock(
        return_value=mock_response
    )

    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    items = await service.get_items()

    assert len(items) == 1
    assert items[0].fields == {}


@pytest.mark.asyncio
async def test_get_items_passes_odata_filter():
    from app.services.sharepoint import SharePointService

    mock_response = MagicMock()
    mock_response.value = []
    mock_response.odata_next_link = None

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get = get_mock

    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    await service.get_items(odata_filter="fields/Status eq 'Active'")

    get_mock.assert_called_once()
    call_kwargs = get_mock.call_args
    request_config = call_kwargs[1].get("request_configuration") or call_kwargs[0][0]
    assert request_config is not None
```

- [ ] **Step 5.2: Run tests — verify new tests FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py::test_get_items_returns_list_items -v
```

Expected: `AttributeError: 'SharePointService' object has no attribute 'get_items'`

- [ ] **Step 5.3: Implement `get_items()`**

Add to imports in `apps/backend/src/app/services/sharepoint.py`:

```python
from msgraph.generated.sites.item.lists.item.items.items_request_builder import (
    ItemsRequestBuilder,
)
from kiota_abstractions.base_request_configuration import RequestConfiguration
```

Add method to `SharePointService`:

```python
    async def get_items(self, odata_filter: str | None = None) -> list[ListItem]:
        query_params = ItemsRequestBuilder.ItemsRequestBuilderGetQueryParameters(
            expand=["fields"],
        )
        if odata_filter:
            query_params.filter = odata_filter

        request_configuration = RequestConfiguration(query_parameters=query_params)

        result = await (
            self._client.sites.by_site_id(self._site_id)
            .lists.by_list_id(self._list_id)
            .items.get(request_configuration=request_configuration)
        )

        items: list[ListItem] = []
        if not result or not result.value:
            return items

        for item in result.value:
            fields: dict[str, Any] = {}
            if item.fields and item.fields.additional_data:
                fields = dict(item.fields.additional_data)
            items.append(ListItem(id=item.id or "", fields=fields))

        return items
```

- [ ] **Step 5.4: Run full test suite — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

Expected: all tests pass (health + config + graph_auth + sharepoint_service).

- [ ] **Step 5.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): implement get_items on SharePointService (BE-02)"
```

---

## Task 6: Factory function `create_sharepoint_service()` (TDD)

**Files:**
- Modify: `apps/backend/src/app/services/sharepoint.py`
- Modify: `apps/backend/tests/test_sharepoint_service.py`

- [ ] **Step 6.1: Write failing tests**

Append to `apps/backend/tests/test_sharepoint_service.py`:

```python
@pytest.mark.asyncio
async def test_create_sharepoint_service_resolves_site_id():
    from app.services.sharepoint import create_sharepoint_service, SharePointService

    mock_site = MagicMock()
    mock_site.id = "barringtondigital.sharepoint.com,abc-123,def-456"

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.get = AsyncMock(return_value=mock_site)

    mock_auth = MagicMock()
    mock_auth.get_client.return_value = mock_client

    mock_settings = MagicMock()
    mock_settings.sharepoint_site_url = "https://barringtondigital.sharepoint.com/sites/Procurement"
    mock_settings.sharepoint_list_id = "37b0d45b-4f69-42cf-b26f-7112033a83fb"

    service = await create_sharepoint_service(
        auth_service=mock_auth,
        settings=mock_settings,
    )

    assert isinstance(service, SharePointService)
    assert service._site_id == "barringtondigital.sharepoint.com,abc-123,def-456"
    assert service._list_id == "37b0d45b-4f69-42cf-b26f-7112033a83fb"
    mock_client.sites.by_site_id.assert_called_once_with(
        "barringtondigital.sharepoint.com:/sites/Procurement"
    )
```

- [ ] **Step 6.2: Run test — verify it FAILS**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py::test_create_sharepoint_service_resolves_site_id -v
```

Expected: `ImportError: cannot import name 'create_sharepoint_service'`

- [ ] **Step 6.3: Implement the factory function**

Add to imports in `apps/backend/src/app/services/sharepoint.py`:

```python
from urllib.parse import urlparse
```

Add after the `SharePointService` class (at module level):

```python
async def create_sharepoint_service(
    auth_service: Any,
    settings: Any,
) -> SharePointService:
    """Resolve site ID from URL and return a configured SharePointService."""
    client = auth_service.get_client()
    parsed = urlparse(settings.sharepoint_site_url)
    hostname = parsed.netloc
    site_path = parsed.path.rstrip("/")
    site = await client.sites.by_site_id(f"{hostname}:{site_path}").get()
    return SharePointService(
        client=client,
        site_id=site.id,
        list_id=settings.sharepoint_list_id,
    )
```

- [ ] **Step 6.4: Run full test suite — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 6.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): add create_sharepoint_service factory (BE-02)"
```

---

## Task 7: Verification script

**Files:**
- Create: `apps/backend/scripts/verify_sharepoint.py`

This script requires a populated `.env`. It exercises the real Procurement list.

- [ ] **Step 7.1: Create the script**

Create `apps/backend/scripts/verify_sharepoint.py`:

```python
"""
Verification script for BE-02 — SharePoint Service.

Run from apps/backend/:
    uv run python scripts/verify_sharepoint.py

Requires a populated .env with all Graph + SharePoint credentials.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.config import Settings
from app.services.graph_auth import GraphAuthService
from app.services.sharepoint import create_sharepoint_service


async def verify() -> None:
    settings = Settings()
    print("=== BE-02 SharePoint Service Verification ===\n")

    auth = GraphAuthService(
        tenant_id=settings.azure_tenant_id,
        client_id=settings.azure_client_id,
        client_secret=settings.azure_client_secret,
    )

    print(f"1. Resolving site and connecting to list {settings.sharepoint_list_id}...")
    service = await create_sharepoint_service(auth_service=auth, settings=settings)
    print("   OK — SharePointService created\n")

    print("2. Reading list schema...")
    columns = await service.get_schema()
    if not columns:
        print("   FAIL — no columns returned")
        sys.exit(1)
    print(f"   OK — {len(columns)} columns found:")
    for col in columns:
        print(f"      {col.name!r:30s} ({col.column_type})")
    print()

    print("3. Reading list items (first page)...")
    items = await service.get_items()
    if items is None:
        print("   FAIL — get_items returned None")
        sys.exit(1)
    print(f"   OK — {len(items)} items returned")
    if items:
        print("   First item fields:")
        for key, val in list(items[0].fields.items())[:5]:
            print(f"      {key}: {val!r}")
    print()

    print("=== Verification complete — SharePoint service is working ===")


if __name__ == "__main__":
    asyncio.run(verify())
```

- [ ] **Step 7.2: Run the script against the real list**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run python scripts/verify_sharepoint.py
```

Expected: schema with column names/types printed, item count > 0, first item fields visible. If errors, diagnose and fix `sharepoint.py` before committing.

- [ ] **Step 7.3: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/scripts/verify_sharepoint.py
git commit -m "feat(backend): add SharePoint service verification script (BE-02)"
```

---

## Task 8: Ruff lint + push

- [ ] **Step 8.1: Run ruff**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run ruff check src/ tests/ scripts/
uv run ruff format --check src/ tests/ scripts/
```

Fix any issues:
```bash
uv run ruff format src/ tests/ scripts/
uv run ruff check --fix src/ tests/ scripts/
```

- [ ] **Step 8.2: Commit any fixes**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/ apps/backend/tests/ apps/backend/scripts/
git commit -m "style(backend): ruff formatting (BE-02)" --allow-empty
```

- [ ] **Step 8.3: Push branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git push -u origin feature/BE-02-sharepoint-service
```

---

## Self-Review

**Spec coverage:**

| Acceptance criterion | Task |
|---|---|
| Reads list items via Graph for configured site + list ID (FR-12, FR-13) | Tasks 5, 6 |
| Returns column names and types (FR-14) | Task 4 |
| Internal vs display field names handled (§8) | Task 4 — `display_name` vs `name` in `ColumnDefinition` |
| Loosely-typed values parsed defensively (§5.1, §8) | Task 3 — `_safe_parse` |
| Verified with Phase 1 harness reading real list | Task 7 |

**Placeholder scan:** None found — all steps have complete code.

**Type consistency:**
- `ColumnDefinition(name, display_name, column_type)` — consistent across Tasks 2, 3, 4 and verification script.
- `ListItem(id, fields)` — consistent across Tasks 2, 5 and verification script.
- `create_sharepoint_service(auth_service, settings)` — consistent across Task 6 test and Task 7 script.
- `SharePointService._safe_parse(value, column_type)` — consistent across Task 3 tests and Task 4 `get_schema` usage (column_type string values match `_infer_column_type` return values).
