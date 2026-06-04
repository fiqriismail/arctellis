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
