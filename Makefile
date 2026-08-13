.PHONY: setup seed ingest index eval serve test lint
setup:
	uv sync --locked --extra dev
seed:  ; uv run python scripts/set_seed.py
ingest:; uv run python scripts/run_ingest.py
index: ; uv run python scripts/run_index.py
eval:  ; uv run python scripts/run_eval.py
serve: ; uv run uvicorn doc_agent.serve.api:app --host 0.0.0.0 --port 8000
lint:  ; uv run ruff check . && uv run black --check . && uv run mypy src
test:  ; uv run pytest
