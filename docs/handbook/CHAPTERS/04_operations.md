# 04. Operations (로컬/도커/관측/런북)

이 챕터는 EvalVault를 “안전하게 돌리고, 고장 나면 복구하는” 운영 관점 문서다.
개발 환경(로컬)과 실험/배포 환경(도커/오프라인)을 모두 다루며, 선택 기능(트레이싱/트래커/Stage)을 켜고 끄는 기준과 런북(runbook)을 포함한다.

## TL;DR

- 운영의 3대 불변식: (1) 프로필/시크릿 분리 (2) DB 설정 고정 (3) `run_id`로 교차 확인.
- “결과가 보인다/공유된다”의 의미는 같은 DB 설정을 UI/API/CLI가 함께 본다는 뜻이다. (근거: `src/evalvault/config/settings.py#Settings`, `src/evalvault/adapters/inbound/api/main.py#create_app`)
- 관측(트레이싱/트래커)은 기본 루프의 필수 전제가 아니다. 다만 디버깅 속도를 크게 올리므로, 켤 조건/꺼둘 조건을 팀 룰로 고정하는 것이 운영 비용을 줄인다.

## 목표

- 로컬에서 CLI/API/UI를 안정적으로 띄운다.
- 프로필/환경변수 운영 규칙을 “문서화 가능한 수준”으로 고정한다.
- 도커/오프라인/관측 옵션을 필요할 때만 켠다.
- 장애 시 1차 진단 루틴을 수행할 수 있다.

---

## 1) 운영 기본 원칙(실수 방지)

### 1.1 프로필과 시크릿은 분리한다

운영에서 가장 흔한 사고는 “시크릿이 git에 남는 것”이다. EvalVault는 이를 구조적으로 분리한다.

- 프로필(버전 관리 대상): `config/models.yaml` (근거: `src/evalvault/config/settings.py#apply_profile`)
- 시크릿/인프라(커밋 금지): `.env` / 환경변수 (근거: `.env.example`, `src/evalvault/config/settings.py#Settings.model_config`)

### 1.2 DB 설정을 고정한다

EvalVault의 실행 데이터는 DB를 중심으로 재사용된다.

- 기본 저장소: Postgres+pgvector (근거: `src/evalvault/config/settings.py#Settings.postgres_*`)
- SQLite를 쓰는 경우 `--db` 또는 `DB_BACKEND=sqlite` + `EVALVAULT_DB_PATH`를 지정한다. (근거: `src/evalvault/config/settings.py#Settings.evalvault_db_path`)
- CLI와 API/Web UI가 같은 DB 설정을 봐야 결과가 연결된다. (근거: `src/evalvault/adapters/inbound/api/main.py#create_app`는 settings의 DB를 사용하고, CLI는 `--db` 또는 settings fallback을 사용)

### 1.3 `run_id`를 운영의 단일 키로 쓴다

run_id는 “조회/리포트/아티팩트/트레이싱 링크”의 조인 키다.

- run 엔티티: `src/evalvault/domain/entities/result.py#EvaluationRun`
- history/export/compare 등은 DB에서 run_id로 조회한다. (근거: `src/evalvault/adapters/inbound/cli/commands/history.py`, `src/evalvault/adapters/inbound/cli/commands/compare.py`)

---

## 2) 로컬 운영(개발자 기본)

### 2.1 준비

```bash
cp .env.example .env
uv sync --extra dev
```

근거:

- 설치/빠른 시작: `README.md`
- 개발 환경 가이드: `AGENTS.md`
- 환경변수 예시: `.env.example`

### 2.2 5분 스모크(기본 루프가 살아있는지)

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev
```

근거:

- Quickstart: `README.md`
- handbook 최소 실행: `docs/handbook/CHAPTERS/00_overview.md`

### 2.3 평가 + 자동 분석(운영에서 가장 자주 쓰는 형태)

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --auto-analyze
```

SQLite를 쓰는 경우 `--db` 또는 `DB_BACKEND=sqlite` + `EVALVAULT_DB_PATH`로 경로를 고정한다.

기대 산출물(기본 경로 형태):

- `reports/analysis/analysis_<RUN_ID>.json`
- `reports/analysis/analysis_<RUN_ID>.md`
- `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`

근거:

