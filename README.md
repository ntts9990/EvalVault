# EvalVault

> A full-stack evaluation & observability platform for Retrieval-Augmented Generation (RAG) systems.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

Prefer Korean docs? Read the [한국어 README](README.ko.md).

---

## What is EvalVault?

EvalVault aims to be **“the operations console where you can measure, compare, trace, and improve RAG systems in one place.”**
It is not just a scoring script, but a full **evaluation, observability, and analysis layer** for RAG workloads.

- **Dataset‑centric evaluation**: datasets carry metrics, thresholds, and domain knowledge together
- **Decoupled retrievers/LLMs/profiles**: switch OpenAI, Ollama, vLLM, Azure, Anthropic via `config/models.yaml` profiles
- **Stage‑level tracing**: capture fine‑grained `StageEvent`/`StageMetric` across input → retrieval → rerank → generation
- **Domain Memory & analysis pipelines**: learn from past runs to auto‑tune thresholds, enrich context, and generate improvement guides
- **Web UI + CLI**: FastAPI + React Evaluation Studio / Analysis Lab and Typer CLI all operate on the same DB and traces

EvalVault is **an evaluation and analysis hub that spans RAGAS metrics, domain-specific metrics, KG/GraphRAG, stage-level tracing, and analysis pipelines.**

---

## Quickstart (Web & CLI)

