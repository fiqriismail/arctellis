# BE-04 List Data Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build six deterministic `@tool`-decorated Python functions that give the LangChain agent a safe, accurate interface to the SharePoint list — all arithmetic runs in Python, never in the LLM.

**Architecture:** A single `list_tools.py` module exposes `make_tools(service: SharePointService) -> list` — a factory that returns six LangChain `@tool` closures capturing the injected `SharePointService`. Each tool is async (delegating to the async service methods) and returns a plain string the model can read. A module-level `_parse_number()` helper centralises defensive float parsing; tools that need numbers skip rows where it returns `None`.

**Tech Stack:** Python 3.13 · `langchain>=0.3` (`langchain.tools.tool`) · `pytest` · `pytest-asyncio` · `uv`

**Story:** BE-04  
**Working directory:** `apps/backend/` inside repo root `/Users/fiqriismail/Projects/Arctellis/group-one-rtp`

**Existing context:**
- `src/app/services/sharepoint.py` — `SharePointService` with `get_schema() -> list[ColumnDefinition]` and `get_items(odata_filter=None) -> list[ListItem]`
- `ColumnDefinition(name, display_name, column_type)` — dataclass
- `ListItem(id, fields: dict[str, Any])` — dataclass
- `src/app/config.py` — `Settings`
- Tests: `pytest-asyncio` already configured with `asyncio_mode = "auto"`

---

## File Map

```
apps/backend/
├── src/app/
│   └── tools/
│       ├── __init__.py         ← empty package marker
│       └── list_tools.py       ← make_tools factory + all 6 @tool closures + _parse_number
└── tests/
    └── test_list_tools.py      ← unit tests (all mocked)
```

---

## Task 1: Git branch

- [ ] **Step 1.1: Create feature branch**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git checkout -b feature/BE-04-list-data-tools
```

Expected: `Switched to a new branch 'feature/BE-04-list-data-tools'`

---

## Task 2: Package skeleton + `_parse_number` + `get_schema` + `filter_rows` (TDD)

**Files:**
- Create: `apps/backend/src/app/tools/__init__.py`
- Create: `apps/backend/src/app/tools/list_tools.py`
- Create: `apps/backend/tests/test_list_tools.py`

- [ ] **Step 2.1: Create the package marker**

Create `apps/backend/src/app/tools/__init__.py` as an empty file.

- [ ] **Step 2.2: Write failing tests**

Create `apps/backend/tests/test_list_tools.py`:

```python
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.sharepoint import ColumnDefinition, ListItem


# --- _parse_number ---

def test_parse_number_valid_float():
    from app.tools.list_tools import _parse_number

    assert _parse_number("42.5") == 42.5


def test_parse_number_valid_int_string():
    from app.tools.list_tools import _parse_number

    assert _parse_number("10") == 10.0


def test_parse_number_invalid_returns_none():
    from app.tools.list_tools import _parse_number

    assert _parse_number("not-a-number") is None


def test_parse_number_none_returns_none():
    from app.tools.list_tools import _parse_number

    assert _parse_number(None) is None


def test_parse_number_actual_float():
    from app.tools.list_tools import _parse_number

    assert _parse_number(3.14) == 3.14


# --- get_schema tool ---

@pytest.mark.asyncio
async def test_get_schema_returns_column_names_and_types():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_schema = AsyncMock(
        return_value=[
            ColumnDefinition(name="Title", display_name="Title", column_type="text"),
            ColumnDefinition(name="Budget", display_name="Budget", column_type="number"),
        ]
    )

    tools = make_tools(mock_service)
    get_schema_tool = next(t for t in tools if t.name == "get_schema")
    result = await get_schema_tool.ainvoke({})

    assert "Title" in result
    assert "Budget" in result
    assert "text" in result
    assert "number" in result


@pytest.mark.asyncio
async def test_get_schema_empty_list():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_schema = AsyncMock(return_value=[])

    tools = make_tools(mock_service)
    get_schema_tool = next(t for t in tools if t.name == "get_schema")
    result = await get_schema_tool.ainvoke({})

    assert "No columns" in result


# --- filter_rows tool ---

