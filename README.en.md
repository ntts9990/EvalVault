# EvalVault

> A full-stack evaluation & observability platform for Retrieval-Augmented Generation (RAG) systems.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

Prefer Korean docs? Read the [한국어 README](README.md).

---

## What EvalVault solves

EvalVault answers **"did this RAG change actually get better?"** with datasets, metrics, and
thresholds — and lets you reproduce, compare, and trace the evidence (scores, traces,
artifacts) in one place. It is not a scoring script but a full **evaluation + observability +
analysis layer** for RAG workloads, binding **Eval → Analysis → Tracing → Improvement** into a
single CLI + Web UI workflow.

- **Dataset-centric evaluation** — datasets carry metrics, thresholds, and domain knowledge together
- **Decoupled retrievers / LLMs / profiles** — switch OpenAI, Ollama, vLLM, Azure, Anthropic via `config/models.yaml`
- **Stage-level tracing** — capture `StageEvent`/`StageMetric` across input → retrieval → rerank → generation
- **Open RAG Trace standard** — trace external RAG systems with the same OpenTelemetry + OpenInference schema
- **Domain Memory & analysis pipelines** — learn from past runs to auto-tune thresholds, enrich context, and generate improvement guides
- **CLI + Web UI** — Typer CLI and the FastAPI + React Evaluation Studio / Analysis Lab operate on the same `run_id`, DB, and traces

> Status: stable (hexagonal architecture, dual trackers, 2,100+ passing tests). Phases 1–14 plus
> the refactor slice program are complete. See [CHANGELOG.md](CHANGELOG.md) for recent changes.

---

## Quickstart

### CLI

```bash
uv sync --extra dev
cp .env.example .env   # set OPENAI_API_KEY or Ollama/vLLM + tracker keys

uv run evalvault run --mode simple tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --profile dev \
  --auto-analyze

uv run evalvault history          # run history
uv run evalvault analyze <RUN_ID> # statistical analysis
```

> The default store is **PostgreSQL + pgvector**. For SQLite use `--db <path>` or
> `DB_BACKEND=sqlite` + `EVALVAULT_DB_PATH`, and keep the same settings so the Web UI reads the run.

### Web UI (React + FastAPI)

```bash
# Terminal 1 — API
uv run evalvault serve-api --reload

# Terminal 2 — frontend
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173` → run an evaluation in **Evaluation Studio**, then review scores and
insights in **Analysis Lab / Reports**. Pick the LLM report language via
`GET /api/v1/runs/{run_id}/report?language=en` (default: ko).

---

## Key capabilities

- **End-to-end evaluation loop** — execution → scoring → DB storage → tracing in one command
- **Simple / Full modes** — one-line runs for newcomers, every flag for power users (`run-simple` / `run-full`)
- **Artifacts-first** — raw per-module outputs saved alongside reports (`reports/analysis/artifacts/...`)
- **Optional observability** — MLflow + Phoenix (dual by default) / Langfuse only when needed (open-circuit: a tracker outage never fails the evaluation)
- **Regression gate (CI/CD)** — `evalvault regress` / `ci-gate` detect statistical regressions vs. a baseline and integrate via stable-schema JSON + exit codes (evaluation-gate verdicts go up to `passed`/`failed` only — never release promote/rollback)
- **Experiment management (A/B)** — `experiment-*` commands compare groups/runs and record conclusions
- **Korean NLP** — Kiwi morphological analysis + BM25 + dense/hybrid retrieval (`--extra korean`)
- **Knowledge Graph / GraphRAG** — KG generation and top-k vs GraphRAG comparison experiments

---

## Architecture (Hexagonal · Ports & Adapters)

The domain never imports adapters; every external integration sits behind a port.

