from unittest.mock import AsyncMock, MagicMock

import pytest


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


def test_infer_column_type_choice():
    from app.services.sharepoint import SharePointService

    mock_col = MagicMock()
    mock_col.number = None
    mock_col.date_time = None
    mock_col.boolean = None
    mock_col.choice = MagicMock()
    mock_col.lookup = None
    mock_col.person_or_group = None
    assert SharePointService._infer_column_type(mock_col) == "choice"


def test_infer_column_type_lookup():
    from app.services.sharepoint import SharePointService

    mock_col = MagicMock()
    mock_col.number = None
    mock_col.date_time = None
    mock_col.boolean = None
    mock_col.choice = None
    mock_col.lookup = MagicMock()
    mock_col.person_or_group = None
    assert SharePointService._infer_column_type(mock_col) == "lookup"


def test_infer_column_type_person():
    from app.services.sharepoint import SharePointService

    mock_col = MagicMock()
    mock_col.number = None
    mock_col.date_time = None
    mock_col.boolean = None
    mock_col.choice = None
    mock_col.lookup = None
    mock_col.person_or_group = MagicMock()
    assert SharePointService._infer_column_type(mock_col) == "person"


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
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.columns.get
    ) = AsyncMock(return_value=mock_response)

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
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.columns.get
    ) = AsyncMock(return_value=mock_response)

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
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.columns.get
    ) = AsyncMock(return_value=mock_response)

    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    columns = await service.get_schema()
    assert columns == []


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
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get
    ) = AsyncMock(return_value=mock_response)

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
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get
    ) = AsyncMock(return_value=mock_response)

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
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get
    ) = AsyncMock(return_value=mock_response)

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
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get
    ) = get_mock

    service = SharePointService(client=mock_client, site_id="site-1", list_id="list-1")
    await service.get_items(odata_filter="fields/Status eq 'Active'")

    get_mock.assert_called_once()
    call_kwargs = get_mock.call_args
    request_config = call_kwargs[1].get("request_configuration") or call_kwargs[0][0]
    assert request_config is not None


@pytest.mark.asyncio
async def test_create_sharepoint_service_resolves_site_id():
    from app.services.sharepoint import SharePointService, create_sharepoint_service

    mock_site = MagicMock()
    mock_site.id = "barringtondigital.sharepoint.com,abc-123,def-456"

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.get = AsyncMock(return_value=mock_site)

    mock_auth = MagicMock()
    mock_auth.get_client.return_value = mock_client

    mock_settings = MagicMock()
    mock_settings.sharepoint_site_url = (
        "https://barringtondigital.sharepoint.com/sites/Procurement"
    )
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
