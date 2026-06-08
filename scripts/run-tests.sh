#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${DB_HOST:-}" && -n "${DB_PORT:-}" ]]; then
  echo "[run-tests] Waiting for Postgres at $DB_HOST:$DB_PORT..."
  for i in {1..60}; do
    nc -z "$DB_HOST" "$DB_PORT" && break
    sleep 1
  done
fi

if [[ -n "${REDIS_HOST:-}" && -n "${REDIS_PORT:-}" ]]; then
  echo "[run-tests] Waiting for Redis at $REDIS_HOST:$REDIS_PORT..."
  for i in {1..60}; do
    nc -z "$REDIS_HOST" "$REDIS_PORT" && break
    sleep 1
  done
fi

if [[ "${RUN_MIGRATIONS:-0}" == "1" ]]; then
  uv run python scripts/run_migrations.py
elif [[ "${WAIT_FOR_MIGRATIONS:-0}" == "1" ]]; then
  uv run python scripts/wait_for_migrations.py
fi

exec uv run pytest "$@"
