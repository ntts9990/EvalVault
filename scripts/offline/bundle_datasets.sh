#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

OUTPUT_TAR=${OUTPUT_TAR:-dist/evalvault_datasets.tar}
INCLUDE_DATA=${INCLUDE_DATA:-1}
INCLUDE_FIXTURES=${INCLUDE_FIXTURES:-1}
INCLUDE_TEMPLATES=${INCLUDE_TEMPLATES:-1}

ITEMS=()

if [ "$INCLUDE_DATA" = "1" ] && [ -d "data" ]; then
  ITEMS+=("data")
fi
if [ "$INCLUDE_FIXTURES" = "1" ] && [ -d "tests/fixtures" ]; then
  ITEMS+=("tests/fixtures")
fi
if [ "$INCLUDE_TEMPLATES" = "1" ] && [ -d "dataset_templates" ]; then
  ITEMS+=("dataset_templates")
fi

if [ ${#ITEMS[@]} -eq 0 ]; then
  echo "No dataset assets to bundle." >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_TAR")"
tar -cf "$OUTPUT_TAR" "${ITEMS[@]}"
sha256sum "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"

echo "Saved: $OUTPUT_TAR"
echo "SHA256: ${OUTPUT_TAR}.sha256"
