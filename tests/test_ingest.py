"""Tests for deterministic page ingest and conservative preprocessing."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw

from doc_agent.contracts import Page
from doc_agent.ingest import loader, preprocess


def _write_text_page(path: Path, *, skew: float = 0.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("L", (320, 220), 255)
    draw = ImageDraw.Draw(image)
    for y in range(35, 190, 28):
        draw.line((45, y, 275, y), fill=20, width=3)
        draw.rectangle((55, y + 5, 72, y + 13), fill=45)
    if skew:
        image = image.rotate(skew, resample=Image.Resampling.BICUBIC, fillcolor=255)
    image.save(path)


def _base_cfg(raw_dir: Path, artifact_dir: Path) -> dict:
    return {
        "runtime": {"mode": "full", "small_max_pages": 20},
        "data": {"raw_dir": str(raw_dir), "artifact_dir": str(artifact_dir)},
        "ingest": {
            "supported_extensions": [".png", ".jpg"],
            "exclude_blank": True,
            "blank_foreground_threshold": 245,
            "blank_min_foreground_fraction": 0.0005,
            "exclude_page_ids": [],
        },
        "preprocess": {
            "deskew": True,
            "denoise": True,
            "binarize": True,
            "preserve_originals": True,
            "deskew_max_angle": 3.0,
            "deskew_min_angle": 0.15,
            "deskew_coarse_step": 1.0,
            "deskew_fine_step": 0.25,
            "binarize_threshold_offset": 0,
        },
    }


def test_load_pages_is_stable_filtered_and_numerically_ordered(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    raw = tmp_path / "raw"
    artifacts = tmp_path / "artifacts"
    _write_text_page(raw / "doc_b" / "page_0010.png")
    _write_text_page(raw / "doc_a" / "page_0002.png")
    _write_text_page(raw / "doc_a" / "page_0001.png")
    Image.new("L", (320, 220), 255).save(raw / "doc_a" / "page_0003.png")
    _write_text_page(raw / "doc_a" / "thumbnail.png")
    (raw / "doc_a" / "page_0004.txt").write_text("not an image", encoding="utf-8")
    cfg = _base_cfg(raw, artifacts)
    cfg["ingest"]["exclude_page_ids"] = ["doc_a_p0002"]
    monkeypatch.delenv("DOC_AGENT_DATA_DIR", raising=False)
    monkeypatch.delenv("DOC_AGENT_RUN_MODE", raising=False)

    first = loader.load_pages(cfg)
    second = loader.load_pages(cfg)

    assert first == second
    assert [page.id for page in first] == ["doc_a_p0001", "doc_b_p0010"]
    assert [page.doc_id for page in first] == ["doc_a", "doc_b"]
    assert all(Path(page.image_path).is_absolute() for page in first)


def test_small_mode_limit_is_applied_per_document(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    raw = tmp_path / "raw"
    cfg = _base_cfg(raw, tmp_path / "artifacts")
    for doc_id in ("doc_a", "doc_b"):
        for page_number in (1, 2, 3):
            _write_text_page(raw / doc_id / f"page_{page_number:04d}.png")
    monkeypatch.setenv("DOC_AGENT_RUN_MODE", "small")
    monkeypatch.setenv("DOC_AGENT_SMALL_MAX_PAGES", "2")
    monkeypatch.delenv("DOC_AGENT_DATA_DIR", raising=False)

    pages = loader.load_pages(cfg)

    assert [page.id for page in pages] == [
        "doc_a_p0001",
        "doc_a_p0002",
        "doc_b_p0001",
        "doc_b_p0002",
    ]


def test_flat_heldout_filename_is_supported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    raw = tmp_path / "raw"
    _write_text_page(raw / "sample_book_p0042.png")
    cfg = _base_cfg(raw, tmp_path / "artifacts")
    monkeypatch.delenv("DOC_AGENT_DATA_DIR", raising=False)
    monkeypatch.delenv("DOC_AGENT_RUN_MODE", raising=False)

    pages = loader.load_pages(cfg)

    assert pages == [
        Page(
            id="sample_book_p0042",
            doc_id="sample_book",
            image_path=str((raw / "sample_book_p0042.png").resolve()),
        )
    ]


def test_preprocess_preserves_identity_originals_and_is_deterministic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    raw = tmp_path / "raw"
    source = raw / "doc_a" / "page_0001.png"
    _write_text_page(source, skew=2.0)
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    cfg = _base_cfg(raw, tmp_path / "artifacts")
    monkeypatch.delenv("DOC_AGENT_ARTIFACT_DIR", raising=False)
    page = Page(id="doc_a_p0001", doc_id="doc_a", image_path=str(source.resolve()))

    first = preprocess.run([page], cfg)
    first_bytes = Path(first[0].image_path).read_bytes()
    second = preprocess.run([page], cfg)

    assert first[0].id == page.id
    assert first[0].doc_id == page.doc_id
    assert first[0].image_path != page.image_path
    assert Path(first[0].image_path).is_relative_to((tmp_path / "artifacts").resolve())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
    assert Path(second[0].image_path).read_bytes() == first_bytes
    with Image.open(first[0].image_path) as cleaned:
        assert cleaned.mode == "1"
        assert set(np.unique(np.asarray(cleaned))).issubset({False, True})


def test_disabled_preprocessing_returns_unchanged_paths(tmp_path: Path) -> None:
    source = tmp_path / "raw" / "doc_a" / "page_0001.png"
    _write_text_page(source)
    page = Page(id="doc_a_p0001", doc_id="doc_a", image_path=str(source.resolve()))
    cfg = _base_cfg(tmp_path / "raw", tmp_path / "artifacts")
    cfg["preprocess"].update({"deskew": False, "denoise": False, "binarize": False})

    result = preprocess.run([page], cfg)

    assert result == [page]
    assert result[0] is not page
