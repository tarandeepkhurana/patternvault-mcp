"""Application settings for PatternVault MCP."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Environment-driven server configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PATTERNVAULT_",
        extra="ignore",
    )

    server_name: str = "PatternVault MCP"
    server_version: str = "0.1.0"
    readmes_dir: Path = Field(default=PROJECT_ROOT / "patternvault-readmes")

    auth_mode: Literal["none", "static"] = "none"
    static_token: str | None = None
    required_scopes: list[str] = Field(default_factory=lambda: ["patternvault:read"])

    mcp_path: str = "/mcp"
    stateless_http: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return cached settings for the current process."""

    return Settings()
