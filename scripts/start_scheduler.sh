#! /usr/bin/env sh

uv run taskiq scheduler core.broker:scheduler modules.tasks
