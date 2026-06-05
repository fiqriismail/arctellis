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

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
