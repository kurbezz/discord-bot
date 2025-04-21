FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /opt/
COPY ./pyproject.toml ./uv.lock ./

RUN --mount=type=ssh uv venv \
    && uv sync --frozen


FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

COPY --from=builder /opt/.venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY ./src /app/src
COPY ./pyproject.toml ./uv.lock /app/

WORKDIR /app/src
