FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /opt/
COPY ./pyproject.toml ./uv.lock ./

RUN --mount=type=ssh uv venv \
    && uv sync --frozen


FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PATH="/opt/venv/bin:$PATH"

COPY ./src /app
COPY --from=builder /opt/.venv /opt/venv

COPY ./scripts/*.sh /
RUN chmod +x /*.sh

WORKDIR /app

ENTRYPOINT ["uv", "run", "-m"]
