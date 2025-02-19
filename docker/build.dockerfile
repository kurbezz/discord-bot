FROM ghcr.io/astral-sh/uv:python3.12-slim

COPY ./scripts/*.sh /
RUN chmod +x /*.sh

WORKDIR /app

COPY ./pyproject.toml ./
COPY ./uv.lock ./

RUN uv env && uv sync

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 80

CMD ["uv", "run", "src/main.py"]
