# syntax=docker/dockerfile:1.4
FROM mcr.microsoft.com/playwright/python:v1.54.0-noble
# build from Dockerfile.playwright

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install uv - this layer rarely changes
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install uv -i https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app

# Copy dependency files first for better layer caching
COPY ./pyproject.toml ./uv.lock /app/

# Install Python dependencies with cache mount
# Cache is preserved across builds even when uv.lock changes
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# Install patchright browser with cache mount
# Browser binaries cache is preserved across builds
RUN --mount=type=cache,target=/root/.cache/ms-playwright \
    uv run patchright install-deps && uv run patchright install

# Copy application code last - this layer changes most frequently
COPY ./ /app

CMD ["gunicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
