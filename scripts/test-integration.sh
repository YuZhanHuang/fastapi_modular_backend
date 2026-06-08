#!/usr/bin/env bash
set -euo pipefail

docker compose -f docker-compose.yml -f docker-compose.test.yml \
  --profile integration run --rm test-integration "$@"
