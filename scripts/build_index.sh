#!/usr/bin/env bash
# A2 — build the vector index once through the fixed end-to-end pipeline.
set -euo pipefail
python scripts/run_index.py
