#!/usr/bin/env bash
set -euo pipefail

docker compose build
docker compose up -d
echo "API:    http://localhost:8000/docs"
echo "Flower: http://localhost:5555"


