import time
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
async def test_get_items_adds_prefer_header_when_filtering():
    from app.services.sharepoint import SharePointService

    mock_response = MagicMock()
    mock_response.value = []
    mock_response.odata_next_link = None

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get
    ) = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l")
    await service.get_items(odata_filter="fields/Status eq 'Active'")

    cfg = get_mock.call_args.kwargs["request_configuration"]
    # Non-indexed columns require this header or Graph rejects the filter.
    assert "HonorNonIndexedQueriesWarningMayFailRandomly" in (
        cfg.headers.get("Prefer") or set()
    )


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
    service = SharePointService(
        client=mock_client, site_id="s", list_id="l", cache_ttl=30
    )
    assert isinstance(service._cache, _TTLCache)
    assert service._cache._ttl == 30


def test_sharepoint_service_default_cache_ttl_is_60():
    from app.services.sharepoint import SharePointService, _TTLCache

    mock_client = MagicMock()
    service = SharePointService(client=mock_client, site_id="s", list_id="l")
    assert isinstance(service._cache, _TTLCache)
    assert service._cache._ttl == 60


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
    mock_site = mock_client.sites.by_site_id.return_value
    mock_list = mock_site.lists.by_list_id.return_value
    mock_list.columns.get = get_mock

    service = SharePointService(
        client=mock_client, site_id="s", list_id="l", cache_ttl=60
    )

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
    mock_site = mock_client.sites.by_site_id.return_value
    mock_list = mock_site.lists.by_list_id.return_value
    mock_list.columns.get = get_mock

    service = SharePointService(
        client=mock_client, site_id="s", list_id="l", cache_ttl=0
    )

    await service.get_schema()
    time.sleep(0.01)
    await service.get_schema()

    assert get_mock.call_count == 2  # Graph called again after expiry


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
    mock_site = mock_client.sites.by_site_id.return_value
    mock_list = mock_site.lists.by_list_id.return_value
    mock_list.items.get = get_mock

    service = SharePointService(
        client=mock_client, site_id="s", list_id="l", cache_ttl=60
    )

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
    mock_site = mock_client.sites.by_site_id.return_value
    mock_list = mock_site.lists.by_list_id.return_value
    mock_list.items.get = get_mock

    service = SharePointService(
        client=mock_client, site_id="s", list_id="l", cache_ttl=60
    )

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
    mock_site = mock_client.sites.by_site_id.return_value
    mock_list = mock_site.lists.by_list_id.return_value
    mock_list.items.get = get_mock

    service = SharePointService(
        client=mock_client, site_id="s", list_id="l", cache_ttl=0
    )

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
    mock_site = mock_client.sites.by_site_id.return_value
    mock_list = mock_site.lists.by_list_id.return_value
    mock_list.items.get = get_mock

    service = SharePointService(
        client=mock_client, site_id="s", list_id="l", cache_ttl=60
    )

    f = "fields/Status eq 'Active'"
    await service.get_items(odata_filter=f)
    await service.get_items(odata_filter=f)

    # Same filter → cache hit on second call
    assert get_mock.call_count == 1


def test_normalize_filter_prefixes_bare_date_column():
    from app.services.sharepoint import SharePointService

    out = SharePointService._normalize_filter("Created ge '2026-05-26T00:00:00Z'")
    assert out == "fields/Created ge '2026-05-26T00:00:00Z'"


def test_normalize_filter_preserves_quoted_datetime_range():
    from app.services.sharepoint import SharePointService

    f = (
        "fields/Created ge '2026-05-26T00:00:00Z'"
        " and fields/Created lt '2026-05-27T00:00:00Z'"
    )
    # Already prefixed and the quoted datetime literals must be left intact.
    assert SharePointService._normalize_filter(f) == f


def test_normalize_filter_rewrites_boolean_true_to_one():
    from app.services.sharepoint import SharePointService

    assert SharePointService._normalize_filter(
        "fields/InfoSecReviewRequired eq true"
    ) == "fields/InfoSecReviewRequired eq 1"


