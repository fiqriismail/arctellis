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
    assert s.sharepoint_site_url == ""
    assert s.sharepoint_list_id == ""


def test_azure_openai_defaults():
    s = _clean_settings()
    assert s.azure_openai_endpoint == ""
    assert s.azure_openai_deployment == ""
    # API version is pinned to a known-good GA version, not "latest".
    assert s.azure_openai_api_version == "2024-10-21"
    # API key is a local-dev fallback only; empty by default (managed identity).
    assert s.azure_openai_api_key == ""


def test_azure_openai_settings_loaded_from_overrides():
    s = _clean_settings(
        azure_openai_endpoint="https://my-aoai.openai.azure.com",
        azure_openai_deployment="gpt-4o-prod",
        azure_openai_api_version="2025-01-01-preview",
        azure_openai_api_key="local-key",
    )
    assert s.azure_openai_endpoint == "https://my-aoai.openai.azure.com"
    assert s.azure_openai_deployment == "gpt-4o-prod"
    assert s.azure_openai_api_version == "2025-01-01-preview"
    assert s.azure_openai_api_key == "local-key"


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
    os.environ["AZURE_TENANT_ID"] = "t"
    os.environ["AZURE_CLIENT_ID"] = "c"
    os.environ["AZURE_CLIENT_SECRET"] = "s"
    try:
        result = get_settings()
        assert isinstance(result, Settings)
    finally:
        get_settings.cache_clear()
        os.environ.pop("AZURE_TENANT_ID", None)
        os.environ.pop("AZURE_CLIENT_ID", None)
        os.environ.pop("AZURE_CLIENT_SECRET", None)


def test_allowed_role_defaults_to_app_access():
    s = _clean_settings()
    assert s.allowed_role == "App.Access"


def test_allowed_role_can_be_overridden():
    s = _clean_settings(allowed_role="Custom.Role")
    assert s.allowed_role == "Custom.Role"
