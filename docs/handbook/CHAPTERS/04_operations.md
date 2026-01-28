# 04. Operations

## 목표

프로필/설정, 실행 환경(로컬/도커), 관측 옵션(Phoenix/Langfuse) 등을 운영 관점에서 정리한다.

## 프로필/설정

- 프로필 정의: `../../config/models.yaml`
- 런타임 설정: `../../src/evalvault/config/settings.py`
- 환경 템플릿: `../../.env.example`, `../../.env.offline.example`

운영 기본 원칙:
- 프로필과 시크릿은 분리한다 (모델 정의는 git, 시크릿은 env).
- `EVALVAULT_PROFILE`로 런타임 구성을 고정한다.

## 실행 환경

로컬:
- 설치 가이드: `../getting-started/INSTALLATION.md`
- API 서버: `uv run evalvault serve-api --reload`
- Web UI: `frontend`에서 `npm run dev`

예시 명령:
- `cp .env.example .env`
- `uv sync --extra dev`
- `EVALVAULT_PROFILE=dev uv run evalvault serve-api --reload`
- `cd frontend && npm install && npm run dev`

도커:
- 기본 스택: `../../docker-compose.yml`
- 오프라인 스택: `../../docker-compose.offline.yml`
- Langfuse 스택: `../../docker-compose.langfuse.yml`
- Phoenix + OTel: `../../docker-compose.phoenix.yaml`

오프라인 운영:
- 이미지 export/import: `../../scripts/offline/`
- 오프라인 가이드: `../guides/OFFLINE_DOCKER.md`

## 관측/트레이싱

옵션 구성:
- Phoenix 추적: `../../src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`
- Langfuse 추적: `../../src/evalvault/adapters/outbound/tracker/langfuse_adapter.py`
- MLflow 추적: `../../src/evalvault/adapters/outbound/tracker/mlflow_adapter.py`

스펙/수집:
- Open RAG Trace 스펙: `../architecture/open-rag-trace-spec.md`
- Collector: `../architecture/open-rag-trace-collector.md`
- 샘플: `../guides/OPEN_RAG_TRACE_SAMPLES.md`

관련 스크립트:
- OTel Collector 설정: `../../scripts/dev/otel-collector-config.yaml`
- Phoenix 모니터링: `../../scripts/ops/phoenix_watch.py`

## 운영 점검 체크리스트

- `run_id` 기준으로 DB/아티팩트/트레이스를 교차 확인한다.
- `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`로 분석 근거를 찾는다.
- `evalvault ops snapshot`으로 실행 환경을 기록한다.
- Web UI/CLI가 같은 DB를 바라보는지 확인한다.

## 참고

- 운영 런북(SSoT): `../new_whitepaper/12_operations.md`
- 오프라인 가이드: `../guides/OFFLINE_DOCKER.md`
- 설정 API: `../api/config.md`
