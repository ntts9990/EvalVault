#!/usr/bin/env bash
set -euo pipefail

# Bundle vLLM model weights for air-gapped transfer.
# Usage:
#   VLLM_MODEL_DIR=/data/vllm/models ./scripts/offline/bundle_vllm_models.sh
#   OUTPUT_TAR=dist/vllm_models.tar ./scripts/offline/bundle_vllm_models.sh

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

OUTPUT_TAR=${OUTPUT_TAR:-dist/vllm_models.tar}

if [ -z "${VLLM_MODEL_DIR:-}" ]; then
  echo "VLLM_MODEL_DIR is required (path to vLLM model weights)." >&2
  exit 1
fi

if [ ! -d "$VLLM_MODEL_DIR" ]; then
  echo "vLLM model directory not found: $VLLM_MODEL_DIR" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_TAR")"

echo "Bundling vLLM models from: $VLLM_MODEL_DIR"
tar -cf "$OUTPUT_TAR" -C "$VLLM_MODEL_DIR" .

if command -v sha256sum &>/dev/null; then
  sha256sum "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"
elif command -v shasum &>/dev/null; then
  shasum -a 256 "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"
fi

echo "Saved: $OUTPUT_TAR"
echo "SHA256: ${OUTPUT_TAR}.sha256"
