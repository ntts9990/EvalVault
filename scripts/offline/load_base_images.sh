#!/usr/bin/env bash
set -euo pipefail

# 베이스 이미지 로드 스크립트
# 폐쇄망에서 베이스 이미지 tar 파일을 로드합니다.

ARCHIVE=${1:-dist/evalvault_base_images.tar}

if [ ! -f "$ARCHIVE" ]; then
  echo "❌ 파일을 찾을 수 없습니다: $ARCHIVE" >&2
  exit 1
fi

# 체크섬 검증 (있는 경우)
if [ -f "${ARCHIVE}.sha256" ]; then
  echo "체크섬 검증 중..."
  sha256sum -c "${ARCHIVE}.sha256"
  if [ $? -ne 0 ]; then
    echo "❌ 체크섬 검증 실패!" >&2
    exit 1
  fi
  echo "✅ 체크섬 검증 완료"
fi

echo "베이스 이미지 로드 중: $ARCHIVE"
docker load -i "$ARCHIVE"

echo ""
echo "✅ 베이스 이미지 로드 완료!"
echo ""
echo "다음 단계(권장: 빌드 없이 실행):"
echo "  1. docker compose --env-file .env.offline -f docker-compose.offline.yml up -d --no-build"
echo ""
echo "빌드가 꼭 필요하면(오프라인 빌드 비권장):"
echo "  2. DOCKER_BUILDKIT=0 docker compose -f docker-compose.offline.yml -f docker-compose.offline.build.yml --env-file .env.offline build"
