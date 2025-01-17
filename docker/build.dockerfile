FROM python:3.12-slim AS build

ARG POETRY_EXPORT_EXTRA_ARGS=''

WORKDIR /opt/venv
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip && /opt/venv/bin/pip install --no-cache-dir httpx poetry poetry-plugin-export

COPY ./pyproject.toml ./poetry.lock ./
RUN --mount=type=ssh /opt/venv/bin/poetry export --without-hashes ${POETRY_EXPORT_EXTRA_ARGS} > requirements.txt \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


FROM python:3.12-slim AS runtime

RUN apt update && \
    apt install -y --no-install-recommends curl jq && \
    apt clean

COPY ./src/ /app

COPY ./scripts/*.sh /
RUN chmod +x /*.sh

ENV PATH="/opt/venv/bin:$PATH"
ENV VENV_PATH=/opt/venv

COPY --from=build /opt/venv /opt/venv

WORKDIR /app

EXPOSE 80

CMD ["python", "main.py"]