- auto-analyze prefix: `src/evalvault/adapters/inbound/cli/commands/run.py`
- 경로 resolve/아티팩트 작성: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`

### 2.4 API 서버(FastAPI)

```bash
uv run evalvault serve-api --reload
```

기본 바인딩:

- host: `127.0.0.1`
- port: `8000`

근거: `src/evalvault/adapters/inbound/cli/commands/api.py#register_api_command`

### 2.5 Web UI(React)

```bash
cd frontend
npm install
npm run dev
```

근거:

- 실행 방법(요약): `README.md`

### 2.6 로컬 운영에서 자주 생기는 문제(최소 진단)

#### (A) UI에서 run이 안 보인다

가장 먼저 확인할 것: “CLI와 API가 같은 DB를 보고 있는가?”

- CLI에서 `--db`로 쓴 경로
- API에서 settings가 해석한 `evalvault_db_path`

근거:

- DB 기본값/정규화: `src/evalvault/config/settings.py#Settings.model_post_init`
- API app은 `get_settings()`를 통해 설정을 읽는다: `src/evalvault/adapters/inbound/api/main.py#create_app`

#### (B) 대시보드(이미지) 생성에서 matplotlib 관련 오류

EvalVault는 GUI 백엔드 충돌을 줄이기 위해 matplotlib 백엔드를 `Agg`로 강제한다.

- 근거(대시보드): `src/evalvault/adapters/outbound/report/dashboard_generator.py#_import_matplotlib_pyplot`
- 근거(네트워크 분석 모듈): `src/evalvault/adapters/outbound/analysis/network_analyzer_module.py#_get_matplotlib_pyplot`
- 설치: `uv sync --extra dashboard` (근거: `pyproject.toml`의 optional dependency `dashboard`)

---

## 3) 설정/프로필 운영(팀 규약으로 고정할 것)

### 3.1 .env vs config/models.yaml

- `.env`: 시크릿/인프라/네트워크(커밋 금지) (근거: `.env.example`)
- `config/models.yaml`: 모델/임베딩 프로필(커밋 대상) (근거: `src/evalvault/config/settings.py#apply_profile`)

### 3.2 prod 프로필의 “강제 실패” 정책

prod 프로필은 안전하지 않은 설정을 빠르게 거부한다.

- 누락된 설정은 에러로 실패한다. (근거: `src/evalvault/config/settings.py#_validate_production_settings`)
- CORS에서 localhost는 prod에서 금지된다. (근거: `src/evalvault/config/settings.py#_validate_production_settings`)

### 3.3 `secret://` 참조(선택)

Settings는 특정 필드에서 `secret://...`을 감지하면 provider를 통해 값을 해석한다.

- 참조 감지/해석: `src/evalvault/config/settings.py#Settings._resolve_secret_references`
- provider 구현: `src/evalvault/config/secret_manager.py`
- 사용 예시는 `.env.example` 참고

---

## 4) 도커/오프라인 운영(실험 환경을 고정하고 싶을 때)

도커는 “환경 차이”를 줄이는 용도로 쓴다. 특히 폐쇄망/에어갭에서는 도커 패키징이 사실상 표준 운영 단위가 된다.

### 4.1 오프라인(폐쇄망) Docker 가이드

핵심 문서:

- `docs/guides/OFFLINE_DOCKER.md`
- `docker-compose.offline.yml`

실행 요약(문서 기준):

```bash
cp .env.offline.example .env.offline
docker compose --env-file .env.offline -f docker-compose.offline.yml up -d --no-build --pull never
```

근거: `docs/guides/OFFLINE_DOCKER.md`

### 4.2 오프라인 compose의 중요한 운영 포인트

- API: 8000, Web UI: 5173→80 프록시 (근거: `docker-compose.offline.yml`)
- 기본 CORS 오리진 예시는 환경/포트에 따라 달라질 수 있으므로, 배포 포트 기준으로 명시적으로 설정한다. (근거: `docs/guides/OFFLINE_DOCKER.md`, `docker-compose.offline.yml`)
- `/app/data` 볼륨 마운트는 이미지에 포함된 `data/`를 가릴 수 있다. (근거: `docs/guides/OFFLINE_DOCKER.md`)

### 4.3 오프라인 패키징 스크립트(운영 자동화)

- 이미지 export/import: `scripts/offline/export_images.sh`, `scripts/offline/import_images.sh`
- 스모크 테스트: `scripts/offline/smoke_test.sh`