**Web (React + FastAPI)**
```bash
uv run evalvault serve-api --reload
```
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`, run an evaluation in Evaluation Studio (for example, upload
`tests/fixtures/e2e/insurance_qa_korean.json`), then check Analysis Lab/Reports for scores
and insights.

**CLI (terminal view)**
```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --db data/db/evalvault.db
uv run evalvault history --db data/db/evalvault.db
uv run evalvault analyze <RUN_ID> --db data/db/evalvault.db
```
Tip: keep the same `--db` (or `EVALVAULT_DB_PATH`) so the Web UI can read the run.

---

## Dataset Format (thresholds live in the dataset)

EvalVault treats thresholds as part of the dataset, so each dataset can carry its own
pass criteria. Missing metric thresholds fall back to `0.7`, and Domain Memory can
adjust them when `--use-domain-memory` is enabled.

```json
{
  "name": "insurance-qa",
  "version": "1.0.0",
  "thresholds": { "faithfulness": 0.8, "answer_relevancy": 0.7 },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "What is the coverage amount?",
      "answer": "The coverage amount is 1M.",
      "contexts": ["Coverage amount is 1M."],
      "ground_truth": "1M"
    }
  ]
}
```

- Required test case fields: `id`, `question`, `answer`, `contexts`
- `ground_truth` is required for `context_precision`, `context_recall`,
  `factual_correctness`, `semantic_similarity`
- CSV/Excel: add `threshold_*` columns (first non-empty row wins). `contexts` can be a
  JSON array string or `|`-separated.
- Generate templates via `uv run evalvault init` (`dataset_templates/`) or start from
  `tests/fixtures/sample_dataset.json`.

---

## Why teams use EvalVault

**Core problems we solve**

- **“이 RAG 시스템이 좋아졌나?”**를 데이터셋·메트릭·threshold 기준으로 명확하게 답하고 싶을 때
- 리트리버/LLM/프롬프트/파라미터가 섞인 복잡한 변경을 **단일 Run ID와 리포트**로 관리하고 싶을 때
- Langfuse·Phoenix·자체 DB에 흩어진 로그를 **Stage 단위로 재구성해 병목과 품질 이슈를 찾고 싶을 때**

**Key capabilities**

- **Unified evaluation CLI**
  - 한 번의 명령으로 실행 → 점수 계산 → DB 저장 → 트레이싱까지 처리
  - Simple/Full 모드로 온보딩과 파워 유저 모두 지원
- **Multi-LLM & profile system**
  - OpenAI / Ollama / vLLM / Azure / Anthropic 등을 `config/models.yaml` 프로필로 스위칭
  - 온프레미스/폐쇄망 환경에서도 동일한 CLI·Web UI 사용 가능
- **Web UI for investigations**
  - Evaluation Studio: 데이터셋 업로드, 실행, 결과 확인
  - Analysis Lab & Reports: 메트릭/히스토리/비교 뷰
- **Stage-level tracing & debugging**
  - `StageEvent` / `StageMetric` / DebugReport로 입력·검색·리랭크·생성 단계를 모두 기록
  - Langfuse / Phoenix 연동으로 외부 트레이싱 시스템과도 연결
- **Domain Memory & analysis pipelines**
  - 도메인 메모리로 과거 실행에서 fact/behavior를 학습해 threshold 보정 및 컨텍스트 보강
  - 통계·NLP·인과 모듈이 포함된 DAG 분석 파이프라인으로 결과를 다각도로 해석

See the [User Guide](docs/guides/USER_GUIDE.md) for end-to-end workflows, Phoenix/Langfuse integration, and troubleshooting.

---

## Installation

### PyPI
```bash
uv pip install evalvault
```

### From Source (recommended for contributors)
```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault
uv sync --extra dev
```

`dev` now bundles analysis/korean/postgres/mlflow/phoenix/perf/anthropic/docs. Add extras as needed:

| Extra | Packages | Purpose |
|-------|----------|---------|
| `analysis` | scikit-learn | Statistical/NLP analysis modules |
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | Korean tokenization & retrieval |
| `postgres` | psycopg | PostgreSQL storage |
| `mlflow` | mlflow | MLflow tracker |
| `docs` | mkdocs, mkdocs-material, mkdocstrings | Docs build |
| `phoenix` | arize-phoenix + OpenTelemetry exporters | Phoenix tracing, dataset/experiment sync |
| `anthropic` | anthropic | Anthropic LLM adapter |
| `perf` | faiss-cpu, ijson | Large dataset performance helpers |

`uv` automatically downloads Python 3.12 based on `.python-version`.

---

## Quick Usage

1. **Configure**
   ```bash
   cp .env.example .env
   # set OPENAI_API_KEY or OLLAMA settings, LANGFUSE/PHOENIX keys, etc.
   ```
   Optional SQLite path override:
   ```bash
   # .env
   EVALVAULT_DB_PATH=/path/to/data/db/evalvault.db
   EVALVAULT_MEMORY_DB_PATH=/path/to/data/db/evalvault_memory.db
   ```
   vLLM (OpenAI-compatible) usage:
   ```bash
   # .env
   EVALVAULT_PROFILE=vllm
   VLLM_BASE_URL=http://localhost:8001/v1
   VLLM_MODEL=gpt-oss-120b
   VLLM_EMBEDDING_MODEL=qwen3-embedding:0.6b
   # optional: VLLM_EMBEDDING_BASE_URL=http://localhost:8002/v1
   ```
   Fast path (Ollama, 3 lines):
   ```bash
   cp .env.example .env
   ollama pull gemma3:1b
   uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
     --metrics faithfulness \
     --db data/db/evalvault.db \
     --profile dev
   ```
   Tip: embedding metrics like `answer_relevancy` also need `qwen3-embedding:0.6b`.

   Fast path (vLLM, 3 lines):
   ```bash
   cp .env.example .env
   printf "\nEVALVAULT_PROFILE=vllm\nVLLM_BASE_URL=http://localhost:8001/v1\nVLLM_MODEL=gpt-oss-120b\n" >> .env
   uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
     --metrics faithfulness \
     --db data/db/evalvault.db
   ```
   Tip: embedding metrics require `VLLM_EMBEDDING_MODEL` and a `/v1/embeddings` endpoint.
   If you use Ollama models that support tool/function calling, list them in
   `OLLAMA_TOOL_MODELS` (comma-separated). Check support via
   `ollama show <model>` and look for `Capabilities: tools`.
   Add Ollama models (optional):
   ```bash
   ollama pull gpt-oss:120b
   ollama pull gpt-oss-safeguard:120b
   ollama list
   ```
   The Web UI model list is sourced from `ollama list`, so newly pulled models
   show up automatically. Suggested models to pre-load:
   `gpt-oss:120b`, `gpt-oss-safeguard:120b`, `gpt-oss-safeguard:20b`.
   Update `config/models.yaml` if you want a default profile model.
   For vLLM (OpenAI-compatible server), set `EVALVAULT_PROFILE=vllm` and
   fill `VLLM_BASE_URL`/`VLLM_MODEL` in `.env`.
   Need empty dataset templates? Run `uv run evalvault init` to generate
   `dataset_templates/` (JSON/CSV/XLSX) or download from the Web UI.

2. **Run the Web UI (FastAPI + React)**
   ```bash
   # Terminal 1: API server
   uv run evalvault serve-api --reload

   # Terminal 2: React frontend
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

