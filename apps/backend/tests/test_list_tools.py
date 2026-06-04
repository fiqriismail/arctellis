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