근거: `docs/guides/OFFLINE_DOCKER.md`

### 4.4 오프라인 모델 캐시(LLM 제외)

폐쇄망에서 NLP 분석은 로컬 모델 캐시로만 동작한다. LLM 모델은 외부 인프라에서 관리한다.

- 모델 캐시 가이드: `docs/guides/OFFLINE_MODELS.md`

---

## 5) 관측/트레이싱(옵션): 켤 기준/꺼둘 기준

이 레포에서 “관측”은 크게 두 층으로 나뉜다.

1) 트래커(외부 시스템으로 run 정보를 남김): Langfuse / Phoenix / MLflow
2) Stage(파이프라인 단계 이벤트/메트릭): 파일 ingest 또는 실행 중 저장

### 5.1 트래커 선택: `tracker_provider` / `--tracker`

- settings에 트래커 provider가 있다. (근거: `src/evalvault/config/settings.py#Settings.tracker_provider`)
- CLI는 `--tracker langfuse|mlflow|phoenix|none`를 제공한다. (근거: `src/evalvault/adapters/inbound/cli/commands/run.py`)
- Web API도 tracker를 구성한다. (근거: `src/evalvault/adapters/inbound/api/adapter.py`)

### 5.2 Phoenix(OpenTelemetry) 켤 때의 현실

- instrumentation을 켜는 유틸이 있다. (근거: `src/evalvault/config/phoenix_support.py#ensure_phoenix_instrumentation`)
- Phoenix tracker는 입력/출력/컨텍스트를 sanitize한다. (근거: `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`, `src/evalvault/adapters/outbound/tracker/log_sanitizer.py`)

### 5.3 Langfuse/MLflow 켤 때의 현실

- Langfuse adapter도 sanitize를 적용한다. (근거: `src/evalvault/adapters/outbound/tracker/langfuse_adapter.py`, `src/evalvault/adapters/outbound/tracker/log_sanitizer.py`)
- MLflow adapter도 sanitize를 적용한다. (근거: `src/evalvault/adapters/outbound/tracker/mlflow_adapter.py`, `src/evalvault/adapters/outbound/tracker/log_sanitizer.py`)

### 5.4 언제 켜야 하나(권장)

- 회귀가 간헐적으로 발생해 원인 재현이 어려울 때
- 지연/비용(토큰)을 함께 추적해야 할 때
- 결과를 조직 단위로 공유/대시보딩해야 할 때

### 5.5 언제 꺼도 되나(권장)

- 로컬에서 기능 개발 중이고, DB/리포트/아티팩트만으로 충분할 때

### 5.6 트래커 스택 운영 가이드(MLflow + Phoenix dual-tracker)

EvalVault는 폐쇄망/자가호스팅 환경에서 실험 버전·아티팩트·관찰(트레이스)을 함께 관리할 수 있도록 **MLflow + Phoenix dual-tracker**를 기본 스택으로 채택한다.

#### 5.6.1 역할 분담

- **MLflow** — 실험 메타데이터, 지표, 아티팩트 저장(실험 버전/모델 버전 관리)
- **Phoenix** — LLM 트레이스 / 관찰 / 디버깅(실시간 가시성)

운영 규칙(필수):

- 기본 tracker는 `mlflow+phoenix`이며, 모든 평가 run은 **두 트래커에 동시에 로깅**된다.
- tracker 옵션에서 둘 중 하나라도 누락되면 실행이 실패한다.
- 어댑터 위치: `src/evalvault/adapters/outbound/tracker/mlflow_adapter.py`, `src/evalvault/adapters/outbound/tracker/phoenix_adapter.py`.

#### 5.6.2 핵심 연결 키(아티팩트 ↔ 트레이스 ↔ run)

- `run_id` (EvalVault Run ID, 모든 추적의 조인 키)
- `dataset_name` / `dataset_version`
- `model_name` / `model_version`
- `prompt_version` / `retrieval_version`
- `evaluation_profile` (예: dev/prod)
- `git_commit` / `git_branch` / `pipeline_version`

이 키들은 MLflow tags/params로 권장 표기하며, ops snapshot(§6)이 남기는 환경 컨텍스트와 함께 재현성의 최소 단위가 된다.

#### 5.6.3 라이선스/자가호스팅 메모(폐쇄망)

