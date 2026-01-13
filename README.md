# EvalVault

RAG(Retrieval-Augmented Generation) 시스템을 대상으로 **평가(Eval) → 분석(Analysis) → 추적(Tracing) → 개선 루프**를 하나의 워크플로로 묶는 CLI + Web UI 플랫폼입니다.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

English version? See `README.en.md`.

---

## Quick Links

- 문서 허브: `docs/INDEX.md`
- 사용자 가이드: `docs/guides/USER_GUIDE.md`
- 개발 가이드: `docs/guides/DEV_GUIDE.md`
- 상태/로드맵: `docs/STATUS.md`, `docs/ROADMAP.md`
- 개발 백서(설계/운영/품질 기준): `docs/new_whitepaper/INDEX.md`
- Open RAG Trace: `docs/architecture/open-rag-trace-spec.md`

---

## EvalVault가 해결하는 문제

RAG를 운영하다 보면 결국 아래 질문으로 귀결됩니다.

- “모델/프롬프트/리트리버를 바꿨는데, **진짜 좋아졌나?**”
- “좋아졌다면 **왜** 좋아졌고, 나빠졌다면 **어디서** 깨졌나?”
- “이 결론을 **재현 가능하게** 팀/CI에서 계속 검증할 수 있나?”

EvalVault는 위 질문을 **데이터셋 + 메트릭 + (선택)트레이싱** 관점에서 한 번에 답할 수 있게 설계했습니다.

---

## 핵심 개념

- **Run 단위**: 평가/분석/아티팩트/트레이스가 하나의 `run_id`로 묶입니다.
- **Dataset 중심**: threshold(합격 기준)는 데이터셋에 포함되어 “도메인별 합격 기준”을 유지합니다.
- **Artifacts-first**: 보고서(요약)뿐 아니라, 분석 모듈별 원본 결과(아티팩트)를 구조화된 디렉터리에 보존합니다.
- **Observability 옵션화**: Phoenix/Langfuse/MLflow는 “필요할 때 켜는” 방식으로, 실행 경로는 최대한 단순하게 유지합니다.

---

## 3분 Quickstart (CLI)

```bash
uv sync --extra dev
cp .env.example .env

uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

- 결과는 기본 DB(`data/db/evalvault.db`)에 저장되어 `history`, Web UI, 비교 분석에서 재사용됩니다.
- `--db`를 생략해도 기본 경로로 저장되며, 모든 데이터가 자동으로 엑셀로 내보내집니다.
- `--auto-analyze`는 요약 리포트 + 모듈별 아티팩트를 함께 생성합니다.

---

## 프롬프트 오버라이드 (RAGAS / 시스템)

**에디터 관점**: 기본 동작은 유지하고 필요한 항목만 YAML/파일로 덮어씁니다.
**개발자 관점**: CLI 옵션 또는 Web API 필드로 주입합니다.

### CLI
- RAGAS 메트릭별 오버라이드: `--ragas-prompts`
- 시스템 프롬프트 적용: `--system-prompt` 또는 `--system-prompt-file`

```bash
uv run evalvault run --mode full tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --ragas-prompts config/ragas_prompts.yaml

uv run evalvault run --mode full tests/fixtures/e2e/insurance_qa_korean.json \
  --system-prompt-file prompts/system.txt
```

`config/ragas_prompts.yaml` 예시:
```yaml
faithfulness: |
  # custom prompt...
answer_relevancy: |
  # custom prompt...
