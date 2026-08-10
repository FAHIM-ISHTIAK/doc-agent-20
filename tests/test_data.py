"""Runtime/data configuration tests used by the Kaggle reproducibility gate."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from doc_agent.settings import Settings


def test_small_mode_paths_and_limit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data_dir = tmp_path / "raw"
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setenv("DOC_AGENT_INPUT_ROOT", str(tmp_path / "input"))
    monkeypatch.setenv("DOC_AGENT_DATA_DIR", str(data_dir))
    monkeypatch.setenv("DOC_AGENT_ARTIFACT_DIR", str(artifact_dir))
    monkeypatch.setenv("DOC_AGENT_RUN_MODE", "small")
    monkeypatch.setenv("DOC_AGENT_SMALL_MAX_PAGES", "7")

    runtime = Settings(_env_file=None)
    runtime.ensure_writable_dirs()

    assert runtime.run_mode == "small"
    assert runtime.page_limit == 7
    assert runtime.data_dir == data_dir
    assert runtime.artifact_dir == artifact_dir
    assert data_dir.is_dir()
    assert artifact_dir.is_dir()


def test_full_mode_has_no_page_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOC_AGENT_RUN_MODE", "full")
    runtime = Settings(_env_file=None)
    assert runtime.page_limit is None


def test_invalid_mode_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOC_AGENT_RUN_MODE", "partial")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
