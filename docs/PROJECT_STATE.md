# EvalVault — 프로젝트 현재 상태 (인수 핸드오프 문서)

> **문서 성격**: 인수받는 사내 팀이 EvalVault 코드/운영을 이어받기 위해 **가장 먼저 읽는 단일 진입점**.
> 세부 운영/설계 결정은 `docs/handbook/`에 위임하고, 이 문서는 "지금 무엇이 진실인가"의 SSoT(Single Source of Truth) 역할만 한다.
>
> - 기준 버전: **v1.77.0** (PyPI 배포 중 — main 기준)
> - 기준 브랜치: `main`
> - 기준 커밋: `bc88726 chore(release): 1.77.0 [skip ci]`
> - 마지막 검증일: **2026-05-22** (Phase 4 W-S6 / W-S3 / L-S2 / W-S5b 슬라이스 머지 대기 중 — §8.1 참조)
> - 작성/검증 책임: 인수 시점에 owner를 명시 → **(TBD: 인수팀 리더 이름 박아두기)**
> - 다음 검증 트리거: 새 minor 릴리스(예: v1.78.0)가 머지되면 이 문서의 §3, §8을 다시 검증

---

## 0. TL;DR (3분 안에 끝내는 요약)

- **무엇인가**: RAG(Retrieval-Augmented Generation) 시스템을 대상으로 **평가(Eval) → 분석(Analysis) → 추적(Tracing) → 개선** 루프를 묶는 **CLI + Web UI 플랫폼**. Ragas v0.4.2를 코어로 쓰고, MLflow + Phoenix dual-tracker가 기본값.
- **누구를 위해 만드는가**: RAG 시스템을 운영하며 "변경이 진짜 개선인지" 데이터셋·메트릭으로 재현 가능하게 검증해야 하는 팀. 한국어 보험 도메인이 1차 검증 도메인.
- **지금 상태**: **Production-ready**. Phase 1–14 완료, v1.77.0이 PyPI에 올라가 있고 CI는 Ubuntu/macOS/Windows × Python 3.12/3.13에서 통과. 1,352 tests passing, coverage 89%.
- **활발한 워크 스트림**: P0(안정성/재현성) · P1(자동 회귀 게이트, `.github/workflows/regression-gate.yml`) · P2(멀티턴 평가) · P3(GraphRAG 실험) · P4(Judge 캘리브레이션 Web UI) — 전부 코드는 있으나 일부는 "운영에서의 강제(브랜치 보호 등)"가 아직 끝나지 않음. §8 참고.
- **5분 안에 동작 확인**:
  ```bash
  uv sync --extra dev
  cp .env.example .env  # OPENAI_API_KEY 채우기
  uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
    --metrics faithfulness,answer_relevancy --profile dev --auto-analyze
  ```
- **무엇이 진실의 출처인가**: 코드 > 테스트 > CLI `--help` > 이 문서 > handbook. 문서와 코드가 충돌하면 코드를 따르고 이 문서를 갱신한다.

---

## 1. 제품 정체성과 비목표

### 1.1 제품 정체성

- **End-to-End 평가 루프**: Eval → Analysis → Tracing → Improvement 한 흐름.
- **Dataset 중심 운영**: 합격 기준(thresholds)을 환경변수가 아닌 **데이터셋 JSON 파일**에 기록 (재현성 보장).
- **Artifacts-first**: 결과 점수만이 아니라 **모듈별 원본 산출물**(retrieval 결과, prompt, judge log, embedding, KG 등)을 구조화 저장.
- **옵션형 Observability**: Phoenix / Langfuse / MLflow는 필요한 만큼만 켤 수 있음 (기본은 MLflow + Phoenix dual).
- **CLI + Web UI 동등성**: 같은 `run_id` 기준으로 히스토리·비교·리포트가 양쪽에서 일관되게 보임.

### 1.2 비목표 (Non-goals)

인수팀이 가장 자주 혼동하는 지점이라 명시한다:

- **RAG 시스템 자체를 만드는 도구가 아님** — EvalVault는 다른 사람이 만든 RAG를 평가/분석하는 layer.
- **LLM/임베딩을 호스팅하지 않음** — 외부 OpenAI/Azure/Anthropic/Ollama/vLLM에 의존. 폐쇄망에서는 **Ollama 또는 vLLM**으로 LLM을 외부 운영하고, EvalVault는 그것을 "사용"만 함.
- **Production traffic을 받는 서비스가 아님** — `serve-api`는 Web UI 백엔드용이며, 외부 SLA 대상이 아님.
- **단일 Judge 모델 의무화 없음** — Judge 모델은 프로필로 분리 가능 (`config/models.yaml`).

### 1.3 한국어/보험 도메인 의존

- 1차 검증 도메인이 **한국어 보험 QA**라서, fixtures와 기본 메트릭(`InsuranceTermAccuracy` 등)이 그 도메인에 맞춰져 있음.
- 한국어 NLP는 **`--extra korean`** 옵션 (kiwipiepy + rank-bm25 + sentence-transformers).
- 다른 도메인으로 옮기려면 fixtures와 일부 custom 메트릭을 교체해야 함 → §10 "다른 도메인으로 이식할 때".

---

## 2. 아키텍처 개요 (한 페이지)

### 2.1 패턴: Hexagonal (Ports & Adapters)

