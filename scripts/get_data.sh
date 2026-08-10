#!/usr/bin/env bash
# Prepare the Team 20 BMA corpus as page images.
#
# Kaggle (preferred): attach the private bma-corpus dataset, then run
#   BMA_CORPUS_DIR=/kaggle/input/datasets/fahimishtiak/bma-corpus \
#     bash scripts/get_data.sh
#
# Fast Phase 1 inventory without rendering all pages:
#   BMA_INVENTORY_ONLY=1 bash scripts/get_data.sh
#
# Small development render (first 10 pages per document):
#   BMA_MAX_PAGES=10 bash scripts/get_data.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT_DIR="${BMA_CORPUS_DIR:-/kaggle/input/datasets/fahimishtiak/bma-corpus}"
RAW_DIR="${BMA_RAW_DIR:-${REPO_ROOT}/data/raw}"
INTERIM_DIR="${BMA_INTERIM_DIR:-${REPO_ROOT}/data/interim}"
CACHE_DIR="${BMA_SOURCE_CACHE:-/kaggle/working/bma-source-cache}"
RENDER_DPI="${BMA_RENDER_DPI:-300}"
MAX_PAGES="${BMA_MAX_PAGES:-0}"
INVENTORY_ONLY="${BMA_INVENTORY_ONLY:-0}"

BHASHA_NAME="bhasha_prakash_1942.pdf"
NCTB_NAME="nctb_bangla_grammar.pdf"
BHASHA_SHA256="2e6a6e08e942d91e0986e2282ddeec9e6b4882ac6f4b89e083bf9bab6e72d39b"
NCTB_SHA256="3cb900fb1ce51bb91e13e41d43c51d98260a29ffffbed5632b0adee130640086"
BHASHA_URL="https://archive.org/download/in.ernet.dli.2015.457377/2015.457377.Bhasha-prakash-Bangala.pdf"

mkdir -p "$RAW_DIR" "$INTERIM_DIR" "$CACHE_DIR"

BHASHA_PDF="${BMA_BHASHA_PDF:-${INPUT_DIR}/${BHASHA_NAME}}"
NCTB_PDF="${BMA_NCTB_PDF:-${INPUT_DIR}/${NCTB_NAME}}"

if [[ ! -f "$BHASHA_PDF" ]]; then
  BHASHA_PDF="${CACHE_DIR}/${BHASHA_NAME}"
  if [[ ! -f "$BHASHA_PDF" ]]; then
    echo "Downloading the declared 1942 source from Internet Archive..."
    curl --fail --location --retry 3 --output "$BHASHA_PDF" "$BHASHA_URL"
  fi
fi

if [[ ! -f "$NCTB_PDF" ]]; then
  if [[ -n "${BMA_NCTB_URL:-}" ]]; then
    NCTB_PDF="${CACHE_DIR}/${NCTB_NAME}"
    echo "Downloading the declared 2026 NCTB source from BMA_NCTB_URL..."
    curl --fail --location --retry 3 --output "$NCTB_PDF" "$BMA_NCTB_URL"
  else
    echo "ERROR: 2026 NCTB PDF not found at: ${NCTB_PDF}" >&2
    echo "Attach the private Kaggle dataset, set BMA_CORPUS_DIR, set BMA_NCTB_PDF," >&2
    echo "or provide the original public URL through BMA_NCTB_URL." >&2
    exit 2
  fi
fi

verify_sha256() {
  local file="$1"
  local expected="$2"
  local actual
  actual="$(sha256sum "$file" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "ERROR: SHA-256 mismatch for ${file}" >&2
    echo "Expected: ${expected}" >&2
    echo "Actual:   ${actual}" >&2
    exit 3
  fi
  echo "Verified: ${file}"
}

verify_sha256 "$BHASHA_PDF" "$BHASHA_SHA256"
verify_sha256 "$NCTB_PDF" "$NCTB_SHA256"

export BMA_REPO_ROOT="$REPO_ROOT"
export BMA_RAW_DIR="$RAW_DIR"
export BMA_INTERIM_DIR="$INTERIM_DIR"
export BMA_BHASHA_PDF="$BHASHA_PDF"
export BMA_NCTB_PDF="$NCTB_PDF"
export BMA_RENDER_DPI="$RENDER_DPI"
export BMA_MAX_PAGES="$MAX_PAGES"
export BMA_INVENTORY_ONLY="$INVENTORY_ONLY"

python - <<'PY'
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import fitz
except ImportError as exc:
    raise SystemExit(
        "PyMuPDF is required. Install the repository dependencies before running get_data.sh."
    ) from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


raw_dir = Path(os.environ["BMA_RAW_DIR"])
interim_dir = Path(os.environ["BMA_INTERIM_DIR"])
dpi = int(os.environ["BMA_RENDER_DPI"])
max_pages = int(os.environ["BMA_MAX_PAGES"])
inventory_only = os.environ["BMA_INVENTORY_ONLY"] == "1"

documents = [
    {
        "doc_id": "bhasha_prakash_1942",
        "path": Path(os.environ["BMA_BHASHA_PDF"]),
        "expected_pages": 565,
        "split": "train",
    },
    {
        "doc_id": "nctb_bangla_grammar_2026",
        "path": Path(os.environ["BMA_NCTB_PDF"]),
        "expected_pages": 218,
        "split": "test",
    },
]

inventory = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "render_dpi": dpi,
    "inventory_only": inventory_only,
    "documents": [],
}

for spec in documents:
    source_path = spec["path"]
    output_dir = raw_dir / spec["doc_id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    with fitz.open(source_path) as pdf:
        page_count = len(pdf)
        if page_count != spec["expected_pages"]:
            raise RuntimeError(
                f"{spec['doc_id']} has {page_count} pages; expected {spec['expected_pages']}"
            )

        render_count = page_count if max_pages <= 0 else min(page_count, max_pages)
        rendered = 0
        if not inventory_only:
            for page_index in range(render_count):
                output_path = output_dir / f"page_{page_index + 1:04d}.png"
                if not output_path.exists():
                    page = pdf.load_page(page_index)
                    pixmap = page.get_pixmap(dpi=dpi, colorspace=fitz.csGRAY, alpha=False)
                    pixmap.save(output_path)
                rendered += 1

        first_page = pdf.load_page(0)
        inventory["documents"].append(
            {
                "doc_id": spec["doc_id"],
                "source_path": str(source_path),
                "source_filename": source_path.name,
                "sha256": sha256(source_path),
                "bytes": source_path.stat().st_size,
                "pages": page_count,
                "split": spec["split"],
                "first_page_size_points": [first_page.rect.width, first_page.rect.height],
                "rendered_pages": rendered,
                "output_dir": str(output_dir),
                "page_id_example": f"{spec['doc_id']}_p0001",
            }
        )

inventory["total_pages"] = sum(item["pages"] for item in inventory["documents"])
inventory["total_bytes"] = sum(item["bytes"] for item in inventory["documents"])

inventory_path = interim_dir / "corpus_inventory.json"
inventory_path.write_text(
    json.dumps(inventory, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(json.dumps(inventory, ensure_ascii=False, indent=2))
print(f"Corpus inventory written to {inventory_path}")
PY

echo "BMA corpus preparation complete."