@pytest.mark.asyncio
async def test_filter_rows_returns_json_fields():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Title": "Alpha", "Budget": "1000"}),
            ListItem(id="2", fields={"Title": "Beta", "Budget": "2000"}),
        ]
    )

    tools = make_tools(mock_service)
    filter_rows_tool = next(t for t in tools if t.name == "filter_rows")
    result = await filter_rows_tool.ainvoke({"odata_filter": ""})

    assert "Alpha" in result
    assert "Beta" in result


@pytest.mark.asyncio
async def test_filter_rows_passes_filter_to_service():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    get_items_mock = AsyncMock(return_value=[])
    mock_service.get_items = get_items_mock

    tools = make_tools(mock_service)
    filter_rows_tool = next(t for t in tools if t.name == "filter_rows")
    await filter_rows_tool.ainvoke({"odata_filter": "fields/Status eq 'Active'"})

    get_items_mock.assert_called_once_with(odata_filter="fields/Status eq 'Active'")


@pytest.mark.asyncio
async def test_filter_rows_empty_filter_passes_none():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    get_items_mock = AsyncMock(return_value=[])
    mock_service.get_items = get_items_mock

    tools = make_tools(mock_service)
    filter_rows_tool = next(t for t in tools if t.name == "filter_rows")
    await filter_rows_tool.ainvoke({"odata_filter": ""})

    get_items_mock.assert_called_once_with(odata_filter=None)


@pytest.mark.asyncio
async def test_filter_rows_no_results():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(return_value=[])

    tools = make_tools(mock_service)
    filter_rows_tool = next(t for t in tools if t.name == "filter_rows")
    result = await filter_rows_tool.ainvoke({"odata_filter": ""})

    assert "No rows" in result
```

- [ ] **Step 2.3: Run tests — verify they FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_list_tools.py::test_parse_number_valid_float -v
```

Expected: `ModuleNotFoundError: No module named 'app.tools'`

- [ ] **Step 2.4: Implement skeleton with `_parse_number`, `get_schema`, `filter_rows`**

Create `apps/backend/src/app/tools/list_tools.py`:

```python
from __future__ import annotations

import json
from typing import Any

from langchain.tools import tool

from app.services.sharepoint import SharePointService


def make_tools(service: SharePointService) -> list:
    """Return LangChain @tool callables wired to the given SharePointService."""

    @tool
    async def get_schema() -> str:
        """Return the column names and data types for the SharePoint list.
        Always call this first to understand the available columns before
        running any query."""
        columns = await service.get_schema()
        if not columns:
            return "No columns found in the list."
        lines = [f"- {col.name} ({col.column_type})" for col in columns]
        return "List columns:\n" + "\n".join(lines)

    @tool
    async def filter_rows(odata_filter: str = "") -> str:
        """Retrieve rows from the SharePoint list, optionally filtered by an
        OData expression (e.g. \"fields/Status eq 'Active'\").
        Leave odata_filter empty to retrieve all rows.
        Returns the row data as JSON."""
        items = await service.get_items(odata_filter=odata_filter or None)
        if not items:
            return "No rows found."
        rows = [item.fields for item in items]
        return json.dumps(rows, default=str)

    return [get_schema, filter_rows]


def _parse_number(value: Any) -> float | None:
    """Return value as float, or None if it cannot be parsed."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
```

- [ ] **Step 2.5: Run tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_list_tools.py -v
```

Expected: 12 passed.

- [ ] **Step 2.6: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/tools/ apps/backend/tests/test_list_tools.py
git commit -m "feat(backend): add list_tools skeleton with get_schema and filter_rows (BE-04)"
```

---

## Task 3: `count_rows` tool (TDD)

**Files:**
- Modify: `apps/backend/src/app/tools/list_tools.py`
- Modify: `apps/backend/tests/test_list_tools.py`

- [ ] **Step 3.1: Append failing tests**

Append to the end of `apps/backend/tests/test_list_tools.py`:

