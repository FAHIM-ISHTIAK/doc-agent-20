FROM ghcr.io/astral-sh/uv:0.12.3 AS uv

FROM python:3.12-slim
WORKDIR /app
COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY . .
RUN uv sync --locked --no-dev
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "doc_agent.serve.api:app", "--host", "0.0.0.0", "--port", "8000"]
