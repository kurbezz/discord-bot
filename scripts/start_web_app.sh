#! /usr/bin/env sh

uv run uvicorn modules.web_app.app:app --host 0.0.0.0 --port 80
