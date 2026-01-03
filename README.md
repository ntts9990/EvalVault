# EvalVault

> An end-to-end evaluation harness for Retrieval-Augmented Generation (RAG) systems.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![Ragas](https://img.shields.io/badge/Ragas-v1.0-green.svg)](https://docs.ragas.io/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)
[![PSF Supporting Member](https://img.shields.io/badge/PSF-Supporting%20Member-3776AB?logo=python&logoColor=FFD343)](https://www.python.org/psf/membership/)

Prefer Korean docs? Read the [한국어 README](docs/README.ko.md).

---

## Overview

EvalVault routes structured datasets through Ragas v1.0 metrics, runs evaluations via a
Typer CLI, and writes results to SQLite or Langfuse for longitudinal tracking. It targets
teams that need reproducible RAG scoring across OpenAI, Ollama, or custom profiles with
minimal wiring.

## Highlights

- Batteries-included Typer CLI for running, comparing, and exporting evaluation runs
- Profile-driven model wiring with OpenAI and Ollama defaults
- Optional Langfuse integration for trace-level inspection
- Phoenix observability hooks for OpenTelemetry tracing, dataset sync, embedding drill-down, and prompt manifest tracking
- Prompt Playground loop that links Phoenix prompt IDs, diffs, and EvalVault runs in one manifest
- Dataset loaders for JSON, CSV, and Excel sources
- Cross-platform support (Linux, macOS, Windows)
- **Web UI**: Streamlit dashboard for evaluation, history, and reports
- **Korean NLP**: Morphological analysis with Kiwi, BM25/Dense/Hybrid retrieval
- **Domain Memory**: Learn from evaluation results for continuous improvement (auto thresholds, context boosts, trend insights)
- **NLP Analysis**: Text statistics, question type classification, keyword extraction
- **Causal Analysis**: Root cause analysis and causal relationship discovery
- **Knowledge Graph**: Automatic test set generation from documents
- **Analysis Pipeline**: DAG-based query analysis with intent classification

## Quick Start

```bash
# Install via PyPI
uv pip install evalvault
evalvault run data.json --metrics faithfulness

# Or from source (recommended for development)
git clone https://github.com/ntts9990/EvalVault.git && cd EvalVault
uv sync --extra dev
uv run evalvault run tests/fixtures/sample_dataset.json --metrics faithfulness
```

> **Why uv?** EvalVault uses [uv](https://docs.astral.sh/uv/) for fast, reliable dependency management. All commands should be prefixed with `uv run` when running from source.

## Key Capabilities

- Standardized scoring with six Ragas v1.0 metrics + domain-specific metrics
- JSON/CSV/Excel dataset loaders with versioned metadata
- Automatic result storage in SQLite + PostgreSQL + Langfuse/MLflow
- Phoenix integration: OpenTelemetry tracing, `--phoenix-max-traces`, dataset/experiment sync, embedding analysis, prompt manifest/diff workflow
- Prompt manifest + diff commands to stamp Phoenix prompt IDs onto agent files and tracker metadata
- Air-gapped compatibility through Ollama profiles
- Cross-platform CLI with thoughtful defaults
- **Web UI**: Streamlit dashboard with evaluation, history, and report generation
- **Korean NLP**: Morphological analysis (Kiwi), BM25/Dense/Hybrid retrieval
- **Domain Memory**: Learn from evaluation results for continuous improvement (auto thresholds, context boosts, trend insights)
- **NLP Analysis**: Text statistics, question type classification, keyword extraction, topic clustering
- **Causal Analysis**: Root cause analysis, causal relationship discovery, improvement suggestions
- **Knowledge Graph**: Automatic test set generation from documents
- **Experiment Management**: A/B testing and cross-group metric comparison
- **Analysis Pipeline**: DAG-based query analysis with 12 intent types

## Installation

### PyPI (Recommended)

```bash
uv pip install evalvault
```

### Development Setup (From Source)

```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault

# Basic development environment
uv sync --extra dev

# Full development environment (recommended)
uv sync --extra dev --extra analysis --extra korean --extra web
```

**Optional Extras:**
| Extra | Packages | Purpose |
|-------|----------|---------|
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | Korean NLP (tokenizer, BM25, Dense retriever) |
| `analysis` | scikit-learn | Statistical/NLP analysis pipeline |
| `web` | streamlit, plotly | Streamlit Web UI Dashboard |
| `postgres` | psycopg | PostgreSQL storage support |
| `mlflow` | mlflow | MLflow tracker integration |
| `phoenix` | arize-phoenix, openinference-instrumentation-langchain, opentelemetry-sdk, opentelemetry-exporter-otlp | Phoenix tracing, dataset sync, embedding analysis |
| `anthropic` | anthropic | Anthropic LLM adapter |

> **Note**: The `.python-version` file pins Python to 3.12. uv will automatically download and use Python 3.12 if not already installed.

## Phoenix Observability (Tracing + Experiments)

EvalVault ships with optional Phoenix instrumentation tested against `arize-phoenix` 12.27.0. Install the `phoenix` extra (`uv sync --extra phoenix`) to pull the OpenTelemetry exporters and Phoenix client helpers, then set the following in `.env`:

```bash
PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_API_TOKEN= # Phoenix Cloud only
PHOENIX_SAMPLE_RATE=1.0
```

### Tracker & Trace Options

- `--tracker phoenix` enables OpenInference tracing for each test case. Use `--phoenix-max-traces` to cap how many cases are pushed per run.
- The CLI automatically pushes span metadata such as dataset path, metric names, Domain Memory status, and per-run reliability snapshots so you can slice traces inside Phoenix.
- JSON output embeds `tracker_metadata["phoenix"]["trace_url"]` whenever Phoenix logging succeeds.

### Dataset / Experiment Sync

Use the new CLI switches to mirror EvalVault datasets and experiments inside Phoenix:

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json \
  --metrics faithfulness,answer_relevancy \
  --tracker phoenix \
  --phoenix-dataset insurance-qa-ko \
  --phoenix-dataset-description "보험 QA v2025.01" \
  --phoenix-experiment gemma3-ko-baseline \
  --phoenix-experiment-description "Gemma3 vs OpenAI 비교"
```

- `--phoenix-dataset` uploads the active EvalVault dataset with contexts, answers, metadata, and thresholds. Add `--phoenix-dataset-description` or rely on dataset metadata/`{name} v{version}`.
- `--phoenix-experiment` creates a Phoenix Experiment tied to the uploaded dataset and stores EvalVault metrics, pass rate, and Domain Memory signals. Override the default description via `--phoenix-experiment-description`.
- Both operations add URLs (dataset + experiment) under `result.tracker_metadata["phoenix"]` so downstream automation can deep-link into Phoenix.

### Embedding Visualization & Analysis

Phoenix 12.27.0 ships an Embeddings Analysis workspace (UMAP + HDBSCAN) that shows:

- **Drift over Time** & Query Distance: Euclidean distance charts highlight when primary vs reference embeddings start diverging.
- **Clusters Ordered by Drift**: Automatic HDBSCAN clustering surfaces under-performing or anomalous semantic regions first.
- **3D Point Cloud Coloring**: Color points by correctness, tags, or inference cohorts to debug failure pockets quickly.

Uploading EvalVault datasets unlocks this view immediately—click the dataset or experiment URL from the CLI output/JSON and open the “Embeddings” tab to inspect question/answer/context vectors, overlay Domain Memory tags, and export clusters back into EvalVault.

### Offline Embedding Export

Generate CSV/Parquet snapshots (text + 2D projections + clusters) for Domain Memory cross-analysis:

```bash
uv run evalvault phoenix export-embeddings \
  --dataset phoenix-dataset-id \
  --endpoint http://localhost:6006 \
  --output tmp/phoenix_embeddings.csv
```

UMAP/HDBSCAN is used when available; otherwise the command falls back to PCA/DBSCAN so you always have quick-look embeddings.

### Prompt Playground Loop (Phoenix Prompts)

Phoenix’s Prompt Playground lets you pin prompt iterations to experiments. EvalVault mirrors that context with a manifest (`agent/prompts/prompt_manifest.json` by default) plus CLI helpers:

1. **Link prompt files to Phoenix IDs**

```bash
uv run evalvault phoenix prompt-link agent/prompts/baseline.txt \
  --prompt-id pr-428 \
  --experiment-id exp-20250115 \
  --notes "Gemma3 baseline prompt"
```

2. **Review drift before shipping**

```bash
uv run evalvault phoenix prompt-diff \
  agent/prompts/baseline.txt agent/prompts/system.txt \
  --manifest agent/prompts/prompt_manifest.json \
  --format table  # or json
```

3. **Attach prompt metadata to evaluation runs**

```bash
uv run evalvault run data.json --metrics faithfulness \
  --profile prod \
  --tracker phoenix \
  --prompt-files agent/prompts/baseline.txt,agent/prompts/system.txt \
  --prompt-manifest agent/prompts/prompt_manifest.json
```

> **Prompt loop tip**: Use the `prod` profile (`gpt-oss-safeguard:20b` via OpenAI OSS) whenever you run Phoenix-instrumented prompt loops. This model supports tool-calling, so Phoenix can attach diff metadata without the “does not support tools” error that lightweight Ollama models (e.g., `gemma3:1b`) raise. The run takes longer but keeps prompt regression telemetry intact.

`result.tracker_metadata["phoenix"]["prompts"]` now captures the status for each file (synced/untracked/modified), checksums, and diffs so release notes, history tables, and the Streamlit UI can show prompt drift next to trace/dataset/experiment links.

> Reference: [Phoenix Embeddings Analysis (arize-phoenix-v12.27.0)](https://github.com/Arize-ai/phoenix/blob/arize-phoenix-v12.27.0/docs/phoenix/cookbook/retrieval-and-inferences/embeddings-analysis.mdx). EvalVault aligns with this tag when surfacing embeddings, prompt metadata, and experiment links.

### Phoenix Drift Watcher & Auto Gate

Use `scripts/ops/phoenix_watch.py` to poll Phoenix experiments, push Slack alerts, and trigger `evalvault gate` when embedding drift climbs above an SLA. The watcher:

- Pulls Phoenix datasets via REST, tracking the last seen timestamp to avoid duplicate notifications.
- Evaluates a configurable metric key (default `embedding_drift_score`) and emits threshold alerts in both the terminal and Slack.
- Can run any EvalVault Gate command (or custom shell pipeline) once drift is above the threshold, guaranteeing the regression suite runs automatically.
- When `--run-regressions threshold` or `--run-regressions event` is supplied, automatically invokes `scripts/tests/run_regressions.py` (backed by `config/regressions/default.json`) so smoke/regression pytest suites execute immediately after a Phoenix alert.

```bash
uv run python scripts/ops/phoenix_watch.py \
  --endpoint http://localhost:6006 \
  --dataset-id ds_123 \
  --drift-key embedding_drift_score \
  --drift-threshold 0.18 \
  --slack-webhook https://hooks.slack.com/services/... \
  --gate-command "uv run evalvault gate tests/fixtures/gates/regression.yaml --profile prod" \
  --run-regressions threshold \
  --regression-config config/regressions/default.json
```

### Release Notes Automation

The `phoenix_trace_url`, dataset, and experiment links are now exposed through a helper (`evalvault.config.phoenix_support.format_phoenix_links`) so downstream surfaces stay in sync. Generate Markdown or Slack-ready release notes straight from the CLI JSON:

```bash
uv run evalvault run tests/fixtures/e2e/insurance_qa_korean.json --output run.json
uv run python scripts/reports/generate_release_notes.py \
  --summary run.json \
  --style markdown \
  --out reports/release_notes.md
```

Passing `--style slack` renders `<>` links that can be posted directly to your on-call channel together with Phoenix trace/dataset/experiment links and the embedding export CLI.

### Phoenix Surfaces in CLI & Web

- `uv run evalvault history` adds `Phoenix P@K` and `Drift` columns whenever the stored run includes Phoenix experiment metadata. The resolver pulls precision@k and drift scores directly from the Phoenix REST API (using `PHOENIX_ENDPOINT`/`PHOENIX_API_TOKEN`) so CLI reviewers can jump straight to anomalous experiments.
- The Streamlit dashboard, history table, and report selector show the same metrics plus deep links to the Phoenix experiment page, making it easy to pivot from EvalVault stats to the Embeddings/Trace workspace.

---

## Complete Setup Guide (git clone → Evaluation with Storage)

This section walks you through every step from cloning the repository to running evaluations with Langfuse tracing and SQLite storage.

### Prerequisites

| Requirement | Version | Installation |
|-------------|---------|--------------|
| **Python** | 3.12.x | Auto-installed by uv |
| **uv** | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Docker** | Latest | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Ollama** | Latest | `curl -fsSL https://ollama.com/install.sh \| sh` |

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault

# Install dependencies (Python 3.12 is auto-selected via .python-version)
uv sync --extra dev

# Verify Python version
uv run python --version
# Expected: Python 3.12.x
```

### Step 2: Set Up Ollama (Local LLM)

EvalVault uses Ollama for air-gapped/local LLM evaluation. Start the Ollama server and pull the required models:

```bash
# Start Ollama server (runs in background)
ollama serve &

# Pull required models for dev profile
ollama pull gemma3:1b              # LLM for evaluation
ollama pull qwen3-embedding:0.6b   # Embedding model

# Verify models are installed
ollama list
```

**Expected output:**
```
NAME                    SIZE
gemma3:1b               815 MB
qwen3-embedding:0.6b    639 MB
```

### Step 3: Start Langfuse (Evaluation Tracking)

Langfuse provides trace-level inspection and historical comparison of evaluation runs.

```bash
# Start Langfuse with Docker Compose
docker compose -f docker-compose.langfuse.yml up -d

# Verify all containers are healthy
docker compose -f docker-compose.langfuse.yml ps
```

**Expected containers:**
| Container | Port | Status |
|-----------|------|--------|
| langfuse-web | 3000 | healthy |
| langfuse-worker | 3030 | healthy |
| postgres | 5432 | healthy |
| clickhouse | 8123 | healthy |
| redis | 6379 | healthy |
| minio | 9090 | healthy |

### Step 4: Create Langfuse Project and API Keys

1. Open http://localhost:3000 in your browser
2. **Sign Up** - Create an account (email + password)
3. **New Organization** - Create an organization (e.g., "EvalVault")
4. **New Project** - Create a project (e.g., "RAG-Evaluation")
5. **Settings → API Keys** - Generate new API keys
6. Copy the **Public Key** (`pk-lf-...`) and **Secret Key** (`sk-lf-...`)

### Step 5: Configure Environment Variables

Create a `.env` file with your settings:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# EvalVault Configuration
EVALVAULT_PROFILE=dev

# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

# Langfuse Settings (paste your keys here)
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=http://localhost:3000
```

### Step 6: Run Your First Evaluation

```bash
# Run evaluation with sample dataset
uv run evalvault run tests/fixtures/sample_dataset.json \
  --metrics faithfulness,answer_relevancy

# Expected output:
# ╭───────────────────────────── Evaluation Results ─────────────────────────────╮
# │ Evaluation Summary                                                           │
# │   Run ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx                               │
# │   Dataset: test_dataset v1.0.0                                               │
# │   Model: ollama/gemma3:1b                                                    │
# │   Duration: ~45s                                                             │
# │ Results                                                                      │
# │   Total Test Cases: 4                                                        │
# │   Passed: 4                                                                  │
# │   Pass Rate: 100.0%                                                          │
# ╰──────────────────────────────────────────────────────────────────────────────╯
```

### Step 7: Run Evaluation with Storage

Save results to both Langfuse and SQLite for historical tracking:

```bash
# Run with Langfuse tracing + SQLite storage
uv run evalvault run tests/fixtures/sample_dataset.json \
  --metrics faithfulness,answer_relevancy \
  --langfuse \
  --db evalvault.db

# Expected output includes:
# Logged to Langfuse (trace_id: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)
# Results saved to database: evalvault.db
# Run ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Step 8: Verify Saved Results

**SQLite History:**
```bash
uv run evalvault history --db evalvault.db

# ┏━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┓
# ┃ Run ID      ┃ Dataset    ┃ Model       ┃ Started At ┃ Pass Rate ┃ Test Cases ┃
# ┡━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━┩
# │ 51f0286a... │ test_data… │ ollama/gem… │ 2025-12-29 │    100.0% │          4 │
# └─────────────┴────────────┴─────────────┴────────────┴───────────┴────────────┘
```

**Langfuse Dashboard:**
- Open http://localhost:3000
- Navigate to **Traces** tab
- View detailed trace information for each evaluation run

### Quick Reference

| Task | Command |
|------|---------|
| Run evaluation | `uv run evalvault run data.json --metrics faithfulness` |
| Run with storage | `uv run evalvault run data.json --metrics faithfulness --langfuse --db evalvault.db` |
| View history | `uv run evalvault history --db evalvault.db` |
| List metrics | `uv run evalvault metrics` |
| Show config | `uv run evalvault config` |
| Stop Langfuse | `docker compose -f docker-compose.langfuse.yml down` |

---

## Supported Metrics

| Metric | Description | Ground truth |
|--------|-------------|--------------|
| `faithfulness` | Detects hallucinations by checking if answers stay within retrieved context | Not required |
| `answer_relevancy` | Scores how well the answer addresses the user question | Not required |
| `context_precision` | Measures precision of retrieved passages | Required |
| `context_recall` | Ensures necessary passages were retrieved | Required |
| `factual_correctness` | Compares generated answers to known truths | Required |
| `semantic_similarity` | Semantic overlap between answer and ground truth | Required |

## CLI Reference

> **Note**: When running from source, prefix all commands with `uv run`. When installed via PyPI, use `evalvault` directly.

```bash
# Run evaluations
uv run evalvault run data.json --metrics faithfulness,answer_relevancy

# Run with Langfuse tracing + SQLite storage
uv run evalvault run data.json --metrics faithfulness --langfuse --db evalvault.db

# Parallel evaluation (faster for large datasets)
uv run evalvault run data.json --metrics faithfulness --parallel --batch-size 10

# Select Ollama profile
uv run evalvault run data.json --profile dev --metrics faithfulness

# Select OpenAI profile
uv run evalvault run data.json -p openai --metrics faithfulness

# Show run history
uv run evalvault history --db evalvault.db --limit 10

# Compare runs
uv run evalvault compare <run_id1> <run_id2> --db evalvault.db

# Export results
uv run evalvault export <run_id> -o result.json --db evalvault.db

# Inspect configuration
uv run evalvault config

# List available metrics
uv run evalvault metrics

# Launch Web UI (requires --extra web)
uv run evalvault web --port 8501

# Query-based analysis pipeline (requires --extra korean)
uv run evalvault pipeline analyze "요약해줘" --run-id <run_id>
uv run evalvault pipeline intents     # List analysis intents
uv run evalvault pipeline templates   # List pipeline templates

# Domain Memory (auto threshold tuning)
uv run evalvault run data.json --metrics faithfulness \
  --use-domain-memory --memory-domain insurance --memory-language ko

# Domain Memory + context augmentation
uv run evalvault run data.json --metrics faithfulness \
  --use-domain-memory --augment-context --memory-domain insurance

# Ingest Phoenix embedding clusters into Domain Memory
uv run evalvault domain memory ingest-embeddings phoenix_embeddings.csv \
  --domain insurance \
  --language ko \
  --min-cluster-size 5 \
  --sample-size 3

# Run benchmarks
uv run evalvault benchmark run --name korean-rag
uv run evalvault benchmark list
```

## A/B Testing Guide

EvalVault supports A/B testing to compare different models, prompts, or configurations. This guide walks you through a complete experiment.

### Step 1: Create an Experiment

```bash
uv run evalvault experiment-create \
  --name "Model Comparison" \
  --hypothesis "Larger model will score higher on answer relevancy" \
  --db experiment.db
```

Output:
```
Created experiment: 20421536-e09a-4255-89a3-c402b2b80a2d
  Name: Model Comparison
  Status: draft
```

> Save the experiment ID for the following steps.

### Step 2: Add Groups (A/B)

Create two groups to compare:

```bash
# Group A: Baseline
uv run evalvault experiment-add-group \
  --id <experiment-id> \
  -g "baseline" \
  -d "gemma3:1b (1B params)" \
  --db experiment.db

# Group B: Challenger
uv run evalvault experiment-add-group \
  --id <experiment-id> \
  -g "challenger" \
  -d "gemma3n:e2b (4.5B params)" \
  --db experiment.db
```

### Step 3: Run Evaluations

Run evaluations with different configurations for each group:

```bash
# Group A: Run with baseline model
uv run evalvault run tests/fixtures/sample_dataset.json \
  --profile dev \
  --model gemma3:1b \
  --metrics faithfulness,answer_relevancy \
  --db experiment.db

# Save the Run ID from output (e.g., 34f364e9-cd28-4cf9-a93d-5c706aaf9f14)

# Group B: Run with challenger model
uv run evalvault run tests/fixtures/sample_dataset.json \
  --profile dev \
  --model gemma3n:e2b \
  --metrics faithfulness,answer_relevancy \
  --db experiment.db

# Save the Run ID from output (e.g., 034da928-0f74-4205-8654-6492712472b3)
```

### Step 4: Add Runs to Groups

Link evaluation runs to their respective groups:

```bash
# Add baseline run to Group A
uv run evalvault experiment-add-run \
  --id <experiment-id> \
  -g "baseline" \
  -r <baseline-run-id> \
  --db experiment.db

# Add challenger run to Group B
uv run evalvault experiment-add-run \
  --id <experiment-id> \
  -g "challenger" \
  -r <challenger-run-id> \
  --db experiment.db
```

### Step 5: Compare Results

View the comparison table:

```bash
uv run evalvault experiment-compare --id <experiment-id> --db experiment.db
```

Output:
```
Experiment Comparison

Model Comparison
Hypothesis: Larger model will score higher on answer relevancy

┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric           ┃ baseline ┃ challenger ┃ Best Group ┃ Improvement ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ faithfulness     │    1.000 │      1.000 │  baseline  │       +0.0% │
│ answer_relevancy │    0.908 │      0.957 │ challenger │       +5.4% │
└──────────────────┴──────────┴────────────┴────────────┴─────────────┘
```

### Step 6: Conclude the Experiment

Record your findings:

```bash
uv run evalvault experiment-conclude \
  --id <experiment-id> \
  --conclusion "Challenger model shows 5.4% improvement in answer relevancy with 2x latency trade-off" \
  --db experiment.db
```

### Additional Commands

```bash
# View experiment summary
uv run evalvault experiment-summary --id <experiment-id> --db experiment.db

# List all experiments
uv run evalvault experiment-list --db experiment.db
```

### Quick Reference

| Step | Command |
|------|---------|
| Create experiment | `experiment-create --name "..." --hypothesis "..."` |
| Add group | `experiment-add-group --id <exp> -g "name" -d "desc"` |
| Run evaluation | `run dataset.json --model <model> --db experiment.db` |
| Link run to group | `experiment-add-run --id <exp> -g "group" -r <run>` |
| Compare results | `experiment-compare --id <exp>` |
| Conclude | `experiment-conclude --id <exp> --conclusion "..."` |

---

## Dataset Formats

### JSON (recommended)

```json
{
  "name": "my-dataset",
  "version": "1.0.0",
  "thresholds": {
    "faithfulness": 0.8,
    "answer_relevancy": 0.7
  },
  "test_cases": [
    {
      "id": "tc-001",
      "question": "How much is the payout?",
      "answer": "The payout is 100M KRW.",
      "contexts": ["Life insurance covers 100M KRW."],
      "ground_truth": "100M KRW"
    }
  ]
}
```

> `thresholds` define metric pass criteria (0.0–1.0). Defaults to 0.7 when omitted.

### CSV

```csv
id,question,answer,contexts,ground_truth
tc-001,"How much is the payout?","The payout is 100M KRW.","[""Life insurance covers 100M KRW.""]","100M KRW"
```

## Environment Configuration

```bash
# .env

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano

# Ollama (air-gapped)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TIMEOUT=120

# Langfuse (optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Model Profiles (`config/models.yaml`)

| Profile | LLM | Embedding | Purpose |
|---------|-----|-----------|---------|
| `dev` | gemma3:1b (Ollama) | qwen3-embedding:0.6b | Local development |
| `prod` | gpt-oss-safeguard:20b (Ollama) | qwen3-embedding:8b | Production |
| `openai` | gpt-5-nano | text-embedding-3-small | External network |

## Architecture Overview

```
EvalVault/
├── config/               # Model profiles and runtime config
├── src/evalvault/
│   ├── domain/           # Entities, services, metrics
│   ├── ports/            # Inbound/outbound contracts
│   ├── adapters/         # CLI, LLM, storage, tracers
│   └── config/           # Settings + providers
├── docs/                 # Architecture, user guide, roadmap
└── tests/                # unit / integration / e2e_data suites
```

## Documentation

| File | Description |
|------|-------------|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Installation, configuration, troubleshooting |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Hexagonal architecture deep dive |
| [docs/COMPLETED.md](docs/COMPLETED.md) | Phase 1-14 achievements and technical specs |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 2026-2027 development roadmap |
| [docs/IMPROVEMENT_PLAN.md](docs/IMPROVEMENT_PLAN.md) | Code quality improvement plan |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide |

## Development

```bash
# Tests (always use uv run)
uv run pytest tests/ -v
# Total: 1,352 tests (1,261 unit + 91 integration) | Coverage: 89%

# E2E scenarios (requires external APIs)
uv run pytest tests/integration/test_e2e_scenarios.py -v

# Linting & formatting
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Community & PSF Membership

EvalVault is stewarded by a [Python Software Foundation](https://www.python.org/psf/)
Supporting Member. We reinvest contributions into open-source tooling and the broader
Python community.

<p align="left">
  <a href="https://www.python.org/psf/membership/">
    <img src="docs/assets/psf-supporting-member.png" alt="PSF Supporting Member badge" width="130" />
  </a>
</p>

## License

Apache 2.0 — see [LICENSE.md](LICENSE.md).

---

<div align="center">
  <strong>EvalVault</strong> — raising the bar for dependable RAG evaluation.
</div>
