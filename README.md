# EvalVault

> RAG(Retrieval-Augmented Generation) 시스템의 **품질 측정 · 관측 · 개선**을 한 번에 처리하는 평가 플랫폼

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

English version? See [README.en.md](README.en.md).

---

## EvalVault 한눈에 보기

EvalVault의 목표는 **"RAG 시스템의 품질을 데이터셋/메트릭/트레이싱 관점에서 일관되게 관리하는 운영 콘솔"**입니다.
단순 점수 계산기가 아니라, 아래 네 가지 축을 모두 다룹니다.

- **평가(Evaluation)**: 데이터셋 기반으로 다양한 LLM/리트리버/프롬프트 조합을 실험하고 점수/threshold 관리
- **관측(Observability)**: Stage 단위 이벤트와 메트릭, Langfuse/Phoenix 트레이스를 한 Run ID로 연결
- **학습(Domain Memory)**: 과거 실행으로부터 도메인 지식/패턴을 축적해 threshold, 컨텍스트, 리포트를 자동 보정
- **분석(Analysis Pipelines)**: 통계·NLP·인과 모듈이 포함된 DAG 파이프라인으로 결과를 다각도로 해석

EvalVault는 **RAGAS 메트릭과 도메인 맞춤형 메트릭, KG/GraphRAG, Stage-level 트레이싱, 분석 파이프라인까지 아우르는 평가/분석 허브**를 지향합니다.

---

## 가장 빠르게 Web + CLI로 시작하기

EvalVault의 가장 큰 장점은 **평가 → 자동 분석 → 보고서/아티팩트 저장 → 비교**가 하나의 `run_id`로 끊김 없이 이어져서, 재현성과 개선 루프가 매우 빠르다는 점입니다. 점수만 보는 게 아니라 통계·NLP·원인 분석까지 묶어서 바로 "왜 좋아졌는지/나빠졌는지"로 이어지는 게 핵심입니다.

### 초간단 실행 (CLI)

```bash
uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db \
  --auto-analyze
```

### 결과 확인 경로

평가 실행 후 자동 분석이 완료되면 다음 파일들이 생성됩니다:

- **요약 JSON**: `reports/analysis/analysis_<RUN_ID>.json`
- **Markdown 보고서**: `reports/analysis/analysis_<RUN_ID>.md`
- **아티팩트 인덱스**: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`
- **노드별 결과**: `reports/analysis/artifacts/analysis_<RUN_ID>/<node_id>.json`

요약 JSON에는 `artifacts.dir`와 `artifacts.index`가 포함되어 있어 경로 조회가 쉽습니다.

### A/B 비교

두 실행 결과를 비교하려면:

```bash
uv run evalvault analyze-compare <RUN_A> <RUN_B> --db data/db/evalvault.db
```

결과는 `reports/comparison/comparison_<RUN_A>_<RUN_B>.md`에 저장됩니다.

### Web UI 연동

CLI와 Web UI가 동일한 DB를 사용하면 Web UI에서 바로 결과를 확인할 수 있습니다:

**Web (React + FastAPI)**
```bash
uv run evalvault serve-api --reload
```
```bash
cd frontend
npm install
npm run dev
```
브라우저에서 `http://localhost:5173`에 접속한 뒤 Evaluation Studio에서 평가를 실행하고
Analysis Lab/Reports에서 점수와 분석 결과를 확인하세요. (예: `tests/fixtures/e2e/insurance_qa_korean.json` 업로드)

동일한 DB(`data/db/evalvault.db`)를 사용하면 Web UI에서 바로 이어서 볼 수 있습니다.

---

## 분석 아티팩트 (모듈별 원본 결과)

보고서는 요약본이고, 분석 파이프라인에서 생성된 **모듈별 원본 결과**는 자동으로 별도 저장됩니다.
아래 명령에서 항상 함께 저장됩니다.

- `evalvault run ... --auto-analyze`
- `evalvault analyze-compare <RUN_A> <RUN_B>`