- MLflow: Apache 2.0 (상업 사용 가능)
- Phoenix: Elastic License 2.0 (자가호스팅 허용, 제3자에게 SaaS로 재판매 금지)

#### 5.6.4 폐쇄망 배포 체크리스트

네트워크/보안:
- [ ] 외부 outbound 차단 환경 스모크 통과
- [ ] 내부 PKI 또는 사설 TLS 인증서 적용
- [ ] 사설 DNS/레지스트리 준비

스토리지:
- [ ] MLflow backend store: Postgres
- [ ] MLflow artifact store: MinIO(S3 호환) 또는 내부 오브젝트 스토리지
- [ ] Phoenix 저장소: Postgres (분리 권장)

서비스 구성:
- [ ] MLflow Tracking Server
- [ ] Phoenix Server
- [ ] Postgres (MLflow/Phoenix 인스턴스 분리 권장)
- [ ] Object Storage (MinIO)

운영:
- [ ] 백업/복구 정책 수립
- [ ] 아티팩트 보관 기간/정책 정의
- [ ] 접근 제어(사용자/토큰/권한) 설정

#### 5.6.5 아티팩트 폴더 규약(권장)

```
artifacts/
  dataset/
  metrics/
    metrics.json
    metrics.csv
  analysis/
    analysis.json
    analysis.md
  reports/
    report.pdf
    report.xlsx
  prompts/
    prompt_snapshot.json
  config/
    run_config.json
    model_config.json
```

데이터셋/프롬프트/파라미터는 immutable snapshot으로 저장하고, 각 스냅샷에 `sha256`을 함께 기록한다(재현성 보장).

#### 5.6.6 설정 값 / CLI

```bash
# 환경 변수
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=evalvault-experiments
PHOENIX_ENDPOINT=http://localhost:6006
PHOENIX_API_TOKEN=...      # 옵션
TRACKER_PROVIDER=mlflow+phoenix

# CLI
uv run evalvault run <DATASET> --tracker mlflow+phoenix
```

라이선스/자가호스팅 결정과 어댑터의 sanitize 정책은 §5.2~§5.3과 일관되게 적용된다.

---

## 6) Ops snapshot(재현성: “조건도 같이 남기기”)

비교/회귀가 느려지는 가장 큰 이유는 “실험 조건을 다시 못 맞추는 것”이다.
`evalvault ops snapshot`은 run을 기준으로 운영 스냅샷 JSON을 남긴다.

```bash
uv run evalvault ops snapshot \
  --run-id <RUN_ID> \
  --db data/db/evalvault.db \
  --include-model-config \
  --include-env \
  --redact OPENAI_API_KEY \
  --redact LANGFUSE_SECRET_KEY \
  --output reports/ops_snapshot_<RUN_ID>.json
```

근거:

- CLI 옵션/동작: `src/evalvault/adapters/inbound/cli/commands/ops.py`
- env redact 로직: `src/evalvault/domain/services/ops_snapshot_service.py#_build_env_snapshot`

---

## 7) Stage 이벤트 운영(관찰가능성: 외부/내부 파이프라인 로그)

Stage는 “RAG 파이프라인 단계”를 이벤트로 저장하고, 요약/메트릭/가이드를 생성하는 워크플로다.

### 7.1 ingest(외부 로그를 EvalVault로 가져오기)

- 입력 포맷: `.json` 또는 `.jsonl` (근거: `src/evalvault/adapters/inbound/cli/commands/stage.py`)
- 유효성 실패를 일부 건너뛸 수 있다: `--skip-invalid` (근거: `src/evalvault/adapters/inbound/cli/commands/stage.py`)

```bash
uv run evalvault stage ingest path/to/stage_events.jsonl --db data/db/evalvault.db --skip-invalid
uv run evalvault stage summary <RUN_ID> --db data/db/evalvault.db
```

근거:

- stage CLI: `src/evalvault/adapters/inbound/cli/commands/stage.py`
- Stage 이벤트 엔티티: `src/evalvault/domain/entities/stage.py#StageEvent`

---

## 8) 운영 점검 체크리스트(주간/배포 전)

