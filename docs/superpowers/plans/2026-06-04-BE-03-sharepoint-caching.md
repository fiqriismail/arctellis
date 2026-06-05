# BE-03 SharePoint Data Caching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a short-lived in-memory TTL cache to `SharePointService` so that repeated Graph calls within a single multi-step answer reuse cached data.

**Architecture:** A lightweight `_TTLCache` helper class (dict + `time.monotonic` timestamps) lives inside `sharepoint.py`. `SharePointService` holds one cache instance, keyed by `"schema"` for `get_schema()` and by `f"items:{odata_filter or ''}"` for `get_items()`. The TTL (in seconds) is injected at construction time from `settings.cache_ttl_seconds`, keeping it tunable without a code change.

**Tech Stack:** Python 3.13 · `time.monotonic` (stdlib) · pytest · pytest-asyncio · uv

**Story:** BE-03  
**Working directory:** `apps/backend/` inside repo root `/Users/fiqriismail/Projects/Arctellis/group-one-rtp`

**Existing context:**
- `src/app/services/sharepoint.py` — `SharePointService` with `get_schema()` and `get_items()`; `create_sharepoint_service()` factory
- `src/app/config.py` — `Settings.cache_ttl_seconds: int = 60`
- `tests/test_sharepoint_service.py` — 40 tests already passing

---

## File Map

```
apps/backend/
├── src/app/
│   └── services/
│       └── sharepoint.py    ← add _TTLCache, update __init__, wrap get_schema/get_items, update factory
└── tests/
    └── test_sharepoint_service.py  ← add cache tests
```

---

## Task 1: Git branch

- [ ] **Step 1.1: Create feature branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git checkout -b feature/BE-03-sharepoint-caching
```

Expected: `Switched to a new branch 'feature/BE-03-sharepoint-caching'`

---

## Task 2: `_TTLCache` helper class (TDD)

**Files:**
- Modify: `apps/backend/src/app/services/sharepoint.py`
- Modify: `apps/backend/tests/test_sharepoint_service.py`

The `_TTLCache` is a simple dict-backed cache: `set(key, value)` stores `(value, expiry)`, `get(key)` returns the value if not expired else `None`, `invalidate(key)` removes a key.

- [ ] **Step 2.1: Append failing tests**

Append to the end of `apps/backend/tests/test_sharepoint_service.py`:

```python
# --- _TTLCache tests ---

import time


def test_ttl_cache_get_returns_value_before_expiry():
    from app.services.sharepoint import _TTLCache

    cache = _TTLCache(ttl=60)
    cache.set("key1", ["data"])
    result = cache.get("key1")
    assert result == ["data"]


def test_ttl_cache_get_returns_none_for_missing_key():
    from app.services.sharepoint import _TTLCache

    cache = _TTLCache(ttl=60)
    assert cache.get("missing") is None


def test_ttl_cache_get_returns_none_after_expiry():
    from app.services.sharepoint import _TTLCache

    cache = _TTLCache(ttl=0)  # expires immediately
    cache.set("key1", "value")
    time.sleep(0.01)  # tiny sleep ensures monotonic clock has advanced
    assert cache.get("key1") is None


def test_ttl_cache_set_overwrites_existing_key():
    from app.services.sharepoint import _TTLCache

    cache = _TTLCache(ttl=60)
    cache.set("key1", "first")
    cache.set("key1", "second")
    assert cache.get("key1") == "second"


def test_ttl_cache_different_keys_are_independent():
    from app.services.sharepoint import _TTLCache

    cache = _TTLCache(ttl=60)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    assert cache.get("b") == 2
```

- [ ] **Step 2.2: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py::test_ttl_cache_get_returns_value_before_expiry -v
```

Expected: `ImportError: cannot import name '_TTLCache'`

- [ ] **Step 2.3: Implement `_TTLCache`**

Add to `apps/backend/src/app/services/sharepoint.py` — insert after existing imports, before `@dataclass class ColumnDefinition`:

Add `import time` to the imports block (after `from datetime import datetime`).

Then add this class:

```python
class _TTLCache:
    """Simple in-memory TTL cache backed by a dict and monotonic timestamps."""

    def __init__(self, ttl: int) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if time.monotonic() >= expiry:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (value, time.monotonic() + self._ttl)
```