```
┌──────────────────────────────────────────────────────────────────┐
│                          inbound adapters                         │
│   ┌─────────────┐                       ┌─────────────────────┐   │
│   │  CLI (Typer)│                       │ FastAPI (Web UI 백) │   │
│   └──────┬──────┘                       └──────────┬──────────┘   │
└──────────┼─────────────────────────────────────────┼──────────────┘
           │                                         │
           ▼ EvaluatorPort                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                            domain layer                           │
│   entities (TestCase, Dataset, EvaluationRun, Experiment, ...)    │
│   services (RagasEvaluator, ExperimentManager, KGGenerator,       │
│             RegressionGateService, JudgeCalibrationService, ...)   │
│   metrics  (insurance, no_answer, contextual_relevancy,            │
│             multiturn_metrics, retrieval_rank, summary_*, ...)     │
└────┬───────────┬─────────────┬──────────────────┬─────────────────┘
     │           │             │                  │
     ▼ LLMPort   ▼ DatasetPort ▼ StoragePort       ▼ TrackerPort
┌──────────────────────────────────────────────────────────────────┐
│                          outbound adapters                        │
│   LLM:     OpenAI · Anthropic · Azure · Ollama · vLLM             │
│   Dataset: CSV · Excel · JSON                                     │
│   Storage: SQLite · PostgreSQL (pgvector)                         │
│   Tracker: MLflow · Phoenix · Langfuse  (MultiTracker: planned)   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 데이터 흐름

```
Input dataset (JSON/CSV/Excel)
       ↓
RagasEvaluator (+ custom metrics)            ←  LLMPort (judge LLM)
       ↓
EvaluationRun + per-test MetricScore
       ↓                                ↘
StoragePort (SQLite/PG)              TrackerPort (MLflow + Phoenix [+ Langfuse])
       ↓
AnalysisPipeline (DAG, intent 분류, 클러스터링, 리포트)
       ↓
