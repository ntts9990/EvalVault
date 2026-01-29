# 폐쇄망(에어갭) Docker 배포 가이드

EvalVault를 외부망 없이 운영하기 위한 **오프라인 Docker 패키지** 구성 가이드입니다.
모델 가중치는 폐쇄망 내부에 이미 존재한다는 전제로, EvalVault는 **외부 모델 서버**를 호출합니다.

## 목표 구성

- EvalVault API + Web UI를 docker-compose로 실행
- 모델 서버(vLLM/Ollama)는 **외부 엔드포인트**로 연결
- 필요 시 Postgres는 compose 프로필로 선택

## 핵심 파일

- `docker-compose.offline.yml`: 오프라인용 compose
- `.env.offline.example`: 환경 변수 템플릿
- `frontend/Dockerfile`: Web UI 정적 서빙 이미지
- `frontend/nginx.conf`: `/api/*` 프록시 + SPA 라우팅
- `scripts/offline/*.sh`: 이미지 export/import/smoke-test
 - `.env.offline.example`: 오프라인 빌드용 베이스 이미지 고정

## 1) 환경 파일 준비

```bash
cp .env.offline.example .env.offline
```

`.env.offline`에 아래 항목을 **직접 입력**하세요.

- `EVALVAULT_PROFILE` (dev/prod/vllm)
- `OLLAMA_BASE_URL` 또는 `VLLM_BASE_URL`
- `CORS_ORIGINS` (기본: http://localhost:8080)

### 폐쇄망 사용자에게 전달할 필수 정보

아래 내용을 그대로 전달하면 됩니다.

**필수 입력값**
- `EVALVAULT_PROFILE`: `dev`(Ollama) / `openai` / `vllm` 중 선택
- `OLLAMA_BASE_URL` 또는 `OPENAI_API_KEY` 또는 `VLLM_BASE_URL` 중 하나 이상
- `CORS_ORIGINS`: 기본 `http://localhost:8080`

**포트 안내**
- API: `http://<HOST>:8000`
- Web UI: `http://<HOST>:8080`

**실행 명령**
```bash
cp .env.offline.example .env.offline
# .env.offline 편집 후
docker compose --env-file .env.offline -f docker-compose.offline.yml up -d
```

**검증 명령**
```bash
curl -f http://<HOST>:8000/health
curl -f http://<HOST>:8000/api/v1/config/profiles
curl -f http://<HOST>:8000/api/v1/runs/options/datasets
curl -I http://<HOST>:8080/
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

## 3) 폐쇄망 반입 및 로드

```bash
./scripts/offline/import_images.sh dist/evalvault_offline.tar
```

## 4) 오프라인 실행

```bash
docker compose --env-file .env.offline -f docker-compose.offline.yml up -d
```

주의: 폐쇄망에서는 외부 레지스트리 접근이 불가하므로, 반드시 `import_images.sh`로 이미지를 로드한 뒤 실행해야 합니다.

- API: `http://localhost:8000`
- Web UI: `http://localhost:8080`

Postgres를 함께 띄우려면:

```bash
docker compose --env-file .env.offline -f docker-compose.offline.yml --profile postgres up -d
```

## 5) 간단 스모크 테스트

```bash
./scripts/offline/smoke_test.sh
```

스모크 테스트가 실패하면 다음을 확인하세요.
- Docker Desktop 실행 상태
- `.env.offline`의 모델 서버 주소
- 포트 충돌 여부 (8000/8080)

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

## 참고 문서 (공식 Docker)

- Docker image save: https://docs.docker.com/reference/cli/docker/image/save/
- Docker image load: https://docs.docker.com/reference/cli/docker/image/load/
- Docker compose pull: https://docs.docker.com/reference/cli/docker/compose/pull/
