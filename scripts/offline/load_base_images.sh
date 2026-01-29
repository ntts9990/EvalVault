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
echo "다음 단계:"
echo "  1. docker compose -f docker-compose.offline.yml build"
echo "  2. docker compose -f docker-compose.offline.yml --env-file .env.offline up -d"
