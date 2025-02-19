#! /usr/bin/env sh

uv run --directory src taskiq scheduler core.broker:scheduler modules.tasks
