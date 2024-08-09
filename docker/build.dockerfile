FROM python:3.12-slim AS build

ARG POETRY_EXPORT_EXTRA_ARGS=''

WORKDIR /opt/venv
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --upgrade pip && /opt/venv/bin/pip install --no-cache-dir httpx poetry

COPY ./pyproject.toml ./poetry.lock ./
RUN --mount=type=ssh /opt/venv/bin/poetry export --without-hashes --with app ${POETRY_EXPORT_EXTRA_ARGS} > requirements.txt \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


FROM python:3.11-slim AS runtime

RUN apt update && apt install -y --no-install-recommends netcat-traditional wkhtmltopdf && apt clean

COPY ./src/ /app

ENV PATH="/opt/venv/bin:$PATH"
ENV VENV_PATH=/opt/venv

COPY --from=build /opt/venv /opt/venv

WORKDIR /app

EXPOSE 80

CMD ["python", "/app/main.py"]
