#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

OUTPUT_DIR=${OUTPUT_DIR:-dist/offline_AIA_full}
IMAGES_TAR=${IMAGES_TAR:-dist/evalvault_airgap.tar}
MODELS_TAR=${MODELS_TAR:-dist/evalvault_model_cache.tar}
OLLAMA_MODELS_TAR=${OLLAMA_MODELS_TAR:-dist/ollama_models.tar}
VLLM_MODELS_TAR=${VLLM_MODELS_TAR:-dist/vllm_models.tar}
DATASETS_TAR=${DATASETS_TAR:-}
INCLUDE_MODEL_CACHE=${INCLUDE_MODEL_CACHE:-1}
INCLUDE_OLLAMA_MODELS=${INCLUDE_OLLAMA_MODELS:-0}
INCLUDE_VLLM_MODELS=${INCLUDE_VLLM_MODELS:-0}

mkdir -p "$OUTPUT_DIR"

REQUIRED=(
  "$IMAGES_TAR"
  "$IMAGES_TAR.sha256"
  "docker-compose.offline.yml"
  "docker-compose.offline.build.yml"
  "docker-compose.offline.modelcache.yml"
  ".env.offline.example"
  ".env.offline.ollama.example"
  ".env.offline.vllm.example"
  "scripts/offline/import_images.sh"
  "scripts/offline/smoke_test.sh"
  "docs/guides/OFFLINE_DOCKER.md"
  "config/models.yaml"
)

if [ "$INCLUDE_MODEL_CACHE" = "1" ]; then
  REQUIRED+=(
    "$MODELS_TAR"
    "$MODELS_TAR.sha256"
    "scripts/offline/restore_model_cache.sh"
    "docs/guides/OFFLINE_MODELS.md"
  )
fi

if [ "$INCLUDE_OLLAMA_MODELS" = "1" ]; then
  REQUIRED+=(
    "$OLLAMA_MODELS_TAR"
    "$OLLAMA_MODELS_TAR.sha256"
    "scripts/offline/restore_ollama_models.sh"
  )
fi

if [ "$INCLUDE_VLLM_MODELS" = "1" ]; then
  REQUIRED+=(
    "$VLLM_MODELS_TAR"
    "$VLLM_MODELS_TAR.sha256"
    "scripts/offline/restore_vllm_models.sh"
  )
fi

for item in "${REQUIRED[@]}"; do
  if [ ! -f "$item" ]; then
    echo "Missing required file: $item" >&2
    exit 1
  fi
done

cp "$IMAGES_TAR" "$OUTPUT_DIR/"
cp "$IMAGES_TAR.sha256" "$OUTPUT_DIR/"
if [ "$INCLUDE_MODEL_CACHE" = "1" ]; then
  cp "$MODELS_TAR" "$OUTPUT_DIR/"
  cp "$MODELS_TAR.sha256" "$OUTPUT_DIR/"
fi
if [ "$INCLUDE_OLLAMA_MODELS" = "1" ]; then
  cp "$OLLAMA_MODELS_TAR" "$OUTPUT_DIR/"
  cp "$OLLAMA_MODELS_TAR.sha256" "$OUTPUT_DIR/"
fi
if [ "$INCLUDE_VLLM_MODELS" = "1" ]; then
  cp "$VLLM_MODELS_TAR" "$OUTPUT_DIR/"
  cp "$VLLM_MODELS_TAR.sha256" "$OUTPUT_DIR/"
fi
cp docker-compose.offline.yml "$OUTPUT_DIR/"
cp docker-compose.offline.build.yml "$OUTPUT_DIR/"
cp docker-compose.offline.modelcache.yml "$OUTPUT_DIR/"
cp .env.offline.example "$OUTPUT_DIR/"
cp .env.offline.ollama.example "$OUTPUT_DIR/"
cp .env.offline.vllm.example "$OUTPUT_DIR/"
cp docs/guides/OFFLINE_DOCKER.md "$OUTPUT_DIR/"

# Copy config folder (required for API server)
mkdir -p "$OUTPUT_DIR/config"
cp -r config/* "$OUTPUT_DIR/config/"

# Create empty data folder structure
mkdir -p "$OUTPUT_DIR/data/db"

# Copy scripts (already support auto-detection in current directory)
cp scripts/offline/import_images.sh "$OUTPUT_DIR/"
chmod +x "$OUTPUT_DIR/import_images.sh"

cp scripts/offline/smoke_test.sh "$OUTPUT_DIR/"
chmod +x "$OUTPUT_DIR/smoke_test.sh"

if [ "$INCLUDE_MODEL_CACHE" = "1" ]; then
  cp scripts/offline/restore_model_cache.sh "$OUTPUT_DIR/"
  chmod +x "$OUTPUT_DIR/restore_model_cache.sh"
  cp docs/guides/OFFLINE_MODELS.md "$OUTPUT_DIR/"
fi
if [ "$INCLUDE_OLLAMA_MODELS" = "1" ]; then
  cp scripts/offline/restore_ollama_models.sh "$OUTPUT_DIR/"
fi
if [ "$INCLUDE_VLLM_MODELS" = "1" ]; then
  cp scripts/offline/restore_vllm_models.sh "$OUTPUT_DIR/"
fi

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

# Generate standalone README
cat > "$OUTPUT_DIR/README.md" << 'README_EOF'
# EvalVault 오프라인 번들

이 폴더만으로 폐쇄망 환경에서 EvalVault를 실행할 수 있습니다.

## 사전 요구사항

- Docker + Docker Compose 설치
- vLLM 또는 Ollama 서버가 폐쇄망 내부에서 실행 중

## 빠른 시작 (vLLM)

```bash
# 1. Docker 이미지 로드
./import_images.sh

# 2. 모델 캐시 복원
./restore_model_cache.sh

# 3. 환경 설정
cp .env.offline.vllm.example .env.offline
# .env.offline 편집: VLLM_BASE_URL, VLLM_MODEL 등 설정

# 4. 서비스 시작
docker compose -f docker-compose.offline.yml \
  -f docker-compose.offline.modelcache.yml \
  --env-file .env.offline up -d --no-build --pull never

# 5. 확인
./smoke_test.sh
```

## 빠른 시작 (Ollama)

```bash
# 1. Docker 이미지 로드
./import_images.sh

# 2. 모델 캐시 복원
./restore_model_cache.sh

# 3. 환경 설정
cp .env.offline.ollama.example .env.offline
# .env.offline 편집: OLLAMA_BASE_URL 등 설정

# 4. 서비스 시작
docker compose -f docker-compose.offline.yml \
  -f docker-compose.offline.modelcache.yml \
  --env-file .env.offline up -d --no-build --pull never

# 5. 확인
./smoke_test.sh
```

## 접속

- Web UI: http://localhost:5173
- API: http://localhost:5173/api

## 문제 해결

자세한 내용은 `OFFLINE_DOCKER.md` 참조.
README_EOF

tar -cf "$OUTPUT_DIR/offline_bundle_full.tar" -C "$OUTPUT_DIR" .

# Generate checksum (cross-platform)
if command -v sha256sum &>/dev/null; then
  sha256sum "$OUTPUT_DIR/offline_bundle_full.tar" > "$OUTPUT_DIR/offline_bundle_full.tar.sha256"
elif command -v shasum &>/dev/null; then
  shasum -a 256 "$OUTPUT_DIR/offline_bundle_full.tar" > "$OUTPUT_DIR/offline_bundle_full.tar.sha256"
fi

echo "Saved: $OUTPUT_DIR/offline_bundle_full.tar"
echo "SHA256: $OUTPUT_DIR/offline_bundle_full.tar.sha256"
