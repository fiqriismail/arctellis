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
