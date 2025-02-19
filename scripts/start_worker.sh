#! /usr/bin/env sh

cd ./src

uv run --directory src taskiq worker core.broker:broker modules.tasks
