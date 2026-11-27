"""Settings loaded from environment variables and the repo-root `.env` file."""

from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]

CsvList = Annotated[list[str], NoDecode]


class ConfigError(RuntimeError):
    """Required settings are missing or invalid."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    confluence_url: str | None = None
    confluence_username: str | None = None
    confluence_api_token: SecretStr | None = None
    confluence_spaces: CsvList = Field(default_factory=list)
    confluence_labels: CsvList = Field(default_factory=list)

    google_genai_use_vertexai: bool = True
    google_cloud_project: str | None = None
    google_cloud_location: str | None = None
    gemini_pro_model: str | None = None
    gemini_flash_model: str | None = None
    gemini_embed_model: str | None = None

    github_token: SecretStr | None = None
    github_repo: str | None = None

    bigquery_project: str | None = None
    bigquery_datasets: CsvList = Field(default_factory=list)

    state_db_path: Path = REPO_ROOT / "data" / "state.db"

    @field_validator("confluence_spaces", "confluence_labels", "bigquery_datasets", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def missing(self, *fields: str) -> list[str]:
        """Env var names of the given fields that are unset or empty."""
        return [name.upper() for name in fields if getattr(self, name) in (None, "", [])]

    def require(self, *fields: str) -> None:
        if missing := self.missing(*fields):
            raise ConfigError(f"Missing settings in .env: {', '.join(missing)}")


def get_settings() -> Settings:
    return Settings()
