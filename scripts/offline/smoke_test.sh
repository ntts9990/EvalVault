#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=${ENV_FILE:-.env.offline}

if [ ! -f "$ENV_FILE" ]; then
  echo "Env file not found: $ENV_FILE" >&2
  exit 1
fi

docker compose --env-file "$ENV_FILE" -f docker-compose.offline.yml up -d

curl -fsS http://localhost:8000/health >/dev/null
curl -fsS http://localhost:8080/ >/dev/null

echo "Smoke test passed"