**단일 실행 자동 분석**
- 요약 JSON: `reports/analysis/analysis_<RUN_ID>.json`
- 보고서: `reports/analysis/analysis_<RUN_ID>.md`
- 아티팩트 인덱스: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`
- 노드별 결과: `reports/analysis/artifacts/analysis_<RUN_ID>/<node_id>.json`

**두 실행 비교**
- 요약 JSON: `reports/comparison/comparison_<RUN_A>_<RUN_B>.json` (파일명은 Run ID 앞 8자리)
- 보고서: `reports/comparison/comparison_<RUN_A>_<RUN_B>.md`
- 아티팩트 인덱스: `reports/comparison/artifacts/comparison_<RUN_A>_<RUN_B>/index.json`
- 노드별 결과: `reports/comparison/artifacts/comparison_<RUN_A>_<RUN_B>/<node_id>.json`

요약 JSON에는 `artifacts.dir`, `artifacts.index`가 함께 들어가므로 경로 조회가 쉽습니다.

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
- CSV/Excel: `threshold_*` 컬럼으로 임계값 지정 (첫 번째로 채워진 행 기준).
  `contexts`는 JSON 배열 문자열 또는 `|`로 구분합니다.
- 템플릿: `uv run evalvault init`로 `dataset_templates/` 생성,
  또는 `tests/fixtures/sample_dataset.json` 참고.

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
- 템플릿: `docs/templates/retriever_docs_template.json`,
  `docs/templates/kg_template.json`
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

## 왜 EvalVault인가?

**우리가 풀고 싶은 문제**

- "모델/프롬프트/리트리버를 바꿨을 때 **정말 좋아진 건지** 수치로 설명하기 어렵다."
- LLM 로그, 검색 로그, 트레이스가 여러 곳에 흩어져 있고 **한 눈에 병목·품질 이슈를 잡기 힘들다.**
- 팀/프로젝트마다 ad-hoc 스크립트가 늘어나 **재현성과 회귀 테스트가 깨지기 쉽다.**

EvalVault는 이 문제를 위해 다음과 같은 축으로 설계되었습니다.

- **데이터셋 중심 평가**
  - JSON/CSV/XLSX 데이터셋에 메트릭/threshold/도메인 정보를 함께 정의
  - 동일 데이터셋으로 모델/리트리버/프롬프트 실험을 반복 가능하게 관리
- **LLM/리트리버 프로필 시스템**
  - OpenAI, Ollama, vLLM, Azure, Anthropic 등을 `config/models.yaml` 프로필로 선언
  - 로컬/클라우드/폐쇄망 환경 간에도 동일한 CLI·Web 흐름 유지
- **Stage 단위 트레이싱 & 디버깅**
  - `StageEvent`/`StageMetric`/DebugReport로 입력 → 검색 → 리랭크 → 최종 답변까지 단계별로 기록
  - Langfuse·Phoenix 트레이서와 연동해 외부 관측 시스템과 바로 연결
- **Domain Memory & 분석 파이프라인**
  - 과거 실행에서 fact/behavior를 추출해 threshold 튜닝, 컨텍스트 보강, 개선 가이드 자동화
  - 통계·NLP·인과 분석 모듈이 포함된 DAG 파이프라인으로 성능 저하 원인 추적
- **Web UI + CLI 일관성**
  - Typer CLI와 **FastAPI + React Web UI**가 동일한 DB/트레이스 위에서 동작
  - 로컬 실험 → 팀 공유 → CI/CD 게이트까지 하나의 도구 체인으로 연결

상세 워크플로와 Phoenix/자동화 예시는 [사용자 가이드](docs/guides/USER_GUIDE.md)를 참고하세요.

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

`dev`는 analysis/korean/postgres/mlflow/phoenix/perf/anthropic/docs를 포함합니다. 필요하면 extras로 확장합니다.

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

`.python-version` 덕분에 uv가 Python 3.12를 자동으로 내려받습니다.

---

## 빠른 사용법

1. **환경 설정**
   ```bash
   cp .env.example .env
   # OPENAI_API_KEY, OLLAMA_BASE_URL, LANGFUSE_* , PHOENIX_* 등을 채워 넣으세요.
   ```
   SQLite 경로를 바꾸려면 아래 값을 추가합니다.
   ```bash
   # .env
   EVALVAULT_DB_PATH=/path/to/data/db/evalvault.db
   EVALVAULT_MEMORY_DB_PATH=/path/to/data/db/evalvault_memory.db
   ```
   Ollama에서 tool/function calling 지원 모델을 쓰려면 `OLLAMA_TOOL_MODELS`에
   콤마로 모델명을 추가하세요. 확인은 `ollama show <model>`로 하고
   `Capabilities`에 `tools`가 표시되는 모델만 넣으면 됩니다.
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

2. **Web UI 실행 (FastAPI + React)**
   ```bash
   # 터미널 1: API 서버
   uv run evalvault serve-api --reload

   # 터미널 2: React 프론트엔드
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

Langfuse, Phoenix Dataset/Experiment 업로드, Prompt manifest diff, Prompt snapshot(System/Ragas), Streaming dataset 처리 등 고급 시나리오는 [USER_GUIDE.md](docs/guides/USER_GUIDE.md)에 정리되어 있습니다.

---

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

## 지원 메트릭

EvalVault는 RAG 평가에 널리 쓰이는 Ragas 0.4.x 계열 메트릭을 기본으로 제공하면서,
도메인 특화 메트릭과 Stage-level 메트릭을 함께 다루도록 설계되어 있습니다.

| 메트릭 | 설명 |
|--------|------|
| `faithfulness` | 답변이 제공된 컨텍스트에 얼마나 충실한지 |
| `answer_relevancy` | 답변이 질문 의도와 얼마나 잘 맞는지 |
| `context_precision` | 검색된 컨텍스트가 얼마나 불필요한 내용을 적게 포함하는지 |
| `context_recall` | 필요한 정보가 컨텍스트에 충분히 포함되었는지 |
| `factual_correctness` | ground_truth 대비 사실적 정확성 |
| `semantic_similarity` | 답변과 ground_truth 간 의미적 유사도 |
| `summary_score` | 요약 품질 점수 |
| `summary_faithfulness` | 요약이 원본에 얼마나 충실한지 |
| `entity_preservation` | 입력과 출력 간 엔티티 보존 |
| `insurance_term_accuracy` | 보험 도메인 용어 정합성 (예시 도메인 메트릭) |

또한 `StageMetricService`를 통해 다음과 같은 **파이프라인 단계 메트릭**을 함께 다룹니다.

- `retrieval.precision_at_k`, `retrieval.recall_at_k`, `retrieval.result_count`, `retrieval.latency_ms`
- `rerank.keep_rate`, `rerank.avg_score`, `rerank.latency_ms`
- `output.citation_count`, `output.token_ratio`, `input.query_length` 등

---

## 문서
- [docs/INDEX.md](docs/INDEX.md): 전체 문서 인덱스
- [docs/guides/USER_GUIDE.md](docs/guides/USER_GUIDE.md): 설치/환경설정/CLI/Web UI/Phoenix/자동화/문제 해결
- [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md): 설계 문서
- [CHANGELOG.md](CHANGELOG.md): 릴리스 히스토리

---

## 기여 & 라이선스

Pull Request는 언제든 환영합니다. [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하고 제출 전 `uv run ruff check`, `uv run pytest`를 실행해주세요.

EvalVault는 [Apache 2.0](LICENSE.md) 라이선스를 따릅니다.
