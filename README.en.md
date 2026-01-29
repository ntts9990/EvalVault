# EvalVault

> A full-stack evaluation & observability platform for Retrieval-Augmented Generation (RAG) systems.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

Prefer Korean docs? Read the [한국어 README](README.md).

---

## What is EvalVault?

EvalVault aims to be **"the operations console where you can measure, compare, trace, and improve RAG systems in one place."**
It is not just a scoring script, but a full **evaluation, observability, and analysis layer** for RAG workloads.

- **Dataset‑centric evaluation**: datasets carry metrics, thresholds, and domain knowledge together
- **Decoupled retrievers/LLMs/profiles**: switch OpenAI, Ollama, vLLM, Azure, Anthropic via `config/models.yaml` profiles
- **Stage‑level tracing**: capture fine‑grained `StageEvent`/`StageMetric` across input → retrieval → rerank → generation
- **Open RAG Trace standard**: trace external RAG systems with OpenTelemetry + OpenInference schema
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

- LLM report language: `/api/v1/runs/{run_id}/report?language=en` (default: ko)
  - Details: `docs/handbook/CHAPTERS/00_overview.md`
- Feedback aggregation: latest value per `rater_id` + `test_case_id` (cancellations excluded)
  - Details: `docs/handbook/CHAPTERS/02_data_and_metrics.md`

**CLI (terminal view)**
```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev
uv run evalvault history
uv run evalvault analyze <RUN_ID>
```
Tip: Postgres is the default store. Use `--db` or `DB_BACKEND=sqlite` + `EVALVAULT_DB_PATH` for SQLite, and keep the same settings so the Web UI can read the run.

---

## Analysis Artifacts (Raw Module Outputs)

Reports summarize the analysis, but the raw module outputs are saved separately for easy reuse.
This happens automatically when you run:

- `evalvault run ... --auto-analyze`
- `evalvault analyze-compare <RUN_A> <RUN_B>`

**Single-run analysis (auto)**
- Summary JSON: `reports/analysis/analysis_<RUN_ID>.json`
- Report: `reports/analysis/analysis_<RUN_ID>.md`
- Artifacts index: `reports/analysis/artifacts/analysis_<RUN_ID>/index.json`
- Per-node outputs: `reports/analysis/artifacts/analysis_<RUN_ID>/<node_id>.json`

**Run comparison**
- Summary JSON: `reports/comparison/comparison_<RUN_A>_<RUN_B>.json` (IDs are truncated to 8 chars)
- Report: `reports/comparison/comparison_<RUN_A>_<RUN_B>.md`
- Artifacts index: `reports/comparison/artifacts/comparison_<RUN_A>_<RUN_B>/index.json`
- Per-node outputs: `reports/comparison/artifacts/comparison_<RUN_A>_<RUN_B>/<node_id>.json`

The summary JSON also includes `artifacts.dir` and `artifacts.index` for quick lookup.

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

## Open RAG Trace Standard (External/Internal Systems)

EvalVault ships an **OpenTelemetry + OpenInference-based Open RAG Trace standard** so
external RAG systems can emit traces in the same schema and be analyzed alongside EvalVault runs.
The core contract is **module-level spans (`rag.module`) + log events + shared attributes**.

**What you get**
- Unified Phoenix traces across systems
- Comparable analysis using shared fields
- Non-standard metrics preserved under `custom.*`

**Minimal integration steps**
1. **Run the collector**
   ```bash
   docker run --rm \
     -p 4317:4317 -p 4318:4318 \
     -v "$(pwd)/scripts/dev/otel-collector-config.yaml:/etc/otelcol/config.yaml" \
     otel/opentelemetry-collector:latest \
     --config=/etc/otelcol/config.yaml
   ```
2. **Instrument your system**
   - Python: `OpenRagTraceAdapter`, `trace_module`, `install_open_rag_log_handler`
   - Attribute helpers: `build_retrieval_attributes`, `build_llm_attributes`, etc.
3. **Send OTLP**
   - Via collector: `http://localhost:4318/v1/traces`
   - Direct to Phoenix: `http://localhost:6006/v1/traces`
4. **Validate**
   ```bash
   python3 scripts/dev/validate_open_rag_trace.py --input traces.json
   ```

**OTel attribute limits**
- Only scalars/arrays are supported. Serialize complex objects as JSON strings
  (e.g., `retrieval.documents_json`) or store them as `artifact.uri`.

