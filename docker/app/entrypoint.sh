#!/usr/bin/env bash
set -euo pipefail

# 等待 Postgres
if [[ -n "${DB_HOST:-}" && -n "${DB_PORT:-}" ]]; then
  echo "[entrypoint] Waiting for Postgres at $DB_HOST:$DB_PORT..."
  for i in {1..60}; do
    nc -z "$DB_HOST" "$DB_PORT" && break
    sleep 1
  done
fi

# 等待 Redis (作為 cache / broker)
if [[ -n "${REDIS_HOST:-}" && -n "${REDIS_PORT:-}" ]]; then
  echo "[entrypoint] Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
  for i in {1..60}; do
    nc -z "$REDIS_HOST" "$REDIS_PORT" && break
    sleep 1
  done
fi

# DB migration
if [[ "${RUN_MIGRATIONS:-1}" == "1" ]]; then
  echo "[entrypoint] Running alembic migrations..."
  uv run alembic upgrade head
fi

# 根據角色啟動對應服務
case "${SERVICE_ROLE:-api}" in
  api)
    echo "[entrypoint] Starting API..."
    exec uv run uvicorn app.application.app:app --host 0.0.0.0 --port 8000
    ;;
  worker)
    echo "[entrypoint] Starting Celery worker..."
    exec uv run celery -A app.worker.celery_app.celery worker -l info
    ;;
  beat)
    echo "[entrypoint] Starting Celery beat (DB scheduler)..."
    exec uv run celery -A app.worker.celery_app.celery beat \
      -S celery_sqlalchemy_scheduler.schedulers:DatabaseScheduler \
      -l info
    ;;
  flower)
    echo "[entrypoint] Starting Flower..."
    exec uv run celery -A app.worker.celery_app.celery flower \
      --port=5555
    ;;
  *)
    echo "[entrypoint] Unknown SERVICE_ROLE: ${SERVICE_ROLE}"
    exit 1
    ;;
esac


