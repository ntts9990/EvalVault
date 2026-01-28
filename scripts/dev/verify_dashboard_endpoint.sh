#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://127.0.0.1:8001/api/v1}"
RUN_ID="${1:-}"
PORT="${API_PORT:-8001}"
HOST="${API_HOST:-127.0.0.1}"
OUTPUT_PATH="${OUTPUT_PATH:-/tmp/evalvault_dashboard.png}"
START_API="${START_API:-auto}"

usage() {
  echo "Usage: $0 [run_id]"
  echo "Environment variables:"
  echo "  API_BASE_URL (default: http://127.0.0.1:8001/api/v1)"
  echo "  API_HOST (default: 127.0.0.1)"
  echo "  API_PORT (default: 8001)"
  echo "  OUTPUT_PATH (default: /tmp/evalvault_dashboard.png)"
  echo "  START_API (auto|true|false, default: auto)"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

API_PID=""
cleanup() {
  if [[ -n "${API_PID}" ]]; then
    kill "${API_PID}" 2>/dev/null || true
    wait "${API_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

probe_api() {
  curl -sS -L --max-time 2 "${API_BASE_URL}/runs" >/dev/null
}

start_api() {
  MPLBACKEND=Agg uv run evalvault serve-api --reload --host "${HOST}" --port "${PORT}" >/tmp/evalvault_api_verify.log 2>&1 &
  API_PID=$!
  sleep 4
}

if [[ "${START_API}" == "true" ]]; then
  start_api
elif [[ "${START_API}" == "false" ]]; then
  :
else
  if ! probe_api; then
    start_api
  fi
fi

if [[ -z "${RUN_ID}" ]]; then
  RUN_ID=$(curl -sS -L "${API_BASE_URL}/runs" | python3 - <<'PY'
import json, sys
data = json.load(sys.stdin)
if not data:
    raise SystemExit(1)
print(data[0].get("run_id", ""))
PY
  )
fi

if [[ -z "${RUN_ID}" ]]; then
  echo "No run_id available." >&2
  exit 1
fi

STATUS=$(curl -sS --max-time 10 -o "${OUTPUT_PATH}" -w "%{http_code}" \
  "${API_BASE_URL}/runs/${RUN_ID}/dashboard?format=png")

if [[ "${STATUS}" != "200" ]]; then
  echo "Dashboard request failed (status=${STATUS})." >&2
  exit 1
fi

SIZE=$(wc -c < "${OUTPUT_PATH}" | tr -d ' ')
if [[ "${SIZE}" -le 0 ]]; then
  echo "Dashboard response empty." >&2
  exit 1
fi

echo "OK: dashboard image saved to ${OUTPUT_PATH} (run_id=${RUN_ID})"