**Docs**
- `docs/architecture/open-rag-trace-spec.md`
- `docs/architecture/open-rag-trace-collector.md`
- `docs/guides/OPEN_RAG_TRACE_INTERNAL_ADAPTER.md`
- `docs/guides/OPEN_RAG_TRACE_SAMPLES.md`

---

## Why teams use EvalVault

**Core problems we solve**

- **"Did this RAG system get better?"** — Answer clearly with datasets, metrics, and thresholds.
- **Complex changes** involving retriever/LLM/prompt/parameters → manage with a single **Run ID and report**.
- **Scattered logs** across Langfuse, Phoenix, or your own DB → reconstruct at the **Stage level** to pinpoint bottlenecks and quality issues.

**Key capabilities**

- **Unified evaluation CLI**
  - Single command handles execution → scoring → DB storage → tracing
  - Simple/Full modes to support onboarding and power users alike
- **Multi-LLM & profile system**
  - Switch between OpenAI / Ollama / vLLM / Azure / Anthropic via `config/models.yaml` profiles
  - Same CLI and Web UI work in on-premise and air-gapped environments
- **Web UI for investigations**
  - Evaluation Studio: Upload datasets, run evaluations, view results
  - Analysis Lab & Reports: Metrics, history, and comparison views
- **Stage-level tracing & debugging**
  - Record every step—input → retrieval → rerank → generation—with `StageEvent`, `StageMetric`, DebugReport
  - Integrate with Langfuse / Phoenix for external observability
- **Domain Memory & analysis pipelines**
  - Learn facts/behaviors from past runs to auto-tune thresholds and augment context
  - DAG-based analysis pipeline with statistical, NLP, and causal modules for multi-faceted interpretation

See the [Handbook](docs/handbook/INDEX.md) for end-to-end workflows, operations, and troubleshooting.

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
Optional SQLite path override (when using SQLite):
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
  --profile dev
   ```
   Tip: embedding metrics like `answer_relevancy` also need `qwen3-embedding:0.6b`.

   Fast path (vLLM, 3 lines):
   ```bash
   cp .env.example .env
   printf "\nEVALVAULT_PROFILE=vllm\nVLLM_BASE_URL=http://localhost:8001/v1\nVLLM_MODEL=gpt-oss-120b\n" >> .env
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness \
  --profile dev
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
  --profile dev
   ```
   Tip: For SQLite, pass `--db` (or set `DB_BACKEND=sqlite` + `EVALVAULT_DB_PATH`).
   For Postgres, set `POSTGRES_*` or `POSTGRES_CONNECTION_STRING` so the Web UI can
   read the same DB. Add `--tracker phoenix` only if Phoenix is configured
   (and `uv sync --extra phoenix` is installed).

4. **Inspect history**
   ```bash
    uv run evalvault history
   ```

More examples (parallel runs, dataset streaming, Langfuse logging, Phoenix dataset sync, prompt manifest diffs, etc.) live in the [Handbook](docs/handbook/INDEX.md) and `examples/`.

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

## Prompt Language Defaults (RAGAS)

- Korean is the default for summary faithfulness judgment, prompt candidate scoring, and KG relation augmentation.
- Use `language="en"` or `prompt_language="en"` in API/SDK when English is required.

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
| `summary_score` | Summary quality score |
| `summary_faithfulness` | How faithful the summary is to the source |
| `entity_preservation` | Entity preservation between input and output |
| `insurance_term_accuracy` | Domain-specific metric for insurance terminology grounding |

On top of these, `StageMetricService` derives **pipeline-stage metrics** such as:

- `retrieval.precision_at_k`, `retrieval.recall_at_k`, `retrieval.result_count`, `retrieval.latency_ms`
- `rerank.keep_rate`, `rerank.avg_score`, `rerank.latency_ms`
- `output.citation_count`, `output.token_ratio`, `input.query_length`, and more.

---

## Documentation
- [Docs Index](docs/INDEX.md): documentation hub.
- [Handbook](docs/handbook/INDEX.md): internal SSoT (architecture, workflows, ops, quality).
- [External Summary](docs/handbook/EXTERNAL.md): shareable overview.
- [Open RAG Trace Spec](docs/architecture/open-rag-trace-spec.md): tracing schema and integration guide.
- [CHANGELOG](CHANGELOG.md) for release history.

---

## Contributing

PRs are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and run `uv run ruff check` + `uv run pytest` before submitting.

---

## License

EvalVault is licensed under the [Apache 2.0](LICENSE.md) license.
