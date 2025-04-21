FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app
COPY ./pyproject.toml ./uv.lock ./

RUN --mount=type=ssh uv venv \
    && uv sync --frozen

COPY ./src /app/src

WORKDIR /app/src