```python
# --- count_rows tool ---

@pytest.mark.asyncio
async def test_count_rows_returns_count():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Title": "A"}),
            ListItem(id="2", fields={"Title": "B"}),
            ListItem(id="3", fields={"Title": "C"}),
        ]
    )

    tools = make_tools(mock_service)
    count_rows_tool = next(t for t in tools if t.name == "count_rows")
    result = await count_rows_tool.ainvoke({"odata_filter": ""})

    assert result == "3"


@pytest.mark.asyncio
async def test_count_rows_zero():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(return_value=[])

    tools = make_tools(mock_service)
    count_rows_tool = next(t for t in tools if t.name == "count_rows")
    result = await count_rows_tool.ainvoke({"odata_filter": ""})

    assert result == "0"


@pytest.mark.asyncio
async def test_count_rows_passes_filter():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    get_items_mock = AsyncMock(return_value=[])
    mock_service.get_items = get_items_mock

    tools = make_tools(mock_service)
    count_rows_tool = next(t for t in tools if t.name == "count_rows")
    await count_rows_tool.ainvoke({"odata_filter": "fields/Status eq 'Active'"})

    get_items_mock.assert_called_once_with(odata_filter="fields/Status eq 'Active'")
```

- [ ] **Step 3.2: Run — verify FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_list_tools.py::test_count_rows_returns_count -v
```

Expected: FAIL — `StopIteration` (no tool named `count_rows` yet).

- [ ] **Step 3.3: Add `count_rows` to `list_tools.py`**

Inside `make_tools`, add this function **before** `return [get_schema, filter_rows]`, and add `count_rows` to the return list:

```python
    @tool
    async def count_rows(odata_filter: str = "") -> str:
        """Count the number of rows in the SharePoint list matching an
        optional filter (OData expression, e.g. \"fields/Status eq 'Active'\").
        Leave odata_filter empty to count all rows.
        Returns the count as a plain number."""
        items = await service.get_items(odata_filter=odata_filter or None)
        return str(len(items))
```

Update the return statement:
```python
    return [get_schema, filter_rows, count_rows]
```

- [ ] **Step 3.4: Run all tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_list_tools.py -v
```

Expected: 15 passed.

- [ ] **Step 3.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/tools/list_tools.py apps/backend/tests/test_list_tools.py
git commit -m "feat(backend): add count_rows tool (BE-04)"
```

---

## Task 4: `sum_column` and `average_column` tools (TDD)

**Files:**
- Modify: `apps/backend/src/app/tools/list_tools.py`
- Modify: `apps/backend/tests/test_list_tools.py`

- [ ] **Step 4.1: Append failing tests**

Append to the end of `apps/backend/tests/test_list_tools.py`:

```python
# --- sum_column tool ---

@pytest.mark.asyncio
async def test_sum_column_sums_numeric_values():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Budget": "1000"}),
            ListItem(id="2", fields={"Budget": "2500"}),
            ListItem(id="3", fields={"Budget": "500"}),
        ]
    )

    tools = make_tools(mock_service)
    sum_tool = next(t for t in tools if t.name == "sum_column")
    result = await sum_tool.ainvoke({"column_name": "Budget", "odata_filter": ""})

    assert result == "4000.0"


@pytest.mark.asyncio
async def test_sum_column_skips_unparseable_rows():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Budget": "1000"}),
            ListItem(id="2", fields={"Budget": "N/A"}),   # unparseable — skipped
            ListItem(id="3", fields={"Budget": None}),     # None — skipped
        ]
    )

    tools = make_tools(mock_service)
    sum_tool = next(t for t in tools if t.name == "sum_column")
    result = await sum_tool.ainvoke({"column_name": "Budget", "odata_filter": ""})

    assert result == "1000.0"


@pytest.mark.asyncio
async def test_sum_column_no_parseable_values():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Budget": "N/A"}),
        ]
    )

    tools = make_tools(mock_service)
    sum_tool = next(t for t in tools if t.name == "sum_column")
    result = await sum_tool.ainvoke({"column_name": "Budget", "odata_filter": ""})

    assert "No parseable" in result


# --- average_column tool ---

@pytest.mark.asyncio
async def test_average_column_returns_average():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Score": "10"}),
            ListItem(id="2", fields={"Score": "20"}),
            ListItem(id="3", fields={"Score": "30"}),
        ]
    )

    tools = make_tools(mock_service)
    avg_tool = next(t for t in tools if t.name == "average_column")
    result = await avg_tool.ainvoke({"column_name": "Score", "odata_filter": ""})

    assert result == "20.0"


