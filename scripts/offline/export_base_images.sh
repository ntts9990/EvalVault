#!/usr/bin/env bash
set -euo pipefail

# 베이스 이미지 export 스크립트
# 폐쇄망에서 빌드하기 위해 필요한 모든 베이스 이미지를 export합니다.

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

OUTPUT_TAR=${OUTPUT_TAR:-dist/evalvault_base_images.tar}
INCLUDE_POSTGRES=${INCLUDE_POSTGRES:-1}

# .env.offline에서 이미지 태그 읽기 (없으면 기본값 사용)
if [ -f .env.offline ]; then
  source .env.offline
fi

BASE_IMAGES=(
  "${EVALVAULT_PYTHON_IMAGE:-python:3.12.6-slim}"
  "${EVALVAULT_UV_IMAGE:-ghcr.io/astral-sh/uv:0.4.28}"
  "${EVALVAULT_NODE_IMAGE:-node:20.11-alpine}"
  "${EVALVAULT_NGINX_IMAGE:-nginx:1.27.3-alpine}"
)

if [ "$INCLUDE_POSTGRES" = "1" ]; then
  BASE_IMAGES+=("${POSTGRES_IMAGE:-postgres:16.4-alpine}")
fi

echo "다음 베이스 이미지들을 pull합니다:"
for img in "${BASE_IMAGES[@]}"; do
  echo "  - $img"
done

# 모든 베이스 이미지 pull
for img in "${BASE_IMAGES[@]}"; do
  echo "Pulling $img..."
  docker pull "$img"
done

# 이미지들을 하나의 tar 파일로 저장
mkdir -p "$(dirname "$OUTPUT_TAR")"
echo "베이스 이미지들을 저장합니다: $OUTPUT_TAR"
docker save -o "$OUTPUT_TAR" "${BASE_IMAGES[@]}"

# 체크섬 생성
sha256sum "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"

echo ""
echo "✅ 완료!"
echo "저장된 파일: $OUTPUT_TAR"
echo "체크섬: ${OUTPUT_TAR}.sha256"
echo ""
echo "폐쇄망에서 로드하려면:"
echo "  docker load -i $OUTPUT_TAR"
