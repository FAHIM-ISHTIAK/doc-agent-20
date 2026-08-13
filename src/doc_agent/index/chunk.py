"""Stage 4: provenance-preserving fixed and grammar-rule-aware chunking."""

from __future__ import annotations

import re
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass

from ..contracts import Chunk

_RULE_START = re.compile(
    r"^\s*(?:\[[০-৯\d]+(?:[.]?[০-৯\d]+)*\]|[ক-হ][.)]|(?:পরিচ্ছেদ|অধ্যায়|সূত্র)\s*[০-৯\d]*)"
)


@dataclass(frozen=True)
class _Token:
    value: str
    page_ids: tuple[str, ...]


@dataclass
class _Unit:
    text: str
    page_ids: list[str]
    label: str = ""
    table: bool = False


def _ordered_union(groups: list[list[str]] | list[tuple[str, ...]]) -> list[str]:
    return list(dict.fromkeys(page_id for group in groups for page_id in group))


def _tokens(text: str, page_ids: list[str]) -> list[_Token]:
    normalized = unicodedata.normalize("NFC", text)
    return [
        _Token(value=value, page_ids=tuple(page_ids)) for value in re.findall(r"\S+", normalized)
    ]


def _validate(index_cfg: dict) -> tuple[int, int]:
    size = int(index_cfg.get("chunk_tokens", 256))
    overlap = int(index_cfg.get("overlap", 32))
    if size < 1:
        raise ValueError("index.chunk_tokens must be at least 1")
    if overlap < 0 or overlap >= size:
        raise ValueError("index.overlap must be non-negative and smaller than chunk_tokens")
    return size, overlap


def _windows(tokens: list[_Token], size: int, overlap: int) -> list[tuple[str, list[str]]]:
    if not tokens:
        return []
    windows: list[tuple[str, list[str]]] = []
    step = size - overlap
    for start in range(0, len(tokens), step):
        selected = tokens[start : start + size]
        if not selected:
            break
        windows.append(
            (
                " ".join(token.value for token in selected),
                _ordered_union([token.page_ids for token in selected]),
            )
        )
        if start + size >= len(tokens):
            break
    return windows


def _fixed(chunks: list[Chunk], size: int, overlap: int) -> list[tuple[str, str, list[str]]]:
    by_document: OrderedDict[str, list[_Token]] = OrderedDict()
    for chunk in chunks:
        by_document.setdefault(chunk.doc_id, []).extend(_tokens(chunk.text, chunk.page_ids))
    output: list[tuple[str, str, list[str]]] = []
    for doc_id, tokens in by_document.items():
        output.extend((doc_id, text, pages) for text, pages in _windows(tokens, size, overlap))
    return output


def _paragraphs(chunk: Chunk) -> list[str]:
    text = unicodedata.normalize("NFC", chunk.text).replace("\r\n", "\n").replace("\r", "\n")
    blocks: list[str] = []
    current: list[str] = []
    for raw_line in text.split("\n"):
        line = " ".join(raw_line.split())
        if not line:
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        if _RULE_START.match(line) and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def _rule_units(chunks: list[Chunk]) -> tuple[list[_Unit], bool]:
    units: list[_Unit] = []
    current: _Unit | None = None
    found_boundary = False
    current_doc = ""
    for chunk in chunks:
        if chunk.doc_id != current_doc:
            current = None
            current_doc = chunk.doc_id
        is_table = chunk.id.endswith("_table")
        is_heading = chunk.id.endswith("_heading")
        for paragraph in _paragraphs(chunk):
            match = _RULE_START.match(paragraph)
            starts_unit = bool(match) or is_heading or is_table
            found_boundary = found_boundary or starts_unit
            if starts_unit or current is None or current.table:
                label = match.group(0).strip() if match else paragraph.split("\n", 1)[0]
                current = _Unit(
                    text=paragraph,
                    page_ids=list(chunk.page_ids),
                    label=label,
                    table=is_table,
                )
                units.append(current)
            else:
                current.text = f"{current.text}\n\n{paragraph}"
                current.page_ids = _ordered_union([current.page_ids, chunk.page_ids])
    return units, found_boundary


def _split_unit(unit: _Unit, size: int, overlap: int) -> list[tuple[str, list[str]]]:
    tokens = _tokens(unit.text, unit.page_ids)
    if len(tokens) <= size:
        return [(unit.text.strip(), list(unit.page_ids))] if tokens else []

    prefix = _tokens(unit.label, unit.page_ids) if unit.label else []
    body_size = size - len(prefix)
    if body_size < max(1, size // 2):
        prefix = []
        body_size = size
    body_overlap = min(overlap, body_size - 1)
    pieces = _windows(tokens, body_size, body_overlap)
    output: list[tuple[str, list[str]]] = []
    for index, (text, pages) in enumerate(pieces):
        if index and prefix:
            text = " ".join(token.value for token in prefix) + " [চলমান] " + text
            pages = _ordered_union([list(unit.page_ids), pages])
        output.append((text, pages))
    return output


def split(chunks: list[Chunk], cfg: dict) -> list[Chunk]:
    """Create deterministic retrieval chunks while retaining source-page provenance."""

    if not chunks:
        return []
    index_cfg = cfg.get("index", {})
    size, overlap = _validate(index_cfg)
    rule_aware = bool(index_cfg.get("rule_aware", False))

    records: list[tuple[str, str, list[str]]] = []
    if not rule_aware:
        records = _fixed(chunks, size, overlap)
    else:
        by_document: OrderedDict[str, list[Chunk]] = OrderedDict()
        for chunk in chunks:
            by_document.setdefault(chunk.doc_id, []).append(chunk)
        for doc_id, document_chunks in by_document.items():
            units, found_boundary = _rule_units(document_chunks)
            if not found_boundary:
                records.extend(_fixed(document_chunks, size, overlap))
                continue
            for unit in units:
                records.extend(
                    (doc_id, text, pages) for text, pages in _split_unit(unit, size, overlap)
                )

    counters: dict[str, int] = {}
    output: list[Chunk] = []
    for doc_id, text, page_ids in records:
        if not text.strip():
            continue
        counters[doc_id] = counters.get(doc_id, 0) + 1
        output.append(
            Chunk(
                id=f"{doc_id}_c{counters[doc_id]:06d}",
                doc_id=doc_id,
                text=unicodedata.normalize("NFC", text.strip()),
                page_ids=list(dict.fromkeys(page_ids)),
            )
        )
    return output