@pytest.mark.asyncio
async def test_average_column_skips_unparseable_rows():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Score": "10"}),
            ListItem(id="2", fields={"Score": "bad"}),   # skipped
            ListItem(id="3", fields={"Score": "30"}),
        ]
    )

    tools = make_tools(mock_service)
    avg_tool = next(t for t in tools if t.name == "average_column")
    result = await avg_tool.ainvoke({"column_name": "Score", "odata_filter": ""})

    assert result == "20.0"


@pytest.mark.asyncio
async def test_average_column_no_parseable_values():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Score": "N/A"}),
        ]
    )

    tools = make_tools(mock_service)
    avg_tool = next(t for t in tools if t.name == "average_column")
    result = await avg_tool.ainvoke({"column_name": "Score", "odata_filter": ""})

    assert "No parseable" in result
```

- [ ] **Step 4.2: Run — verify FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_list_tools.py::test_sum_column_sums_numeric_values -v
```

Expected: FAIL — `StopIteration` (no tool named `sum_column` yet).

- [ ] **Step 4.3: Add `sum_column` and `average_column` to `list_tools.py`**

Inside `make_tools`, add these two functions before the `return` statement:

```python
    @tool
    async def sum_column(column_name: str, odata_filter: str = "") -> str:
        """Sum the values of a numeric column in the SharePoint list.
        column_name: exact column name as returned by get_schema.
        odata_filter: optional OData filter expression.
        Rows whose value cannot be parsed as a number are silently skipped.
        Returns the total as a number."""
        items = await service.get_items(odata_filter=odata_filter or None)
        total = 0.0
        parsed_count = 0
        for item in items:
            val = _parse_number(item.fields.get(column_name))
            if val is not None:
                total += val
                parsed_count += 1
        if parsed_count == 0:
            return f"No parseable numeric values found in column '{column_name}'."
        return str(total)

    @tool
    async def average_column(column_name: str, odata_filter: str = "") -> str:
        """Calculate the average of a numeric column in the SharePoint list.
        column_name: exact column name as returned by get_schema.
        odata_filter: optional OData filter expression.
        Rows whose value cannot be parsed as a number are silently skipped.
        Returns the average as a number."""
        items = await service.get_items(odata_filter=odata_filter or None)
        total = 0.0
        parsed_count = 0
        for item in items:
            val = _parse_number(item.fields.get(column_name))
            if val is not None:
                total += val
                parsed_count += 1
        if parsed_count == 0:
            return f"No parseable numeric values found in column '{column_name}'."
        return str(total / parsed_count)
```

Update the return statement:
```python
    return [get_schema, filter_rows, count_rows, sum_column, average_column]
```

- [ ] **Step 4.4: Run all tests — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_list_tools.py -v
```

Expected: 21 passed.

- [ ] **Step 4.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/tools/list_tools.py apps/backend/tests/test_list_tools.py
git commit -m "feat(backend): add sum_column and average_column tools (BE-04)"
```

---

## Task 5: `group_and_aggregate` tool (TDD)

**Files:**
- Modify: `apps/backend/src/app/tools/list_tools.py`
- Modify: `apps/backend/tests/test_list_tools.py`

- [ ] **Step 5.1: Append failing tests**

Append to the end of `apps/backend/tests/test_list_tools.py`:

