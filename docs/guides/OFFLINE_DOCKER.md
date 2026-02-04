# 폐쇄망(에어갭) Docker 배포 가이드

EvalVault를 외부망 없이 운영하기 위한 **오프라인 Docker 패키지** 구성 가이드입니다.
모델 가중치는 폐쇄망 내부에 이미 존재한다는 전제로, EvalVault는 **외부 모델 서버**를 호출합니다.

## 목표 구성

- EvalVault API + Web UI를 docker-compose로 실행
- 모델 서버(vLLM/Ollama)는 **폐쇄망 내부 엔드포인트**로 연결
- 오프라인 런타임에서는 **빌드를 하지 않음** (이미지 사전 로드)

## 핵심 파일

- `docker-compose.offline.yml`: 오프라인 런타임용 compose (build 없음)
- `docker-compose.offline.build.yml`: 온라인 빌드 전용 override
- `.env.offline.example`: 환경 변수 템플릿
- `.env.offline.ollama.example`: Ollama용 템플릿 (dev/prod)
- `.env.offline.vllm.example`: vLLM용 템플릿
- `frontend/Dockerfile`: Web UI 정적 서빙 이미지
- `frontend/nginx.conf`: `/api/*` 프록시 + SPA 라우팅
- `scripts/offline/*.sh`: 이미지 export/import/smoke-test
  - `scripts/offline/bundle_ollama_models.sh`, `restore_ollama_models.sh`
  - `scripts/offline/bundle_vllm_models.sh`, `restore_vllm_models.sh`
  - `.env.offline.example`: 오프라인 빌드용 베이스 이미지 고정

## 1) 환경 파일 준비

```bash
# Ollama (dev/prod)
cp .env.offline.ollama.example .env.offline

# vLLM
# cp .env.offline.vllm.example .env.offline
```

`.env.offline`에 아래 항목을 **직접 입력**하세요.

