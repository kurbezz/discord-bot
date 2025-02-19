#! /usr/bin/env sh

uv run --directory src taskiq worker core.broker:broker modules.tasks
