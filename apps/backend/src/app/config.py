from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Entra ID — required, no defaults
    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str

    # Azure OpenAI
    # Resource endpoint, e.g. "https://my-resource.openai.azure.com".
    azure_openai_endpoint: str = ""
    # Deployment name configured in the Azure OpenAI resource (may differ from
    # the underlying model id, e.g. a deployment "gpt-4o-prod" serving gpt-4o).
    azure_openai_deployment: str = ""
    # Pin a known-good GA API version rather than tracking latest.
    azure_openai_api_version: str = "2024-10-21"
    # Static key for local development only. In Azure, leave empty and
    # authenticate via the container's managed identity (Entra ID).
    azure_openai_api_key: str = ""

    # SharePoint / Microsoft Graph
    sharepoint_site_url: str = ""
    sharepoint_list_id: str = ""
    # IANA timezone the SharePoint site displays dates in. Graph stores/filters
    # dates in UTC; user-typed calendar dates are interpreted in this zone.
    site_timezone: str = "Europe/London"

    # Cache and retrieval
    cache_ttl_seconds: int = 60
    list_row_threshold: int = 1000

    # CORS — comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000"

    # Access control — Entra Object ID of the M365 group allowed to use the app
    allowed_group_id: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
