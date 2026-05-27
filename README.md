# EvalVault

RAG(Retrieval-Augmented Generation) 시스템을 대상으로 **평가(Eval) → 분석(Analysis) → 추적(Tracing) → 개선 루프**를 하나의 워크플로로 묶는 CLI + Web UI 플랫폼입니다.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

English version? See `README.en.md`.

---

## EvalVault이 푸는 문제

"이번에 바꾼 RAG, 정말 좋아졌나?"를 **데이터셋·메트릭·임계값으로 명확히 답하고**, 그 근거(점수·트레이스·아티팩트)를 한곳에서 재현·비교·추적하게 하는 것이 목표입니다. 단순 채점 스크립트가 아니라, RAG 워크로드를 위한 **평가 + 관측(Observability) + 분석 레이어**입니다.

- **데이터셋 중심 운영** — 합격 기준(threshold)·메트릭·도메인 지식을 데이터셋이 함께 들고 다님
- **리트리버/LLM/프로필 분리** — OpenAI·Ollama·vLLM·Azure·Anthropic를 `config/models.yaml` 프로필로 교체
- **Stage 단위 추적** — input → retrieval → rerank → generation 전 구간을 `StageEvent`/`StageMetric`으로 기록
- **Open RAG Trace 표준** — OpenTelemetry + OpenInference 스키마로 외부 RAG 시스템도 동일 포맷으로 추적
- **Domain Memory & 분석 파이프라인** — 과거 실행에서 학습해 임계값 자동 조정·컨텍스트 보강·개선 가이드 생성
- **CLI + Web UI** — 동일 `run_id`/DB/트레이스 위에서 실행·히스토리·비교·리포트를 통합

> 상태: 안정(Hexagonal 아키텍처, 듀얼 트래커, 2,100+ 통과 테스트). Phase 1–14 + 리팩토링 슬라이스 완료. 최신 변경은 [CHANGELOG.md](CHANGELOG.md) 참조.

---

## Quickstart

### CLI

```bash
uv sync --extra dev
cp .env.example .env   # OPENAI_API_KEY 또는 Ollama/vLLM, 트래커 키 설정

uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --auto-analyze

uv run evalvault history          # 실행 이력
uv run evalvault analyze <RUN_ID> # 통계 분석
```

> 기본 저장소는 **PostgreSQL + pgvector**입니다. SQLite를 쓰려면 `--db <path>` 또는 `DB_BACKEND=sqlite` + `EVALVAULT_DB_PATH`를 지정하고, Web UI가 같은 DB를 읽도록 설정을 통일하세요.

### Web UI (React + FastAPI)

```bash
# 터미널 1 — API
uv run evalvault serve-api --reload

# 터미널 2 — 프론트엔드
cd frontend && npm install && npm run dev
```

브라우저에서 `http://localhost:5173` 접속 → **Evaluation Studio**에서 실행/히스토리, **Analysis Lab/Reports**에서 점수·인사이트 확인. LLM 리포트 언어는 `GET /api/v1/runs/{run_id}/report?language=en`(기본 ko)로 선택합니다.

---

## 핵심 기능

- **End-to-End 평가 루프** — 실행 → 채점 → DB 저장 → 추적을 한 명령으로
- **Simple / Full 모드** — 입문자는 한 줄 실행, 전문가는 모든 플래그 유지 (`run-simple` / `run-full`)
- **Artifacts-first** — 리포트뿐 아니라 모듈별 원본 결과를 구조화 저장(`reports/analysis/artifacts/...`)
- **옵션형 Observability** — MLflow·Phoenix(기본 듀얼) / Langfuse는 필요할 때만 활성화 (open-circuit: 트래커 장애가 평가를 막지 않음)
- **회귀 게이트(CI/CD)** — `evalvault regress` / `ci-gate`가 baseline 대비 통계적 회귀를 감지, 안정 스키마 JSON + exit code로 CI 통합 (평가 게이트 verdict는 `passed`/`failed`까지 — 릴리스 promote/rollback은 emit하지 않음)
- **실험 관리(A/B)** — `experiment-*` 명령으로 그룹/실행 비교, 결론 기록
- **한국어 NLP** — Kiwi 형태소 분석 + BM25 + Dense/Hybrid 리트리벌 (`--extra korean`)
- **Knowledge Graph / GraphRAG** — KG 생성 및 top-k vs GraphRAG 비교 실험

---

## 아키텍처 (Hexagonal · Ports & Adapters)

도메인은 어댑터를 import하지 않으며, 외부 연동은 모두 포트 뒤에 있습니다.

