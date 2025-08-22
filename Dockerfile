FROM playwright-py:v1.47.0-noble

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY ./pyproject.toml ./uv.lock  /app/

RUN pip install --no-cache-dir uv -i https://mirrors.aliyun.com/pypi/simple/ && \
    uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv sync --no-cache --no-dev

COPY ./ /app

CMD ["gunicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