- [ ] `.env`/시크릿 파일이 커밋/아티팩트에 포함되지 않았는가? (근거: `.env.example`)
- [ ] CLI/API/Web UI가 같은 DB를 바라보는가? (근거: `src/evalvault/config/settings.py#Settings.evalvault_db_path`)
- [ ] 실행 결과는 `run_id`로 찾을 수 있는가? (근거: `src/evalvault/adapters/inbound/cli/commands/history.py`)
- [ ] 분석 아티팩트 `index.json`이 생성되어 근거 추적이 가능한가? (근거: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py#write_pipeline_artifacts`)
- [ ] (선택) 트래커를 켰다면 sanitize가 적용되는가? (근거: `src/evalvault/adapters/outbound/tracker/log_sanitizer.py`)

---

## 9) 장애 대응(1차 진단 루틴)

1) 문제 재현이 되는 `run_id` 확보
2) DB에서 run 조회 가능 여부 확인(history/export)
3) 리포트/아티팩트 생성 여부 확인(특히 `index.json`)
4) (선택) 트래커 링크/Stage 이벤트로 원인 후보 좁히기

근거:

- history/export: `src/evalvault/adapters/inbound/cli/commands/history.py`
- 아티팩트 작성/목차: `src/evalvault/adapters/inbound/cli/utils/analysis_io.py`
- Phoenix/Langfuse 링크 추출 유틸: `src/evalvault/config/phoenix_support.py`, `src/evalvault/config/langfuse_support.py`

### 9.1 진단 플레이북(증상 → 분석 Intent 결정 트리)

“점수가 왜 낮은가”를 운영자가 빠르게 좁힐 수 있도록, EvalVault는 분석 파이프라인에 **AnalysisIntent**를 두고 증상별로 권장 경로를 정의한다(`src/evalvault/domain/entities/analysis_pipeline.py`).

#### 9.1.1 진단 가능 상태 사전 점검

본격 분석 전에 아래를 확인한다.

- Postgres 연결 설정 정상(`POSTGRES_*` 또는 `POSTGRES_CONNECTION_STRING`)
- SQLite 사용 시 `--db` 또는 `EVALVAULT_DB_PATH`가 올바른가
- 대상 `run_id`가 DB에 존재하는가 (`evalvault history`)
- 데이터셋에 `thresholds`가 포함되어 있는가(없으면 0.7 기본값)
- 메트릭이 요구하는 환경(임베딩 등)이 갖춰져 있는가

#### 9.1.2 증상 → 권장 Intent 매핑(요약)

| 증상 | 1차 목표 | 권장 Intent | 우선 확인 아티팩트 |
|---|---|---|---|
| 특정 메트릭이 임계치 미달 | 원인 후보 추출 | `analyze_low_metrics` 또는 `analyze_playbook` | `diagnostic_playbook.json`, `root_cause_analyzer.json` |
| `faithfulness` 낮음 | 검색 vs 생성 분리 | `verify_retrieval` + `analyze_low_metrics` | `retrieval_quality_checker.json` |
| `answer_relevancy` 낮음 | 의도/프롬프트 정렬 | `analyze_patterns` (+ `analyze_low_metrics`) | `nlp_analyzer.json`, `pattern_detector.json` |
| `context_precision` 낮음 | 노이즈 컨텍스트 제거 | `verify_retrieval` (+ `compare_search`) | `retrieval_analyzer.json` |
| `context_recall` 낮음 | top_k/청킹/쿼리 확장 | `verify_retrieval` + `benchmark_retrieval` | `retrieval_benchmark.json` |
| 임베딩 지표 불안정 | 임베딩 백엔드/분포 | `verify_embedding` | `embedding_analyzer.json` |
| 한국어 토큰화 의심 | 형태소 검증 | `verify_morpheme` | `morpheme_quality_checker.json` |
| 릴리즈 직후 회귀 | 시점·변경점 추적 | `analyze_trends` + `generate_comparison` | `trend_detector.json`, `run_change_detector.json` |
| A/B 결론 흔들림 | 유의성/표본수 점검 | `evalvault analyze-compare`(t-test / mann-whitney) | `comparison_<A>_<B>.md` |
| 스테이지 병목/트레이스 누락 | 단계별 진단 | `evalvault stage` + `evalvault debug report` | debug report, stage metrics |

핵심 산출물 경로(고정 패턴):

- 단일 실행 자동 분석: `reports/analysis/analysis_<RUN_ID>.{json,md}`, `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`
- A/B 비교: `reports/comparison/comparison_<RUN_A>_<RUN_B>.{json,md}`

