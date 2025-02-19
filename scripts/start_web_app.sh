#! /usr/bin/env sh

uv run --directory src uvicorn modules.web_app.app:app --host 0.0.0.0 --port 80
