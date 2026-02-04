# 폐쇄망 배포 번들 생성 (vLLM 가중치 제외)

이 문서는 **로컬 macOS에서** 오프라인 배포용 번들을 만들고, 폐쇄망으로 전달하는 절차를 정리한다.
목표는 **vLLM 가중치 제외** 상태로도 폐쇄망에서 바로 실행 가능한 번들을 생성하는 것이다.

## 전제

- vLLM 서버는 **폐쇄망 내부에서 이미 구동** 중이며, 모델 가중치도 폐쇄망 내부에 존재한다.
- EvalVault는 **vLLM 서버에 API로 연결**한다.
- 폐쇄망에서 외부 네트워크 접근은 불가하므로, **이미지와 모델 캐시를 사전에 번들링**한다.

## 산출물

모든 파일은 `dist/` 아래에 생성된다.

- `dist/evalvault_offline_<timestamp>.tar` (Docker 이미지 번들)
- `dist/evalvault_offline_<timestamp>.tar.sha256`
- `dist/evalvault_model_cache.tar` (NLP 모델 캐시)
- `dist/evalvault_model_cache.tar.sha256`
- `dist/offline_AIA_full/offline_bundle_full.tar` (통합 번들)
- `dist/offline_AIA_full/offline_bundle_full.tar.sha256`

## 0) 도커 재시작 후 확인

```bash
docker version
docker compose version
```

둘 다 정상 출력되어야 한다. 실패하면 Docker Desktop 재실행 후 다시 확인한다.

## 1) 오프라인 이미지 번들 생성

```bash
./scripts/offline/export_images.sh
```

생성 파일:

- `dist/evalvault_offline_<timestamp>.tar`
- `dist/evalvault_offline_<timestamp>.tar.sha256`

## 2) NLP 모델 캐시 번들 생성

```bash
OUTPUT_TAR=dist/evalvault_model_cache.tar \
  CACHE_ROOT=model_cache \
  INCLUDE_KIWI=1 \
  ./scripts/offline/bundle_model_cache.sh
```

생성 파일:

- `dist/evalvault_model_cache.tar`
- `dist/evalvault_model_cache.tar.sha256`

## 3) 통합 번들 생성 (vLLM 가중치 제외)

```bash
IMAGES_TAR=dist/evalvault_offline_<timestamp>.tar \
MODELS_TAR=dist/evalvault_model_cache.tar \
INCLUDE_MODEL_CACHE=1 \
INCLUDE_VLLM_MODELS=0 \
./scripts/offline/build_full_offline_bundle.sh
```

생성 파일:

- `dist/offline_AIA_full/offline_bundle_full.tar`
- `dist/offline_AIA_full/offline_bundle_full.tar.sha256`

## 4) 폐쇄망 전달 및 실행

폐쇄망으로 다음 파일을 전달한다:

- `dist/evalvault_offline_<timestamp>.tar`
- `dist/evalvault_offline_<timestamp>.tar.sha256`
- `dist/evalvault_model_cache.tar`
- `dist/evalvault_model_cache.tar.sha256`
- `dist/offline_AIA_full/offline_bundle_full.tar`
- `dist/offline_AIA_full/offline_bundle_full.tar.sha256`

폐쇄망에서 실행:

```bash
./scripts/offline/import_images.sh dist/evalvault_offline_<timestamp>.tar
./scripts/offline/restore_model_cache.sh dist/evalvault_model_cache.tar

cp .env.offline.vllm.example .env.offline
# .env.offline 편집: VLLM_BASE_URL, VLLM_MODEL 등 입력

docker compose --env-file .env.offline -f docker-compose.offline.yml up -d --no-build --pull never
```

NLP 캐시 마운트를 명시하려면:

```bash
docker compose --env-file .env.offline \
  -f docker-compose.offline.yml \
  -f docker-compose.offline.modelcache.yml \
  up -d --no-build --pull never
```

## 5) 실패 시 체크리스트

- Docker Desktop 실행 상태 확인
- 디스크 여유 공간 확인 (이미지 크기 x2 이상)
- `dist/` 경로 쓰기 권한 확인
- 네트워크 차단 환경이라면 빌드 시 `--pull`로 인해 지연될 수 있음
  - 재시도 시에는 Docker Desktop 로그 확인 권장

## 참고 파일

- `docs/guides/OFFLINE_DOCKER.md`
- `docs/guides/OFFLINE_MODELS.md`
- `scripts/offline/export_images.sh`
- `scripts/offline/bundle_model_cache.sh`
- `scripts/offline/build_full_offline_bundle.sh`
