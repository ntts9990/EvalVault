#!/usr/bin/env bash
set -euo pipefail

PHOENIX_IMAGE="${PHOENIX_IMAGE:-arizephoenix/phoenix:latest}"
PHOENIX_CONTAINER_NAME="${PHOENIX_CONTAINER_NAME:-evalvault-phoenix}"
PHOENIX_PORT="${PHOENIX_PORT:-6006}"
started_phoenix=0

if command -v docker >/dev/null 2>&1; then
    if docker ps --format '{{.Names}}' | grep -q "^${PHOENIX_CONTAINER_NAME}$"; then
        echo "Phoenix already running: http://localhost:${PHOENIX_PORT}"
    else
        if docker ps -a --format '{{.Names}}' | grep -q "^${PHOENIX_CONTAINER_NAME}$"; then
            docker start "${PHOENIX_CONTAINER_NAME}" >/dev/null
        else
            docker run -d --rm --name "${PHOENIX_CONTAINER_NAME}" \
                -p "${PHOENIX_PORT}:6006" "${PHOENIX_IMAGE}" >/dev/null
        fi
        started_phoenix=1
        echo "Phoenix UI: http://localhost:${PHOENIX_PORT}"
    fi
else
    echo "Docker not found; skipping Phoenix startup."
fi

cleanup() {
    if [ -n "${api_pid:-}" ]; then
        kill "${api_pid}" 2>/dev/null || true
    fi
    if [ -n "${frontend_pid:-}" ]; then
        kill "${frontend_pid}" 2>/dev/null || true
    fi
    if [ "${started_phoenix}" -eq 1 ] && command -v docker >/dev/null 2>&1; then
        docker stop "${PHOENIX_CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
}

trap cleanup INT TERM EXIT

uv run evalvault serve-api --reload &
api_pid=$!

(cd frontend && npm run dev) &
frontend_pid=$!

wait "${api_pid}"
