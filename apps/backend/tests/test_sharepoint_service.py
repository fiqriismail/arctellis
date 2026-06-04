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
