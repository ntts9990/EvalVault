#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

OUTPUT_TAR=${OUTPUT_TAR:-dist/evalvault_offline.tar}
INCLUDE_POSTGRES=${INCLUDE_POSTGRES:-0}

IMAGES=(
  "evalvault-api:offline"
  "evalvault-web:offline"
)

if [ "$INCLUDE_POSTGRES" = "1" ]; then
  IMAGES+=("postgres:16-alpine")
fi

docker compose -f docker-compose.offline.yml build

mkdir -p "$(dirname "$OUTPUT_TAR")"
docker save -o "$OUTPUT_TAR" "${IMAGES[@]}"
sha256sum "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"

echo "Saved: $OUTPUT_TAR"
echo "SHA256: ${OUTPUT_TAR}.sha256"