```

### Web UI / API
- `EvalRequest` 필드:
  - `system_prompt`, `system_prompt_name`
  - `ragas_prompt_overrides` (메트릭명 → 프롬프트 문자열)
  - `prompt_set_name`, `prompt_set_description`

---

## 프롬프트 후보 추천 (`evalvault prompts suggest`)

특정 `run_id`의 프롬프트 스냅샷을 기준으로, **자동/수동 후보 프롬프트**를 모은 뒤 **holdout 분리 데이터**에서 Ragas 메트릭을 평가하고, **가중치 합산 점수**로 Top 후보를 추천합니다.

- 필수 전제: `run_id`가 `--db`에 저장되어 있고, 해당 run에 **프롬프트 스냅샷**이 연결되어 있어야 합니다 (`evalvault run` 실행 시 `--db` 사용).
- 자동 후보: 기본 프롬프트를 바탕으로 템플릿 기반 변형을 생성합니다. (`--candidates`, `--auto/--no-auto`)
- 수동 후보: `--prompt`(반복 가능), `--prompt-file`(반복 가능)로 후보를 추가합니다. (`--no-auto` 사용 시 수동 후보는 필수)
- holdout 분리: `--holdout-ratio`(기본 0.2)로 dev/holdout을 나누고, **holdout 쪽 점수로 랭킹**을 계산합니다. 재현이 필요하면 `--seed`를 지정하세요.
- 가중치: `--weights faithfulness=0.7,answer_relevancy=0.3` 형태로 입력하며, 내부에서 합이 1이 되도록 정규화합니다. 미지정 시 메트릭 균등 가중치가 적용됩니다.

### 사용 예시

```bash
# 기본 사용 (자동 후보 + 수동 후보 파일)
uv run evalvault prompts suggest <RUN_ID> --db data/db/evalvault.db \
  --role system \
  --metrics faithfulness,answer_relevancy \
  --weights faithfulness=0.7,answer_relevancy=0.3 \
  --candidates 5 \
  --prompt-file prompts/candidates.txt

# 요약 평가(다중 메트릭) + 가중치
uv run evalvault prompts suggest <RUN_ID> --db data/db/evalvault.db \
  --metrics summary_score,summary_faithfulness,entity_preservation \
  --weights summary_score=0.5,summary_faithfulness=0.3,entity_preservation=0.2 \
  --candidates 3

# 샘플링 2개 중 index 선택
uv run evalvault prompts suggest <RUN_ID> --db data/db/evalvault.db \
  --generation-n 2 \
  --selection-policy index \
  --selection-index 1
```

- `--prompt-file`은 **한 줄당 후보 프롬프트 1개**를 읽습니다(빈 줄 제외).

### 주요 옵션 요약
- `--role`: 개선 대상 프롬프트 role (기본 system)
- `--metrics`: 평가 메트릭 목록 (기본 run에서 사용한 메트릭)
- `--weights`: 메트릭 가중치 (합이 1이 되도록 정규화)
- `--candidates`: 자동 후보 수 (기본 5)
- `--auto/--no-auto`: 자동 후보 생성 on/off
- `--holdout-ratio`: dev/holdout 분리 비율 (기본 0.2)
- `--seed`: 분리/샘플 재현성
- `--generation-n`: 후보당 샘플 수
- `--selection-policy`: 샘플 선택 정책 (`best`|`index`)
- `--selection-index`: `selection-policy=index` 시 선택할 샘플 인덱스

### 출력(기본 경로)

- 요약 JSON: `reports/analysis/prompt_suggestions_<RUN_ID>.json`
- 보고서(Markdown): `reports/analysis/prompt_suggestions_<RUN_ID>.md`
- 아티팩트 디렉터리: `reports/analysis/artifacts/prompt_suggestions_<RUN_ID>/`
  - 후보 목록: `reports/analysis/artifacts/prompt_suggestions_<RUN_ID>/candidates.json`
  - 후보 점수/샘플 점수: `reports/analysis/artifacts/prompt_suggestions_<RUN_ID>/scores.json`
  - 최종 랭킹: `reports/analysis/artifacts/prompt_suggestions_<RUN_ID>/ranking.json`
  - 인덱스: `reports/analysis/artifacts/prompt_suggestions_<RUN_ID>/index.json`

경로를 바꾸려면 `--analysis-dir` 또는 `--output`/`--report`를 사용합니다. 설계 배경은 `docs/guides/prompt_suggestions_design.md`를 참고하세요.

### FAQ
- Q. "프롬프트 스냅샷이 없습니다" 오류가 납니다.
  - A. 해당 run이 `--db`로 저장되었는지 확인하고, `evalvault run` 실행 시 `--db`를 지정하세요.
- Q. 자동 후보를 끄면 어떻게 되나요?
  - A. `--no-auto` 사용 시 `--prompt` 또는 `--prompt-file`로 수동 후보를 반드시 넣어야 합니다.
- Q. 점수는 어떤 기준인가요?
  - A. holdout 데이터에서 Ragas 메트릭을 평가하고, `--weights` 가중치로 합산한 점수입니다.

---

## 엑셀 내보내기 (자동)

**에디터 관점**: DB 저장과 동시에 Excel이 자동 생성됩니다.
**개발자 관점**: 저장 로직에서 `export_run_to_excel`이 자동 호출됩니다.

- 기본 DB 경로: `data/db/evalvault.db`
- 엑셀 경로: `data/db/evalvault_run_<RUN_ID>.xlsx`

**시트 구성(요약 → 상세)**
- `Summary`, `Run`, `TestCases`, `MetricScores`, `MetricsSummary`
- `RunPromptSets`, `PromptSets`, `PromptSetItems`, `Prompts`
- `Feedback`, `ClusterMaps`, `StageEvents`, `StageMetrics`
- `AnalysisReports`, `PipelineResults`
- 시트별 컬럼 설명: `docs/guides/EVALVAULT_RUN_EXCEL_SHEETS.md`

---

## 외부 시스템 로그 연동 (의도분석/리트리브/리랭킹 등)

**에디터 관점**: 표준 포맷(OTel/JSON/JSONL)으로 붙일 수 있어야 합니다.
**개발자 관점**: OpenTelemetry + OpenInference 또는 Stage Events로 연결합니다.

### 1) Open RAG Trace (권장)
- OpenTelemetry + OpenInference 기반 표준 스키마
- 스펙: `docs/architecture/open-rag-trace-spec.md`
- 연동 규격: `docs/guides/EXTERNAL_TRACE_API_SPEC.md`
- 샘플: `docs/guides/OPEN_RAG_TRACE_SAMPLES.md`

**OTLP HTTP 전송(권장)**
- 엔드포인트: `http://<host>:6006/v1/traces`
- Collector 사용 시: `http://<collector-host>:4318/v1/traces`