```python
# --- group_and_aggregate tool ---

@pytest.mark.asyncio
async def test_group_and_aggregate_count():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Status": "Active", "Budget": "1000"}),
            ListItem(id="2", fields={"Status": "Active", "Budget": "2000"}),
            ListItem(id="3", fields={"Status": "Closed", "Budget": "500"}),
        ]
    )

    tools = make_tools(mock_service)
    group_tool = next(t for t in tools if t.name == "group_and_aggregate")
    result = await group_tool.ainvoke({
        "group_by_column": "Status",
        "aggregate_column": "Budget",
        "aggregate_func": "count",
        "odata_filter": "",
    })

    assert "Active: 2" in result
    assert "Closed: 1" in result


@pytest.mark.asyncio
async def test_group_and_aggregate_sum():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Dept": "Finance", "Budget": "1000"}),
            ListItem(id="2", fields={"Dept": "Finance", "Budget": "2000"}),
            ListItem(id="3", fields={"Dept": "IT", "Budget": "500"}),
        ]
    )

    tools = make_tools(mock_service)
    group_tool = next(t for t in tools if t.name == "group_and_aggregate")
    result = await group_tool.ainvoke({
        "group_by_column": "Dept",
        "aggregate_column": "Budget",
        "aggregate_func": "sum",
        "odata_filter": "",
    })

    assert "Finance: 3000.0" in result
    assert "IT: 500.0" in result


@pytest.mark.asyncio
async def test_group_and_aggregate_average():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Dept": "Finance", "Score": "80"}),
            ListItem(id="2", fields={"Dept": "Finance", "Score": "100"}),
            ListItem(id="3", fields={"Dept": "IT", "Score": "90"}),
        ]
    )

    tools = make_tools(mock_service)
    group_tool = next(t for t in tools if t.name == "group_and_aggregate")
    result = await group_tool.ainvoke({
        "group_by_column": "Dept",
        "aggregate_column": "Score",
        "aggregate_func": "average",
        "odata_filter": "",
    })

    assert "Finance: 90.0" in result
    assert "IT: 90.0" in result


@pytest.mark.asyncio
async def test_group_and_aggregate_skips_unparseable_in_sum():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(
        return_value=[
            ListItem(id="1", fields={"Dept": "Finance", "Budget": "1000"}),
            ListItem(id="2", fields={"Dept": "Finance", "Budget": "N/A"}),  # skipped
        ]
    )

    tools = make_tools(mock_service)
    group_tool = next(t for t in tools if t.name == "group_and_aggregate")
    result = await group_tool.ainvoke({
        "group_by_column": "Dept",
        "aggregate_column": "Budget",
        "aggregate_func": "sum",
        "odata_filter": "",
    })

    assert "Finance: 1000.0" in result


@pytest.mark.asyncio
async def test_group_and_aggregate_invalid_func():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(return_value=[])

    tools = make_tools(mock_service)
    group_tool = next(t for t in tools if t.name == "group_and_aggregate")
    result = await group_tool.ainvoke({
        "group_by_column": "Dept",
        "aggregate_column": "Budget",
        "aggregate_func": "median",
        "odata_filter": "",
    })

    assert "Invalid" in result


@pytest.mark.asyncio
async def test_group_and_aggregate_empty_list():
    from app.tools.list_tools import make_tools

    mock_service = MagicMock()
    mock_service.get_items = AsyncMock(return_value=[])

    tools = make_tools(mock_service)
    group_tool = next(t for t in tools if t.name == "group_and_aggregate")
    result = await group_tool.ainvoke({
        "group_by_column": "Dept",
        "aggregate_column": "Budget",
        "aggregate_func": "count",
        "odata_filter": "",
    })

    assert "No rows" in result
```

