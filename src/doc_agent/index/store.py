"""Stage 4: persisted FAISS FlatIP index and provenance metadata."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ..contracts import Chunk

_SCHEMA_VERSION = 1
_INDEX_FILENAME = "index.faiss"
_METADATA_FILENAME = "metadata.json"


@dataclass(frozen=True)
class LoadedIndex:
    """A FAISS index and the exact chunks addressed by its row numbers."""

    index: Any
    chunks: list[Chunk]
    dimension: int


def _faiss(index_cfg: dict[str, Any]) -> Any:
    injected = index_cfg.get("_faiss")
    if injected is not None:
        return injected
    try:
        import faiss
    except ImportError as exc:
        raise RuntimeError(
            "FAISS is required to build or load an index. Install faiss-cpu or inject "
            "index._faiss in a unit test."
        ) from exc
    return faiss


def _artifact_root(cfg: dict) -> Path:
    return Path(
        os.getenv("DOC_AGENT_ARTIFACT_DIR", cfg.get("data", {}).get("artifact_dir", "artifacts"))
    ).expanduser()


def _index_dir(cfg: dict) -> Path:
    """Resolve the configured index under the writable artifact root."""

    index_cfg = cfg.get("index", {})
    configured = Path(str(index_cfg.get("path", "index"))).expanduser()
    root = _artifact_root(cfg)
    configured_root = Path(str(cfg.get("data", {}).get("artifact_dir", "artifacts")))
    if configured.is_absolute():
        target = configured
    elif configured.parts and configured.parts[0] == configured_root.name:
        target = root.joinpath(*configured.parts[1:])
    else:
        target = root / configured

    input_root = os.getenv("DOC_AGENT_INPUT_ROOT")
    if input_root:
        try:
            target.resolve().relative_to(Path(input_root).expanduser().resolve())
        except ValueError:
            pass
        else:
            raise ValueError("index.path must not point inside DOC_AGENT_INPUT_ROOT")
    return target


def _normalise_vectors(vectors: Any, expected_count: int) -> np.ndarray:
    matrix = np.asarray(vectors, dtype=np.float32)
    if matrix.ndim != 2:
        raise ValueError("vectors must be a two-dimensional matrix")
    if matrix.shape[0] != expected_count:
        raise ValueError(
            f"vectors contains {matrix.shape[0]} rows but {expected_count} chunks were supplied"
        )
    if matrix.shape[1] < 1:
        raise ValueError("vectors must have at least one dimension")
    if not np.isfinite(matrix).all():
        raise ValueError("vectors must contain only finite values")
    if expected_count == 0:
        return np.ascontiguousarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("vectors must not contain zero rows")
    return np.ascontiguousarray(matrix / norms, dtype=np.float32)


def _chunk_record(chunk: Chunk) -> dict[str, Any]:
    return chunk.model_dump()


def _metadata(chunks: list[Chunk], dimension: int) -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "index_type": "faiss:flatip",
        "vector_count": len(chunks),
        "dimension": dimension,
        "chunks": [_chunk_record(chunk) for chunk in chunks],
    }


def _atomic_write_index(faiss: Any, index: Any, path: Path) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".faiss", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        faiss.write_index(index, str(temporary_path))
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _atomic_write_json(payload: dict[str, Any], path: Path) -> None:
    with tempfile.NamedTemporaryFile(
        dir=path.parent, mode="w", encoding="utf-8", suffix=".json", delete=False
    ) as temporary:
        json.dump(payload, temporary, ensure_ascii=False, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    try:
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def build(chunks: list[Chunk], vectors: Any, cfg: dict) -> None:
    """Build a normalized FlatIP index and provenance-complete JSON metadata."""

    index_cfg = cfg.get("index", {})
    if str(index_cfg.get("type", "faiss:flatip")).lower() != "faiss:flatip":
        raise ValueError("Only index.type 'faiss:flatip' is supported")
    matrix = _normalise_vectors(vectors, len(chunks))
    faiss = _faiss(index_cfg)
    index = faiss.IndexFlatIP(int(matrix.shape[1]))
    if len(chunks):
        index.add(matrix)

    destination = _index_dir(cfg)
    destination.mkdir(parents=True, exist_ok=True)
    _atomic_write_index(faiss, index, destination / _INDEX_FILENAME)
    _atomic_write_json(_metadata(chunks, int(matrix.shape[1])), destination / _METADATA_FILENAME)


def _read_metadata(path: Path) -> tuple[list[Chunk], int]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read index metadata: {path}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError("Index metadata has an unsupported or missing schema version")
    if payload.get("index_type") != "faiss:flatip":
        raise ValueError("Index metadata does not describe a faiss:flatip index")
    try:
        dimension = int(payload["dimension"])
        records = payload["chunks"]
        vector_count = int(payload["vector_count"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Index metadata is missing required count or dimension fields") from exc
    if dimension < 1 or not isinstance(records, list) or vector_count != len(records):
        raise ValueError("Index metadata has inconsistent vector count, chunks, or dimension")
    try:
        chunks = [Chunk.model_validate(record) for record in records]
    except (TypeError, ValueError) as exc:
        raise ValueError("Index metadata contains an invalid chunk record") from exc
    return chunks, dimension


def load(cfg: dict) -> LoadedIndex:
    """Load a persisted index, rejecting missing or inconsistent sidecar metadata."""

    destination = _index_dir(cfg)
    index_path = destination / _INDEX_FILENAME
    metadata_path = destination / _METADATA_FILENAME
    if not index_path.is_file() or not metadata_path.is_file():
        raise FileNotFoundError(
            f"Index requires both {index_path} and {metadata_path}; rebuild the knowledge base"
        )
    chunks, dimension = _read_metadata(metadata_path)
    faiss = _faiss(cfg.get("index", {}))
    try:
        index = faiss.read_index(str(index_path))
    except Exception as exc:  # FAISS exposes implementation-specific error classes.
        raise ValueError(f"Cannot read FAISS index: {index_path}") from exc

    index_dimension = int(getattr(index, "d", -1))
    index_count = int(getattr(index, "ntotal", -1))
    if index_dimension != dimension or index_count != len(chunks):
        raise ValueError(
            "FAISS index and metadata disagree on vector count or embedding dimension; "
            "rebuild the index"
        )
    return LoadedIndex(index=index, chunks=chunks, dimension=dimension)