- [ ] **Step 2.4: Run tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py -v
```

Expected: 45 passed (40 existing + 5 new).

- [ ] **Step 2.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): add _TTLCache helper to SharePointService (BE-03)"
```

---

## Task 3: Wire cache into `SharePointService.__init__` (TDD)

**Files:**
- Modify: `apps/backend/src/app/services/sharepoint.py`
- Modify: `apps/backend/tests/test_sharepoint_service.py`

`SharePointService.__init__` gains a `cache_ttl: int = 60` parameter and creates a `self._cache` instance.

- [ ] **Step 3.1: Append failing test**

Append to the end of `apps/backend/tests/test_sharepoint_service.py`:

```python
def test_sharepoint_service_creates_cache_with_given_ttl():
    from app.services.sharepoint import SharePointService, _TTLCache

    mock_client = MagicMock()
    service = SharePointService(client=mock_client, site_id="s", list_id="l", cache_ttl=30)
    assert isinstance(service._cache, _TTLCache)
    assert service._cache._ttl == 30


def test_sharepoint_service_default_cache_ttl_is_60():
    from app.services.sharepoint import SharePointService, _TTLCache

    mock_client = MagicMock()
    service = SharePointService(client=mock_client, site_id="s", list_id="l")
    assert isinstance(service._cache, _TTLCache)
    assert service._cache._ttl == 60
```

- [ ] **Step 3.2: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py::test_sharepoint_service_creates_cache_with_given_ttl -v
```

Expected: `TypeError: SharePointService.__init__() got an unexpected keyword argument 'cache_ttl'`

- [ ] **Step 3.3: Update `SharePointService.__init__`**

Replace the existing `__init__` in `apps/backend/src/app/services/sharepoint.py`:

```python
    def __init__(
        self,
        client: GraphServiceClient,
        site_id: str,
        list_id: str,
        cache_ttl: int = 60,
    ) -> None:
        self._client = client
        self._site_id = site_id
        self._list_id = list_id
        self._cache = _TTLCache(ttl=cache_ttl)
```

- [ ] **Step 3.4: Run tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py -v
```

Expected: 47 passed.

- [ ] **Step 3.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): add cache_ttl parameter to SharePointService (BE-03)"
```

---

## Task 4: Cache `get_schema()` (TDD)

**Files:**
- Modify: `apps/backend/src/app/services/sharepoint.py`
- Modify: `apps/backend/tests/test_sharepoint_service.py`

On first call, fetch from Graph and store under key `"schema"`. On subsequent calls within TTL, return cached value without calling Graph.

- [ ] **Step 4.1: Append failing tests**

Append to the end of `apps/backend/tests/test_sharepoint_service.py`:

```python
@pytest.mark.asyncio
async def test_get_schema_cached_on_second_call():
    from app.services.sharepoint import SharePointService

    mock_col = MagicMock()
    mock_col.name = "Title"
    mock_col.display_name = "Title"
    mock_col.hidden = False
    mock_col.number = None
    mock_col.date_time = None
    mock_col.boolean = None
    mock_col.choice = None
    mock_col.lookup = None
    mock_col.person_or_group = None

    mock_response = MagicMock()
    mock_response.value = [mock_col]

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.columns.get = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l", cache_ttl=60)

    first = await service.get_schema()
    second = await service.get_schema()

    assert first == second
    assert get_mock.call_count == 1  # Graph called only once


@pytest.mark.asyncio
async def test_get_schema_refetches_after_ttl_expiry():
    from app.services.sharepoint import SharePointService

    mock_col = MagicMock()
    mock_col.name = "Title"
    mock_col.display_name = "Title"
    mock_col.hidden = False
    mock_col.number = None
    mock_col.date_time = None
    mock_col.boolean = None
    mock_col.choice = None
    mock_col.lookup = None
    mock_col.person_or_group = None

    mock_response = MagicMock()
    mock_response.value = [mock_col]

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.columns.get = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l", cache_ttl=0)

    await service.get_schema()
    time.sleep(0.01)
    await service.get_schema()

    assert get_mock.call_count == 2  # Graph called again after expiry
```

- [ ] **Step 4.2: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py::test_get_schema_cached_on_second_call -v
```

Expected: FAIL — `get_mock.call_count == 2` (cache not wired yet).

- [ ] **Step 4.3: Update `get_schema()` with cache**

Replace `get_schema` in `apps/backend/src/app/services/sharepoint.py`:

```python
    async def get_schema(self) -> list[ColumnDefinition]:
        cached = self._cache.get("schema")
        if cached is not None:
            return cached
        result = await (
            self._client.sites.by_site_id(self._site_id)
            .lists.by_list_id(self._list_id)
            .columns.get()
        )
        columns: list[ColumnDefinition] = []
        if not result or not result.value:
            self._cache.set("schema", columns)
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
        self._cache.set("schema", columns)
        return columns
```

- [ ] **Step 4.4: Run all tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py -v
```

Expected: 49 passed.

- [ ] **Step 4.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): cache get_schema results in SharePointService (BE-03)"
```

---

## Task 5: Cache `get_items()` with filter-aware keys (TDD)

**Files:**
- Modify: `apps/backend/src/app/services/sharepoint.py`
- Modify: `apps/backend/tests/test_sharepoint_service.py`

Cache key for items is `f"items:{odata_filter or ''}"`. Different filters produce different keys, so they never collide.

- [ ] **Step 5.1: Append failing tests**

Append to the end of `apps/backend/tests/test_sharepoint_service.py`:

```python
@pytest.mark.asyncio
async def test_get_items_cached_on_second_call():
    from app.services.sharepoint import SharePointService

    mock_fields = MagicMock()
    mock_fields.additional_data = {"Title": "Row 1"}
    mock_item = MagicMock()
    mock_item.id = "1"
    mock_item.fields = mock_fields
    mock_response = MagicMock()
    mock_response.value = [mock_item]
    mock_response.odata_next_link = None

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l", cache_ttl=60)

    first = await service.get_items()
    second = await service.get_items()

    assert first == second
    assert get_mock.call_count == 1  # Graph called only once


@pytest.mark.asyncio
async def test_get_items_different_filters_have_separate_cache_keys():
    from app.services.sharepoint import SharePointService

    mock_response = MagicMock()
    mock_response.value = []
    mock_response.odata_next_link = None

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l", cache_ttl=60)

    await service.get_items(odata_filter="fields/Status eq 'Active'")
    await service.get_items(odata_filter="fields/Status eq 'Closed'")

    # Two different filters → two Graph calls (no cache collision)
    assert get_mock.call_count == 2


@pytest.mark.asyncio
async def test_get_items_refetches_after_ttl_expiry():
    from app.services.sharepoint import SharePointService

    mock_response = MagicMock()
    mock_response.value = []
    mock_response.odata_next_link = None

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l", cache_ttl=0)

    await service.get_items()
    time.sleep(0.01)
    await service.get_items()

    assert get_mock.call_count == 2  # Refetched after TTL expiry


@pytest.mark.asyncio
async def test_get_items_same_filter_reuses_cache():
    from app.services.sharepoint import SharePointService

    mock_response = MagicMock()
    mock_response.value = []
    mock_response.odata_next_link = None

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l", cache_ttl=60)

    f = "fields/Status eq 'Active'"
    await service.get_items(odata_filter=f)
    await service.get_items(odata_filter=f)

    # Same filter → cache hit on second call
    assert get_mock.call_count == 1
```

- [ ] **Step 5.2: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py::test_get_items_cached_on_second_call -v
```

Expected: FAIL — `get_mock.call_count == 2` (cache not wired yet).

- [ ] **Step 5.3: Update `get_items()` with cache**

Replace `get_items` in `apps/backend/src/app/services/sharepoint.py`:

```python
    async def get_items(self, odata_filter: str | None = None) -> list[ListItem]:
        cache_key = f"items:{odata_filter or ''}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        builder = items_request_builder.ItemsRequestBuilder
        query_params = builder.ItemsRequestBuilderGetQueryParameters(expand=["fields"])
        if odata_filter:
            query_params.filter = odata_filter

        request_configuration = RequestConfiguration(query_parameters=query_params)

        result = await (
            self._client.sites.by_site_id(self._site_id)
            .lists.by_list_id(self._list_id)
            .items.get(request_configuration=request_configuration)
        )

        # Note: only fetches first page (~200 items). Pagination via
        # odata_next_link not implemented.
        items: list[ListItem] = []
        if not result or not result.value:
            self._cache.set(cache_key, items)
            return items

        for item in result.value:
            fields: dict[str, Any] = {}
            if item.fields and item.fields.additional_data:
                fields = dict(item.fields.additional_data)
            items.append(ListItem(id=item.id or "", fields=fields))

        self._cache.set(cache_key, items)
        return items