- [ ] **Step 5.2: Run — verify FAIL**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest tests/test_list_tools.py::test_group_and_aggregate_count -v
```

Expected: FAIL — `StopIteration` (no tool named `group_and_aggregate` yet).

- [ ] **Step 5.3: Add `group_and_aggregate` to `list_tools.py`**

Inside `make_tools`, add this function before the `return` statement:

```python
    @tool
    async def group_and_aggregate(
        group_by_column: str,
        aggregate_column: str,
        aggregate_func: str,
        odata_filter: str = "",
    ) -> str:
        """Group rows by one column and aggregate another column.
        group_by_column: column to group by (exact name from get_schema).
        aggregate_column: column to aggregate (exact name from get_schema).
        aggregate_func: one of 'count', 'sum', or 'average'.
          - count: count all rows in each group (aggregate_column is not used).
          - sum: sum numeric values in aggregate_column per group.
          - average: average numeric values in aggregate_column per group.
        odata_filter: optional OData filter applied before grouping.
        Rows whose aggregate_column value cannot be parsed as a number are
        skipped (for sum and average only).
        Returns one line per group: 'group_value: result'."""
        if aggregate_func not in ("count", "sum", "average"):
            return (
                f"Invalid aggregate_func '{aggregate_func}'. "
                "Must be 'count', 'sum', or 'average'."
            )
        items = await service.get_items(odata_filter=odata_filter or None)
        if not items:
            return "No rows found."

        groups: dict[str, list[Any]] = {}
        for item in items:
            group_val = str(item.fields.get(group_by_column, "(blank)"))
            if group_val not in groups:
                groups[group_val] = []
            groups[group_val].append(item.fields.get(aggregate_column))

        lines = []
        for group_val, vals in sorted(groups.items()):
            if aggregate_func == "count":
                agg_result = str(len(vals))
            elif aggregate_func == "sum":
                nums = [_parse_number(v) for v in vals]
                nums = [n for n in nums if n is not None]
                agg_result = str(sum(nums)) if nums else "0 (no parseable values)"
            else:  # average
                nums = [_parse_number(v) for v in vals]
                nums = [n for n in nums if n is not None]
                agg_result = (
                    str(sum(nums) / len(nums)) if nums else "0 (no parseable values)"
                )
            lines.append(f"{group_val}: {agg_result}")
        return "\n".join(lines)
```

You also need to add `Any` to the imports at the top of `list_tools.py` — it is already imported via `from typing import Any`.

Update the return statement:
```python
    return [
        get_schema,
        filter_rows,
        count_rows,
        sum_column,
        average_column,
        group_and_aggregate,
    ]
```

- [ ] **Step 5.4: Run full test suite — verify all pass**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

Expected: all tests pass (previous 54 + new list_tools tests).

- [ ] **Step 5.5: Commit**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/app/tools/list_tools.py apps/backend/tests/test_list_tools.py
git commit -m "feat(backend): add group_and_aggregate tool (BE-04)"
```

---

## Task 6: Ruff lint + push

- [ ] **Step 6.1: Run ruff**

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

- [ ] **Step 6.2: Commit fixes if any**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git add apps/backend/src/ apps/backend/tests/
git diff --staged --quiet || git commit -m "style(backend): ruff formatting (BE-04)"
```

- [ ] **Step 6.3: Final test run**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp/apps/backend
uv run pytest -v
```

All tests must pass.

- [ ] **Step 6.4: Push**

```bash
cd /Users/fiqriismail/Projects/Arctellis/group-one-rtp
git push -u origin feature/BE-04-list-data-tools
```

---

## Self-Review

**Spec coverage:**

| Acceptance criterion | Task |
|---|---|
| `get_schema` — column names/types (FR-14) | Task 2 |
| `filter_rows` — retrieve filtered rows (FR-8) | Task 2 |
| `count_rows` — count by condition (FR-8) | Task 3 |
| `sum_column` — sum a numeric column (FR-8) | Task 4 |
| `average_column` — average a numeric column (FR-8) | Task 4 |
| `group_and_aggregate` — group-by + aggregate (FR-8) | Task 5 |
| All numeric computation in Python, not LLM (FR-9, NFR-5) | Tasks 3–5: all sums/averages/counts are Python |
| Loosely-typed values parsed defensively; skip non-parseable (§8) | Tasks 4–5: `_parse_number` returns None → row skipped |
| Tool names/descriptions/schemas clear and unambiguous (§6.3, NFR-6) | All tasks: docstrings designed to guide the model |
| Tools never invent column names or values (NFR-6) | All tasks: tools only return data from the service |

**Placeholder scan:** None found — all steps have complete code.

**Type consistency:**
- `make_tools(service: SharePointService) -> list` — consistent across all tasks.
- `_parse_number(value: Any) -> float | None` — consistent across Tasks 2, 4, 5.
- Tool names: `get_schema`, `filter_rows`, `count_rows`, `sum_column`, `average_column`, `group_and_aggregate` — consistent across implementation and tests (`t.name == "..."` lookups).
- `ListItem(id=..., fields={...})` and `ColumnDefinition(name=..., display_name=..., column_type=...)` — imported from `app.services.sharepoint` in tests, consistent with service layer.