#### 9.1.3 반복 개선 루프(운영 표준)

1. 기준 run 확보(`evalvault run ... --auto-analyze`)
2. 결정 트리로 Intent 선택(1차 진단)
3. 아티팩트 인덱스 → 핵심 노드 JSON으로 근거 확인
4. **한 번에 한 축만** 변경(프롬프트/검색/데이터 중 1개)
5. 동일 데이터셋/메트릭으로 재실행
6. `evalvault analyze-compare`로 방향/유의성/변경점 확인
7. 비교 보고서를 “결정 기록”으로 보관

#### 9.1.4 오판 방지 체크

- A/B 비교는 **동일 데이터셋 조건**에서만 안전하다 (`run_change_detector`로 변경 축 확인).
- 임베딩 기반 지표는 환경에 민감하다 — `verify_embedding`으로 변동성부터 제거.
- 한국어 분석은 `verify_morpheme` 결과가 실패인 상태에서 NLP/검색 결과를 과신하지 않는다.
- 보고서 결론은 반드시 아티팩트(노드 JSON)로 추적 가능해야 한다.

#### 9.1.5 빠른 의도→모듈 매핑(부록)

| Intent | 운영자의 질문 | 핵심 모듈 |
|---|---|---|
| `analyze_low_metrics` | “왜 낮지? 뭘 바꿔야 하지?” | `ragas_evaluator`, `diagnostic_playbook`, `root_cause_analyzer`, `llm_report` |
| `verify_retrieval` | “검색이 문제인가?” | `retrieval_analyzer`, `retrieval_quality_checker` |
| `verify_embedding` | “임베딩이 정상인가?” | `embedding_analyzer`, `embedding_distribution` |
| `verify_morpheme` | “한국어 토큰화가 정상인가?” | `morpheme_analyzer`, `morpheme_quality_checker` |
| `generate_comparison` | “A/B에서 뭐가 바뀌었고 유의미한가?” | `run_metric_comparator`, `run_change_detector`, `llm_report` |
| `analyze_trends` | “언제부터 나빠졌나?” | `time_series_analyzer`, `trend_detector` |
| `generate_hypotheses` | “다음 실험 가설을 자동으로?” | `hypothesis_generator` |
| `analyze_network` | “메트릭 구조가 바뀌었나?” | `network_analyzer` |

> 스테이지/디버그 진단은 Intent 분류 없이 `evalvault stage`, `evalvault debug report`로 진입한다.

---

## 9) 운영 작업 로그(최근)

운영 관련 변경은 아래 worklog에 append-only로 기록한다.

- P0 설정/프로필 검증: `.sisyphus/notepads/p0-settings/worklog.md`
- P1 Web UI 운영 항목: `.sisyphus/notepads/p1-webui/worklog.md`
- P2 관측/멀티턴 평가: `.sisyphus/notepads/p2-observability/worklog.md`
- P3 성능/데이터 로더: `.sisyphus/notepads/p3-performance/worklog.md`
- P7 회귀 게이트: `.sisyphus/notepads/p7-regression/worklog.md`
- P9 오프라인 운영: `.sisyphus/notepads/p9-offline/worklog.md`

최근 항목은 00_overview의 “최근 작업 로그(SSoT 요약)”과 동일 근거를 공유한다.

---

## 10) 자기 점검 질문

1) 운영에서 DB 경로를 고정해야 하는 이유는 무엇인가?
2) 관측 옵션(트래커/Stage)을 켜는 기준을 팀에서 어떻게 정하면 좋은가?
3) 장애 대응에서 “run_id 확보”가 왜 첫 단계인가?

---

## 11) 향후 변경 시 업데이트 가이드

아래가 바뀌면 이 장을 함께 업데이트한다.

- `.env` 키/의미가 바뀜: `.env.example`, `src/evalvault/config/settings.py`
- `serve-api` 옵션/기본값이 바뀜: `src/evalvault/adapters/inbound/cli/commands/api.py`
- 오프라인 운영이 바뀜: `docs/guides/OFFLINE_DOCKER.md`, `docker-compose.offline.yml`, `scripts/offline/*.sh`
- ops snapshot/stage 명령이 바뀜: `src/evalvault/adapters/inbound/cli/commands/ops.py`, `src/evalvault/adapters/inbound/cli/commands/stage.py`
