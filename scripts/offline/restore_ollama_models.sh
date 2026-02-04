#!/usr/bin/env bash
set -euo pipefail

# Restore Ollama model store from tar archive.
# Usage:
#   OLLAMA_MODELS_DIR=/var/lib/ollama ./scripts/offline/restore_ollama_models.sh dist/ollama_models.tar

ARCHIVE=${1:-dist/ollama_models.tar}

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE" >&2
  exit 1
fi

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

mkdir -p "$OLLAMA_MODELS_DIR"

if [ -f "${ARCHIVE}.sha256" ]; then
  if command -v sha256sum &>/dev/null; then
    sha256sum -c "${ARCHIVE}.sha256"
  elif command -v shasum &>/dev/null; then
    shasum -a 256 -c "${ARCHIVE}.sha256"
  fi
fi

tar -xf "$ARCHIVE" -C "$OLLAMA_MODELS_DIR"
echo "Restored Ollama models to: $OLLAMA_MODELS_DIR"
