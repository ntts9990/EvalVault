#!/usr/bin/env bash
set -euo pipefail

# Find archive: use argument, or auto-detect in current directory
if [ -n "${1:-}" ]; then
  ARCHIVE="$1"
elif ls evalvault_offline_*.tar 1>/dev/null 2>&1; then
  ARCHIVE=$(ls -t evalvault_offline_*.tar | head -1)
  echo "Auto-detected: $ARCHIVE"
else
  ARCHIVE="dist/evalvault_offline.tar"
fi

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE" >&2
  echo "Usage: $0 [archive.tar]" >&2
  exit 1
fi

# Verify checksum if available (cross-platform)
if [ -f "${ARCHIVE}.sha256" ]; then
  if command -v sha256sum &>/dev/null; then
    sha256sum -c "${ARCHIVE}.sha256"
  elif command -v shasum &>/dev/null; then
    shasum -a 256 -c "${ARCHIVE}.sha256"
  else
    echo "Warning: sha256sum not found, skipping checksum verification"
  fi
fi

docker load -i "$ARCHIVE"
echo "Loaded: $ARCHIVE"
