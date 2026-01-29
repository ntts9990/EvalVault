# EvalVault (한국어)

> RAG(Retrieval-Augmented Generation) 시스템 평가 자동화를 위한 CLI · Web UI 도구

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/ntts9990/EvalVault/blob/main/LICENSE.md)

English version? See the [root README](https://github.com/ntts9990/EvalVault/blob/main/README.md).

---

## 가장 빠르게 Ragas 결과 보는 방법 (Web -> CLI)

**Web (React + FastAPI)**
```bash
uv run evalvault serve-api --reload
```
```bash
cd frontend
npm install
npm run dev
```
또는 Phoenix까지 함께 띄우려면 다음 스크립트를 사용하세요.
```bash
bash scripts/dev/start_web_ui_with_phoenix.sh
```
브라우저에서 `http://localhost:5173`에 접속한 뒤 Evaluation Studio에서 평가를 실행하고
Analysis Lab/Reports에서 점수와 분석 결과를 확인하세요. (예: `tests/fixtures/e2e/insurance_qa_korean.json` 업로드)

**CLI (터미널)**
```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev
uv run evalvault history
uv run evalvault analyze <RUN_ID>
```
Tip: 기본 저장소는 Postgres입니다. SQLite를 쓰려면 `--db` 또는 `DB_BACKEND=sqlite` + `EVALVAULT_DB_PATH`를 지정하세요.
Web UI에서 보려면 Postgres 연결 설정을 동일하게 맞추고, SQLite 사용 시 `--db` 또는 `EVALVAULT_DB_PATH`를 맞추세요.

---

## 데이터셋 구성 (threshold는 데이터셋별)

EvalVault는 임계값(threshold)을 **데이터셋에 포함**시켜 데이터셋마다 다른 합격 기준을
가질 수 있게 합니다. 메트릭별 threshold가 비어 있으면 기본값 `0.7`을 사용하며,
Domain Memory를 켜면 자동 조정될 수 있습니다.

```json
{
  "name": "insurance-qa",
  "version": "1.0.0",
  "thresholds": { "faithfulness": 0.8, "answer_relevancy": 0.7 },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "보장금액은 얼마인가요?",
      "answer": "보장금액은 1억원입니다.",
      "contexts": ["보장금액은 1억원입니다."],
      "ground_truth": "1억원"
    }
  ]
}
```

- 테스트케이스 필수 필드: `id`, `question`, `answer`, `contexts`
- `ground_truth`는 `context_precision`, `context_recall`,
  `factual_correctness`, `semantic_similarity`에 필요
- 한국어 데이터셋이면 `answer_relevancy`, `factual_correctness`는
  한국어 프롬프트가 기본 적용됩니다. 영어만 사용할 때는
  `metadata.language: "en"` 또는 `--ragas-prompts`로 덮어쓰세요.
- CSV/Excel: `threshold_*` 컬럼으로 임계값 지정 (첫 번째로 채워진 행 기준).
  `contexts`는 JSON 배열 문자열 또는 `|`로 구분합니다.
- 템플릿: `uv run evalvault init`로 `dataset_templates/` 생성,
  또는 `tests/fixtures/sample_dataset.json` 참고.

---

## 실행 결과 엑셀 컬럼 설명

- 시트/컬럼 상세: `guides/EVALVAULT_RUN_EXCEL_SHEETS.md`

---

## 검색 성능 평가 메트릭 흐름

EvalVault의 검색 성능 메트릭은 크게 3갈래로 수집됩니다.
1) 런타임 Stage 이벤트 기반 메트릭
2) Ragas 커스텀 랭킹 메트릭
3) 벤치마크/분석 파이프라인 메트릭

```mermaid
flowchart TD
    A[입력 데이터셋/실행 결과\nquestion, answer, contexts, ground_truth] --> B[EvaluationRun]
    B --> C[StageEvent]
    C --> C1[StageMetricService\nretrieval.precision_at_k / recall_at_k\navg_score / score_gap / latency]
    B --> D[RagasEvaluator (custom)]
    D --> D1[MRR / NDCG / HitRate]
    B --> E[Analysis Pipeline]
    E --> E1[RetrievalAnalyzer\nkeyword_overlap / ground_truth_hit_rate]
    E --> E2[BM25/Embedding/Hybrid Searcher\nrecall@k / avg_recall@k]
    B --> F[Retrieval Benchmark Runner]
    F --> F1[precision@k / recall@k / mrr / ndcg@k]
    C1 --> G[Reports/Scorecard]
    D1 --> G
    E1 --> G
    E2 --> G
    F1 --> G
```