def test_normalize_filter_rewrites_boolean_false_to_zero():
    from app.services.sharepoint import SharePointService

    assert SharePointService._normalize_filter(
        "InfoSecReviewRequired eq false"
    ) == "fields/InfoSecReviewRequired eq 0"


def test_normalize_filter_rewrites_quoted_boolean_literals():
    from app.services.sharepoint import SharePointService

    assert SharePointService._normalize_filter(
        "fields/SourcingCompleted eq 'true'"
    ) == "fields/SourcingCompleted eq 1"


def test_normalize_filter_preserves_non_boolean_string_literals():
    from app.services.sharepoint import SharePointService

    assert SharePointService._normalize_filter(
        "fields/Status eq 'Active'"
    ) == "fields/Status eq 'Active'"


# --- person column resolution (LookupId -> display name + email) ---


def test_merge_person_fields_resolves_single_person():
    from app.services.sharepoint import SharePointService

    fields = {"Title": "Req", "SMEEmailLookupId": "7"}
    person_names = {"SMEEmail"}
    user_map = {"7": {"LookupValue": "Kit Wood", "Email": "kit@trustpredict.ai"}}

    out = SharePointService._merge_person_fields(fields, person_names, user_map)

    assert out["SMEEmail"] == {
        "LookupValue": "Kit Wood",
        "Email": "kit@trustpredict.ai",
    }
    assert "SMEEmailLookupId" not in out
    assert out["Title"] == "Req"


def test_merge_person_fields_resolves_multi_value():
    from app.services.sharepoint import SharePointService

    fields = {"ReviewersLookupId": ["7", "8"]}
    person_names = {"Reviewers"}
    user_map = {
        "7": {"LookupValue": "Kit Wood", "Email": "kit@trustpredict.ai"},
        "8": {"LookupValue": "Jo Bloggs", "Email": "jo@example.com"},
    }

    out = SharePointService._merge_person_fields(fields, person_names, user_map)

    assert out["Reviewers"] == [
        {"LookupValue": "Kit Wood", "Email": "kit@trustpredict.ai"},
        {"LookupValue": "Jo Bloggs", "Email": "jo@example.com"},
    ]


def test_merge_person_fields_unknown_id_yields_nulls():
    from app.services.sharepoint import SharePointService

    out = SharePointService._merge_person_fields(
        {"SMEEmailLookupId": "999"}, {"SMEEmail"}, {}
    )
    assert out["SMEEmail"] == {"LookupValue": None, "Email": None}


def test_merge_person_fields_ignores_non_person_lookups():
    from app.services.sharepoint import SharePointService

    # Category is resolved separately by _merge_lookup_fields, not here.
    out = SharePointService._merge_person_fields(
        {"CategoryLookupId": "99"}, {"SMEEmail"}, {}
    )
    assert out["CategoryLookupId"] == "99"


def test_merge_lookup_fields_resolves_single_lookup():
    from app.services.sharepoint import SharePointService

    fields = {"Title": "Req", "CategoryLookupId": "109"}
    lookup_configs = {
        "Category": ("a451dd1a-0644-4cb2-a559-fe06394d3064", "Title"),
    }
    lookup_maps = {
        "a451dd1a-0644-4cb2-a559-fe06394d3064": {
            "109": {"LookupValue": "IT Software & Services – Engineering"},
        },
    }

    out = SharePointService._merge_lookup_fields(
        fields, lookup_configs, lookup_maps
    )

    assert out["Category"] == {"LookupValue": "IT Software & Services – Engineering"}
    assert "CategoryLookupId" not in out
    assert out["Title"] == "Req"


def test_merge_lookup_fields_unknown_id_yields_null():
    from app.services.sharepoint import SharePointService

    out = SharePointService._merge_lookup_fields(
        {"CategoryLookupId": "999"},
        {"Category": ("list-1", "Title")},
        {},
    )
    assert out["Category"] == {"LookupValue": None}