Reports + Artifacts (data/, reports/) — run_id 기반 조회
```

### 2.3 핵심 관찰

- 도메인은 어떤 어댑터도 알지 못함. 모든 결합은 `ports/`에서만 일어남.
- 모든 실행은 `run_id`로 묶임 — 인수받았을 때 "이 결과를 만든 환경이 무엇이었나"를 추적할 수 있는 1차 키.
- Tracker는 **dual이 기본**: MLflow는 experiment 관리, Phoenix는 trace/observability. Langfuse는 옵션.

**상세 → `docs/handbook/CHAPTERS/01_architecture.md`** (다이어그램, 디렉토리 트리, 의사결정 근거 포함)

---

## 3. 구현 현황 (SSoT 표)

> 이 표는 **이 문서 작성 시점(v1.77.0, 2026-05-21)에 코드와 1:1 검증된** 상태다.
> 표의 ✅는 "코드가 있고 테스트가 있다"는 의미이며, 운영에서 강제되는지는 §9를 봐라.

### 3.1 도메인 레이어

| 영역 | 상태 | 근거 |
|---|---|---|
| Entities (22개) | ✅ Complete | `src/evalvault/domain/entities/` — TestCase, Dataset, EvaluationRun, Experiment, Benchmark, MultiTurn, GraphRAG, JudgeCalibration, KG, Analysis, RagTrace, Stage, Method, OpsReport, Memory, Feedback, Improvement, Prompt, PromptSuggestion, Result, Debug |
| Services (61개) | ✅ Complete | `src/evalvault/domain/services/` — 핵심: RagasEvaluator, ExperimentManager, KGGenerator, RegressionGateService, JudgeCalibrationService, MultiturnEvaluator, GraphRAGExperiment, AnalysisService, PipelineOrchestrator, BatchExecutor (async/sync) |
| Custom Metrics | ✅ Complete | `src/evalvault/domain/metrics/` — insurance, no_answer, entity_preservation, contextual_relevancy, retrieval_rank, multiturn_metrics, summary_*, text_match, confidence |
| Ragas 빌트인 메트릭 | ✅ Complete | 6종: faithfulness, answer_relevancy, context_precision, context_recall, factual_correctness, semantic_similarity |

### 3.2 Port × Adapter 매트릭스

| Port | Adapter | 상태 | 근거 |
|---|---|---|---|
| LLMPort | OpenAI | ✅ | `adapters/outbound/llm/openai_adapter.py` |
| LLMPort | Anthropic | ✅ | `adapters/outbound/llm/anthropic_adapter.py` (`--extra anthropic`) |
| LLMPort | Azure OpenAI | ✅ | `adapters/outbound/llm/azure_adapter.py` |
| LLMPort | Ollama | ✅ | `adapters/outbound/llm/ollama_adapter.py` |
| LLMPort | vLLM | ✅ | `adapters/outbound/llm/vllm_adapter.py` |
| DatasetPort | CSV / Excel / JSON | ✅ | `adapters/outbound/dataset/` |
| StoragePort | SQLite | ✅ | `adapters/outbound/storage/sqlite_adapter.py` |
| StoragePort | PostgreSQL (+pgvector) | ✅ | `adapters/outbound/storage/postgres_adapter.py` + `postgres_schema.sql` (`--extra postgres`) |
| TrackerPort | MLflow | ✅ | `adapters/outbound/tracker/mlflow_adapter.py` (`--extra mlflow`) |
| TrackerPort | Phoenix | ✅ | `adapters/outbound/tracker/phoenix_adapter.py` (`--extra phoenix`) |
| TrackerPort | Langfuse | ✅ | `adapters/outbound/tracker/langfuse_adapter.py` |
| TrackerPort | MultiTracker (MLflow + Phoenix dual) | ⚠️ 문서상 명시, 실구현 없음 — A-S3에서 구현 예정 | dual-logging은 현재 `cli/commands/run_helpers.py:339-377` + `api/adapter.py:238-286`에서 수동 합성. `MultiTrackerAdapter` 클래스 grep 0건. 결정: Option A (실제 구현) → `REFACTOR_DIAGNOSIS.md §0.5` |
| EvaluatorPort | RagasEvaluator | ✅ | `domain/services/evaluator.py` |

### 3.3 인수 시 알아야 할 부가 컴포넌트

| 영역 | 상태 | 근거 |
|---|---|---|
| Korean NLP (Kiwi 형태소, BM25, Dense/Hybrid Retrieval) | ✅ | `adapters/outbound/nlp/`, `adapters/outbound/retriever/` (`--extra korean`) |
| Knowledge Graph (KG) 생성·실험 | ✅ | `domain/services/kg_generator.py`, `graph_rag_experiment.py` |
| 멀티턴 평가 | ✅ | `domain/entities/multiturn.py`, `domain/services/multiturn_evaluator.py` |
| 자동 회귀 게이트 (CI) | ⚠️ 코드 ✅ / 운영 강제 ⚠️ | `domain/services/regression_gate_service.py` + `.github/workflows/regression-gate.yml` — **GitHub 브랜치 보호 설정은 별도로 운영팀이 해야 강제됨** |
| Web UI (React 19 + Vite 7 + Tailwind 4) | ✅ | `frontend/` (17개 페이지, Playwright e2e 포함) |
| FastAPI Web 백엔드 | ✅ | `adapters/inbound/api/` (CLI `evalvault serve-api`) |
| 오프라인 번들 (Docker + 모델 캐시) | ✅ | `scripts/offline/`, `docker-compose.offline*.yml` |

### 3.4 테스트 요약

- **Test 파일**: 130개 (`tests/unit` 119 + `tests/integration` 11)
- **테스트 케이스**: 1,261 unit + 91 integration = **1,352 passing**
- **Coverage**: 89%
- **마커**: `slow`, `requires_openai`, `requires_langfuse`, `requires_phoenix`
- CI 매트릭스: Ubuntu/macOS/Windows × Python 3.12/3.13

> 검증 방법: `uv run pytest tests/ -v -m "not requires_openai and not requires_langfuse"` 로 외부 키 없이도 대부분 통과해야 함.

---

## 4. CLI / API / UI Surface

### 4.1 CLI 진입점

배포 시 `evalvault` 명령으로 노출되며 (`pyproject.toml` → `[project.scripts]`),
구조는 **루트 커맨드 + 서브앱**으로 나뉜다.

**루트 커맨드 (17개)** — 등록 코드: `src/evalvault/adapters/inbound/cli/commands/__init__.py` (`COMMAND_MODULES`):

| 명령 | 한 줄 설명 |
|---|---|
| `init` | 새 프로젝트/데이터셋 스캐폴딩 |
| `run` | 평가 실행 (메인 진입) |
| `pipeline` | 분석 파이프라인 실행 (`pipeline analyze "..."` 등) |
| `history` | 과거 run 목록 조회 |
| `compare` | 두 run 비교 |
| `analyze` | 단독 분석 실행 |
| `calibrate` | RAGAS 보정 |
| `calibrate-judge` | Judge LLM 캘리브레이션 |
| `generate` | testset 생성 (Basic + KG 기반) |
| `gate` | 임계값 기반 합/불합격 판정 |
| `profile-difficulty` | 데이터셋 난이도 프로파일링 |
| `regress` | 회귀 비교 (`regress`, `regress-baseline`, `ci-gate`) |
| `agent` | 운영 에이전트 호출 (CLI 명령, `src/evalvault/config/agent_types.py` 기반 — repo-root `agent/` 폴더와 무관) |
| `experiment` | A/B 실험 관리 |
| `config` | 현재 설정 출력/검증 |
| `langfuse` | Langfuse 동기화/유틸 |
| `api` | FastAPI 서버 기동 (`serve-api` 등) |

**서브앱 (11개)** — 등록 코드: 같은 파일의 `SUB_APPLICATIONS`. 호출 형식은 `evalvault <서브앱> <명령>`:

`kg`, `domain`, `benchmark`, `graphrag`, `method`, `ops`, `phoenix`, `prompts`, `stage`, `artifacts`, `debug`

> **검증 명령**: `uv run evalvault --help` 출력이 위 표와 1:1 일치해야 함. 어긋나면 이 문서가 stale.

### 4.2 Web UI 페이지 (총 16개; W-S3-Phase2에서 orphan `ComprehensiveAnalysis` 삭제됨)

`frontend/src/pages/`:

`AiSdkChat`, `AnalysisCompareView`, `AnalysisLab`, `AnalysisResultView`, `Chat`, `CompareRuns`, `CustomerReport`, `Dashboard`, `DomainMemory`, `EvaluationStudio`, `JudgeCalibration`, `KnowledgeBase`, `RunDetails`, `Settings`, `Visualization`, `VisualizationHome`

- 진입점: `EvaluationStudio` (실행) / `AnalysisLab` (분석) / `Dashboard` (요약).
- 시각화: Plotly + Recharts.
- e2e 테스트: Playwright (`frontend/` 디렉토리에 구성).

### 4.3 FastAPI 백엔드

- 기동: `uv run evalvault serve-api --reload` (개발) 또는 `uv run evalvault serve-api --host 0.0.0.0 --port 8000` (프로덕션).
- 위치: `src/evalvault/adapters/inbound/api/` (Web UI 전용).
- 외부 SLA 대상 아님. Web UI 백엔드로만 사용.

---

## 5. 데이터 / 설정 / 계약

### 5.1 입력 데이터셋 스키마 (JSON 표준 형식)

```json
{
  "name": "insurance-qa-dataset",
  "version": "1.0.0",
  "thresholds": {
    "faithfulness": 0.8,
    "answer_relevancy": 0.7,
    "context_precision": 0.7,
    "context_recall": 0.7
  },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "이 보험의 보장금액은 얼마인가요?",
      "answer": "보장금액은 1억원입니다.",
      "contexts": ["해당 보험의 사망 보장금액은 1억원입니다."],
      "ground_truth": "1억원"
    }
  ]
}
```

- **thresholds**: 메트릭별 통과 기준 (0.0–1.0). 미지정 시 0.7 default.
- CSV/Excel 포맷도 동일 컬럼 구조 — `id, question, answer, contexts, ground_truth`.
- 멀티턴 데이터셋은 별도 스키마 — `tests/fixtures/e2e/multiturn_benchmark.json` 참고.

### 5.2 환경변수 (필수/선택)

`.env.example`을 복사한 뒤 채워 넣는다.

| 변수 | 필수 | 용도 |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Judge LLM (default `gpt-5-mini`) |
| `OPENAI_MODEL` | ⛔ | Override (예: `gpt-5-nano`) |
| `OPENAI_EMBEDDING_MODEL` | ⛔ | 기본 `text-embedding-3-small` |
| `MLFLOW_TRACKING_URI` | ✅ (default tracker일 때) | 기본 `http://localhost:5000` |
| `PHOENIX_ENDPOINT` | ✅ (default tracker일 때) | 기본 `http://localhost:6006` |
| `TRACKER_PROVIDER` | ⛔ | `mlflow+phoenix` (default) / `mlflow` / `phoenix` / `langfuse` |
| `LANGFUSE_*` | 옵션 | Langfuse 사용 시 |
| `DB_BACKEND`, `EVALVAULT_DB_PATH` | 옵션 | 기본 Postgres+pgvector, SQLite로 바꿀 때 |
| `EVALVAULT_PROFILE` | 옵션 | 예: `vllm`, `dev`, `ollama` (config/models.yaml 키와 매칭) |
| `VLLM_BASE_URL`, `VLLM_MODEL` | vLLM 사용 시 | 외부 vLLM 서버 |
| `ANTHROPIC_API_KEY` | Anthropic LLM 사용 시 (`--extra anthropic`) | `adapters/outbound/llm/anthropic_adapter.py` 의존 |

