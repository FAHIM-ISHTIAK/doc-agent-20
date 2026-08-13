"""Tests for chunking plus locally reproducible embedding/index persistence."""

from __future__ import annotations

import pickle
import unicodedata
from pathlib import Path

import numpy as np
import pytest

from doc_agent.contracts import Chunk
from doc_agent.index import chunk, embed, store


def _source(identifier: str, text: str, page_ids: list[str] | None = None) -> Chunk:
    return Chunk(
        id=identifier,
        doc_id="grammar",
        text=text,
        page_ids=page_ids or ["grammar_p0001"],
    )


class _FakeEncoder:
    """Small deterministic encoder: no checkpoint, GPU, or network access in tests."""

    def encode(self, texts: list[str], batch_size: int) -> np.ndarray:
        del batch_size
        return np.asarray(
            [[float(len(text)), float(sum(map(ord, text)) % 17), 2.0] for text in texts],
            dtype=np.float32,
        )


class _FakeFlatIP:
    def __init__(self, dimension: int) -> None:
        self.d = dimension
        self._vectors = np.empty((0, dimension), dtype=np.float32)

    @property
    def ntotal(self) -> int:
        return int(self._vectors.shape[0])

    def add(self, vectors: np.ndarray) -> None:
        if vectors.ndim != 2 or vectors.shape[1] != self.d:
            raise ValueError("invalid fake FAISS vector shape")
        self._vectors = np.vstack([self._vectors, vectors])

    def search(self, queries: np.ndarray, count: int) -> tuple[np.ndarray, np.ndarray]:
        scores = queries @ self._vectors.T
        order = np.argsort(-scores, axis=1)[:, :count]
        return np.take_along_axis(scores, order, axis=1), order.astype(np.int64)


class _FakeFaiss:
    """Tiny persistence-compatible FAISS facade used to exercise store.build/load."""

    IndexFlatIP = _FakeFlatIP

    @staticmethod
    def write_index(index: _FakeFlatIP, path: str) -> None:
        Path(path).write_bytes(pickle.dumps(index))

    @staticmethod
    def read_index(path: str) -> _FakeFlatIP:
        return pickle.loads(Path(path).read_bytes())


def _index_cfg(tmp_path: Path) -> dict:
    return {
        "device": "cpu",
        "data": {"artifact_dir": str(tmp_path / "artifacts")},
        "embed": {
            "model": "test/deterministic",
            "dim": 3,
            "normalize": True,
            "batch_size": 2,
            "_encoder": _FakeEncoder(),
        },
        "index": {
            "type": "faiss:flatip",
            "path": "artifacts/index",
            "_faiss": _FakeFaiss,
        },
    }


def test_fixed_chunks_overlap_and_keep_page_provenance() -> None:
    source = [
        _source("a", "এক দুই তিন চার পাঁচ", ["grammar_p0001"]),
        _source("b", "ছয় সাত আট নয় দশ", ["grammar_p0002"]),
    ]

    result = chunk.split(source, {"index": {"chunk_tokens": 6, "overlap": 2, "rule_aware": False}})

    assert [item.id for item in result] == ["grammar_c000001", "grammar_c000002"]
    assert result[0].text.split()[-2:] == result[1].text.split()[:2]
    assert result[0].page_ids == ["grammar_p0001", "grammar_p0002"]
    assert result[1].page_ids == ["grammar_p0001", "grammar_p0002"]


def test_rule_aware_keeps_definition_with_example_and_splits_next_rule() -> None:
    source = [
        _source(
            "grammar_p0001_r0001_text",
            "[২.১১২] যে ধ্বনি নিজে উচ্চারিত হয় তাকে স্বরধ্বনি বলে।\nযেমন: আ, ই, উ।\n"
            "[২.১১৩] যে ধ্বনি স্বরের সাহায্যে উচ্চারিত হয় তাকে ব্যঞ্জনধ্বনি বলে।\nযেমন: ক্, চ্।",
        )
    ]

    result = chunk.split(source, {"index": {"chunk_tokens": 40, "overlap": 4, "rule_aware": True}})

    assert len(result) == 2
    assert "[২.১১২]" in result[0].text and "যেমন:" in result[0].text
    assert "[২.১১৩]" not in result[0].text
    assert result[1].text.startswith("[২.১১৩]")


def test_oversized_rule_uses_overlap_and_repeats_rule_label() -> None:
    text = "[৩.২১] " + " ".join(f"শব্দ{i}" for i in range(18))
    source = [_source("grammar_p0001_r0001_text", text)]

    result = chunk.split(source, {"index": {"chunk_tokens": 8, "overlap": 2, "rule_aware": True}})

    assert len(result) >= 3
    assert result[0].text.startswith("[৩.২১]")
    assert all("[৩.২১]" in item.text for item in result[1:])
    assert all(len(item.text.split()) <= 10 for item in result)


