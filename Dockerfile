FROM mcr.microsoft.com/playwright/python:v1.54.0-noble
# build from Dockerfile.playwright

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install --no-cache-dir uv -i https://mirrors.aliyun.com/pypi/simple/

WORKDIR /app
COPY ./pyproject.toml ./uv.lock  /app/

RUN uv sync --no-cache --no-dev
RUN uv run patchright install-deps && uv run patchright install

COPY ./ /app

CMD ["gunicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