### 5.3 프로필 (Model Configuration)

- 위치: `config/models.yaml`
- 역할: judge model, embedding model, retrieval 파라미터를 **환경별 묶음**으로 관리.
- 사용: `--profile dev`, `--profile vllm` 등 CLI 옵션으로 선택.
- 잘못된 프로필명은 **초기 단계에서 실패**해야 함 (P0 안정성 정책, 2026-01-26 적용).

### 5.4 산출물(Artifacts) 저장 규약

- `data/` — 평가 입력/중간 데이터
- `reports/` — run 단위 리포트 (markdown/HTML/Excel)
- DB는 SQLite 또는 PostgreSQL — `EvaluationRun`, `MetricScore`, `Experiment` 등이 영속화됨.
- 모든 산출물은 **`run_id`로 1:1 매칭** 가능해야 함 — 안 그러면 P0 위반.

---

## 6. 외부 의존성 / 인프라

### 6.1 런타임 의존

- **Python 3.12+** (`requires-python = ">=3.12"`)
- 핵심 런타임 (pyproject.toml `[project.dependencies]`):
  `ragas==0.4.2`, `langfuse`, `instructor`, `openai`, `langchain-openai`, `networkx`, `pydantic`, `pydantic-settings`, `typer`, `rich`, `pandas`, `openpyxl`, `pypdf`, `xlrd`, `chardet`, `truststore` (macOS+uv SSL fix), `fastapi`, `uvicorn`, `matplotlib`, `chainlit`
- 옵션 extras (`pyproject.toml`):
  `dev`, `docs`, `analysis`, `anthropic`, `dashboard`, `timeseries`, `postgres`, `mlflow`, `phoenix`, `korean`, `perf`, `benchmark`, `secrets`

### 6.2 Frontend 의존 스택

- React 19, Vite 7, TypeScript 5.9, Tailwind 4
- AI SDK (Vercel `ai`, `@ai-sdk/react`)
- Plotly + Recharts (시각화)
- Playwright (e2e — 18 specs, 머지 대기 중인 W-S6에서 lucide 1.16 호환 refresh)
- `lucide-react` 아이콘 (W-S6 머지 후 1.16)
- 디자인 시스템 (W-S1 머지 후): `frontend/src/design/` — Button, Card, Table, EmptyState, MetricChip, AuthorityBadge primitive + Claude 토큰 (`tokens.css`)

### 6.3 외부 서비스/도구