```
src/evalvault/
├── domain/
│   ├── entities/   # TestCase, Dataset, EvaluationRun, MetricScore, Experiment ...
│   ├── services/   # RagasEvaluator + extracted services (cost / fallback / metric
│   │               #   scoring / prompt catalog·overrides / Korean·language detection /
│   │               #   claim-level conversion)
│   └── metrics/    # domain-specific custom metrics
├── ports/
│   ├── inbound/    # EvaluatorPort
│   └── outbound/   # LLMPort, DatasetPort, StoragePort, TrackerPort, DomainMemoryPort ...
├── adapters/
│   ├── inbound/    # CLI (Typer), Web API (FastAPI), MCP
│   └── outbound/
│       ├── llm/       # OpenAI, Azure, Anthropic, Ollama, vLLM (+RetryPolicy)
│       ├── storage/   # SQLite, PostgreSQL (+pgvector)
│       └── tracker/   # MLflow, Phoenix, Langfuse, MultiTrackerAdapter (dual logging)
└── config/         # Settings, ModelConfig (pydantic-settings), profiles
```

| Port | Adapter | Notes |
|------|---------|-------|
| LLMPort | OpenAI / Azure / Anthropic / Ollama / vLLM | shared `RetryPolicy` (timeout + backoff) |
| StoragePort | SQLite / PostgreSQL (+pgvector) | an explicit `--db` forces SQLite |
| TrackerPort | MLflow / Phoenix / Langfuse / **MultiTrackerAdapter** | `mlflow+phoenix` dual by default, open-circuit |
| EvaluatorPort | RagasEvaluator | Ragas 0.4.x + custom / stage metrics |

Details: [docs/handbook/CHAPTERS/01_architecture.md](docs/handbook/CHAPTERS/01_architecture.md)

---

## Supported metrics

**Ragas family**

| Metric | Description |
|--------|-------------|
| `faithfulness` | How well the answer is grounded in the context |
| `answer_relevancy` | How relevant the answer is to the question (needs embeddings) |
| `context_precision` | Precision of the retrieved context (needs ground_truth) |
| `context_recall` | Recall of the retrieved context (needs ground_truth) |
| `factual_correctness` | Factual accuracy vs. ground truth |
| `semantic_similarity` | Semantic similarity between answer and ground truth (needs embeddings) |
| `summary_score` / `summary_faithfulness` | Summary quality / summary faithfulness |

**Domain · retrieval · summary custom metrics**

`insurance_term_accuracy`, `entity_preservation`, `exact_match`, `f1_score`, `no_answer_accuracy`,
`confidence_score`, `contextual_relevancy`, ranking (`mrr`, `ndcg`, `hit_rate`), and summary
(`summary_accuracy`, `summary_risk_coverage`, `summary_non_definitive`, `summary_needs_followup`).

**Stage metrics** — `StageMetricService` derives per-stage metrics: `retrieval.precision_at_k`,
`retrieval.recall_at_k`, `retrieval.latency_ms`, `rerank.keep_rate`, `rerank.avg_score`,
`output.citation_count`, `input.query_length`, and more.

Definitions & threshold policy: [docs/handbook/CHAPTERS/02_data_and_metrics.md](docs/handbook/CHAPTERS/02_data_and_metrics.md) · live list via `uv run evalvault metrics`.

---

## CLI surface

Command groups (root + sub-apps). Full options via `uv run evalvault <command> --help`.

- **Run / evaluate**: `run`, `run-simple`, `run-full`, `pipeline`, `generate` (synthetic datasets)
- **History / compare / analyze**: `history`, `export`, `compare`, `analyze`, `analyze-compare`, `profile-difficulty`
- **Regression / gate**: `regress`, `ci-gate`, `regress-baseline`, `gate`
- **Experiments (A/B)**: `experiment-create|add-group|add-run|list|compare|conclude|summary`
- **Calibration**: `calibrate`, `calibrate-judge`
- **Config / observability**: `config`, `metrics`, `serve-api`, `langfuse-dashboard`
- **Sub-apps**: `kg`, `domain`, `graphrag`, `benchmark`, `method`, `ops`, `phoenix`, `prompts`, `stage`, `artifacts`, `debug`

Workflow details: [docs/handbook/CHAPTERS/03_workflows.md](docs/handbook/CHAPTERS/03_workflows.md)

---

## Dataset format (thresholds live in the dataset)