```
src/evalvault/
├── domain/
│   ├── entities/   # TestCase, Dataset, EvaluationRun, MetricScore, Experiment ...
│   ├── services/   # RagasEvaluator + 분리된 서비스(비용/fallback/메트릭 스코어링/
│   │               #   프롬프트 카탈로그·오버라이드·한국어/언어 판별/claim-level)
│   └── metrics/    # 도메인 커스텀 메트릭
├── ports/
│   ├── inbound/    # EvaluatorPort
│   └── outbound/   # LLMPort, DatasetPort, StoragePort, TrackerPort, DomainMemoryPort ...
├── adapters/
│   ├── inbound/    # CLI(Typer), Web API(FastAPI), MCP
│   └── outbound/
│       ├── llm/       # OpenAI, Azure, Anthropic, Ollama, vLLM (+RetryPolicy)
│       ├── storage/   # SQLite, PostgreSQL(+pgvector)
│       └── tracker/   # MLflow, Phoenix, Langfuse, MultiTrackerAdapter(듀얼 로깅)
└── config/         # Settings, ModelConfig (pydantic-settings), 프로필
```

| Port | Adapter | 비고 |
|------|---------|------|
| LLMPort | OpenAI / Azure / Anthropic / Ollama / vLLM | 공통 `RetryPolicy`(timeout+backoff) |
| StoragePort | SQLite / PostgreSQL(+pgvector) | 명시적 `--db`는 SQLite 강제 |
| TrackerPort | MLflow / Phoenix / Langfuse / **MultiTrackerAdapter** | 기본 `mlflow+phoenix` 듀얼, open-circuit |
| EvaluatorPort | RagasEvaluator | Ragas 0.4.x + 커스텀/스테이지 메트릭 |

상세: [docs/handbook/CHAPTERS/01_architecture.md](docs/handbook/CHAPTERS/01_architecture.md)

---

## 지원 메트릭

**Ragas 계열**

| 메트릭 | 설명 |
|--------|------|
| `faithfulness` | 답변이 컨텍스트에 충실한지 |
| `answer_relevancy` | 답변이 질문과 관련있는지 (임베딩 필요) |
| `context_precision` | 검색 컨텍스트의 정밀도 (ground_truth 필요) |
| `context_recall` | 필요한 정보가 검색됐는지 (ground_truth 필요) |
| `factual_correctness` | ground_truth 대비 사실 정확성 |
| `semantic_similarity` | 답변–ground_truth 의미 유사도 (임베딩 필요) |
| `summary_score` / `summary_faithfulness` | 요약 품질 / 요약 충실도 |

**도메인·검색·요약 커스텀 메트릭**

`insurance_term_accuracy`, `entity_preservation`, `exact_match`, `f1_score`, `no_answer_accuracy`, `confidence_score`, `contextual_relevancy`, 검색 랭킹(`mrr`, `ndcg`, `hit_rate`), 요약(`summary_accuracy`, `summary_risk_coverage`, `summary_non_definitive`, `summary_needs_followup`).

**스테이지 메트릭** — `StageMetricService`가 파이프라인 단계별로 파생: `retrieval.precision_at_k`, `retrieval.recall_at_k`, `retrieval.latency_ms`, `rerank.keep_rate`, `rerank.avg_score`, `output.citation_count`, `input.query_length` 등.

전체 정의·임계값 정책: [docs/handbook/CHAPTERS/02_data_and_metrics.md](docs/handbook/CHAPTERS/02_data_and_metrics.md) · 사용 가능한 목록은 `uv run evalvault metrics`.

---

## CLI 표면

명령군(루트 + 서브앱). 전체 옵션은 `uv run evalvault <command> --help`.

- **평가/실행**: `run`, `run-simple`, `run-full`, `pipeline`, `generate`(합성 데이터셋)
- **이력/비교/분석**: `history`, `export`, `compare`, `analyze`, `analyze-compare`, `profile-difficulty`
- **회귀/게이트**: `regress`, `ci-gate`, `regress-baseline`, `gate`
- **실험(A/B)**: `experiment-create|add-group|add-run|list|compare|conclude|summary`
- **보정**: `calibrate`, `calibrate-judge`
- **설정/관측**: `config`, `metrics`, `serve-api`, `langfuse-dashboard`
- **서브앱**: `kg`, `domain`, `graphrag`, `benchmark`, `method`, `ops`, `phoenix`, `prompts`, `stage`, `artifacts`, `debug`

워크플로 상세: [docs/handbook/CHAPTERS/03_workflows.md](docs/handbook/CHAPTERS/03_workflows.md)

---

## 데이터셋 포맷 (임계값은 데이터셋에 둔다)