| 서비스 | 역할 | 운영자 책임 |
|---|---|---|
| OpenAI / Azure / Anthropic | Judge LLM, 임베딩 | 키 관리, 비용 모니터링 |
| Ollama / vLLM | 폐쇄망/로컬 LLM | 폐쇄망 인프라팀이 별도 운영. EvalVault는 endpoint만 사용 |
| MLflow Tracking Server | 실험 기록 | `MLFLOW_TRACKING_URI` 지정. 기본 `localhost:5000` |
| Phoenix (Arize) | Trace observability | `PHOENIX_ENDPOINT` 지정. 기본 `localhost:6006` |
| Langfuse | 옵션 trace logging | self-hosted or cloud |
| PostgreSQL + pgvector | 기본 DB | 인수팀이 운영. SQLite로 대체 가능 |

### 6.4 Docker Compose 시나리오

- `docker-compose.yml` — 기본 개발 스택
- `docker-compose.langfuse.yml` — Langfuse playground
- `docker-compose.phoenix.yaml` — Phoenix 단독
- `docker-compose.offline.yml` + `.build.yml` + `.modelcache.yml` — 폐쇄망 배포

상세 → `docs/guides/OFFLINE_DOCKER.md`, `docs/guides/OFFLINE_MODELS.md`

---

## 7. 운영 / 배포 / 릴리스

### 7.1 로컬 개발 (5분 셋업)

```bash
uv sync --extra dev          # dev + 전체 extras 한 번에
cp .env.example .env         # OPENAI_API_KEY 채우기
uv run pytest tests/ -v -m "not requires_openai and not requires_langfuse"
uv run evalvault --help      # CLI 확인
```

### 7.2 CI/CD

**GitHub Actions 워크플로 (`.github/workflows/`)**:

| 워크플로 | 트리거 | 역할 |
|---|---|---|
| `ci.yml` | push/PR → main, develop | Lint(ruff), format, pytest (전 플랫폼) |
| `regression-gate.yml` | PR | baseline 대비 회귀 자동 비교 → PR 코멘트로 근거 표시 |
| `release.yml` | push → main | python-semantic-release 기반 자동 버전 + PyPI 배포 + GitHub Release |
| `stale.yml` | 주기 | 오래된 이슈/PR 정리 |

**자동 버저닝 (python-semantic-release)**:

| Commit type | Bump | 예시 |
|---|---|---|
| `feat:` | minor | `1.77.0 → 1.78.0` |
| `fix:`, `perf:` | patch | `1.77.0 → 1.77.1` |
| `docs:`, `chore:`, `ci:`, `test:`, `style:`, `refactor:` | no release | — |

**중요**: `pyproject.toml`의 `version` 필드는 릴리스 워크플로가 동기화. **실제 배포 버전은 git tag가 1차 진실**.

### 7.3 릴리스 절차

- 자동 — `main` 머지 시 commit type에 따라 버전 결정 → 태그 → PyPI 업로드 → GitHub Release 생성.
- 수동 개입 필요한 경우: `docs/guides/RELEASE_CHECKLIST.md` 참고.

### 7.4 오프라인/폐쇄망 배포

1. `./scripts/offline/build_full_offline_bundle.sh` — 빌드머신에서 이미지 + 모델 캐시 번들 생성.
2. 폐쇄망으로 번들 옮김.
3. `./scripts/offline/import_images.sh` + `./scripts/offline/restore_model_cache.sh`
4. `docker compose -f docker-compose.offline.yml up -d`

상세 → `docs/guides/OFFLINE_DOCKER.md`, `docs/guides/OFFLINE_MODELS.md`
주의 → **LLM 자체는 폐쇄망 내부 인프라가 관리**. EvalVault는 분석용 NLP 모델 캐시만 번들에 포함.

### 7.5 기여 / 코드 품질 게이트

```bash
uv run ruff check src/ tests/        # 라인 길이 100
uv run ruff format src/ tests/
uv run pytest tests/ -v
```

- 모든 PR은 위 3개 통과 + CI 매트릭스 통과 + regression gate 통과해야 함.
- Conventional Commits 강제 — 안 그러면 자동 릴리스가 깨짐.

---

## 8. 활발한 워크 스트림 (Active Work)

> SSoT는 `docs/handbook/CHAPTERS/08_roadmap.md`. 이 섹션은 인수팀이 "지금 무엇이 움직이고 있나"를 한눈에 보기 위한 요약.

| P-level | 주제 | 상태 | 인수팀이 알아야 할 것 |
|---|---|---|---|
| **P0** 안정성/재현성 | 프로필 검증, run_id 규약, DB 저장 일관성 | 진행 중 (지속) | 2026-01-26 `apply_profile` 에러 처리 추가. 인수 후에도 **P0가 가장 우선**임을 합의해야 함 |
| **P1** 자동 회귀 게이트 | baseline vs current 자동 비교 → PR 차단 | 코드 ✅, 운영 강제 ⚠️ | `regression-gate.yml`은 있지만, **GitHub 브랜치 보호 룰에서 required check로 지정해야 진짜로 막힘**. 인수팀이 직접 설정 필요 |
| **P2** 멀티턴 RAG 평가 | 턴별/전체 일관성·드리프트 메트릭 | 진행 중 | 스키마/CLI 로더 추가됨 (2026-01-27). 벤치마크 데이터셋(`tests/fixtures/e2e/multiturn_benchmark.json`)이 3–10턴 + 드리프트 케이스 |
| **P3** GraphRAG 실험 프레임워크 | top-k vs GraphRAG A/B, 하이브리드(BM25+Dense), pgvector | 진행 중 | `graph_rag_experiment.py` 있음. 범위 폭발 위험 — v0(휴리스틱) → v1(LLM) 단계화 합의 필요 |
| **P4** Judge 캘리브레이션 Web UI | 캘리브레이션 결과 UI 탐색·공유 | 진행 중 | `frontend/src/pages/JudgeCalibration.tsx` + Playwright e2e 추가됨 (2026-01-27) |

