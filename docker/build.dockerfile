FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

COPY ./scripts/*.sh /
RUN chmod +x /*.sh

WORKDIR /app

COPY ./pyproject.toml ./
COPY ./uv.lock ./

RUN uv venv && uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 80

CMD ["uv", "run", "src/main.py"]