```json
{
  "name": "insurance-qa",
  "version": "1.0.0",
  "thresholds": { "faithfulness": 0.8, "answer_relevancy": 0.7 },
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

- 필수 필드: `id`, `question`, `answer`, `contexts`. 미지정 임계값은 `0.7`로 폴백.
- `ground_truth`는 `context_precision`/`context_recall`/`factual_correctness`/`semantic_similarity`에 필요.
- CSV/Excel: `threshold_*` 컬럼 지원, `contexts`는 JSON 배열 문자열 또는 `|` 구분.
- 템플릿: `uv run evalvault init`(`dataset_templates/`) 또는 `tests/fixtures/sample_dataset.json`.

---

## LLM 프로필 & 저장소

- **프로필**: `config/models.yaml`의 프로필로 provider/model/embedding을 묶어 `--profile dev|prod|vllm ...`로 전환. 폐쇄망/온프렘에서도 동일 CLI·Web UI 동작.
- **vLLM(OpenAI 호환)**: `EVALVAULT_PROFILE=vllm` + `VLLM_BASE_URL`/`VLLM_MODEL`(+임베딩 엔드포인트).
- **Ollama**: `ollama pull <model>` 후 사용. 툴콜 지원 모델은 `OLLAMA_TOOL_MODELS`에 나열.
- **저장소**: PostgreSQL(+pgvector) 기본, SQLite 옵션. 환경변수는 [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md) §5.2 / `.env.example` 참조.

---

## Open RAG Trace 표준 (외부/내부 시스템 추적)

OpenTelemetry + OpenInference 기반 표준으로 외부 RAG 시스템도 **모듈 단위 span(`rag.module`) + 로그 이벤트 + 공통 속성** 스키마로 트레이스를 emit해 EvalVault 실행과 나란히 분석할 수 있습니다.

```bash
# OTel Collector 실행 → http://localhost:4318/v1/traces (또는 Phoenix :6006)
python3 scripts/dev/validate_open_rag_trace.py --input traces.json
```

- 어댑터: `OpenRagTraceAdapter`, `trace_module`, `install_open_rag_log_handler`
- 스펙: [docs/architecture/open-rag-trace-spec.md](docs/architecture/open-rag-trace-spec.md)

---

## 오프라인 / 폐쇄망

- Docker 이미지 번들: [docs/guides/OFFLINE_DOCKER.md](docs/guides/OFFLINE_DOCKER.md)
- NLP 모델 캐시 번들: [docs/guides/OFFLINE_MODELS.md](docs/guides/OFFLINE_MODELS.md)

LLM 모델은 폐쇄망 내부 인프라가 관리하고, EvalVault는 **분석용 NLP 모델 캐시**만 번들에 포함합니다.

---

## 문서 허브

- 진입 문서(SSoT): [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md)
- 문서 인덱스: [docs/INDEX.md](docs/INDEX.md) · 핸드북: [docs/handbook/INDEX.md](docs/handbook/INDEX.md) · 외부 요약: [docs/handbook/EXTERNAL.md](docs/handbook/EXTERNAL.md)
- 아키텍처: [01_architecture](docs/handbook/CHAPTERS/01_architecture.md) · 데이터/메트릭: [02_data_and_metrics](docs/handbook/CHAPTERS/02_data_and_metrics.md) · 워크플로: [03_workflows](docs/handbook/CHAPTERS/03_workflows.md)
- 운영 런북: [04_operations](docs/handbook/CHAPTERS/04_operations.md) · 품질/테스트/CI: [06_quality_and_testing](docs/handbook/CHAPTERS/06_quality_and_testing.md) · 로드맵: [08_roadmap](docs/handbook/CHAPTERS/08_roadmap.md)
- 어댑터 계약(외부 도구 통합): [docs/adapter-contract.md](docs/adapter-contract.md) · 머신 리더블 상태: `.ai-tool-suite/project-state.json` · 변경 narrative: [docs/development-journal.md](docs/development-journal.md)

> 호환성: `docs/guides/USER_GUIDE.md`, `docs/guides/DEV_GUIDE.md` 등 일부 문서는 과거 링크 호환용 deprecated 스텁이며 최신 내용은 handbook을 따릅니다.

---

## Acknowledgements

[![PSF Supporting Member](https://img.shields.io/badge/PSF-Supporting%20Member-3776AB?logo=python&logoColor=white)](https://www.python.org/psf/)

메인테이너는 [Python Software Foundation](https://www.python.org/psf/) 후원 회원(supporting member)으로, 파이썬 생태계를 지원합니다. 🐍

---

## License

EvalVault is licensed under the [Apache 2.0](LICENSE.md) license.