def test_rule_can_span_pages_without_losing_citations() -> None:
    source = [
        _source(
            "grammar_p0001_r0001_text",
            "[৪.১] প্রত্যয়ের সংজ্ঞা।",
            ["grammar_p0001"],
        ),
        _source(
            "grammar_p0002_r0001_text",
            "যেমন: কৃত + অ = কর।",
            ["grammar_p0002"],
        ),
    ]

    result = chunk.split(source, {"index": {"chunk_tokens": 30, "overlap": 4, "rule_aware": True}})

    assert len(result) == 1
    assert result[0].page_ids == ["grammar_p0001", "grammar_p0002"]


def test_table_is_atomic_when_it_fits() -> None:
    source = [_source("grammar_p0001_r0001_table", "উপসর্গ | শব্দ | অর্থ\nঅতি | অতিকায় | বৃহৎ")]

    result = chunk.split(source, {"index": {"chunk_tokens": 30, "overlap": 4, "rule_aware": True}})

    assert len(result) == 1
    assert "উপসর্গ | শব্দ | অর্থ" in result[0].text
    assert "অতি | অতিকায় | বৃহৎ" in result[0].text


def test_chunking_is_deterministic_nfc_and_validates_config() -> None:
    source = [_source("a", "কো নিয়ম")]
    cfg = {"index": {"chunk_tokens": 10, "overlap": 2, "rule_aware": False}}

    assert chunk.split(source, cfg) == chunk.split(source, cfg)
    assert chunk.split(source, cfg)[0].text == unicodedata.normalize("NFC", "কো নিয়ম")
    assert chunk.split([], cfg) == []
    with pytest.raises(ValueError):
        chunk.split(source, {"index": {"chunk_tokens": 4, "overlap": 4}})


def test_embedding_keeps_input_order_shape_and_unit_normalization(tmp_path: Path) -> None:
    chunks = [
        _source("grammar_c000001", "স্বরধ্বনির উদাহরণ", ["grammar_p0001"]),
        _source("grammar_c000002", "ব্যঞ্জনধ্বনির উদাহরণ", ["grammar_p0002"]),
    ]

    vectors = embed.encode(chunks, _index_cfg(tmp_path))

    assert vectors.shape == (2, 3)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0)
    assert not np.array_equal(vectors[0], vectors[1])


def test_flatip_build_reload_search_preserves_bangla_chunk_provenance(tmp_path: Path) -> None:
    cfg = _index_cfg(tmp_path)
    chunks = [
        _source("grammar_c000001", "[১.১] স্বরধ্বনির উদাহরণ আ ই উ", ["grammar_p0001"]),
        _source(
            "grammar_c000002",
            "[১.২] ব্যঞ্জনধ্বনির উদাহরণ ক খ গ",
            ["grammar_p0002", "grammar_p0003"],
        ),
    ]
    vectors = embed.encode(chunks, cfg)

    store.build(chunks, vectors, cfg)
    restarted = store.load(cfg)
    scores, positions = restarted.index.search(vectors[:1], 1)
    recovered = restarted.chunks[int(positions[0, 0])]

    assert scores[0, 0] == pytest.approx(1.0)
    assert recovered.id == "grammar_c000001"
    assert recovered.doc_id == "grammar"
    assert recovered.text == "[১.১] স্বরধ্বনির উদাহরণ আ ই উ"
    assert recovered.page_ids == ["grammar_p0001"]
    assert restarted.chunks[1].page_ids == ["grammar_p0002", "grammar_p0003"]


def test_store_fails_closed_for_corrupt_or_mismatched_metadata(tmp_path: Path) -> None:
    cfg = _index_cfg(tmp_path)
    source = [_source("grammar_c000001", "বাংলা ব্যাকরণ")]
    store.build(source, embed.encode(source, cfg), cfg)
    metadata_path = tmp_path / "artifacts" / "index" / "metadata.json"

    metadata_path.write_text("not JSON", encoding="utf-8")
    with pytest.raises(ValueError, match="Cannot read index metadata"):
        store.load(cfg)

    store.build(source, embed.encode(source, cfg), cfg)
    metadata = metadata_path.read_text(encoding="utf-8").replace(
        '"vector_count": 1', '"vector_count": 2'
    )
    metadata_path.write_text(metadata, encoding="utf-8")
    with pytest.raises(ValueError, match="inconsistent"):
        store.load(cfg)