- `EVALVAULT_PROFILE` (dev/prod/vllm)
- `OLLAMA_BASE_URL` 또는 `VLLM_BASE_URL`
- `CORS_ORIGINS` (기본: http://localhost:5173)

### 폐쇄망 사용자에게 전달할 필수 정보

아래 내용을 그대로 전달하면 됩니다.

**필수 입력값**
- `EVALVAULT_PROFILE`: `dev`(Ollama) / `prod`(Ollama) / `vllm` 중 선택
- `OLLAMA_BASE_URL` 또는 `VLLM_BASE_URL` 중 하나 이상
- `CORS_ORIGINS`: 기본 `http://localhost:5173`

**포트 안내**
- API: `http://<HOST>:8000`
- Web UI: `http://<HOST>:5173`

**실행 명령 (오프라인 런타임)**
```bash
cp .env.offline.example .env.offline
# .env.offline 편집 후
docker compose --env-file .env.offline -f docker-compose.offline.yml up -d --no-build --pull never
```

**검증 명령**
```bash
curl -f http://<HOST>:8000/health
curl -f http://<HOST>:8000/api/v1/config/profiles
curl -f http://<HOST>:8000/api/v1/runs/options/datasets
curl -I http://<HOST>:5173/
```

**참고**
- 모델 서버는 폐쇄망 내부에 이미 존재한다고 가정합니다.
- vLLM은 폐쇄망에서 사용할 수 있으며, 로컬(macOS)에서는 테스트하지 않았습니다.

### vLLM 사용자 안내

폐쇄망에서 vLLM을 사용할 경우 다음을 설정합니다.

**필수 설정**
- `EVALVAULT_PROFILE=vllm`
- `VLLM_BASE_URL=http://<VLLM_HOST>:8000/v1`

**선택 설정**
- `VLLM_API_KEY`: vLLM 서버가 인증을 요구할 때만 사용
- `VLLM_MODEL`: 서버 기본 모델과 다를 때 지정
- `VLLM_EMBEDDING_MODEL`, `VLLM_EMBEDDING_BASE_URL`: 임베딩 서버를 분리 운용할 때 지정

**검증 명령**
```bash
curl -f http://<HOST>:8000/api/v1/config/profiles
```

`vllm` 프로필이 보이고, `VLLM_BASE_URL`이 실제 vLLM 서버를 가리키면 정상입니다.

## 2) 온라인 빌드/패키징

스크립트를 실행하기 전 권한을 부여하세요.

```bash
chmod +x scripts/offline/*.sh
```

```bash
./scripts/offline/export_images.sh
```

직접 빌드하려면 다음을 사용합니다.

```bash
docker compose -f docker-compose.offline.yml -f docker-compose.offline.build.yml \
  --env-file .env.offline build --pull
```

- 산출물: `dist/evalvault_offline_<timestamp>.tar`
- 체크섬: `dist/evalvault_offline_<timestamp>.tar.sha256`

파일명을 고정하려면 `OUTPUT_TAR`를 지정하세요.

```bash
OUTPUT_TAR=dist/evalvault_offline_legacy.tar ./scripts/offline/export_images.sh
```

이미지 태그를 고정하려면 `.env.offline` 또는 환경 변수로 다음을 지정합니다.

- `EVALVAULT_PYTHON_IMAGE`
- `EVALVAULT_UV_IMAGE`
- `EVALVAULT_NODE_IMAGE`
- `EVALVAULT_NGINX_IMAGE`
- `POSTGRES_IMAGE` (옵션)

Postgres 이미지를 함께 포함하려면:

```bash
INCLUDE_POSTGRES=1 ./scripts/offline/export_images.sh
```

전체 오프라인 번들을 만들려면(모델 캐시 포함):

```bash
IMAGES_TAR=dist/evalvault_offline_<timestamp>.tar \
MODELS_TAR=dist/evalvault_model_cache.tar \
./scripts/offline/build_full_offline_bundle.sh
```

vLLM 전용 번들(모델 캐시 생략):

```bash
IMAGES_TAR=dist/evalvault_offline_<timestamp>.tar \
INCLUDE_MODEL_CACHE=0 \
./scripts/offline/build_full_offline_bundle.sh
```

## 3) 폐쇄망 반입 및 로드

```bash
./scripts/offline/import_images.sh dist/evalvault_offline.tar
```

Ollama 모델을 포함했다면:

```bash
OLLAMA_MODELS_DIR=/var/lib/ollama \
  ./scripts/offline/restore_ollama_models.sh dist/ollama_models.tar
```

vLLM 모델을 포함했다면:

```bash
VLLM_MODEL_DIR=/data/vllm/models \
  ./scripts/offline/restore_vllm_models.sh dist/vllm_models.tar
```

## 4) 오프라인 실행

```bash
docker compose --env-file .env.offline -f docker-compose.offline.yml up -d --no-build --pull never
```

주의: 폐쇄망에서는 외부 레지스트리 접근이 불가하므로, 반드시 `import_images.sh`로 이미지를 로드한 뒤 실행해야 합니다.

- API: `http://localhost:8000`
- Web UI: `http://localhost:5173`

Postgres를 함께 띄우려면:

```bash
docker compose --env-file .env.offline -f docker-compose.offline.yml --profile postgres up -d --no-build --pull never
```

## 5) 간단 스모크 테스트

```bash
./scripts/offline/smoke_test.sh
```

스모크 테스트가 실패하면 다음을 확인하세요.
- Docker Desktop 실행 상태
- `.env.offline`의 모델 서버 주소
- 포트 충돌 여부 (8000/5173)

## 데이터 포함 정책

`data/`는 이미지에 포함됩니다.
단, `/app/data`를 볼륨으로 마운트하면 **이미지에 포함된 데이터가 가려집니다**.
필요 시 아래처럼 선택적으로 마운트하세요.

```yaml
# docker-compose.override.yml 예시
services:
  evalvault-api:
    volumes:
      - evalvault_data:/app/data

volumes:
  evalvault_data:
```

## 배포 버전(3종) 안내

### 1) Ollama 기반 (dev/prod)
- `EVALVAULT_PROFILE=dev` 또는 `prod`
- `OLLAMA_BASE_URL` 설정
- vLLM 관련 변수는 비워둠

### 2) vLLM 기반
- `EVALVAULT_PROFILE=vllm`
- `VLLM_BASE_URL` 설정
- **Ollama 모델은 포함하지 않음** (폐쇄망 내 vLLM 서버가 모델을 보유)

### 3) 오픈 모델 풀 번들 (OpenAI/Anthropic 제외)
- EvalVault 이미지 + Ollama 모델 + vLLM 모델 + NLP 모델 캐시를 모두 포함
- 폐쇄망에서 **외부 모델 다운로드 없이** dev/prod/vllm 모두 실행 가능

> 참고: EvalVault 이미지에는 LLM 가중치가 포함되지 않습니다.
> OpenAI/Anthropic 등 클로즈 모델은 번들에 포함하지 않습니다.

### 버전별 패키징 예시

**1) Ollama 기반 (dev/prod)**
```bash
INCLUDE_POSTGRES=1 ./scripts/offline/export_images.sh
OLLAMA_MODELS_DIR=/var/lib/ollama ./scripts/offline/bundle_ollama_models.sh

IMAGES_TAR=dist/evalvault_offline_<timestamp>.tar \
OLLAMA_MODELS_TAR=dist/ollama_models.tar \
INCLUDE_OLLAMA_MODELS=1 \
INCLUDE_MODEL_CACHE=1 \
./scripts/offline/build_full_offline_bundle.sh
```

