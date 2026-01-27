#!/usr/bin/env bash
set -euo pipefail

ARCHIVE=${1:-dist/evalvault_datasets.tar}

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE" >&2
  exit 1
fi

if [ -f "${ARCHIVE}.sha256" ]; then
  sha256sum -c "${ARCHIVE}.sha256"
fi

tar -xf "$ARCHIVE"
echo "Restored dataset assets from $ARCHIVE"
