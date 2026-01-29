#!/usr/bin/env bash
# 독립 스크립트: evalvault-api 빌드용 베이스 이미지 2개만 pull → tar 저장
# 어디서든 실행 가능 (프로젝트/ .env 의존 없음)

set -euo pipefail

PYTHON_IMAGE="${EVALVAULT_PYTHON_IMAGE:-python:3.12.6-slim}"
UV_IMAGE="${EVALVAULT_UV_IMAGE:-ghcr.io/astral-sh/uv:0.4.28}"
OUTPUT_TAR="${OUTPUT_TAR:-evalvault_api_base_only.tar}"

echo "다음 2개 이미지를 pull 후 저장합니다:"
echo "  1. $PYTHON_IMAGE"
echo "  2. $UV_IMAGE"
echo "출력: $OUTPUT_TAR"
echo ""

docker pull "$PYTHON_IMAGE"
docker pull "$UV_IMAGE"

echo ""
echo "저장 중: $OUTPUT_TAR"
docker save -o "$OUTPUT_TAR" "$PYTHON_IMAGE" "$UV_IMAGE"

if command -v sha256sum &>/dev/null; then
  sha256sum "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"
  echo "체크섬: ${OUTPUT_TAR}.sha256"
elif command -v shasum &>/dev/null; then
  shasum -a 256 "$OUTPUT_TAR" > "${OUTPUT_TAR}.sha256"
  echo "체크섬: ${OUTPUT_TAR}.sha256"
fi

echo ""
echo "✅ 완료! 폐쇄망에서: docker load -i $OUTPUT_TAR"
