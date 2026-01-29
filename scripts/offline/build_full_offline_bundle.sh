set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

OUTPUT_DIR=${OUTPUT_DIR:-dist/offline_AIA_full}
IMAGES_TAR=${IMAGES_TAR:-dist/evalvault_airgap.tar}
MODELS_TAR=${MODELS_TAR:-dist/evalvault_model_cache.tar}
DATASETS_TAR=${DATASETS_TAR:-}

mkdir -p "$OUTPUT_DIR"

REQUIRED=(
  "$IMAGES_TAR"
  "$IMAGES_TAR.sha256"
  "$MODELS_TAR"
  "$MODELS_TAR.sha256"
  "docker-compose.offline.yml"
  "docker-compose.offline.modelcache.yml"
  ".env.offline.example"
  "scripts/offline/import_images.sh"
  "scripts/offline/smoke_test.sh"
  "scripts/offline/restore_model_cache.sh"
  "docs/guides/OFFLINE_DOCKER.md"
  "docs/guides/OFFLINE_MODELS.md"
)

for item in "${REQUIRED[@]}"; do
  if [ ! -f "$item" ]; then
    echo "Missing required file: $item" >&2
    exit 1
  fi
done

cp "$IMAGES_TAR" "$OUTPUT_DIR/"
cp "$IMAGES_TAR.sha256" "$OUTPUT_DIR/"
cp "$MODELS_TAR" "$OUTPUT_DIR/"
cp "$MODELS_TAR.sha256" "$OUTPUT_DIR/"
cp docker-compose.offline.yml "$OUTPUT_DIR/"
cp docker-compose.offline.modelcache.yml "$OUTPUT_DIR/"
cp .env.offline.example "$OUTPUT_DIR/"
cp scripts/offline/import_images.sh "$OUTPUT_DIR/"
cp scripts/offline/smoke_test.sh "$OUTPUT_DIR/"
cp scripts/offline/restore_model_cache.sh "$OUTPUT_DIR/"
cp docs/guides/OFFLINE_DOCKER.md "$OUTPUT_DIR/"
cp docs/guides/OFFLINE_MODELS.md "$OUTPUT_DIR/"

if [ -n "$DATASETS_TAR" ]; then
  if [ ! -f "$DATASETS_TAR" ]; then
    echo "Dataset archive not found: $DATASETS_TAR" >&2
    exit 1
  fi
  cp "$DATASETS_TAR" "$OUTPUT_DIR/"
  if [ -f "$DATASETS_TAR.sha256" ]; then
    cp "$DATASETS_TAR.sha256" "$OUTPUT_DIR/"
  fi
  cp scripts/offline/restore_datasets.sh "$OUTPUT_DIR/"
fi

tar -cf "$OUTPUT_DIR/offline_bundle_full.tar" -C "$OUTPUT_DIR" .
sha256sum "$OUTPUT_DIR/offline_bundle_full.tar" > "$OUTPUT_DIR/offline_bundle_full.tar.sha256"

echo "Saved: $OUTPUT_DIR/offline_bundle_full.tar"
echo "SHA256: $OUTPUT_DIR/offline_bundle_full.tar.sha256"
