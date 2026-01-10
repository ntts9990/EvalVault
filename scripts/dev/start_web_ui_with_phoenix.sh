#!/usr/bin/env bash
set -euo pipefail

PHOENIX_IMAGE="${PHOENIX_IMAGE:-arizephoenix/phoenix:latest}"
PHOENIX_CONTAINER_NAME="${PHOENIX_CONTAINER_NAME:-evalvault-phoenix}"
PHOENIX_PORT="${PHOENIX_PORT:-6006}"
PHOENIX_OTLP_ENDPOINT="${PHOENIX_OTLP_ENDPOINT:-http://host.docker.internal:${PHOENIX_PORT}}"

OTEL_COLLECTOR_IMAGE="${OTEL_COLLECTOR_IMAGE:-otel/opentelemetry-collector:latest}"
OTEL_COLLECTOR_CONTAINER_NAME="${OTEL_COLLECTOR_CONTAINER_NAME:-evalvault-otel-collector}"
OTEL_COLLECTOR_GRPC_PORT="${OTEL_COLLECTOR_GRPC_PORT:-4317}"
OTEL_COLLECTOR_HTTP_PORT="${OTEL_COLLECTOR_HTTP_PORT:-4318}"
OTEL_COLLECTOR_CONFIG="${OTEL_COLLECTOR_CONFIG:-$(pwd)/scripts/dev/otel-collector-config.yaml}"

started_phoenix=0
started_collector=0

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

    if [ -f "${OTEL_COLLECTOR_CONFIG}" ]; then
        if docker ps --format '{{.Names}}' | grep -q "^${OTEL_COLLECTOR_CONTAINER_NAME}$"; then
            echo "OTel Collector already running: http://localhost:${OTEL_COLLECTOR_HTTP_PORT}/v1/traces"
        else
            if docker ps -a --format '{{.Names}}' | grep -q "^${OTEL_COLLECTOR_CONTAINER_NAME}$"; then
                docker start "${OTEL_COLLECTOR_CONTAINER_NAME}" >/dev/null
            else
                docker run -d --rm --name "${OTEL_COLLECTOR_CONTAINER_NAME}" \
                    -p "${OTEL_COLLECTOR_GRPC_PORT}:4317" \
                    -p "${OTEL_COLLECTOR_HTTP_PORT}:4318" \
                    -e PHOENIX_OTLP_ENDPOINT="${PHOENIX_OTLP_ENDPOINT}" \
                    -v "${OTEL_COLLECTOR_CONFIG}:/etc/otelcol/config.yaml:ro" \
                    "${OTEL_COLLECTOR_IMAGE}" \
                    --config=/etc/otelcol/config.yaml >/dev/null
            fi
            started_collector=1
            echo "OTel Collector: http://localhost:${OTEL_COLLECTOR_HTTP_PORT}/v1/traces"
        fi
    else
        echo "Collector config not found; skipping OTel Collector startup."
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
    if [ "${started_collector}" -eq 1 ] && command -v docker >/dev/null 2>&1; then
        docker stop "${OTEL_COLLECTOR_CONTAINER_NAME}" >/dev/null 2>&1 || true
    fi
}

trap cleanup INT TERM EXIT

uv run evalvault serve-api --reload &
api_pid=$!

(cd frontend && npm run dev) &
frontend_pid=$!

wait "${api_pid}"
