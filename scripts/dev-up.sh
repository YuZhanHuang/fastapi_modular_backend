#!/usr/bin/env bash
set -euo pipefail

docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
echo "API:    http://localhost:8000/docs"
echo "Flower: http://localhost:5555"


