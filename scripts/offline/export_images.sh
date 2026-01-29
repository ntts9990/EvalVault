#!/usr/bin/env bash
set -euo pipefail

# EvalVault 오프라인 이미지 export 스크립트
# 온라인 환경에서 실행하여 빌드된 이미지를 tar 파일로 저장합니다.
# 빌드된 이미지에는 모든 베이스 이미지 레이어가 포함되어 있어,
# 폐쇄망에서 docker load만 하면 바로 사용 가능합니다.

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

TIMESTAMP=${TIMESTAMP:-$(date +%Y%m%d_%H%M%S)}
OUTPUT_TAR=${OUTPUT_TAR:-dist/evalvault_offline_${TIMESTAMP}.tar}
INCLUDE_POSTGRES=${INCLUDE_POSTGRES:-0}

# .env.offline에서 이미지 태그 읽기 (있는 경우)
if [ -f .env.offline ]; then
  source .env.offline
fi

IMAGES=(
  "evalvault-api:offline"
  "evalvault-web:offline"
)

if [ "$INCLUDE_POSTGRES" = "1" ]; then
  IMAGES+=("${POSTGRES_IMAGE:-postgres:16.4-alpine}")
  echo "📦 Postgres 이미지 포함: ${POSTGRES_IMAGE:-postgres:16.4-alpine}"
fi

echo "🔨 빌드할 이미지:"
for img in "${IMAGES[@]}"; do
  echo "  - $img"
done
echo ""

# 빌드 (베이스 이미지 포함 모든 레이어가 포함됨)
echo "🔨 Docker 이미지 빌드 중..."
docker compose -f docker-compose.offline.yml --env-file .env.offline build --pull

# tar 파일로 저장
mkdir -p "$(dirname "$OUTPUT_TAR")"
echo ""
echo "💾 이미지를 tar 파일로 저장 중: $OUTPUT_TAR"
docker save -o "$OUTPUT_TAR" "${IMAGES[@]}"

# 체크섬 생성
sha256sum "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"

echo ""
echo "✅ 완료!"
echo "📦 저장된 파일: $OUTPUT_TAR"
echo "🔐 체크섬: ${OUTPUT_TAR}.sha256"
echo ""
echo "📋 폐쇄망에서 사용 방법:"
echo "  1. tar 파일을 폐쇄망으로 복사"
echo "  2. docker load -i $OUTPUT_TAR"
echo "  3. docker compose --env-file .env.offline -f docker-compose.offline.yml up -d"
