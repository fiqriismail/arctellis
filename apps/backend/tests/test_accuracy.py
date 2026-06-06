"""
BE-11 Accuracy Test Suite

Representative questions with manually-verified expected answers. Every
assertion compares the tool-computed result against a direct calculation on the
same fixture dataset so that numeric accuracy is provable, not assumed.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.sharepoint import ListItem

# ---------------------------------------------------------------------------
# Fixture dataset — representative procurement request list (8 rows)
# ---------------------------------------------------------------------------

_FIXTURE = [
    {"Title": "Laptop - Dev Team",  "Status": "Active", "Budget": 1200.0, "Department": "IT",      "Priority": "High"},
    {"Title": "Monitor Stand",       "Status": "Active", "Budget":   85.0, "Department": "IT",      "Priority": "Low"},
    {"Title": "Software License",    "Status": "Closed", "Budget": 3500.0, "Department": "Finance", "Priority": "High"},
    {"Title": "Office Chair",        "Status": "Active", "Budget":  450.0, "Department": "HR",      "Priority": "Medium"},
    {"Title": "Server Upgrade",      "Status": "Active", "Budget": 8000.0, "Department": "IT",      "Priority": "High"},
    {"Title": "Training Course",     "Status": "Closed", "Budget":  600.0, "Department": "HR",      "Priority": "Medium"},
    {"Title": "Printer",             "Status": "Active", "Budget":  320.0, "Department": "Finance", "Priority": "Low"},
    {"Title": "Keyboard",            "Status": "Closed", "Budget":   75.0, "Department": "IT",      "Priority": "Low"},
]

# Direct calculations — manually verified against the fixture above.
_TOTAL_ROWS     = 8
_ACTIVE_ROWS    = 5    # Laptop, Monitor, Chair, Server, Printer
_CLOSED_ROWS    = 3    # Software License, Training Course, Keyboard
_IT_ROWS        = 4    # Laptop, Monitor, Server, Keyboard
_FINANCE_ROWS   = 2    # Software License, Printer
_HR_ROWS        = 2    # Chair, Training Course
_HIGH_PRI_ROWS  = 3    # Laptop, Software License, Server Upgrade

_TOTAL_BUDGET   = 14230.0   # sum of all 8
_ACTIVE_BUDGET  = 10055.0   # 1200+85+450+8000+320
_CLOSED_BUDGET  =  4175.0   # 3500+600+75
_IT_BUDGET      =  9360.0   # 1200+85+8000+75
_FINANCE_BUDGET =  3820.0   # 3500+320
_HR_BUDGET      =  1050.0   # 450+600
_HIGH_BUDGET    = 12700.0   # 1200+3500+8000

_AVG_ALL_BUDGET    = 1778.75  # 14230/8
_AVG_ACTIVE_BUDGET = 2011.0   # 10055/5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _items(rows: list[dict]) -> list[ListItem]:
    return [ListItem(id=str(i), fields=dict(f)) for i, f in enumerate(rows)]


def _mock_service(rows: list[dict]) -> MagicMock:
    svc = MagicMock()
    svc.get_items = AsyncMock(return_value=_items(rows))
    return svc


def _all_items()        -> list[dict]: return list(_FIXTURE)
def _active()           -> list[dict]: return [f for f in _FIXTURE if f["Status"] == "Active"]
def _closed()           -> list[dict]: return [f for f in _FIXTURE if f["Status"] == "Closed"]
def _by_dept(d: str)    -> list[dict]: return [f for f in _FIXTURE if f["Department"] == d]
def _high_priority()    -> list[dict]: return [f for f in _FIXTURE if f["Priority"] == "High"]


# ---------------------------------------------------------------------------
# count_rows accuracy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_all_rows_equals_dataset_size():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_all_items()))
    tool = next(t for t in tools if t.name == "count_rows")
    result = await tool.ainvoke({"odata_filter": ""})

    assert result == str(_TOTAL_ROWS)


@pytest.mark.asyncio
async def test_count_active_rows_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_active()))
    tool = next(t for t in tools if t.name == "count_rows")
    result = await tool.ainvoke({"odata_filter": "fields/Status eq 'Active'"})

    assert result == str(_ACTIVE_ROWS)


@pytest.mark.asyncio
async def test_count_closed_rows_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_closed()))
    tool = next(t for t in tools if t.name == "count_rows")
    result = await tool.ainvoke({"odata_filter": "fields/Status eq 'Closed'"})

    assert result == str(_CLOSED_ROWS)


@pytest.mark.asyncio
async def test_count_it_department_rows_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_by_dept("IT")))
    tool = next(t for t in tools if t.name == "count_rows")
    result = await tool.ainvoke({"odata_filter": "fields/Department eq 'IT'"})

    assert result == str(_IT_ROWS)


# ---------------------------------------------------------------------------
# sum_column accuracy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sum_budget_all_rows_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_all_items()))
    tool = next(t for t in tools if t.name == "sum_column")
    result = await tool.ainvoke({"column_name": "Budget", "odata_filter": ""})

    assert float(result) == _TOTAL_BUDGET


@pytest.mark.asyncio
async def test_sum_budget_active_rows_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_active()))
    tool = next(t for t in tools if t.name == "sum_column")
    result = await tool.ainvoke({"column_name": "Budget", "odata_filter": "fields/Status eq 'Active'"})

    assert float(result) == _ACTIVE_BUDGET


@pytest.mark.asyncio
async def test_sum_budget_it_department_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_by_dept("IT")))
    tool = next(t for t in tools if t.name == "sum_column")
    result = await tool.ainvoke({"column_name": "Budget", "odata_filter": "fields/Department eq 'IT'"})

    assert float(result) == _IT_BUDGET


@pytest.mark.asyncio
async def test_sum_budget_high_priority_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_high_priority()))
    tool = next(t for t in tools if t.name == "sum_column")
    result = await tool.ainvoke({"column_name": "Budget", "odata_filter": "fields/Priority eq 'High'"})

    assert float(result) == _HIGH_BUDGET


# ---------------------------------------------------------------------------
# average_column accuracy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_average_budget_all_rows_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_all_items()))
    tool = next(t for t in tools if t.name == "average_column")
    result = await tool.ainvoke({"column_name": "Budget", "odata_filter": ""})

    assert float(result) == _AVG_ALL_BUDGET


@pytest.mark.asyncio
async def test_average_budget_active_rows_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_active()))
    tool = next(t for t in tools if t.name == "average_column")
    result = await tool.ainvoke({"column_name": "Budget", "odata_filter": "fields/Status eq 'Active'"})

    assert float(result) == _AVG_ACTIVE_BUDGET


# ---------------------------------------------------------------------------
# group_and_aggregate accuracy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_group_by_department_count_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_all_items()))
    tool = next(t for t in tools if t.name == "group_and_aggregate")
    result = await tool.ainvoke({
        "group_by_column": "Department",
        "aggregate_column": "Budget",
        "aggregate_func": "count",
        "odata_filter": "",
    })

    assert f"Finance: {_FINANCE_ROWS}" in result
    assert f"HR: {_HR_ROWS}" in result
    assert f"IT: {_IT_ROWS}" in result


@pytest.mark.asyncio
async def test_group_by_department_sum_budget_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_all_items()))
    tool = next(t for t in tools if t.name == "group_and_aggregate")
    result = await tool.ainvoke({
        "group_by_column": "Department",
        "aggregate_column": "Budget",
        "aggregate_func": "sum",
        "odata_filter": "",
    })

    assert f"Finance: {_FINANCE_BUDGET}" in result
    assert f"HR: {_HR_BUDGET}" in result
    assert f"IT: {_IT_BUDGET}" in result


@pytest.mark.asyncio
async def test_group_by_status_count_matches_direct_calculation():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_all_items()))
    tool = next(t for t in tools if t.name == "group_and_aggregate")
    result = await tool.ainvoke({
        "group_by_column": "Status",
        "aggregate_column": "Budget",
        "aggregate_func": "count",
        "odata_filter": "",
    })

    assert f"Active: {_ACTIVE_ROWS}" in result
    assert f"Closed: {_CLOSED_ROWS}" in result


# ---------------------------------------------------------------------------
# filter_rows completeness
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_filter_rows_active_returns_all_active_titles():
    from app.tools.list_tools import make_tools

    tools = make_tools(_mock_service(_active()))
    tool = next(t for t in tools if t.name == "filter_rows")
    result = await tool.ainvoke({"odata_filter": "fields/Status eq 'Active'"})

    import json
    rows = json.loads(result)
    assert len(rows) == _ACTIVE_ROWS
    titles = {r["Title"] for r in rows}
    assert "Laptop - Dev Team" in titles
    assert "Server Upgrade" in titles
    assert "Software License" not in titles  # Closed — must not appear
