#! /usr/bin/env sh

export $(/env.sh)

printenv

/opt/venv/bin/taskiq worker core.broker:broker modules.tasks