- Stage 메트릭: `StageEvent`의 `doc_ids/scores/top_k` + `relevance_map(test_case_id -> relevant docs)`로 계산
- Ragas 커스텀 메트릭: `contexts` + `ground_truth` 기반으로 `mrr/ndcg/hit_rate` 산출
- 벤치마크 메트릭: `documents` + `relevant_doc_ids`를 입력으로 `precision/recall/mrr/ndcg` 산출
- 분석 파이프라인: 실행 결과로 검색 커버리지/키워드 오버랩/리트리버 비교 점수 요약

참고 구현 위치:
- Stage 메트릭 계산: `src/evalvault/domain/services/stage_metric_service.py`
- 랭킹 메트릭(MRR/NDCG/HitRate): `src/evalvault/domain/metrics/retrieval_rank.py`
- 벤치마크 계산(precision/recall/mrr/ndcg): `src/evalvault/domain/services/retrieval_metrics.py`
- 분석 모듈: `src/evalvault/adapters/outbound/analysis/`

---

## KG/GraphRAG 사용 (문서 기반)

EvalVault에서 KG는 **평가 데이터셋이 아니라 문서 지식**에서 생성합니다.
데이터셋은 질문/답변/컨텍스트를 담는 평가 케이스이고, GraphRAG는
`contexts`가 비어 있는 케이스에만 문서 기반 컨텍스트를 채웁니다.

**입력 양식**
- Retriever 문서: JSON/JSONL/TXT 지원.
  - JSON은 `{"documents":[{"doc_id":"...","content":"..."}]}` 또는 리스트 형식.
- KG JSON: `entities`/`relations` 배열.
  - `source_document_id`는 retriever 문서의 `doc_id`와 반드시 일치해야 합니다.
- 템플릿: `templates/retriever_docs_template.json`,
  `templates/kg_template.json`
- Web UI 템플릿(JSON/CSV/XLSX)은 CLI 로더와 동일해 지정된 양식이면 정상 파싱됩니다.

**CLI 예시 (GraphRAG)**
```bash
uv run evalvault run tests/fixtures/e2e/graphrag_smoke.json \
  --retriever graphrag \
  --retriever-docs tests/fixtures/e2e/graphrag_retriever_docs.json \
  --kg tests/fixtures/kg/minimal_graph.json \
  --metrics faithfulness \
  --profile dev
```

**Web UI 제약**
- Evaluation Studio는 `bm25/hybrid`만 노출되며 GraphRAG/KG 입력은 없습니다.
- Knowledge Base가 생성한 `data/kg/knowledge_graph.json`은 `graph`로 감싸져 있어
  `--kg`에 바로 사용할 수 없습니다. `graph`만 추출하거나
  `{ "knowledge_graph": ... }`로 감싸서 사용하세요.

---

## 개요

EvalVault는 Ragas 0.4.x 메트릭을 기반으로 Typer CLI와 FastAPI + React Web UI를 제공하여 RAG 품질을 일관되게 측정하고 저장합니다. OpenAI, Ollama, Azure, Anthropic 등 프로필 기반으로 모델을 교체할 수 있으며, Langfuse · Phoenix · Domain Memory · DAG 분석 파이프라인을 통해 추적 및 개선 업무를 자동화합니다.

**주요 특징**
- Typer CLI 한 번으로 평가/비교/내보내기/저장 실행
- OpenAI/Ollama/vLLM/폐쇄망을 아우르는 프로필 기반 모델 구성
- FastAPI + React Web UI에서 평가, 히스토리, 보고서 생성
- Langfuse 및 Phoenix 트래커로 트레이스/데이터셋/실험/프롬프트 동기화
- OpenTelemetry + OpenInference 기반 Open RAG Trace 표준으로 외부 시스템 트레이싱 통합
- Domain Memory로 과거 결과를 학습하여 threshold 조정·컨텍스트 보강·트렌드 분석
- 통계·NLP·인과 모듈을 가진 DAG 분석 파이프라인

**현재 상태 메모**
- Web UI 보고서는 기본/상세 템플릿 + LLM 보고서 중심이며 비교 템플릿은 준비 중입니다.
- Domain Memory 인사이트는 CLI 중심으로 제공되며 Web UI 패널은 준비 중입니다.

**개선 필요**
- Web UI에서 GraphRAG/`--kg` 입력과 KG 파일 검증 흐름 추가
- `kg build`/Web UI 산출물과 `--kg` 로더 포맷 통일
- Knowledge Base의 KG 통계/파일 목록/문서 매핑 UI 보강
- `doc_id` 정합성 검증 및 자동 매핑 도구 제공

상세 워크플로와 Phoenix/자동화 예시는 [사용자 가이드](guides/USER_GUIDE.md)를 참고하세요.

---

## 설치

### PyPI
```bash
uv pip install evalvault
```

