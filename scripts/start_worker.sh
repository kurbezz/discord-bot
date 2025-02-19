#! /usr/bin/env sh

uv run taskiq worker core.broker:broker modules.tasks