**2) vLLM 기반**
```bash
INCLUDE_POSTGRES=1 ./scripts/offline/export_images.sh
VLLM_MODEL_DIR=/data/vllm/models ./scripts/offline/bundle_vllm_models.sh

IMAGES_TAR=dist/evalvault_offline_<timestamp>.tar \
VLLM_MODELS_TAR=dist/vllm_models.tar \
INCLUDE_VLLM_MODELS=1 \
INCLUDE_MODEL_CACHE=0 \
./scripts/offline/build_full_offline_bundle.sh
```

> NLP 분석이 필요하면 `INCLUDE_MODEL_CACHE=1`로 설정하세요.

**3) 오픈 모델 풀 번들 (dev/prod/vllm 전체)**
```bash
INCLUDE_POSTGRES=1 ./scripts/offline/export_images.sh
./scripts/offline/bundle_model_cache.sh
OLLAMA_MODELS_DIR=/var/lib/ollama ./scripts/offline/bundle_ollama_models.sh
VLLM_MODEL_DIR=/data/vllm/models ./scripts/offline/bundle_vllm_models.sh

IMAGES_TAR=dist/evalvault_offline_<timestamp>.tar \
MODELS_TAR=dist/evalvault_model_cache.tar \
OLLAMA_MODELS_TAR=dist/ollama_models.tar \
VLLM_MODELS_TAR=dist/vllm_models.tar \
INCLUDE_MODEL_CACHE=1 \
INCLUDE_OLLAMA_MODELS=1 \
INCLUDE_VLLM_MODELS=1 \
./scripts/offline/build_full_offline_bundle.sh
```

## Ollama 모델 포함(선택)

dev/prod에서 사용하는 Ollama 모델을 폐쇄망에 포함하려면 **Ollama 서버 측**에서 모델을 사전 로드해야 합니다.

**권장 절차(요약)**
- 온라인 환경에서 Ollama 서버에 필요한 모델을 `pull`
  - dev: `gemma3:1b`, `qwen3-embedding:0.6b`
  - prod: `gpt-oss-safeguard:20b`, `qwen3-embedding:8b`
- Ollama 모델 저장소를 tar로 백업
- 폐쇄망으로 전달 후, Ollama 서버 저장소로 복원