**우선순위 결정 규칙** (인수 후에도 유지 권장):

1. 이것이 없으면 다른 작업 결과가 신뢰되지 않는가? → P0
2. 사람이 매번 판단해야 해서 실수 위험이 있는가? → P1
3. 사용자가 실제로 겪는 문제를 측정 못 하는가? → P2
4. 성능 개선 주장에 실험 프레임이 필요한가? → P3
5. 공유/운영 효율을 크게 올리는가? → P4

### 8.1 머지 대기 중인 슬라이스 (2026-05-22 기준)

> 메인(main, `bc88726`)에 아직 머지되지 않은 feature 브랜치 진행 상황. 각 브랜치는 자체 build / Playwright / unit-test 검증을 통과하고 origin에 푸시되어 있음.

**Phase 4 — Web frontend overhaul** (Claude 디자인 시스템 surgical 마이그레이션):

| 슬라이스 | 브랜치 | 커밋 | 적용 영역 |
|---|---|---|---|
| W-S1 design system | `refactor/w-s1-design-system` | — | Button, Card, Table, EmptyState, MetricChip, AuthorityBadge 6 primitive 추가 |
| W-S2 ~ W-S5 | `refactor/w-s2-*` … `refactor/w-s5-secondary-pages` | (누적) | Dashboard, EvaluationStudio, AnalysisLab, RunDetails, CompareRuns, AiSdkChat, JudgeCalibration, KnowledgeBase, VisualizationHome, CustomerReport 토큰화 |
| W-S6 lucide bump + e2e | `refactor/w-s6-playwright-lucide-bump` | `6220202` | lucide-react 0.562 → 1.16, Playwright 18/18, 3개 dead-import 정리 |
| W-S3 Analysis 통합 plan | `refactor/w-s3-analysis-consolidation` | `853c8c1` | `docs/guides/W-S3-ANALYSIS-CONSOLIDATION.md` plan + 2개 페이지 surgical |
| W-S5b Settings | `refactor/w-s5b-settings-migration` | `78464fd` | Settings.tsx 에러/버튼 design primitive 적용 |

**Phase 3.5 — 의존성 라인 업데이트:**

| 슬라이스 | 브랜치 | 커밋 | 변경 |
|---|---|---|---|
| L-S0 / L-S1 / L-S2i | (누적, 일부는 main에 머지됨) | — | Anthropic 0.34→0.43, mkdocstrings 0→1.0.4 등 |
| L-S2 LLM 클러스터 | `refactor/l-s2-llm-cluster-bump` | `88739ab` | openai 1.40→2.38, instructor 1.4→1.15, langchain-openai 0.2→1.2 |

**알아야 할 것**:

- 모든 위 슬라이스는 origin에 푸시되어 있고 머지/리뷰 대기.
- L-S2는 `src/` diff 0줄 (LLM 프롬프트 byte-identical 보존, [[feedback_llm_prompt_discipline]] 원칙 준수).
- rich 15+ bump은 instructor 1.15 metadata가 rich<15를 강제하여 deferred (US-008 트래킹).
- T0-T4 권한 hierarchy 준수: T2 cap, T3 (promote/rollback) 문자열 신규 도입 0건.
- 회귀 anti-target 비변경 (`regression_gate_service.py`, `regression_baseline.json`, `regression-gate.yml`, `domain/metrics/*`).

---

## 9. 알려진 갭 / 리스크 (Known Gaps)

인수받는 팀이 **모르고 들어왔다가 다칠 곳**만 솔직하게 적는다.

### 9.1 운영 강제력 갭

- **회귀 게이트는 코드만 있고 강제는 GitHub 브랜치 보호에 의존**. 인수 직후 확인할 것:
  - Repo Settings → Branches → `main` → Require status checks → `regression-gate` 포함 여부
  - 없으면 추가해야 P1 DoD 충족.
- **메인 보호 룰 자체가 약하면** 자동 릴리스가 부적절한 커밋으로 발화될 수 있음.

### 9.2 문서 거버넌스 갭

- `docs/STATUS.md`, `docs/ROADMAP.md`, `docs/guides/USER_GUIDE.md`, `docs/guides/DEV_GUIDE.md`, `docs/getting-started/INSTALLATION.md` 등이 **deprecated 스텁**. 인수팀이 새로 검색하면 stale 문서로 진입할 수 있음. handbook으로 강제 리디렉션 필요.
- `docs/guides/` 아래 50+개 plan/worklog 문서가 적층 — 일부는 완료된 작업의 잔재. 정리 결정: handbook으로 흡수 vs 삭제 vs 보존 — 인수팀이 결정해야 함.
- `docs/handbook/CHAPTERS/00_overview.md`가 985줄로 비대. 외부 진입자 관점에서는 무거움 — 이 PROJECT_STATE.md가 그 대안.

### 9.3 버전/배포 갭

