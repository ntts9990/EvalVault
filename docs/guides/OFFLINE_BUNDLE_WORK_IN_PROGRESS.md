# 오프라인 번들 개선 작업 (진행 중)

> 작성일: 2026-02-02
> 상태: 번들 재생성 대기 (Docker 빌드 필요)

## 목표

`dist/offline_AIA_full/` 폴더만 전달하면 폐쇄망 환경(Ubuntu, Windows, macOS)에서 바로 실행 가능하도록 개선

## 완료된 수정 사항

### 1. 플랫폼 호환성 (linux/amd64 고정)

macOS Apple Silicon에서 빌드해도 Ubuntu/Windows에서 실행 가능하도록 수정

#### `docker-compose.offline.yml`
```yaml
services:
  postgres:
    platform: linux/amd64
  evalvault-api:
    platform: linux/amd64
  evalvault-web:
    platform: linux/amd64
```

#### `docker-compose.offline.build.yml`
```yaml
services:
  evalvault-api:
    platform: linux/amd64
    build:
      platforms:
        - linux/amd64
  evalvault-web:
    platform: linux/amd64
    build:
      platforms:
        - linux/amd64
```

### 2. 클로즈드 모델 API 지원

#### `docker-compose.offline.yml` 환경변수 추가
```yaml
# OpenAI
OPENAI_API_KEY: ${OPENAI_API_KEY:-}
OPENAI_MODEL: ${OPENAI_MODEL:-}
OPENAI_BASE_URL: ${OPENAI_BASE_URL:-}
# Anthropic
ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
ANTHROPIC_MODEL: ${ANTHROPIC_MODEL:-}
# Azure OpenAI
AZURE_OPENAI_API_KEY: ${AZURE_OPENAI_API_KEY:-}
AZURE_OPENAI_ENDPOINT: ${AZURE_OPENAI_ENDPOINT:-}
AZURE_OPENAI_DEPLOYMENT: ${AZURE_OPENAI_DEPLOYMENT:-}
AZURE_OPENAI_API_VERSION: ${AZURE_OPENAI_API_VERSION:-}
```

#### `.env.offline.vllm.example` 추가 섹션
```bash
# vLLM (내부 모델)
VLLM_BASE_URL=http://vllm-server:8000/v1
VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct

# 클로즈드 모델 (프록시 필요)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AZURE_OPENAI_API_KEY=...
```

### 3. 스크립트 개선

#### `scripts/offline/import_images.sh`
- 현재 디렉토리에서 `evalvault_offline_*.tar` 자동 탐색
- macOS 호환 checksum (`shasum -a 256`)
- 인자 없이 실행 가능

#### `scripts/offline/restore_model_cache.sh`
- 현재 디렉토리에서 `evalvault_model_cache.tar` 자동 탐색
- macOS 호환 checksum
- 인자 없이 실행 가능

#### `scripts/offline/export_images.sh`
- Postgres 이미지 `linux/amd64` 플랫폼 지정 pull
- macOS 호환 checksum

#### `scripts/offline/bundle_model_cache.sh`
- shebang 추가
- macOS 호환 checksum

#### `scripts/offline/build_full_offline_bundle.sh`
- `config/` 폴더 포함 (models.yaml 등 필수 설정)
- `data/db/` 폴더 생성
- `README.md` 자동 생성
- macOS 호환 checksum

### 4. 번들 구조 (목표)

```
dist/offline_AIA_full/
├── README.md                         # 실행 가이드 (자동 생성)
├── config/                           # API 설정 파일들
│   ├── models.yaml
│   ├── methods.yaml
│   ├── ragas_prompts_override.yaml
│   └── ...
├── data/
│   └── db/                           # 데이터 저장 경로
├── evalvault_offline_*.tar           # Docker 이미지 (linux/amd64)
├── evalvault_offline_*.tar.sha256
├── evalvault_model_cache.tar         # NLP 모델 캐시
├── evalvault_model_cache.tar.sha256
├── docker-compose.offline.yml
├── docker-compose.offline.build.yml
├── docker-compose.offline.modelcache.yml
├── .env.offline.example
├── .env.offline.ollama.example
├── .env.offline.vllm.example
├── import_images.sh                  # 인자 없이 실행 가능
├── restore_model_cache.sh            # 인자 없이 실행 가능
├── smoke_test.sh
├── OFFLINE_DOCKER.md
├── OFFLINE_MODELS.md
└── offline_bundle_full.tar           # 통합 번들 (선택적)
```

---

## 남은 작업

### 1. 번들 재생성

Docker Desktop 재시작 후 다음 명령어 순서대로 실행:

```bash
cd /Users/isle/PycharmProjects/EvalVault

# 1. Docker 이미지 빌드 및 export (약 5-10분)
INCLUDE_POSTGRES=1 ./scripts/offline/export_images.sh

# 2. 모델 캐시 번들 생성 (약 5분)
OUTPUT_TAR=dist/evalvault_model_cache.tar \
CACHE_ROOT=model_cache \
INCLUDE_KIWI=1 \
./scripts/offline/bundle_model_cache.sh

# 3. 통합 번들 생성
# export_images.sh 실행 후 생성된 timestamp 확인
ls dist/evalvault_offline_*.tar

# timestamp를 확인한 후 실행 (예: 20260202_123456)
IMAGES_TAR=dist/evalvault_offline_<timestamp>.tar \
MODELS_TAR=dist/evalvault_model_cache.tar \
INCLUDE_MODEL_CACHE=1 \
./scripts/offline/build_full_offline_bundle.sh
```

### 2. 테스트

번들 생성 완료 후:

```bash
# 번들 내용 확인
ls -la dist/offline_AIA_full/

# 번들 폴더로 이동하여 테스트
cd dist/offline_AIA_full/

# 이미지 로드
./import_images.sh

# 모델 캐시 복원
./restore_model_cache.sh

# 환경 설정
cp .env.offline.vllm.example .env.offline
# 편집: VLLM_BASE_URL 등 설정

# 서비스 시작
docker compose -f docker-compose.offline.yml \
  -f docker-compose.offline.modelcache.yml \
  --env-file .env.offline up -d --no-build --pull never

# 확인
./smoke_test.sh
```

---

## 수정된 파일 목록

| 파일 | 수정 내용 |
|------|-----------|
| `docker-compose.offline.yml` | platform 추가, 클로즈드 모델 환경변수 추가 |
| `docker-compose.offline.build.yml` | platform, platforms 추가 |
| `.env.offline.vllm.example` | OpenAI/Anthropic/Azure 설정 추가 |
| `scripts/offline/export_images.sh` | postgres platform 지정, macOS checksum |
| `scripts/offline/bundle_model_cache.sh` | shebang, macOS checksum |
| `scripts/offline/import_images.sh` | 자동 탐색, macOS checksum |
| `scripts/offline/restore_model_cache.sh` | 자동 탐색, macOS checksum |
| `scripts/offline/build_full_offline_bundle.sh` | config 폴더, data 폴더, README 생성 |

---

## 사용 시나리오

### 시나리오 1: 내부 모델만 사용 (vLLM)

```bash
# .env.offline 설정
EVALVAULT_PROFILE=vllm
VLLM_BASE_URL=http://내부-vllm-서버:8000/v1
VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct
VLLM_EMBEDDING_MODEL=BAAI/bge-m3
```

### 시나리오 2: 클로즈드 모델 사용 (프록시 경유)

```bash
# .env.offline 설정
EVALVAULT_PROFILE=dev
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
# 또는
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### 시나리오 3: 혼합 사용

```bash
# 내부 모델 + 클로즈드 모델 fallback
EVALVAULT_PROFILE=vllm
VLLM_BASE_URL=http://내부-vllm-서버:8000/v1
VLLM_MODEL=Qwen/Qwen2.5-7B-Instruct

# Faithfulness 메트릭은 더 강력한 모델 사용
FAITHFULNESS_FALLBACK_PROVIDER=openai
FAITHFULNESS_FALLBACK_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

---

## 플랫폼 호환성

| 빌드 환경 | 타겟 이미지 | 실행 가능 환경 |
|-----------|-------------|----------------|
| macOS (Apple Silicon) | linux/amd64 | Ubuntu, Windows, Intel Mac |
| macOS (Intel) | linux/amd64 | Ubuntu, Windows, Intel Mac |
| Ubuntu | linux/amd64 | Ubuntu, Windows, Intel Mac |

> **참고**: Windows Docker Desktop은 WSL2/Hyper-V에서 Linux 컨테이너를 실행하므로 `linux/amd64` 이미지 사용

---

## 문제 해결

### Docker 빌드 실패 시

```bash
# Docker Desktop 재시작
# 메뉴바 아이콘 → Restart

# Docker 상태 확인
docker version
docker compose version

# 디스크 공간 확인 (최소 20GB 필요)
df -h
```

### 이미지 로드 실패 시

```bash
# 체크섬 확인
shasum -a 256 -c evalvault_offline_*.tar.sha256

# 수동 로드
docker load -i evalvault_offline_*.tar
```

### 컨테이너 시작 실패 시

```bash
# 로그 확인
docker compose -f docker-compose.offline.yml logs evalvault-api

# config 폴더 확인
ls -la config/
```
