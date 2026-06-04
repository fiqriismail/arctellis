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
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"

    # SharePoint / Microsoft Graph
    sharepoint_site_url: str = ""
    sharepoint_list_id: str = ""

    # Cache and retrieval
    cache_ttl_seconds: int = 60
    list_row_threshold: int = 1000


@lru_cache
def get_settings() -> Settings:
    return Settings()