- **`pyproject.toml` 버전 vs git tag**: 자동 릴리스가 sync하지만, 수동 머지나 hot-fix 시 어긋날 수 있음. 항상 **git tag를 1차 진실로 본다**.
- PyPI 패키지명(`evalvault`) vs 명령어(`evalvault`) vs 모듈(`evalvault`) — 동일하지만, 다른 이름의 fork가 PyPI에 올라와 혼동될 수 있으므로 인수팀이 ownership 명확히 해야 함.

### 9.4 외부 의존 리스크

- **OpenAI 비용/레이트리밋**: 기본 judge가 `gpt-5-mini`라 평가 횟수 늘면 비용 폭증 가능. 프로필로 ollama/vllm으로 옮기는 시나리오 준비 필요.
- **Ragas v0.4.2 pin**: ragas major bump이 일어나면 RagasEvaluator를 손봐야 함. 자동 dependency bump 정책 확인 필요.
- **`matplotlib<3.9.0`** 핀 — manim/scikit-learn 호환 때문일 가능성. 무심코 풀면 OS별 빌드가 깨질 수 있음.
- **LLM 클러스터 transitive coupling** (L-S2에서 확인): `openai` / `instructor` / `langchain-openai` / `rich`가 서로 metadata 캡으로 묶여 있어, 한 패키지만 bump 시도하면 다른 패키지가 backwards로 강제됨. 머지 대기 중인 L-S2가 openai 2.x / instructor 1.15 / langchain-openai 1.2를 같이 올렸고, rich 15는 instructor 1.15 metadata 캡(`rich<15.0`)에 막혀 별도 follow-up. 추후 single-package bump 제안 들어오면 transitive 검증 먼저 할 것.
- **manim → pycairo → Cairo 시스템 라이브러리**: `uv sync --extra dev`가 `pycairo` 빌드 단계에서 `pkg-config`/`cairo` 부재 시 실패. 인수 머신에서 `brew install pkg-config cairo` (macOS) 또는 패키지 매니저 등가물 사전 설치 필요. dev extras 슬림화 검토 가치 있음.

### 9.5 도메인 의존 리스크

- 한국어 보험 도메인에 최적화된 fixtures와 메트릭이 있어, 다른 도메인으로 옮기면 **회귀 게이트 baseline이 의미 없을 수 있음**. baseline 재설정 정책 합의 필요.

### 9.6 (제거됨) 에이전트 시스템 의존

> 2026-05-21: 인수팀 결정 (`REFACTOR_DIAGNOSIS.md §0.5`) 에 따라 `agent/` 디렉토리 전면 제거 (슬라이스 X-S1). 이 항목은 더 이상 리스크가 아니다. CLI 명령 `evalvault agent`(운영 에이전트, `src/evalvault/config/agent_types.py` 기반)는 별개 기능으로 유지.

---

## 10. 인수팀을 위한 첫 30일 가이드

### 10.1 첫 일주일: "실제로 동작시켜본다"

1. 로컬 환경 구성 (`uv sync --extra dev`).
2. `uv run pytest tests/ -v -m "not requires_openai and not requires_langfuse"` 전체 통과 확인.
3. `tests/fixtures/e2e/insurance_qa_korean.json`로 dry-run.
4. Web UI 띄워서 `EvaluationStudio`에서 같은 데이터셋 실행 → 같은 `run_id`로 history/compare 동작 확인.
5. `docs/handbook/CHAPTERS/00_overview.md` + `01_architecture.md` 정독.

### 10.2 둘째 주: "운영을 점검한다"

1. `regression-gate.yml`이 실제 PR에서 발화되는지 의도적 PR로 검증.
2. GitHub 브랜치 보호 룰 점검 (§9.1).
3. PyPI 자동 배포 권한 점검 (누가 publish 권한인가?).
4. MLflow + Phoenix 백엔드의 운영 위치/접근 권한 점검.
5. 폐쇄망 번들 빌드 테스트 (`scripts/offline/build_full_offline_bundle.sh`).

### 10.3 셋째 주: "도메인을 이해한다"

1. 한국어 보험 fixtures 정독: `tests/fixtures/e2e/insurance_qa_korean.json`, `multiturn_benchmark.json`.
2. Custom 메트릭 코드 정독: `src/evalvault/domain/metrics/insurance.py`, `summary_*.py`.
3. `docs/handbook/CHAPTERS/02_data_and_metrics.md` 정독.
4. 자신의 도메인 데이터셋 1개로 fixtures를 교체해 실행 → §9.5의 baseline 재설정 정책 결정.

### 10.4 넷째 주: "다음 우선순위를 정한다"

1. §8의 P0–P4 워크 스트림 중 어떤 것을 유지/일시중지/종료할지 결정.
2. 결정 사항을 `docs/handbook/CHAPTERS/08_roadmap.md`와 이 PROJECT_STATE.md §8에 반영.
3. 이 PROJECT_STATE.md의 책임자(owner) 항목을 인수팀 리더로 갱신.

### 10.5 다른 도메인으로 이식할 때 (선택)

1. `tests/fixtures/`의 한국어 보험 fixtures → 신규 도메인 fixtures로 교체.
2. `src/evalvault/domain/metrics/insurance.py` → 도메인 custom 메트릭으로 대체 (registry에 등록).
3. `--extra korean`이 필요 없으면 빌드에서 제외.
4. Threshold 재설정 (도메인마다 기준이 다름).
5. Baseline 재실행 후 회귀 게이트 baseline 갱신.