**OpenInference 필수 키(요약)**
- `rag.module`, `spec.version`
- 권장: `input.value`, `output.value`, `llm.model_name`, `retrieval.documents_json`

### 2) EvalVault 직접 Ingest (Draft)
- `POST /api/v1/ingest/otel-traces` (OTLP JSON)
- `POST /api/v1/ingest/stage-events` (JSONL)
- 예시: `docs/templates/otel_openinference_trace_example.json`

**OTLP JSON 예시(요약)**
```json
{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [
          { "key": "service.name", "value": { "stringValue": "rag-service" } }
        ]
      },
      "scopeSpans": [
        {
          "spans": [
            {
              "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
              "spanId": "00f067aa0ba902b7",
              "name": "retrieve",
              "startTimeUnixNano": 1730000000000000000,
              "endTimeUnixNano": 1730000000500000000,
              "attributes": [
                { "key": "rag.module", "value": { "stringValue": "retrieve" } },
                { "key": "spec.version", "value": { "stringValue": "0.1" } },
                { "key": "input.value", "value": { "stringValue": "보험금 지급 조건" } }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

**응답 예시(요약)**
```json
{
  "status": "ok",
  "ingested": 12,
  "trace_ids": ["4bf92f3577b34da6a3ce929d0e0e4736"]
}
```

**HTTP 상태 코드(요약)**
- `200 OK`: 정상 수집
- `400 Bad Request`: JSON/JSONL 파싱 실패
- `422 Unprocessable Entity`: 필수 필드 누락/스키마 불일치
- `500 Internal Server Error`: 저장/파이프라인 내부 오류

### 3) Stage Events / Metrics 적재
- 외부 파이프라인 로그를 JSON/JSONL로 저장 → DB ingest

```bash
uv run evalvault stage ingest path/to/stage_events.jsonl --db data/db/evalvault.db
uv run evalvault stage summary <RUN_ID> --db data/db/evalvault.db
```

**Stage Event JSONL 예시(요약)**
```jsonl
{"run_id":"run_20260103_001","stage_id":"stg_sys_01","stage_type":"system_prompt","stage_name":"system_prompt_v1","duration_ms":18,"attributes":{"prompt_id":"sys-01"}}
{"run_id":"run_20260103_001","stage_id":"stg_input_01","parent_stage_id":"stg_sys_01","stage_type":"input","stage_name":"user_query","duration_ms":6,"attributes":{"query":"보험금 지급 조건","language":"ko"}}
```

- Stage Event에는 **의도분석/리트리브/리랭킹**의 입력/출력/파라미터/결과를 넣습니다.
- `--stage-store` 사용 시 EvalVault 내부 실행 로그도 자동 저장됩니다.

### 4) 분석 전환 규칙(요약)
- **RAGAS 형식 데이터셋**이면 `evalvault run` 기반 평가/분석
- **OTel/OpenInference 트레이스**는 Phoenix로 트레이싱 연결
- **비정형 로그(Stage Event)**는 `stage ingest` → `stage summary` → 분석 모듈로 전환

---

## Web UI (FastAPI + React)

```bash
# API
uv run evalvault serve-api --reload

