"""Typed environment settings. Secrets and machine-specific paths stay out of code/config."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Portable runtime settings for local and Kaggle execution."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    llm_api_key: str = Field(default="", validation_alias="LLM_API_KEY")
    wandb_api_key: str = Field(default="", validation_alias="WANDB_API_KEY")

    input_root: Path = Field(default=Path("data"), validation_alias="DOC_AGENT_INPUT_ROOT")
    data_dir: Path = Field(default=Path("data/raw"), validation_alias="DOC_AGENT_DATA_DIR")
    artifact_dir: Path = Field(default=Path("artifacts"), validation_alias="DOC_AGENT_ARTIFACT_DIR")
    run_mode: Literal["small", "full"] = Field(
        default="small", validation_alias="DOC_AGENT_RUN_MODE"
    )
    small_max_pages: int = Field(default=20, ge=1, validation_alias="DOC_AGENT_SMALL_MAX_PAGES")

    @property
    def page_limit(self) -> int | None:
        """Maximum pages per document in small mode; no limit in full mode."""

        return self.small_max_pages if self.run_mode == "small" else None

    def ensure_writable_dirs(self) -> None:
        """Create only writable/generated-data directories, never the input root."""

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
