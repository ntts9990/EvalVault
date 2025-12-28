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
uv pip install evalvault
evalvault run data.json --metrics faithfulness
```

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

### Development Setup

```bash
git clone https://github.com/ntts9990/EvalVault.git
cd EvalVault
uv sync --extra dev
```

## Run Your First Evaluation

```bash
# 1. Configure secrets
cp .env.example .env
echo "OPENAI_API_KEY=sk-your-key" >> .env

# 2. Execute an evaluation
evalvault run data.json --metrics faithfulness

# 3. Inspect history
evalvault history
```

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

```bash
# Run evaluations
evalvault run data.json --metrics faithfulness,answer_relevancy

# Parallel evaluation (faster for large datasets)
evalvault run data.json --metrics faithfulness --parallel --batch-size 10

# Select Ollama profile
evalvault run data.json --profile dev --metrics faithfulness

# Select OpenAI profile
evalvault run data.json -p openai --metrics faithfulness

# Enable Langfuse tracing
evalvault run data.json --metrics faithfulness --langfuse

# Show run history
evalvault history --limit 10

# Compare runs
evalvault compare <run_id1> <run_id2>

# Export results
evalvault export <run_id> -o result.json

# Inspect configuration
evalvault config
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

## Ollama Setup (Air-gapped)

1. Install Ollama
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh  # Linux/macOS
   ```
2. Download models
   ```bash
   ollama pull gemma3:1b
   ollama pull qwen3-embedding:0.6b
   ```
3. Run via a profile
   ```bash
   evalvault run data.json --profile dev --metrics faithfulness
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