> EvalVault 이미지에는 Ollama 모델을 직접 포함하지 않습니다.
> 필요하면 Ollama 서버 이미지/볼륨 번들까지 함께 패키징해야 합니다.

## vLLM 모델 포함(선택)

vLLM 모델은 별도 스토리지에 존재하므로 **모델 디렉터리를 tar로 묶어 전달**합니다.

```bash
VLLM_MODEL_DIR=/data/vllm/models \
  ./scripts/offline/bundle_vllm_models.sh
```

폐쇄망에서 복원:

```bash
VLLM_MODEL_DIR=/data/vllm/models \
  ./scripts/offline/restore_vllm_models.sh dist/vllm_models.tar
```

## 오픈 모델 풀 번들 만들기 (3번)

```bash
# 1) EvalVault 이미지
INCLUDE_POSTGRES=1 ./scripts/offline/export_images.sh

# 2) NLP 모델 캐시
./scripts/offline/bundle_model_cache.sh

# 3) Ollama 모델 저장소
OLLAMA_MODELS_DIR=/var/lib/ollama ./scripts/offline/bundle_ollama_models.sh

# 4) vLLM 모델 디렉터리
VLLM_MODEL_DIR=/data/vllm/models ./scripts/offline/bundle_vllm_models.sh

# 5) 통합 번들
IMAGES_TAR=dist/evalvault_offline_<timestamp>.tar \
MODELS_TAR=dist/evalvault_model_cache.tar \
OLLAMA_MODELS_TAR=dist/ollama_models.tar \
VLLM_MODELS_TAR=dist/vllm_models.tar \
INCLUDE_MODEL_CACHE=1 \
INCLUDE_OLLAMA_MODELS=1 \
INCLUDE_VLLM_MODELS=1 \
./scripts/offline/build_full_offline_bundle.sh
```

## 크로스 플랫폼 체크리스트 (Ubuntu/macOS/Windows/WSL)

**공통(필수)**
- `docker load`로 이미지 로드 완료 확인 (`docker images`)
- `docker compose up --no-build --pull never` 사용
- `.env.offline`의 LLM URL/CORS/포트 확인
- 디스크 여유 공간 확보 (이미지 크기 x2)

**Ubuntu/Linux**
- SELinux/AppArmor 환경이면 볼륨 마운트 권한 확인
- 방화벽에서 8000/5173 포트 접근 허용

**macOS (Docker Desktop)**
- 파일 공유 경로가 Docker Desktop에서 허용되어야 함 (`/Users`, `/Volumes`, `/tmp` 등)
- VirtioFS 사용 시 파일 접근성 이슈 확인

## macOS 로컬 테스트 절차

macOS 전용 이미지는 없습니다. Docker Desktop이 Linux 이미지를 실행합니다.

```bash
# 1) 이미지 로드
./scripts/offline/import_images.sh dist/evalvault_offline_<timestamp>.tar

# 2) 환경 파일 준비
cp .env.offline.ollama.example .env.offline
# 또는
# cp .env.offline.vllm.example .env.offline

# 3) 오프라인 실행
docker compose --env-file .env.offline -f docker-compose.offline.yml up -d --no-build --pull never

# 4) 스모크 테스트
./scripts/offline/smoke_test.sh
```

**Windows (Docker Desktop)**
- 경로 구분자 `\` 사용 금지 (Compose는 `/` 사용)
- Windows Defender 예외 설정으로 IO 병목 방지

**WSL2**
- WSL2 네트워킹/포트 포워딩 확인
- 경로는 WSL 내부 기준(`./data`) 사용 권장

## 참고 문서 (공식 Docker)

- Docker image save: https://docs.docker.com/reference/cli/docker/image/save/
- Docker image load: https://docs.docker.com/reference/cli/docker/image/load/
- Docker compose pull: https://docs.docker.com/reference/cli/docker/compose/pull/
