#!/usr/bin/env bash
# A2 — build the vector index once through the fixed end-to-end pipeline.
set -euo pipefail

# The submission entry point reproduces the reported full-corpus index unless a
# caller explicitly requests small mode for development.
export DOC_AGENT_RUN_MODE="${DOC_AGENT_RUN_MODE:-full}"

python scripts/run_index.py
