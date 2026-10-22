from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AIVIKINGS_", env_file=".env", extra="ignore"
    )

    api_base_url: str = "http://127.0.0.1:8080"
    public_api_base_url: str = "https://api.aivikings.ai"
    mcp_url: str = "https://mcp.aivikings.ai/mcp"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8081
    mcp_path: str = "/mcp"
    mcp_request_timeout_seconds: float = 120.0
    oauth_scopes: str = "openid email profile domains:read domains:write domains:transfer billing:read audit:read contacts:read contacts:write offline_access"

    @field_validator("api_base_url", "public_api_base_url", "mcp_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        from urllib.parse import urlsplit

        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Expected an HTTP(S) URL without credentials, query, or fragment"
            )
        return value.rstrip("/")

    @field_validator("mcp_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if not value.startswith("/") or value == "/" or "?" in value or "#" in value:
            raise ValueError("MCP path must start with / and contain a non-empty path")
        return value.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