```json
{
  "name": "insurance-qa",
  "version": "1.0.0",
  "thresholds": { "faithfulness": 0.8, "answer_relevancy": 0.7 },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "What is the coverage amount?",
      "answer": "The coverage amount is 100M KRW.",
      "contexts": ["The death-benefit coverage amount is 100M KRW."],
      "ground_truth": "100M KRW"
    }
  ]
}
```

- Required fields: `id`, `question`, `answer`, `contexts`. Missing thresholds fall back to `0.7`.
- `ground_truth` is required for `context_precision`, `context_recall`, `factual_correctness`, `semantic_similarity`.
- CSV/Excel: `threshold_*` columns supported; `contexts` may be a JSON-array string or `|`-separated.
- Templates: `uv run evalvault init` (`dataset_templates/`) or `tests/fixtures/sample_dataset.json`.

---

## LLM profiles & storage

- **Profiles**: bundle provider/model/embedding in `config/models.yaml` and switch with `--profile dev|prod|vllm ...`. The same CLI and Web UI run on-prem and air-gapped.
- **vLLM (OpenAI-compatible)**: `EVALVAULT_PROFILE=vllm` + `VLLM_BASE_URL`/`VLLM_MODEL` (+ embedding endpoint).
- **Ollama**: `ollama pull <model>`; list tool-calling models in `OLLAMA_TOOL_MODELS`.
- **Storage**: PostgreSQL (+pgvector) by default, SQLite optional. Env vars: [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md) §5.2 / `.env.example`.

---

## Open RAG Trace standard (external/internal systems)

An OpenTelemetry + OpenInference standard so external RAG systems can emit traces in the same
schema — **module-level spans (`rag.module`) + log events + shared attributes** — and be analyzed
alongside EvalVault runs.

```bash
# Run an OTel Collector → http://localhost:4318/v1/traces (or Phoenix :6006)
python3 scripts/dev/validate_open_rag_trace.py --input traces.json
```

- Adapters: `OpenRagTraceAdapter`, `trace_module`, `install_open_rag_log_handler`
- Spec: [docs/architecture/open-rag-trace-spec.md](docs/architecture/open-rag-trace-spec.md)

---

## Offline / air-gapped

- Docker image bundle: [docs/guides/OFFLINE_DOCKER.md](docs/guides/OFFLINE_DOCKER.md)
- NLP model cache bundle: [docs/guides/OFFLINE_MODELS.md](docs/guides/OFFLINE_MODELS.md)

LLM models are managed by the air-gapped infrastructure; EvalVault bundles only the **analysis NLP model cache**.

---

## Documentation

- Entry point (SSoT): [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md)
- Docs index: [docs/INDEX.md](docs/INDEX.md) · Handbook: [docs/handbook/INDEX.md](docs/handbook/INDEX.md) · External summary: [docs/handbook/EXTERNAL.md](docs/handbook/EXTERNAL.md)
- Architecture: [01_architecture](docs/handbook/CHAPTERS/01_architecture.md) · Data/metrics: [02_data_and_metrics](docs/handbook/CHAPTERS/02_data_and_metrics.md) · Workflows: [03_workflows](docs/handbook/CHAPTERS/03_workflows.md)
- Operations: [04_operations](docs/handbook/CHAPTERS/04_operations.md) · Quality/testing/CI: [06_quality_and_testing](docs/handbook/CHAPTERS/06_quality_and_testing.md) · Roadmap: [08_roadmap](docs/handbook/CHAPTERS/08_roadmap.md)
- Adapter contract (tool integration): [docs/adapter-contract.md](docs/adapter-contract.md) · machine-readable state: `.ai-tool-suite/project-state.json` · change narrative: [docs/development-journal.md](docs/development-journal.md)

---

## Acknowledgements

[![PSF Supporting Member](https://img.shields.io/badge/PSF-Supporting%20Member-3776AB?logo=python&logoColor=white)](https://www.python.org/psf/)

The maintainer is a [Python Software Foundation](https://www.python.org/psf/) supporting member, backing the Python ecosystem. 🐍

---

## License

EvalVault is licensed under the [Apache 2.0](LICENSE.md) license.
