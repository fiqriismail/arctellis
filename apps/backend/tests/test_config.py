import os

import pytest
from pydantic import ValidationError

# Helpers to isolate tests from env vars and .env files
_REQUIRED = {
    "azure_tenant_id": "t",
    "azure_client_id": "c",
    "azure_client_secret": "s",
}


def _clean_settings(**overrides):
    """Return a Settings instance with no env-file interference."""
    from app.config import Settings

    return Settings(_env_file=None, **{**_REQUIRED, **overrides})


def test_settings_loads_required_fields():
    s = _clean_settings(
        azure_tenant_id="tenant-123",
        azure_client_id="client-456",
        azure_client_secret="secret-789",
    )
    assert s.azure_tenant_id == "tenant-123"
    assert s.azure_client_id == "client-456"
    assert s.azure_client_secret == "secret-789"


def test_settings_defaults():
    s = _clean_settings()
    assert s.cache_ttl_seconds == 60
    assert s.list_row_threshold == 1000
    assert s.openai_model == "gpt-4o"
    assert s.openai_api_key == ""
    assert s.sharepoint_site_url == ""
    assert s.sharepoint_list_id == ""


def test_settings_missing_tenant_id_raises():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            azure_client_id="c",
            azure_client_secret="s",
        )


def test_settings_missing_client_id_raises():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            azure_tenant_id="t",
            azure_client_secret="s",
        )


def test_settings_missing_client_secret_raises():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            azure_tenant_id="t",
            azure_client_id="c",
        )


def test_get_settings_returns_settings_instance():
    from app.config import Settings, get_settings

    get_settings.cache_clear()
    os.environ.setdefault("AZURE_TENANT_ID", "t")
    os.environ.setdefault("AZURE_CLIENT_ID", "c")
    os.environ.setdefault("AZURE_CLIENT_SECRET", "s")
    result = get_settings()
    assert isinstance(result, Settings)
    get_settings.cache_clear()
