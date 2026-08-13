"""Stage 3: EasyOCR-based Bangla text recognition."""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from ..contracts import Chunk, Region

_PAGE_ID = re.compile(r"^(?P<doc_id>.+)_p(?P<page_number>0*[1-9]\d*)$")


def _page_parts(page_id: str) -> tuple[str, int]:
    match = _PAGE_ID.fullmatch(page_id)
    if match is None:
        raise ValueError(f"Region page_id does not use the canonical format: {page_id}")
    return match.group("doc_id"), int(match.group("page_number"))


def _page_path(page_id: str, cfg: dict) -> Path:
    explicit = cfg.get("ocr", {}).get("page_images", {}).get(page_id)
    if explicit:
        path = Path(str(explicit)).expanduser()
        if path.is_file():
            return path

    doc_id, page_number = _page_parts(page_id)
    artifact_root = Path(
        os.getenv("DOC_AGENT_ARTIFACT_DIR", cfg.get("data", {}).get("artifact_dir", "artifacts"))
    ).expanduser()
    raw_root = Path(
        os.getenv("DOC_AGENT_DATA_DIR", cfg.get("data", {}).get("raw_dir", "data/raw"))
    ).expanduser()
    candidates = [
        artifact_root / "preprocessed" / doc_id / f"{page_id}.png",
        raw_root / doc_id / f"page_{page_number:04d}.png",
        raw_root / f"{page_id}.png",
        Path("grading_kit") / "heldout_pages" / f"{page_id}.png",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"No page image found for {page_id}; checked: {candidates}")


def _reconstruct_lines(results: list[Any]) -> str:
    items: list[dict[str, float | str]] = []
    for result in results:
        if len(result) < 2:
            continue
        bbox, value = result[0], str(result[1]).strip()
        if not value:
            continue
        x_values = [float(point[0]) for point in bbox]
        y_values = [float(point[1]) for point in bbox]
        items.append(
            {
                "x": min(x_values),
                "y": (min(y_values) + max(y_values)) / 2,
                "height": max(max(y_values) - min(y_values), 1.0),
                "text": value,
            }
        )

    lines: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda value: (float(value["y"]), float(value["x"]))):
        if lines:
            current = lines[-1]
            tolerance = 0.65 * max(float(current["height"]), float(item["height"]))
            if abs(float(item["y"]) - float(current["y"])) <= tolerance:
                current["items"].append(item)
                current["y"] = sum(float(value["y"]) for value in current["items"]) / len(
                    current["items"]
                )
                current["height"] = max(float(current["height"]), float(item["height"]))
                continue
        lines.append({"y": item["y"], "height": item["height"], "items": [item]})

    return "\n".join(
        " ".join(
            str(item["text"]) for item in sorted(line["items"], key=lambda value: float(value["x"]))
        )
        for line in lines
    )


def _normalize(text: str, form: str) -> str:
    if form != "NFC":
        raise ValueError("Bangla OCR normalization must be NFC")
    normalized = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [" ".join(line.split()) for line in normalized.split("\n")]
    return "\n".join(line for line in lines if line).strip()


class Reader:
    """Lazy EasyOCR reader configured for Bangla and embedded English text."""

    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg["ocr"]
        self._root_cfg = cfg
        self._engine: Any | None = None

    def _load_engine(self) -> Any:
        if self._engine is None:
            import easyocr

            languages = list(self.cfg.get("languages", ["bn", "en"]))
            device = str(self._root_cfg.get("device", "cpu")).lower()
            self._engine = easyocr.Reader(languages, gpu=device.startswith("cuda"), verbose=False)
        return self._engine

    def transcribe_region(self, region: Region) -> str:
        path = _page_path(region.page_id, self._root_cfg)
        try:
            with Image.open(path) as source:
                page = ImageOps.exif_transpose(source).convert("RGB")
                x0, y0, x1, y1 = region.bbox
                if not (0 <= x0 < x1 <= page.width and 0 <= y0 < y1 <= page.height):
                    raise ValueError(f"Invalid OCR crop {region.bbox} for {path} ({page.size})")
                crop = np.asarray(page.crop(region.bbox))
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError(f"Cannot open OCR page image: {path}") from exc
        results = self._load_engine().readtext(
            crop,
            detail=1,
            paragraph=False,
            batch_size=int(self.cfg.get("batch_size", 8)),
            workers=int(self.cfg.get("workers", 0)),
        )
        return _reconstruct_lines(results)


def transcribe(regions: list[Region], cfg: dict) -> list[Chunk]:
    """Transcribe ordered regions into stable NFC-normalized source chunks."""

    reader = Reader(cfg)
    normalization = str(cfg.get("ocr", {}).get("unicode_normalization", "NFC"))
    chunks: list[Chunk] = []
    page_counts: dict[str, int] = {}
    for region in regions:
        page_counts[region.page_id] = page_counts.get(region.page_id, 0) + 1
        ordinal = page_counts[region.page_id]
        raw_text = reader.transcribe_region(region)
        text = _normalize(raw_text, normalization)
        if not text:
            continue
        doc_id, _ = _page_parts(region.page_id)
        chunks.append(
            Chunk(
                id=f"{region.page_id}_r{ordinal:04d}_{region.kind}",
                doc_id=doc_id,
                text=text,
                page_ids=[region.page_id],
            )
        )
    return chunks
