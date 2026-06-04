import os

import pytest
from pydantic import ValidationError


def test_settings_loads_required_fields():
    from app.config import Settings

    s = Settings(
        azure_tenant_id="tenant-123",
        azure_client_id="client-456",
        azure_client_secret="secret-789",
    )
    assert s.azure_tenant_id == "tenant-123"
    assert s.azure_client_id == "client-456"
    assert s.azure_client_secret == "secret-789"


def test_settings_defaults():
    from app.config import Settings

    s = Settings(
        azure_tenant_id="t",
        azure_client_id="c",
        azure_client_secret="s",
    )
    assert s.cache_ttl_seconds == 60
    assert s.list_row_threshold == 1000
    assert s.azure_openai_deployment == "gpt-4o"
    assert s.azure_openai_endpoint == ""
    assert s.azure_openai_api_key == ""
    assert s.sharepoint_site_url == ""
    assert s.sharepoint_list_id == ""


def test_settings_missing_tenant_id_raises():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(azure_client_id="c", azure_client_secret="s")


def test_settings_missing_client_id_raises():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(azure_tenant_id="t", azure_client_secret="s")


def test_settings_missing_client_secret_raises():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(azure_tenant_id="t", azure_client_id="c")


def test_get_settings_returns_settings_instance():
    from app.config import Settings, get_settings

    get_settings.cache_clear()
    os.environ.setdefault("AZURE_TENANT_ID", "t")
    os.environ.setdefault("AZURE_CLIENT_ID", "c")
    os.environ.setdefault("AZURE_CLIENT_SECRET", "s")
    result = get_settings()
    assert isinstance(result, Settings)
    get_settings.cache_clear()
