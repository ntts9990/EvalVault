#!/usr/bin/env bash
set -euo pipefail

# Restore vLLM model weights from tar archive.
# Usage:
#   VLLM_MODEL_DIR=/data/vllm/models ./scripts/offline/restore_vllm_models.sh dist/vllm_models.tar

ARCHIVE=${1:-dist/vllm_models.tar}

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE" >&2
  exit 1
fi

if [ -z "${VLLM_MODEL_DIR:-}" ]; then
  echo "VLLM_MODEL_DIR is required (target directory for vLLM model weights)." >&2
  exit 1
fi

mkdir -p "$VLLM_MODEL_DIR"

if [ -f "${ARCHIVE}.sha256" ]; then
  if command -v sha256sum &>/dev/null; then
    sha256sum -c "${ARCHIVE}.sha256"
  elif command -v shasum &>/dev/null; then
    shasum -a 256 -c "${ARCHIVE}.sha256"
  fi
fi

tar -xf "$ARCHIVE" -C "$VLLM_MODEL_DIR"
echo "Restored vLLM models to: $VLLM_MODEL_DIR"
