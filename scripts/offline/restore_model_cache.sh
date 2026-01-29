set -euo pipefail

ARCHIVE=${1:-dist/evalvault_model_cache.tar}
TARGET_DIR=${TARGET_DIR:-model_cache}

if [ ! -f "$ARCHIVE" ]; then
  echo "Archive not found: $ARCHIVE" >&2
  exit 1
fi

if [ -f "${ARCHIVE}.sha256" ]; then
  sha256sum -c "${ARCHIVE}.sha256"
fi

mkdir -p "$TARGET_DIR"
tar -xf "$ARCHIVE" -C "$(dirname "$TARGET_DIR")"
echo "Restored model cache to $(dirname "$TARGET_DIR")"
