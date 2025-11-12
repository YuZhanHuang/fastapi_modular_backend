FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Install project dependencies (runtime only)
RUN uv sync --frozen --no-dev

# Copy app source & alembic config
COPY src ./src
COPY alembic.ini ./

# Copy shared entrypoint with execute permission
COPY --chmod=755 docker/app/entrypoint.sh /entrypoint.sh

# Create non-root user and fix ownership
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONPATH=/app/src

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]


