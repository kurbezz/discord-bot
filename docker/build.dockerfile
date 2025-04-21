FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /opt/
COPY ./pyproject.toml ./uv.lock ./

RUN --mount=type=ssh uv venv \
    && uv sync --frozen


FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY ./src ./src
COPY ./pyproject.toml ./uv.lock ./

COPY --from=builder /opt/.venv /opt/venv

ENTRYPOINT ["uv", "run", "-m"]
