"""
Configuration settings for the Cookidoo Agent Assistant backend.

Uses pydantic-settings for environment variable management and validation.
Sensitive values should be stored in Azure Key Vault.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is two levels up from backend/config/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application settings
    app_name: str = "Cookidoo Agent Assistant"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    # API settings
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=4, alias="API_WORKERS")

    # CORS settings
    cors_origins: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"], alias="CORS_ORIGINS"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins string into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Azure Key Vault settings
    azure_key_vault_url: str = Field(default="", alias="AZURE_KEY_VAULT_URL")
    azure_tenant_id: Optional[str] = Field(default=None, alias="AZURE_TENANT_ID")
    azure_client_id: Optional[str] = Field(default=None, alias="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(
        default=None, alias="AZURE_CLIENT_SECRET"
    )

    # Databricks settings
    databricks_host: str = Field(default="", alias="DATABRICKS_HOST")
    databricks_token: Optional[str] = Field(default=None, alias="DATABRICKS_TOKEN")
    databricks_catalog: str = Field(default="cookidoo_agent", alias="DATABRICKS_CATALOG")
    databricks_schema: str = Field(default="main", alias="DATABRICKS_SCHEMA")

    # LLM Model settings
    llm_model: str = Field(default="claude-sonnet-4-5", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, alias="LLM_MAX_TOKENS")
    llm_endpoint_name: str = Field(
        default="cookidoo-agent-primary", alias="LLM_ENDPOINT_NAME"
    )

    # AgentBricks settings
    agentbricks_enabled: bool = Field(default=True, alias="AGENTBRICKS_ENABLED")
    agentbricks_max_iterations: int = Field(
        default=5, alias="AGENTBRICKS_MAX_ITERATIONS"
    )

    # MCP Server settings
    mcp_server_url: str = Field(default="http://localhost:8001", alias="MCP_SERVER_URL")
    mcp_sse_url: str = Field(
        default="http://localhost:8002",
        alias="MCP_SSE_URL",
        description="MCP protocol endpoint (SSE transport) for AI agent tool use",
    )
    mcp_timeout: int = Field(default=30, alias="MCP_TIMEOUT")

    # Cookidoo API settings (retrieved from Key Vault in production)
    cookidoo_email: Optional[str] = Field(default=None, alias="COOKIDOO_EMAIL")
    cookidoo_password: Optional[str] = Field(default=None, alias="COOKIDOO_PASSWORD")
    cookidoo_country_code: str = Field(default="us", alias="COOKIDOO_COUNTRY_CODE")
    cookidoo_language: str = Field(default="en-US", alias="COOKIDOO_LANGUAGE")

    # Logging settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")  # json or text

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, alias="RATE_LIMIT_PERIOD")  # seconds

    # Cache settings
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")  # seconds

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
