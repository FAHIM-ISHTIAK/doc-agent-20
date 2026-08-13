"""Stage 4: deterministic, normalized chunk embeddings."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..contracts import Chunk


def _encoder(embed_cfg: dict[str, Any], device: str) -> Any:
    """Return an injected test encoder or lazily load the configured checkpoint."""

    injected = embed_cfg.get("_encoder")
    if injected is not None:
        return injected

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Embedding requires sentence-transformers. Install the project dependencies "
            "or inject embed._encoder in a unit test."
        ) from exc

    return SentenceTransformer(str(embed_cfg["model"]), device=device)


def _as_matrix(values: Any, count: int, expected_dim: int) -> np.ndarray:
    """Validate encoder output before it reaches the persisted vector index."""

    matrix = np.asarray(values, dtype=np.float32)
    if matrix.ndim != 2:
        raise ValueError("The embedding encoder must return a two-dimensional matrix")
    if matrix.shape[0] != count:
        raise ValueError(
            f"The embedding encoder returned {matrix.shape[0]} vectors for {count} chunks"
        )
    if matrix.shape[1] != expected_dim:
        raise ValueError(
            "Embedding dimension does not match embed.dim: "
            f"expected {expected_dim}, received {matrix.shape[1]}"
        )
    if not np.isfinite(matrix).all():
        raise ValueError("Embedding vectors must contain only finite values")
    return matrix


def _normalise(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("Embedding encoder returned a zero vector, which cannot use FlatIP safely")
    return matrix / norms


def encode(chunks: list[Chunk], cfg: dict) -> np.ndarray:
    """Encode chunks in input order for normalized inner-product retrieval.

    The production path lazily loads ``embed.model`` through SentenceTransformers.
    Tests can inject a small deterministic object as ``cfg['embed']['_encoder']``;
    this keeps the test suite independent of model downloads and GPUs.
    """

    embed_cfg = cfg.get("embed", {})
    if "model" not in embed_cfg:
        raise ValueError("embed.model is required")
    dimension = int(embed_cfg.get("dim", 0))
    if dimension < 1:
        raise ValueError("embed.dim must be at least 1")
    if not chunks:
        return np.empty((0, dimension), dtype=np.float32)

    encoder = _encoder(embed_cfg, str(cfg.get("device", "cpu")))
    texts = [chunk.text for chunk in chunks]
    try:
        encoded = encoder.encode(
            texts,
            batch_size=int(embed_cfg.get("batch_size", 32)),
            convert_to_numpy=True,
            normalize_embeddings=False,
            show_progress_bar=False,
        )
    except TypeError:
        # Lightweight test doubles commonly implement only the two essential
        # parameters. Production SentenceTransformer instances take the full set.
        encoded = encoder.encode(texts, batch_size=int(embed_cfg.get("batch_size", 32)))

    matrix = _as_matrix(encoded, len(chunks), dimension)
    if bool(embed_cfg.get("normalize", True)):
        matrix = _normalise(matrix)
    return np.ascontiguousarray(matrix, dtype=np.float32)
