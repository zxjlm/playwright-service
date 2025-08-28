#!/bin/bash

cd /app
uv run --no-dev alembic upgrade head
mkdir -p /var/log/pr-service
uv run --no-dev gunicorn main:app --config gunicorn.config.py