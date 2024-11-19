#! /usr/bin/env sh

export $(/env.sh)

/opt/venv/bin/taskiq worker core.broker:broker modules.tasks
