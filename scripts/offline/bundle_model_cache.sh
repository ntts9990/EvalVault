set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

OUTPUT_TAR=${OUTPUT_TAR:-dist/evalvault_model_cache.tar}
CACHE_ROOT=${CACHE_ROOT:-model_cache}
MODELS=${MODELS:-}
INCLUDE_KIWI=${INCLUDE_KIWI:-1}
SKIP_ST=${SKIP_ST:-0}

ARGS=("--cache-root" "$CACHE_ROOT")
if [ -n "$MODELS" ]; then
  ARGS+=("--models" "$MODELS")
fi
if [ "$SKIP_ST" = "1" ]; then
  ARGS+=("--skip-sentence-transformers")
fi
if [ "$INCLUDE_KIWI" = "1" ]; then
  ARGS+=("--include-kiwi")
fi

uv run python scripts/offline/predownload_nlp_models.py "${ARGS[@]}"

# Kiwi cache is stored under ~/.kiwipiepy; copy if present
if [ -d "$HOME/.kiwipiepy" ]; then
  mkdir -p "$CACHE_ROOT"
  rm -rf "$CACHE_ROOT/kiwipiepy"
  cp -R "$HOME/.kiwipiepy" "$CACHE_ROOT/kiwipiepy"
fi

mkdir -p "$(dirname "$OUTPUT_TAR")"
tar -cf "$OUTPUT_TAR" "$CACHE_ROOT"
sha256sum "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"

echo "Saved: $OUTPUT_TAR"
echo "SHA256: ${OUTPUT_TAR}.sha256"