```

- [ ] **Step 5.4: Run all tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py -v
```

Expected: 53 passed.

- [ ] **Step 5.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): cache get_items with filter-aware keys (BE-03)"
```

---

## Task 6: Wire TTL from `settings.cache_ttl_seconds` in factory (TDD)

**Files:**
- Modify: `apps/backend/src/app/services/sharepoint.py`
- Modify: `apps/backend/tests/test_sharepoint_service.py`

Update `create_sharepoint_service()` to pass `settings.cache_ttl_seconds` into the `SharePointService` constructor.

- [ ] **Step 6.1: Append failing test**

Append to the end of `apps/backend/tests/test_sharepoint_service.py`:

```python
@pytest.mark.asyncio
async def test_create_sharepoint_service_passes_cache_ttl():
    from app.services.sharepoint import create_sharepoint_service, SharePointService

    mock_site = MagicMock()
    mock_site.id = "barringtondigital.sharepoint.com,abc,def"

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.get = AsyncMock(return_value=mock_site)

    mock_auth = MagicMock()
    mock_auth.get_client.return_value = mock_client

    mock_settings = MagicMock()
    mock_settings.sharepoint_site_url = "https://barringtondigital.sharepoint.com/sites/Procurement"
    mock_settings.sharepoint_list_id = "37b0d45b-4f69-42cf-b26f-7112033a83fb"
    mock_settings.cache_ttl_seconds = 120

    service = await create_sharepoint_service(auth_service=mock_auth, settings=mock_settings)

    assert isinstance(service, SharePointService)
    assert service._cache._ttl == 120
```

- [ ] **Step 6.2: Run test — verify it FAILS**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_sharepoint_service.py::test_create_sharepoint_service_passes_cache_ttl -v
```

Expected: FAIL — `assert 60 == 120` (factory uses default 60, not settings value).

- [ ] **Step 6.3: Update `create_sharepoint_service()` factory**

Replace the `return SharePointService(...)` call in the factory function:

```python
    return SharePointService(
        client=client,
        site_id=site.id,
        list_id=settings.sharepoint_list_id,
        cache_ttl=settings.cache_ttl_seconds,
    )
```

- [ ] **Step 6.4: Run all tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

Expected: all tests pass (54 sharepoint tests + the rest = full suite green).

- [ ] **Step 6.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/services/sharepoint.py apps/backend/tests/test_sharepoint_service.py
git commit -m "feat(backend): wire cache_ttl_seconds from settings into SharePointService factory (BE-03)"
```

---

## Task 7: Ruff lint + push

- [ ] **Step 7.1: Run ruff**

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

- [ ] **Step 7.2: Commit fixes if any**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/ apps/backend/tests/
git diff --staged --quiet || git commit -m "style(backend): ruff formatting (BE-03)"
```

- [ ] **Step 7.3: Final test run**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

All tests must pass.

- [ ] **Step 7.4: Push branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git push -u origin feature/BE-03-sharepoint-caching
```

---

## Self-Review

**Spec coverage:**

| Acceptance criterion | Task |
|---|---|
| Cache with configurable TTL, default 30–60s (D-3, FR-15) | Tasks 2–3: `_TTLCache` with `cache_ttl` param, default 60 |
| Multi-tool answer reuses cached data (NFR-4) | Tasks 4–5: `get_schema` and `get_items` both cache-checked first |
| TTL tunable without a code change (D-3) | Task 6: factory reads `settings.cache_ttl_seconds` |
| Different filtered queries not conflated (keyed appropriately) | Task 5: key is `f"items:{odata_filter or ''}"` — separate per filter |

**Placeholder scan:** None found — all steps have complete code.

**Type consistency:**
- `_TTLCache(ttl=60)` — consistent across Tasks 2, 3, 4, 5, 6.
- `SharePointService(client=..., site_id=..., list_id=..., cache_ttl=...)` — consistent across Task 3 (init), Task 4/5 (tests), Task 6 (factory).
- `self._cache.get(key)` / `self._cache.set(key, value)` — consistent across Tasks 4 and 5.
- Cache key `"schema"` in Task 4, `f"items:{odata_filter or ''}"` in Task 5 — unique, no collision.