---

## 11. 진실의 출처 지도 (Source of Truth Map)

| 알고 싶은 것 | 어디를 보라 | 비고 |
|---|---|---|
| 최신 변경사항 | GitHub Releases + `CHANGELOG.md` | release.yml이 자동 생성 |
| 배포된 실제 버전 | `git tag --sort=-v:refname \| head -1` | pyproject.toml보다 우선 |
| CLI 명령어 사양 | `uv run evalvault --help` + `commands/__init__.py` | 이 문서 §4.1 표 |
| 아키텍처 결정/패턴 | `docs/handbook/CHAPTERS/01_architecture.md` | |
| 메트릭 정의/임계값 정책 | `docs/handbook/CHAPTERS/02_data_and_metrics.md` + `src/evalvault/domain/metrics/` | thresholds는 데이터셋 JSON |
| 워크플로 (실행/비교/회귀) | `docs/handbook/CHAPTERS/03_workflows.md` | |
| 운영/런북 (로컬/Docker/오프라인) | `docs/handbook/CHAPTERS/04_operations.md` | |
| 보안 정책 | `SECURITY.md` + `docs/handbook/CHAPTERS/05_security.md` | |
| 품질 게이트/테스트 정책 | `docs/handbook/CHAPTERS/06_quality_and_testing.md` + `AGENTS.md` | |
| UX/제품 방향 | `docs/handbook/CHAPTERS/07_ux_and_product.md` | |
| 로드맵/우선순위 결정 규칙 | `docs/handbook/CHAPTERS/08_roadmap.md` | 이 문서 §8 요약본 |
| 경쟁/포지셔닝 | `docs/handbook/CHAPTERS/09_competitive_positioning.md` | |
| 운영 에이전트 CLI | `src/evalvault/adapters/inbound/cli/commands/agent.py` + `src/evalvault/config/agent_types.py` | `evalvault agent` 서브앱 |
| Open RAG Trace 스펙 | `docs/architecture/open-rag-trace-spec.md` | |
| 진단 플레이북 | `docs/guides/EVALVAULT_DIAGNOSTIC_PLAYBOOK.md` | 장애 대응용 |
| 배포 체크리스트 | `docs/guides/RELEASE_CHECKLIST.md` | |
| 외부 공개 요약 | `docs/handbook/EXTERNAL.md` | 28줄 짜리 외부용 |

**규칙**: 이 표 안에 없는 문서는 deprecated이거나 부차 자료다. 진실을 찾을 때는 이 표부터 본다.

---

## 12. 이 문서의 유지보수

- **위치**: `docs/PROJECT_STATE.md` (이동 금지 — 인수 link 깨짐)
- **언어**: 한국어 1차. 영문 동기화본은 현재 없음 (인수팀이 사내라 불필요 결정).
- **갱신 주기**: 모든 minor 릴리스(`feat:` 머지로 인한 bump) 직후 검증.
- **갱신 책임**: PROJECT_STATE.md owner (인수 시점에 박아둘 것).
- **검증 절차** (자동화 권장):
  1. `uv run evalvault --help` 출력과 §4.1 표 1:1 비교.
  2. `rg -nE 'TODO|TBD|REPLACE_ME|XXX|FIXME' docs/PROJECT_STATE.md`로 placeholder 확인.
  3. `git log --since="<지난 갱신일>" --oneline`로 새 commit 중 §3에 영향 가는 것 식별.
  4. §3의 ✅ 행에 대해 `rg -l "<adapter 이름>" src/` 로 코드 실재 확인.
- **변경 이력**: 큰 변경 시 §0 헤더의 "기준 버전"과 "마지막 검증일"을 반드시 갱신.

---

## 부록 A — Quick Reference

```bash
# 설치
uv sync --extra dev

# 평가 실행
uv run evalvault run --mode simple <dataset.json> \
  --metrics faithfulness,answer_relevancy --profile dev --auto-analyze

# 분석 파이프라인 (한국어 NLP 필요: --extra korean)
uv run evalvault pipeline analyze "요약해줘"

# 회귀 게이트 (CI에서 자동 발화)
uv run evalvault regress
uv run evalvault regress-baseline
uv run evalvault ci-gate

# Web UI
uv run evalvault serve-api --reload      # 백엔드
cd frontend && npm install && npm run dev  # 프론트 (localhost:5173)

# 품질 게이트
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pytest tests/ -v

# 폐쇄망 번들
./scripts/offline/build_full_offline_bundle.sh
```

## 부록 B — 인수 직후 결정해야 할 항목 체크리스트

- [ ] 이 문서의 **owner** 박기 (§0)
- [ ] GitHub 브랜치 보호 룰에 `regression-gate` required check 추가 (§9.1)
- [ ] PyPI publish 권한 인계 (§9.3)
- [ ] MLflow/Phoenix 서버 운영 위치 인계 (§6.3)
- [ ] OpenAI/Azure/Anthropic 키 인계 + 비용 limit 설정 (§9.4)
- [ ] `docs/guides/` 누적 plan/worklog 문서 정리 정책 (§9.2)
- [x] `agent/` 서브시스템 — 제거됨 (X-S1, 2026-05-21)
- [ ] 도메인 이식 여부 결정 (§10.5) — 한국어 보험 유지 vs 신규
- [ ] §8 P0–P4 워크 스트림 우선순위 재합의
- [ ] 이 문서의 다음 검증일 캘린더 등록
