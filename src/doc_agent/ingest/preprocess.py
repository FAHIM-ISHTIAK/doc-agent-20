"""Stage 1: deterministic classical cleanup for scanned page images."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

from ..contracts import Page


def _output_root(cfg: dict) -> Path:
    preprocess_cfg = cfg.get("preprocess", {})
    configured = preprocess_cfg.get("output_dir")
    if configured:
        return Path(str(configured)).expanduser()
    artifact_root = Path(
        os.getenv("DOC_AGENT_ARTIFACT_DIR", cfg.get("data", {}).get("artifact_dir", "artifacts"))
    ).expanduser()
    return artifact_root / "preprocessed"


def _otsu_threshold(image: Image.Image) -> int:
    pixels = np.asarray(image, dtype=np.uint8)
    histogram = np.bincount(pixels.ravel(), minlength=256).astype(np.float64)
    total = histogram.sum()
    if total == 0:
        return 127
    probabilities = histogram / total
    cumulative_probability = np.cumsum(probabilities)
    cumulative_mean = np.cumsum(probabilities * np.arange(256))
    global_mean = cumulative_mean[-1]
    denominator = cumulative_probability * (1.0 - cumulative_probability)
    numerator = (global_mean * cumulative_probability - cumulative_mean) ** 2
    score = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)
    return int(np.argmax(score))


def _projection_score(binary: np.ndarray) -> float:
    row_ink = np.count_nonzero(binary < 128, axis=1).astype(np.float64)
    if not np.any(row_ink):
        return 0.0
    return float(np.mean(np.diff(row_ink) ** 2))


def _estimate_correction_angle(
    image: Image.Image, *, max_angle: float, coarse_step: float, fine_step: float
) -> float:
    """Estimate a small corrective rotation using horizontal projection peaks."""

    preview = image.copy()
    preview.thumbnail((1000, 1000), Image.Resampling.BILINEAR)
    threshold = _otsu_threshold(preview)
    preview = preview.point(lambda value: 0 if value <= threshold else 255, mode="1").convert("L")

    def score(angle: float) -> float:
        rotated = preview.rotate(
            angle,
            resample=Image.Resampling.BILINEAR,
            expand=False,
            fillcolor=255,
        )
        return _projection_score(np.asarray(rotated, dtype=np.uint8))

    coarse_angles = np.arange(-max_angle, max_angle + coarse_step / 2, coarse_step)
    coarse_best = max(coarse_angles, key=lambda angle: (score(float(angle)), -abs(float(angle))))
    fine_start = max(-max_angle, float(coarse_best) - coarse_step)
    fine_stop = min(max_angle, float(coarse_best) + coarse_step)
    fine_angles = np.arange(fine_start, fine_stop + fine_step / 2, fine_step)
    best = max(fine_angles, key=lambda angle: (score(float(angle)), -abs(float(angle))))
    return round(float(best), 3)


def _process_image(image: Image.Image, cfg: dict) -> Image.Image:
    clean = ImageOps.exif_transpose(image).convert("L")
    if cfg.get("deskew", True):
        angle = _estimate_correction_angle(
            clean,
            max_angle=float(cfg.get("deskew_max_angle", 3.0)),
            coarse_step=float(cfg.get("deskew_coarse_step", 1.0)),
            fine_step=float(cfg.get("deskew_fine_step", 0.25)),
        )
        if abs(angle) >= float(cfg.get("deskew_min_angle", 0.15)):
            clean = clean.rotate(
                angle,
                resample=Image.Resampling.BICUBIC,
                expand=False,
                fillcolor=255,
            )
    if cfg.get("denoise", True):
        clean = clean.filter(ImageFilter.MedianFilter(size=3))
    if cfg.get("binarize", True):
        threshold = _otsu_threshold(clean) + int(cfg.get("binarize_threshold_offset", 0))
        threshold = max(0, min(255, threshold))
        clean = clean.point(lambda value: 0 if value <= threshold else 255, mode="1")
    return clean


def run(pages: list[Page], cfg: dict) -> list[Page]:
    """Write cleaned copies and return Pages pointing to the derived images.

    Page identity and document membership are preserved. Raw inputs are opened
    read-only, and every output is written beneath the configured artifact root.
    """

    preprocess_cfg = cfg.get("preprocess", {})
    enabled = any(
        bool(preprocess_cfg.get(operation, True)) for operation in ("deskew", "denoise", "binarize")
    )
    if not enabled:
        return [page.model_copy(deep=True) for page in pages]

    output_root = _output_root(cfg).resolve()
    raw_root = (
        Path(os.getenv("DOC_AGENT_DATA_DIR", cfg.get("data", {}).get("raw_dir", "data/raw")))
        .expanduser()
        .resolve()
    )
    if output_root == raw_root or raw_root in output_root.parents:
        raise ValueError("Preprocessed output must not be written inside the raw input directory")
    output_root.mkdir(parents=True, exist_ok=True)

    processed: list[Page] = []
    for page in pages:
        source_path = Path(page.image_path)
        if not source_path.is_file():
            raise FileNotFoundError(f"Page image does not exist: {source_path}")
        destination = output_root / page.doc_id / f"{page.id}.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(source_path) as source:
                clean = _process_image(source, preprocess_cfg)
                clean.save(destination, format="PNG", optimize=False, compress_level=6)
        except (OSError, UnidentifiedImageError) as exc:
            raise ValueError(f"Cannot preprocess page image: {source_path}") from exc
        processed.append(
            Page(id=page.id, doc_id=page.doc_id, image_path=str(destination.resolve()))
        )
    return processed