### 소스 설치 (개발자 권장)
```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault
uv sync --extra dev
```

`dev`는 analysis/korean/web/postgres/mlflow/phoenix/perf/anthropic/docs를 포함합니다. 필요하면 extras로 확장합니다.

| Extra | 패키지 | 용도 |
|-------|--------|------|
| `analysis` | scikit-learn | 통계/NLP 분석 모듈 |
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | 한국어 형태소·검색 |
| `postgres` | psycopg | PostgreSQL 저장소 |
| `mlflow` | mlflow | MLflow 추적기 |
| `docs` | mkdocs, mkdocs-material, mkdocstrings | 문서 빌드 |
| `phoenix` | arize-phoenix + OpenTelemetry | Phoenix 트레이싱/데이터셋/실험 연동 |
| `anthropic` | anthropic | Anthropic LLM 어댑터 |
| `perf` | faiss-cpu, ijson | 대용량 데이터셋 성능 보조 |
| `secrets` | boto3, google-cloud-secret-manager, hvac | Secret Manager 연동 |

`.python-version` 덕분에 uv가 Python 3.12를 자동으로 내려받습니다.

---

## 빠른 사용법

1. **환경 설정**
   ```bash
   cp .env.example .env
   # OPENAI_API_KEY, OLLAMA_BASE_URL, LANGFUSE_* , PHOENIX_* 등을 채워 넣으세요.
   # API 인증을 쓰려면 API_AUTH_TOKENS를 설정하세요.
   # secret:// 참조를 쓰려면 SECRET_PROVIDER 설정 및 secrets extra가 필요합니다.
   # 레이트리밋은 RATE_LIMIT_ENABLED로 활성화합니다.
   ```
SQLite 경로를 쓰려면 아래 값을 추가합니다.
   ```bash
   # .env
   EVALVAULT_DB_PATH=/path/to/data/db/evalvault.db
   EVALVAULT_MEMORY_DB_PATH=/path/to/data/db/evalvault_memory.db
   ```
   vLLM(OpenAI-compatible)을 쓰려면 `EVALVAULT_PROFILE=vllm`로 설정하고
   `.env`에 `VLLM_BASE_URL`, `VLLM_MODEL`을 추가합니다.
   빈 데이터셋 템플릿이 필요하면 `uv run evalvault init`으로
   `dataset_templates/`(JSON/CSV/XLSX) 폴더를 생성하거나 Web UI에서 내려받을 수 있습니다.
   Ollama 모델을 추가하려면 아래처럼 내려받고 목록을 확인합니다.
   ```bash
   ollama pull gpt-oss:120b
   ollama pull gpt-oss-safeguard:120b
   ollama list
   ```
   Web UI 모델 목록은 `ollama list` 기준으로 표시됩니다.
   미리 받아두면 좋은 모델: `gpt-oss:120b`, `gpt-oss-safeguard:120b`, `gpt-oss-safeguard:20b`.
   기본 프로필 모델을 바꾸려면 `config/models.yaml`을 수정하세요.
   vLLM(OpenAI-compatible) 사용 예:
   ```bash
   # .env
   EVALVAULT_PROFILE=vllm
   VLLM_BASE_URL=http://localhost:8001/v1
   VLLM_MODEL=gpt-oss-120b
   VLLM_EMBEDDING_MODEL=qwen3-embedding:0.6b
   # 선택: VLLM_EMBEDDING_BASE_URL=http://localhost:8002/v1
   ```
   초간단 시작 (Ollama 3줄):
   ```bash
   cp .env.example .env
   ollama pull gemma3:1b
   uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
     --metrics faithfulness \
     --db data/db/evalvault.db \
     --profile dev
   ```
   Tip: `answer_relevancy` 등 임베딩 메트릭을 쓰려면 `qwen3-embedding:0.6b`도 내려받으세요.

   초간단 시작 (vLLM 3줄):
   ```bash
   cp .env.example .env
   printf "\nEVALVAULT_PROFILE=vllm\nVLLM_BASE_URL=http://localhost:8001/v1\nVLLM_MODEL=gpt-oss-120b\n" >> .env
   uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
     --metrics faithfulness \
     --db data/db/evalvault.db
   ```
   Tip: 임베딩 메트릭은 `VLLM_EMBEDDING_MODEL`과 `/v1/embeddings` 엔드포인트가 필요합니다.

2. **API + React 프론트 실행 (dev)**
   ```bash
   # API
   uv run evalvault serve-api --reload

   # Frontend
   cd frontend
   npm install
   npm run dev
   ```
   브라우저에서 `http://localhost:5173`를 열어 확인합니다.

