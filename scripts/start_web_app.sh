#! /usr/bin/env sh

/opt/venv/bin/uvicorn modules.web_app.app:app --host 0.0.0.0 --port 80
