#!/bin/bash

cd /app
uv run --no-dev alembic upgrade head
uv run --no-dev gunicorn main:app --config gunicorn.config.py