# Frontend
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속 후, Evaluation Studio에서 실행/히스토리/리포트를 확인합니다.

- LLM 보고서 언어: `/api/v1/runs/{run_id}/report?language=en` (기본 ko)
  - 상세: `docs/guides/USER_GUIDE.md#보고서-언어-옵션`
- 피드백 집계: 동일 `rater_id` + `test_case_id` 기준 최신 값만 집계, 취소 시 집계 제외
  - 상세: `docs/guides/USER_GUIDE.md#피드백-집계-규칙`

---

## 산출물(Artifacts) 경로

- 단일 실행 자동 분석:
  - 요약 JSON: `reports/analysis/analysis_<RUN_ID>.json`
  - 보고서: `reports/analysis/analysis_<RUN_ID>.md`
  - 아티팩트 인덱스: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`
  - 노드별 결과: `reports/analysis/artifacts/analysis_<RUN_ID>/<node_id>.json`

- A/B 비교 분석:
  - 요약 JSON: `reports/comparison/comparison_<RUN_A>_<RUN_B>.json`
  - 보고서: `reports/comparison/comparison_<RUN_A>_<RUN_B>.md`

---

## 데이터셋 포맷(요약)

```json
{
  "name": "insurance-qa",
  "version": "1.0.0",
  "thresholds": { "faithfulness": 0.8 },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "...",
      "answer": "...",
      "contexts": ["..."]
    }
  ]
}
```

- 필수 필드: `id`, `question`, `answer`, `contexts`
- `ground_truth`는 일부 메트릭에서 필요합니다.
- 템플릿: `docs/templates/dataset_template.json`, `docs/templates/dataset_template.csv`, `docs/templates/dataset_template.xlsx`
- 관련 문서: `docs/guides/USER_GUIDE.md`

---

## 지원 메트릭(대표)

- Ragas 계열: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`, `factual_correctness`, `semantic_similarity`
- 커스텀 예시(도메인): `insurance_term_accuracy`

정확한 옵션/운영 레시피는 `docs/guides/USER_GUIDE.md`를 기준으로 최신화합니다.

---

## RAGAS 0.4.2 데이터 전처리/후처리 (중요)

아래 항목은 **RAGAS 0.4.2 기준**으로 EvalVault가 데이터와 점수를 안정화하기 위해 수행하는 처리들입니다. 모두 재현성과 품질 저하 방지를 위해 의도적으로 설계되었습니다.

### 1) 데이터 전처리 (입력 안정화)
- **빈 질문/답변/컨텍스트 제거**: 평가 불가능한 케이스를 사전에 제거합니다. (`src/evalvault/domain/services/dataset_preprocessor.py`)
- **컨텍스트 정규화**: 공백 정리, 중복 제거, 길이 제한을 통해 컨텍스트 품질을 표준화합니다. (`src/evalvault/domain/services/dataset_preprocessor.py`)
- **레퍼런스 보완**: 레퍼런스가 필요한 메트릭에서 부족할 경우 질문/답변/컨텍스트 기반으로 보완합니다. (`src/evalvault/domain/services/dataset_preprocessor.py`)

**이유**: 입력 품질 편차로 인해 RAGAS 점수 분산이 커지는 것을 방지하고, 메트릭 실행 실패/왜곡을 줄입니다.

