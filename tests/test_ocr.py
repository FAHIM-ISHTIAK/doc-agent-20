"""Tests for layout detection and Bangla OCR orchestration."""

from __future__ import annotations

import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw

from doc_agent.contracts import Page, Region
from doc_agent.vision import layout, ocr


def _layout_cfg() -> dict:
    return {
        "layout": {
            "foreground_threshold": 200,
            "table_horizontal_fraction": 0.45,
            "table_vertical_fraction": 0.20,
        }
    }


def _write_layout_page(path: Path) -> None:
    image = Image.new("L", (600, 800), 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((210, 35, 390, 55), fill=0)
    for y in (120, 150, 180):
        draw.rectangle((40, y, 245, y + 12), fill=0)
        draw.rectangle((355, y, 560, y + 12), fill=0)
    for y in (300, 360, 420, 480):
        draw.line((60, y, 540, y), fill=0, width=3)
    for x in (60, 300, 540):
        draw.line((x, 300, x, 480), fill=0, width=3)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def test_layout_is_deterministic_bounded_and_page_linked(tmp_path: Path) -> None:
    path = tmp_path / "page.png"
    _write_layout_page(path)
    page = Page(id="grammar_p0001", doc_id="grammar", image_path=str(path))

    first = layout.detect([page], _layout_cfg())
    second = layout.detect([page], _layout_cfg())

    assert first == second
    assert first
    assert all(region.page_id == page.id for region in first)
    assert all(region.kind in {"text", "table", "figure", "heading"} for region in first)
    assert all(
        0 <= x0 < x1 <= 600 and 0 <= y0 < y1 <= 800 for x0, y0, x1, y1 in (r.bbox for r in first)
    )


def test_layout_keeps_table_atomic_and_orders_columns(tmp_path: Path) -> None:
    path = tmp_path / "page.png"
    _write_layout_page(path)
    page = Page(id="grammar_p0001", doc_id="grammar", image_path=str(path))

    regions = layout.detect([page], _layout_cfg())

    tables = [region for region in regions if region.kind == "table"]
    assert len(tables) == 1
    text = [region for region in regions if region.kind in {"text", "heading"}]
    left_positions = [index for index, region in enumerate(text) if region.bbox[2] < 300]
    right_positions = [index for index, region in enumerate(text) if region.bbox[0] > 300]
    assert left_positions and right_positions
    assert max(left_positions) < min(right_positions)


def test_transcribe_normalizes_nfc_and_preserves_order(monkeypatch) -> None:
    outputs = iter(["কো ন নিয়ম  ", " যেমন: ক্ + অ = ক "])
    monkeypatch.setattr(ocr.Reader, "transcribe_region", lambda self, region: next(outputs))
    regions = [
        Region(page_id="grammar_p0002", bbox=(0, 0, 10, 10), kind="heading"),
        Region(page_id="grammar_p0002", bbox=(0, 10, 10, 20), kind="text"),
    ]

    chunks = ocr.transcribe(regions, {"ocr": {"unicode_normalization": "NFC"}})

    assert [chunk.id for chunk in chunks] == [
        "grammar_p0002_r0001_heading",
        "grammar_p0002_r0002_text",
    ]
    assert all(chunk.doc_id == "grammar" for chunk in chunks)
    assert all(chunk.page_ids == ["grammar_p0002"] for chunk in chunks)
    assert chunks[0].text == unicodedata.normalize("NFC", "কো ন নিয়ম")


def test_transcribe_skips_empty_regions(monkeypatch) -> None:
    outputs = iter(["  ", "বাংলা ব্যাকরণ"])
    monkeypatch.setattr(ocr.Reader, "transcribe_region", lambda self, region: next(outputs))
    regions = [
        Region(page_id="book_p0001", bbox=(0, 0, 10, 10), kind="text"),
        Region(page_id="book_p0001", bbox=(0, 10, 10, 20), kind="text"),
    ]

    chunks = ocr.transcribe(regions, {"ocr": {"unicode_normalization": "NFC"}})

    assert len(chunks) == 1
    assert chunks[0].id == "book_p0001_r0002_text"
