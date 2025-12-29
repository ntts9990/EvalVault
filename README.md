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
- Dataset loaders for JSON, CSV, and Excel sources
- Cross-platform support (Linux, macOS, Windows)

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

- Standardized scoring with six Ragas v1.0 metrics
- JSON/CSV/Excel dataset loaders with versioned metadata
- Automatic result storage in SQLite (local) and Langfuse (cloud/self-hosted)
- Air-gapped compatibility through Ollama profiles
- Cross-platform CLI with thoughtful defaults

## Installation

### PyPI (Recommended)

```bash
uv pip install evalvault
```

### Development Setup (From Source)

```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault
uv sync --extra dev
```

> **Note**: The `.python-version` file pins Python to 3.12. uv will automatically download and use Python 3.12 if not already installed.

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
```

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
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide |

## Development

```bash
# Tests (always use uv run)
uv run pytest tests/ -v

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