### 2) 한국어/비영어권 대응 (프롬프트 언어 정렬)
- **한국어 데이터셋 자동 감지** 후 `answer_relevancy`, `factual_correctness`에 한국어 프롬프트를 기본 적용합니다. (`src/evalvault/domain/services/evaluator.py`)
- **요약/후보 평가 프롬프트 기본 한국어**: 요약 충실도 판정, 프롬프트 후보 평가, 지식그래프 관계 보강 프롬프트는 기본 `ko`로 동작합니다.
  - 영어가 필요하면 API/SDK에서 `language="en"` 또는 `prompt_language="en"`을 지정하세요.
- **사용자 프롬프트 오버라이드 지원**: 필요 시 YAML로 메트릭별 프롬프트를 덮어쓸 수 있습니다. (`src/evalvault/domain/services/ragas_prompt_overrides.py`)
- **외부 근거(비영어권 이슈)**:
  - https://github.com/explodinggradients/ragas/issues/1829
  - https://github.com/explodinggradients/ragas/issues/402

**이유**: 질문 생성/판정 프롬프트가 영어에 고정될 경우, 비영어 입력에서 언어 불일치로 점수 왜곡이 발생할 수 있으므로 이를 최소화합니다.

### 3) 점수 후처리 (안정성 확보)
- **비숫자/NaN 점수는 0.0 처리**: 메트릭 실패가 전체 파이프라인을 중단시키지 않도록 방어합니다. (`src/evalvault/domain/services/evaluator.py`)
- **Faithfulness 폴백**: RAGAS가 실패하거나 한국어 텍스트에서 불안정할 경우, 한국어 전용 claim-level 분석으로 점수를 재구성합니다. (`src/evalvault/domain/services/evaluator.py`)

**이유**: LLM/임베딩 실패나 NaN으로 인해 결과가 끊기는 문제를 방지하고, 한국어에서 최소한의 신뢰도를 확보하기 위해서입니다.

### 4) 요약/시각화 후처리 (비교 가능성 강화)
- **임계값 기준 정규화**: threshold를 0점 기준으로 정규화하여 성능 개선/악화를 직관적으로 표시합니다. (`src/evalvault/domain/services/visual_space_service.py`)
- **가중 합산**: `faithfulness`, `factual_correctness`, `answer_relevancy` 등을 가중 결합하여 축/지표로 요약합니다. (`src/evalvault/domain/services/visual_space_service.py`)

**이유**: 단일 지표만으로는 해석이 어려운 경우가 많아, 정책적 기준(임계값)과 함께 비교 가능한 요약 점수로 제공하기 위함입니다.

---

## 모델/프로필 설정(요약)

- 프로필 정의: `config/models.yaml`
- 공통 환경 변수(예):
  - `EVALVAULT_PROFILE`
  - `EVALVAULT_DB_PATH`
  - `OPENAI_API_KEY` 또는 `OLLAMA_BASE_URL` 등
- 관련 문서: `docs/guides/USER_GUIDE.md`, `docs/guides/DEV_GUIDE.md`, `config/models.yaml`

---

## Open RAG Trace (외부 RAG 시스템까지 통합)

EvalVault는 OpenTelemetry + OpenInference 기반의 **Open RAG Trace** 스키마를 제공해, 외부/내부 RAG 시스템을 동일한 방식으로 계측/수집/분석할 수 있게 합니다.

- 스펙: `docs/architecture/open-rag-trace-spec.md`
- Collector: `docs/architecture/open-rag-trace-collector.md`
- 샘플/내부 래퍼: `docs/guides/OPEN_RAG_TRACE_SAMPLES.md`, `docs/guides/OPEN_RAG_TRACE_INTERNAL_ADAPTER.md`
- 관련 문서: `docs/INDEX.md`, `docs/architecture/open-rag-trace-collector.md`

---

## 개발/기여

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pytest tests -v
```

- 기여 가이드: `CONTRIBUTING.md`
- 개발 루틴: `docs/guides/DEV_GUIDE.md`
- 관련 문서: `docs/STATUS.md`, `docs/ROADMAP.md`

---

## 문서

- `docs/INDEX.md`: 문서 허브
- `docs/STATUS.md`, `docs/ROADMAP.md`: 현재 상태/방향
- `docs/guides/USER_GUIDE.md`: 사용/운영 종합
- `docs/new_whitepaper/INDEX.md`: 설계/운영/품질 기준(전문가 관점)

---

## License

EvalVault is licensed under the [Apache 2.0](LICENSE.md) license.
