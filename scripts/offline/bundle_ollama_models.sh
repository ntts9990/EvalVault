#!/usr/bin/env bash
set -euo pipefail

# Bundle Ollama model store for air-gapped transfer.
# Usage:
#   OLLAMA_MODELS_DIR=/var/lib/ollama ./scripts/offline/bundle_ollama_models.sh
#   OUTPUT_TAR=dist/ollama_models.tar ./scripts/offline/bundle_ollama_models.sh

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

OUTPUT_TAR=${OUTPUT_TAR:-dist/ollama_models.tar}

if [ -z "${OLLAMA_MODELS_DIR:-}" ]; then
  if [ -d /var/lib/ollama ]; then
    OLLAMA_MODELS_DIR=/var/lib/ollama
  elif [ -d "$HOME/.ollama" ]; then
    OLLAMA_MODELS_DIR="$HOME/.ollama"
  else
    echo "OLLAMA_MODELS_DIR not set and default locations not found." >&2
    echo "Set OLLAMA_MODELS_DIR to your Ollama data directory." >&2
    exit 1
  fi
fi

if [ ! -d "$OLLAMA_MODELS_DIR" ]; then
  echo "Ollama models directory not found: $OLLAMA_MODELS_DIR" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_TAR")"

echo "Bundling Ollama models from: $OLLAMA_MODELS_DIR"
tar -cf "$OUTPUT_TAR" -C "$OLLAMA_MODELS_DIR" .

if command -v sha256sum &>/dev/null; then
  sha256sum "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"
elif command -v shasum &>/dev/null; then
  shasum -a 256 "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"
fi

echo "Saved: $OUTPUT_TAR"
echo "SHA256: ${OUTPUT_TAR}.sha256"
