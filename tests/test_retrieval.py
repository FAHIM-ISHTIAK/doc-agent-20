"""Tests for fixed and grammar-rule-aware chunking."""

from __future__ import annotations

import unicodedata

import pytest

from doc_agent.contracts import Chunk
from doc_agent.index import chunk


def _source(identifier: str, text: str, page_ids: list[str] | None = None) -> Chunk:
    return Chunk(
        id=identifier,
        doc_id="grammar",
        text=text,
        page_ids=page_ids or ["grammar_p0001"],
    )


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
