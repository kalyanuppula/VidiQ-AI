FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --no-install-project

COPY backend ./backend

ENV PYTHONPATH=/app/backend
ENV PORT=8000

CMD ["sh", "-c", "uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]