3. **평가 실행**
   ```bash
   uv run evalvault run tests/fixtures/sample_dataset.json \
     --metrics faithfulness,answer_relevancy \
     --profile dev \
     --db data/db/evalvault.db
   ```
   Tip: 결과를 history/export/Web UI에서 보려면 `--db` 경로를 동일하게 유지하세요.
   Phoenix 추적이 필요하면 `--tracker phoenix`를 추가하고 `uv sync --extra phoenix`로 설치합니다.

4. **히스토리 확인**
   ```bash
   uv run evalvault history --db data/db/evalvault.db
   ```

Langfuse, Phoenix Dataset/Experiment 업로드, Prompt manifest diff, Prompt snapshot(System/Ragas), Streaming dataset 처리 등 고급 시나리오는 [guides/USER_GUIDE.md](guides/USER_GUIDE.md)에 정리되어 있습니다.

## 실행 모드 (Simple / Full)

EvalVault CLI는 **심플(Simple)** 모드와 **전체(Full)** 모드를 제공합니다. 심플 모드는 2개 메트릭과 Phoenix 추적을 자동으로 묶어 초보자에게 안전한 기본값을 제공하고, 전체 모드는 Domain Memory·Prompt manifest·Phoenix Dataset/Experiment·스트리밍 등 모든 플래그를 그대로 노출합니다.

| 모드 | 명령 | 기본 프리셋 | 활용 사례 |
|------|------|-------------|-----------|
| Simple | `uv run evalvault run --mode simple dataset.json`<br>`uv run evalvault run-simple dataset.json` | `faithfulness + answer_relevancy`, Phoenix tracker 고정, Domain Memory/Prompt 비활성 | 첫 실행, 데모, 온보딩 |
| Full | `uv run evalvault run --mode full dataset.json`<br>`uv run evalvault run-full dataset.json` | 모든 고급 옵션 노출 (Domain Memory, Phoenix dataset/experiment, prompt manifest, streaming) | 파워 유저, CI 게이트, 옵저버빌리티 연동 |

```bash
# 심플 모드: dataset + profile 정도만 지정해도 실행 가능
uv run evalvault run-simple tests/fixtures/e2e/insurance_qa_korean.json -p dev

# 전체 모드: Phoenix + Domain Memory 옵션을 한 번에
uv run evalvault run-full tests/fixtures/e2e/insurance_qa_korean.json \
  --profile prod \
  --tracker phoenix \
  --phoenix-dataset insurance-qa-ko \
  --phoenix-experiment gemma3-prod \
  --use-domain-memory --memory-domain insurance --augment-context
```

- `uv run evalvault history --mode simple/full`로 CLI 히스토리를 즉시 필터링할 수 있습니다.
- Web UI에서도 동일한 모드 토글과 Mode Pill이 표시됩니다.

---

## 문서
- [INDEX.md](INDEX.md): 전체 문서 인덱스
- [handbook/INDEX.md](handbook/INDEX.md): handbook(교과서형, 내부 SSoT)
- [handbook/EXTERNAL.md](handbook/EXTERNAL.md): 외부 공개 요약본
- [handbook/CHAPTERS/04_operations.md](handbook/CHAPTERS/04_operations.md): 운영(로컬/도커/오프라인/관측)
- [handbook/CHAPTERS/06_quality_and_testing.md](handbook/CHAPTERS/06_quality_and_testing.md): 테스트/품질/CI
- (참고) `guides/USER_GUIDE.md`, `guides/DEV_GUIDE.md`, `new_whitepaper/*`는 과거 링크 호환을 위한 deprecated 스텁/아카이브일 수 있습니다.
- [architecture/open-rag-trace-spec.md](architecture/open-rag-trace-spec.md): Open RAG Trace 표준 (Draft)
- [architecture/open-rag-trace-collector.md](architecture/open-rag-trace-collector.md): Collector 구성 예시
- [guides/OPEN_RAG_TRACE_SAMPLES.md](guides/OPEN_RAG_TRACE_SAMPLES.md): 최소 계측 샘플
- [guides/OPEN_RAG_TRACE_INTERNAL_ADAPTER.md](guides/OPEN_RAG_TRACE_INTERNAL_ADAPTER.md): 내부 시스템 최소 계측 래퍼
- [CHANGELOG.md](https://github.com/ntts9990/EvalVault/blob/main/CHANGELOG.md): 릴리스 히스토리

---

## 기여 & 라이선스

Pull Request는 언제든 환영합니다. [CONTRIBUTING.md](https://github.com/ntts9990/EvalVault/blob/main/CONTRIBUTING.md)를 참고하고 제출 전 `uv run ruff check`, `uv run pytest`를 실행해주세요.

EvalVault는 [Apache 2.0](https://github.com/ntts9990/EvalVault/blob/main/LICENSE.md) 라이선스를 따릅니다.
