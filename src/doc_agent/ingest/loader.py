"""Stage 1: load rasterized document pages with stable identifiers."""

from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from ..contracts import Page

_CANONICAL_PAGE_NAME = re.compile(r"^page_0*(?P<number>[1-9]\d*)$", re.IGNORECASE)
_FLAT_PAGE_NAME = re.compile(
    r"^(?P<doc_id>[a-z0-9][a-z0-9_-]*)_p0*(?P<number>[1-9]\d*)$", re.IGNORECASE
)
_DEFAULT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")


def _runtime_value(cfg: dict, env_name: str, config_name: str, default: object) -> object:
    """Read a runtime override without relying on import-time global settings."""

    value = os.getenv(env_name)
    if value is not None:
        return value
    return cfg.get("runtime", {}).get(config_name, default)


def _raw_dir(cfg: dict) -> Path:
    override = os.getenv("DOC_AGENT_DATA_DIR")
    return Path(override if override else cfg.get("data", {}).get("raw_dir", "data/raw"))


def _parse_page(path: Path, raw_dir: Path) -> tuple[str, int] | None:
    """Return ``(doc_id, one-based page number)`` for a supported layout."""

    relative = path.relative_to(raw_dir)
    canonical = _CANONICAL_PAGE_NAME.fullmatch(path.stem)
    if canonical and len(relative.parts) >= 2:
        return path.parent.name, int(canonical.group("number"))

    flat = _FLAT_PAGE_NAME.fullmatch(path.stem)
    if flat and len(relative.parts) == 1:
        return flat.group("doc_id"), int(flat.group("number"))
    return None


def _is_blank(path: Path, *, foreground_threshold: int, min_foreground_fraction: float) -> bool:
    """Conservatively detect nearly empty pages from a small grayscale preview."""

    try:
        with Image.open(path) as source:
            image = ImageOps.exif_transpose(source).convert("L")
            image.thumbnail((512, 512), Image.Resampling.BILINEAR)
            pixels = np.asarray(image, dtype=np.uint8)
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"Cannot read page image: {path}") from exc

    if pixels.size == 0:
        return True
    foreground_fraction = float(np.count_nonzero(pixels < foreground_threshold) / pixels.size)
    return foreground_fraction < min_foreground_fraction


def load_pages(cfg: dict) -> list[Page]:
    """Load canonical page images in deterministic document/page order.

    Supported layouts are ``<raw>/<doc_id>/page_0001.png`` (the corpus
    convention) and ``<raw>/<doc_id>_p0001.png`` (useful for held-out samples).
    Small mode applies its limit independently to each document after exclusions.
    """

    raw_dir = _raw_dir(cfg).expanduser()
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"Raw page-image directory does not exist: {raw_dir}")

    ingest_cfg = cfg.get("ingest", {})
    extensions = {
        str(extension).lower()
        for extension in ingest_cfg.get("supported_extensions", _DEFAULT_EXTENSIONS)
    }
    excluded_ids = {str(page_id) for page_id in ingest_cfg.get("exclude_page_ids", [])}
    exclude_blank = bool(ingest_cfg.get("exclude_blank", True))
    foreground_threshold = int(ingest_cfg.get("blank_foreground_threshold", 245))
    min_foreground_fraction = float(ingest_cfg.get("blank_min_foreground_fraction", 0.0005))
    if not 0 <= foreground_threshold <= 255:
        raise ValueError("ingest.blank_foreground_threshold must be between 0 and 255")
    if not 0 <= min_foreground_fraction <= 1:
        raise ValueError("ingest.blank_min_foreground_fraction must be between 0 and 1")

    candidates: list[tuple[str, int, Path]] = []
    seen_ids: dict[str, Path] = {}
    for path in raw_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue
        parsed = _parse_page(path, raw_dir)
        if parsed is None:
            continue
        doc_id, page_number = parsed
        page_id = f"{doc_id}_p{page_number:04d}"
        if page_id in seen_ids:
            raise ValueError(f"Duplicate stable page ID {page_id}: {seen_ids[page_id]} and {path}")
        seen_ids[page_id] = path
        if page_id in excluded_ids:
            continue
        if exclude_blank and _is_blank(
            path,
            foreground_threshold=foreground_threshold,
            min_foreground_fraction=min_foreground_fraction,
        ):
            continue
        candidates.append((doc_id, page_number, path.resolve()))

    candidates.sort(key=lambda item: (item[0].casefold(), item[1], item[2].name.casefold()))

    mode = str(_runtime_value(cfg, "DOC_AGENT_RUN_MODE", "mode", "small")).lower()
    if mode not in {"small", "full"}:
        raise ValueError("runtime mode must be 'small' or 'full'")
    limit: int | None = None
    if mode == "small":
        raw_limit = _runtime_value(cfg, "DOC_AGENT_SMALL_MAX_PAGES", "small_max_pages", 20)
        limit = int(str(raw_limit))
        if limit < 1:
            raise ValueError("small-mode page limit must be at least 1")

    selected: list[tuple[str, int, Path]] = []
    counts: defaultdict[str, int] = defaultdict(int)
    for candidate in candidates:
        doc_id = candidate[0]
        if limit is not None and counts[doc_id] >= limit:
            continue
        selected.append(candidate)
        counts[doc_id] += 1

    return [
        Page(
            id=f"{doc_id}_p{page_number:04d}",
            doc_id=doc_id,
            image_path=str(path),
        )
        for doc_id, page_number, path in selected
    ]