def test_merge_lookup_fields_missing_key_still_yields_null():
    """A row where the lookup was never set has no '{Name}LookupId' key at all
    (SharePoint omits unset lookups from the Graph payload entirely). The
    configured column must still surface as {"LookupValue": None} rather than
    being silently absent, so callers can tell "not populated" from "not
    fetched"."""
    from app.services.sharepoint import SharePointService

    out = SharePointService._merge_lookup_fields(
        {"Title": "Req"},
        {"Category": ("list-1", "Title")},
        {},
    )
    assert out["Category"] == {"LookupValue": None}


@pytest.mark.asyncio
async def test_resolve_lookup_ids_queries_target_list_and_caches():
    from app.services.sharepoint import SharePointService

    mock_fields = MagicMock()
    mock_fields.additional_data = {
        "Title": "Products – Third Party",
        "CategoryDisplayName": "Products – Third Party",
    }
    mock_item = MagicMock()
    mock_item.fields = mock_fields

    get_mock = AsyncMock(return_value=mock_item)
    mock_client = MagicMock()
    mock_list = mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value
    mock_list.items.by_list_item_id.return_value.get = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l")
    list_id = "a451dd1a-0644-4cb2-a559-fe06394d3064"

    first = await service._resolve_lookup_ids(list_id, {"119"})
    assert first["119"] == {"LookupValue": "Products – Third Party"}

    second = await service._resolve_lookup_ids(list_id, {"119"})
    assert second["119"] == {"LookupValue": "Products – Third Party"}
    assert get_mock.call_count == 1


@pytest.mark.asyncio
async def test_get_items_resolves_lookup_columns():
    from app.services.sharepoint import SharePointService

    category_col = MagicMock()
    category_col.name = "Category"
    category_col.display_name = "Category"
    category_col.hidden = False
    category_col.number = None
    category_col.date_time = None
    category_col.boolean = None
    category_col.choice = None
    category_col.person_or_group = None
    category_col.lookup = MagicMock()
    category_col.lookup.list_id = "a451dd1a-0644-4cb2-a559-fe06394d3064"
    category_col.lookup.column_name = "Title"

    schema_resp = MagicMock()
    schema_resp.value = [category_col]

    mf = MagicMock()
    mf.additional_data = {"Title": "Req", "CategoryLookupId": "109"}
    mi = MagicMock()
    mi.id = "1"
    mi.fields = mf
    items_resp = MagicMock()
    items_resp.value = [mi]
    items_resp.odata_next_link = None

    cat_fields = MagicMock()
    cat_fields.additional_data = {
        "Title": "IT Software & Services – Engineering",
        "CategoryDisplayName": "IT Software & Services – Engineering",
    }
    cat_item = MagicMock()
    cat_item.fields = cat_fields

    mock_client = MagicMock()
    mock_list = mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value
    mock_list.items.get = AsyncMock(return_value=items_resp)
    mock_list.columns.get = AsyncMock(return_value=schema_resp)
    mock_list.items.by_list_item_id.return_value.get = AsyncMock(return_value=cat_item)

    service = SharePointService(client=mock_client, site_id="s", list_id="l")
    items = await service.get_items()

    assert items[0].fields["Category"] == {
        "LookupValue": "IT Software & Services – Engineering",
    }
    assert "CategoryLookupId" not in items[0].fields
    assert items[0].fields["Title"] == "Req"


@pytest.mark.asyncio
async def test_resolve_user_ids_queries_user_info_list_and_caches():
    from app.services.sharepoint import SharePointService

    mock_fields = MagicMock()
    mock_fields.additional_data = {"Title": "Kit Wood", "EMail": "kit@trustpredict.ai"}
    mock_item = MagicMock()
    mock_item.fields = mock_fields

    get_mock = AsyncMock(return_value=mock_item)
    mock_client = MagicMock()
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.by_list_item_id.return_value.get
    ) = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l")

    first = await service._resolve_user_ids({"7"})
    assert first["7"] == {"LookupValue": "Kit Wood", "Email": "kit@trustpredict.ai"}

    second = await service._resolve_user_ids({"7"})
    assert second["7"] == {"LookupValue": "Kit Wood", "Email": "kit@trustpredict.ai"}
    assert get_mock.call_count == 1  # cached, no second Graph call