3. **Run an evaluation**
   ```bash
   uv run evalvault run tests/fixtures/sample_dataset.json \
     --metrics faithfulness,answer_relevancy \
     --profile dev \
     --db data/db/evalvault.db
   ```
   Tip: `--db` stores results for `history/export/web`. Add `--tracker phoenix` only if
   Phoenix is configured (and `uv sync --extra phoenix` is installed).

4. **Inspect history**
   ```bash
   uv run evalvault history --db data/db/evalvault.db
   ```

More examples (parallel runs, dataset streaming, Langfuse logging, Phoenix dataset sync, prompt manifest diffs, etc.) live in the [User Guide](docs/guides/USER_GUIDE.md).

---

## Run Modes (Simple vs Full)

EvalVault exposes two presets so beginners can execute an evaluation with a single command while advanced users retain every flag.

| Mode | Shortcut | Preset | Ideal for |
|------|----------|--------|-----------|
| **Simple** | `uv run evalvault run --mode simple DATASET.json`<br>`uv run evalvault run-simple DATASET.json` | Locks `faithfulness,answer_relevancy`, forces Phoenix tracking, hides Domain Memory & prompt manifest knobs. | First run, demos, non-experts |
| **Full** | `uv run evalvault run --mode full DATASET.json`<br>`uv run evalvault run-full DATASET.json` | Restores every advanced option (Domain Memory, Phoenix dataset/experiment sync, streaming, prompt manifests). | Power users, CI/CD gate, observability-heavy runs |

```bash
# Simple mode (dataset + optional profile only)
uv run evalvault run-simple tests/fixtures/e2e/insurance_qa_korean.json -p dev

# Full mode with Phoenix + Domain Memory extras
uv run evalvault run-full tests/fixtures/e2e/insurance_qa_korean.json \
  --profile prod \
  --tracker phoenix \
  --phoenix-dataset insurance-qa-ko \
  --phoenix-experiment gemma3-prod \
  --use-domain-memory --memory-domain insurance --augment-context
```

- `uv run evalvault history --mode simple` (or `full`) keeps CLI reports focused.
- The Web UI includes the same mode toggle and surfaces a "Mode" pill on Reports to make comparisons obvious.

---

## Supported Metrics

EvalVault ships with a set of RAG-focused metrics, including the Ragas 0.4.x family,
and is designed to host additional domain-specific and stage-level metrics.

| Metric | Description |
|--------|-------------|
| `faithfulness` | How well the answer is grounded in the provided context |
| `answer_relevancy` | How relevant the answer is to the question |
| `context_precision` | Precision of the retrieved context |
| `context_recall` | Recall of the retrieved context |
| `factual_correctness` | Factual accuracy compared to ground truth |
| `semantic_similarity` | Semantic similarity between answer and ground truth |
| `insurance_term_accuracy` | Domain-specific metric for insurance terminology grounding |

On top of these, `StageMetricService` derives **pipeline-stage metrics** such as:

- `retrieval.precision_at_k`, `retrieval.recall_at_k`, `retrieval.result_count`, `retrieval.latency_ms`
- `rerank.keep_rate`, `rerank.avg_score`, `rerank.latency_ms`
- `output.citation_count`, `output.token_ratio`, `input.query_length`, and more.

---

## Documentation
- [User Guide](docs/guides/USER_GUIDE.md): installation, configuration, CLI recipes, Web UI, Phoenix, automation.
- [Architecture](docs/architecture/ARCHITECTURE.md) & [C4 Diagram](docs/internal/reference/ARCHITECTURE_C4.md): design details.
- [CHANGELOG](CHANGELOG.md) for release history.

---

## Contributing

PRs are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and run `uv run ruff check` + `uv run pytest` before submitting.

---

## License

EvalVault is licensed under the [Apache 2.0](LICENSE.md) license.
