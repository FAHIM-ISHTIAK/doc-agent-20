"""Stage 2: deterministic layout detection for scanned grammar pages."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from ..contracts import Page, Region


def _runs(values: np.ndarray, *, max_gap: int = 0) -> list[tuple[int, int]]:
    """Return half-open runs, joining gaps no larger than ``max_gap``."""

    indices = np.flatnonzero(values)
    if indices.size == 0:
        return []
    runs: list[tuple[int, int]] = []
    start = previous = int(indices[0])
    for raw_index in indices[1:]:
        index = int(raw_index)
        if index - previous > max_gap + 1:
            runs.append((start, previous + 1))
            start = index
        previous = index
    runs.append((start, previous + 1))
    return runs


def _content_mask(path: Path, layout_cfg: dict) -> np.ndarray:
    try:
        with Image.open(path) as source:
            grayscale = np.asarray(ImageOps.exif_transpose(source).convert("L"), dtype=np.uint8)
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError(f"Cannot read page image: {path}") from exc
    threshold = int(layout_cfg.get("foreground_threshold", 200))
    if not 0 <= threshold <= 255:
        raise ValueError("layout.foreground_threshold must be between 0 and 255")
    return grayscale < threshold


def _longest_run(values: np.ndarray) -> int:
    runs = _runs(values)
    return max((end - start for start, end in runs), default=0)


def _table_boxes(mask: np.ndarray, layout_cfg: dict) -> list[tuple[int, int, int, int]]:
    """Detect ruled tables from repeated long horizontal and vertical strokes."""

    height, width = mask.shape
    horizontal_fraction = float(layout_cfg.get("table_horizontal_fraction", 0.45))
    vertical_fraction = float(layout_cfg.get("table_vertical_fraction", 0.20))
    horizontal = _runs(
        np.asarray([_longest_run(row) >= width * horizontal_fraction for row in mask]),
        max_gap=2,
    )
    vertical = _runs(
        np.asarray([_longest_run(column) >= height * vertical_fraction for column in mask.T]),
        max_gap=2,
    )
    if len(horizontal) < 3 or len(vertical) < 2:
        return []

    y0 = max(0, horizontal[0][0] - 2)
    y1 = min(height, horizontal[-1][1] + 2)
    relevant_vertical = [run for run in vertical if run[0] < width and run[1] > 0]
    if len(relevant_vertical) < 2:
        return []
    x0 = max(0, relevant_vertical[0][0] - 2)
    x1 = min(width, relevant_vertical[-1][1] + 2)
    if x1 <= x0 or y1 <= y0:
        return []
    return [(x0, y0, x1, y1)]


def _text_boxes(
    mask: np.ndarray, excluded: list[tuple[int, int, int, int]]
) -> list[tuple[int, int, int, int]]:
    working = mask.copy()
    for x0, y0, x1, y1 in excluded:
        working[y0:y1, x0:x1] = False

    height, width = working.shape
    active_rows = working.sum(axis=1) >= max(2, int(width * 0.0015))
    line_runs = _runs(active_rows, max_gap=max(1, height // 900))
    lines: list[tuple[int, int, int, int]] = []
    for y0, y1 in line_runs:
        active_columns = working[y0:y1].any(axis=0)
        for x0, x1 in _runs(active_columns, max_gap=max(6, width // 30)):
            if (x1 - x0) * (y1 - y0) >= 12:
                lines.append((x0, y0, x1, y1))
    if not lines:
        return []

    typical_height = float(np.median([box[3] - box[1] for box in lines]))
    blocks: list[tuple[int, int, int, int]] = []
    for box in lines:
        if not blocks:
            blocks.append(box)
            continue
        px0, py0, px1, py1 = blocks[-1]
        x0, y0, x1, y1 = box
        overlap = max(0, min(px1, x1) - max(px0, x0))
        minimum_width = max(1, min(px1 - px0, x1 - x0))
        same_column = overlap / minimum_width >= 0.30
        close = y0 - py1 <= max(4.0, typical_height * 1.25)
        if same_column and close:
            blocks[-1] = (min(px0, x0), py0, max(px1, x1), y1)
        else:
            blocks.append(box)

    padding = max(2, min(height, width) // 350)
    return [
        (
            max(0, x0 - padding),
            max(0, y0 - padding),
            min(width, x1 + padding),
            min(height, y1 + padding),
        )
        for x0, y0, x1, y1 in blocks
    ]


def _kind(box: tuple[int, int, int, int], page_width: int, page_height: int) -> str:
    x0, y0, x1, y1 = box
    width = x1 - x0
    center = (x0 + x1) / 2
    centered = abs(center - page_width / 2) <= page_width * 0.12
    compact = (y1 - y0) <= page_height * 0.09
    if centered and compact and width <= page_width * 0.75:
        return "heading"
    return "text"


def _order_regions(regions: list[Region], page_width: int) -> list[Region]:
    """Order column blocks without interleaving their lines."""

    if len(regions) < 2:
        return regions
    midpoint = page_width / 2
    spanning = [
        region
        for region in regions
        if region.kind == "table"
        or (
            region.bbox[0] < midpoint * 0.75
            and region.bbox[2] > midpoint * 1.25
            and (region.bbox[2] - region.bbox[0]) >= page_width * 0.55
        )
    ]
    columnar = [region for region in regions if region not in spanning]
    ordered: list[Region] = []
    boundaries = sorted(spanning, key=lambda region: (region.bbox[1], region.bbox[0]))
    lower = 0
    for boundary in boundaries:
        upper = boundary.bbox[1]
        section = [
            region for region in columnar if lower <= (region.bbox[1] + region.bbox[3]) / 2 < upper
        ]
        ordered.extend(
            sorted(
                section,
                key=lambda region: (region.bbox[0] >= midpoint, region.bbox[1], region.bbox[0]),
            )
        )
        ordered.append(boundary)
        lower = boundary.bbox[3]
    tail = [region for region in columnar if (region.bbox[1] + region.bbox[3]) / 2 >= lower]
    ordered.extend(
        sorted(
            tail, key=lambda region: (region.bbox[0] >= midpoint, region.bbox[1], region.bbox[0])
        )
    )
    seen = {id(region) for region in ordered}
    ordered.extend(region for region in regions if id(region) not in seen)
    return ordered


def detect(pages: list[Page], cfg: dict) -> list[Region]:
    """Detect bounded text, heading, and ruled-table regions in reading order."""

    layout_cfg = cfg.get("layout", {})
    detected: list[Region] = []
    for page in pages:
        path = Path(page.image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Page image does not exist: {path}")
        mask = _content_mask(path, layout_cfg)
        height, width = mask.shape
        tables = _table_boxes(mask, layout_cfg)
        regions = [Region(page_id=page.id, bbox=box, kind="table") for box in tables]
        regions.extend(
            Region(page_id=page.id, bbox=box, kind=_kind(box, width, height))
            for box in _text_boxes(mask, tables)
        )
        detected.extend(_order_regions(regions, width))
    return detected
