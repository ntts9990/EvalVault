#!/usr/bin/env bash
set -euo pipefail

ARCHIVE=${1:-dist/evalvault_offline.tar}

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE" >&2
  exit 1
fi

if [ -f "${ARCHIVE}.sha256" ]; then
  sha256sum -c "${ARCHIVE}.sha256"
fi

docker load -i "$ARCHIVE"
echo "Loaded: $ARCHIVE"