@pytest.mark.asyncio
async def test_resolve_user_ids_handles_resolution_failure():
    from app.services.sharepoint import SharePointService

    get_mock = AsyncMock(side_effect=Exception("404"))
    mock_client = MagicMock()
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.by_list_item_id.return_value.get
    ) = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l")
    result = await service._resolve_user_ids({"7"})
    assert result["7"] == {"LookupValue": None, "Email": None}


@pytest.mark.asyncio
async def test_get_items_resolves_person_columns():
    from app.services.sharepoint import SharePointService

    sme_col = MagicMock()
    sme_col.name = "SMEEmail"
    sme_col.display_name = "SME"
    sme_col.hidden = False
    sme_col.number = None
    sme_col.date_time = None
    sme_col.boolean = None
    sme_col.choice = None
    sme_col.lookup = None
    sme_col.person_or_group = MagicMock()
    schema_resp = MagicMock()
    schema_resp.value = [sme_col]

    mf = MagicMock()
    mf.additional_data = {"Title": "Req", "SMEEmailLookupId": "7"}
    mi = MagicMock()
    mi.id = "1"
    mi.fields = mf
    items_resp = MagicMock()
    items_resp.value = [mi]
    items_resp.odata_next_link = None

    uf = MagicMock()
    uf.additional_data = {"Title": "Kit Wood", "EMail": "kit@trustpredict.ai"}
    ui = MagicMock()
    ui.fields = uf

    mock_client = MagicMock()
    mock_list = mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value
    mock_list.items.get = AsyncMock(return_value=items_resp)
    mock_list.columns.get = AsyncMock(return_value=schema_resp)
    mock_list.items.by_list_item_id.return_value.get = AsyncMock(return_value=ui)

    service = SharePointService(client=mock_client, site_id="s", list_id="l")
    items = await service.get_items()

    assert items[0].fields["SMEEmail"] == {
        "LookupValue": "Kit Wood",
        "Email": "kit@trustpredict.ai",
    }
    assert "SMEEmailLookupId" not in items[0].fields
    assert items[0].fields["Title"] == "Req"


@pytest.mark.asyncio
async def test_create_sharepoint_service_passes_cache_ttl():
    from app.services.sharepoint import SharePointService, create_sharepoint_service

    mock_site = MagicMock()
    mock_site.id = "barringtondigital.sharepoint.com,abc,def"

    mock_client = MagicMock()
    mock_client.sites.by_site_id.return_value.get = AsyncMock(return_value=mock_site)

    mock_auth = MagicMock()
    mock_auth.get_client.return_value = mock_client

    mock_settings = MagicMock()
    mock_settings.sharepoint_site_url = (
        "https://barringtondigital.sharepoint.com/sites/Procurement"
    )
    mock_settings.sharepoint_list_id = "37b0d45b-4f69-42cf-b26f-7112033a83fb"
    mock_settings.cache_ttl_seconds = 120

    service = await create_sharepoint_service(
        auth_service=mock_auth, settings=mock_settings
    )

    assert isinstance(service, SharePointService)
    assert service._cache._ttl == 120


# --- get_item_count ---


@pytest.mark.asyncio
async def test_get_item_count_returns_count_of_value_items():
    from app.services.sharepoint import SharePointService

    mock_response = MagicMock()
    mock_response.value = [MagicMock() for _ in range(42)]

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get
    ) = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l")
    count = await service.get_item_count()

    assert count == 42


@pytest.mark.asyncio
async def test_get_item_count_cached_on_second_call():
    from app.services.sharepoint import SharePointService

    mock_response = MagicMock()
    mock_response.value = [MagicMock() for _ in range(10)]

    get_mock = AsyncMock(return_value=mock_response)
    mock_client = MagicMock()
    (
        mock_client.sites.by_site_id.return_value.lists.by_list_id.return_value.items.get
    ) = get_mock

    service = SharePointService(client=mock_client, site_id="s", list_id="l", cache_ttl=60)
    await service.get_item_count()
    await service.get_item_count()

    assert get_mock.call_count == 1  # second call served from cache
