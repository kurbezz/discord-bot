#! /usr/bin/env sh

export $(/env.sh)

/opt/venv/bin/taskiq scheduler core.broker:scheduler modules.tasks
