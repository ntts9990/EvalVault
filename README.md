# EvalVault

> Evaluation tooling for Retrieval-Augmented Generation (RAG) systems.

[![PyPI](https://img.shields.io/pypi/v/evalvault.svg)](https://pypi.org/project/evalvault/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ntts9990/EvalVault/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE.md)

Prefer Korean docs? Read the [한국어 README](docs/README.ko.md).

---

## Overview

EvalVault measures RAG quality with Ragas v1.0 metrics, provides a Typer CLI and Streamlit Web UI, and logs every run to SQLite/PostgreSQL, Langfuse, or Phoenix. It targets teams that need reproducible scoring across OpenAI, Ollama, or fully air‑gapped profiles without wiring new scripts for each dataset.

**Highlights**
- One CLI for running, comparing, exporting, and storing evaluation runs
- Profile-driven LLM wiring (OpenAI, Ollama, Azure, Anthropic)
- Streamlit Web UI for evaluation, history, and report generation
- Langfuse + Phoenix trackers for traces, datasets, experiments, prompt manifests, and embedding exports
- Domain Memory layer that learns from past runs (auto thresholds, context boosts, trend insights)
- DAG-based analysis pipeline with statistical/NLP/causal modules

**Status notes**
- Web UI reports focus on basic/detailed templates and LLM analysis; comparison templates are in progress.
- Domain Memory insights are CLI-first today; a Web UI panel is planned.

See the [User Guide](docs/guides/USER_GUIDE.md) for full workflows, Phoenix automation, and troubleshooting.

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

Add extras as needed:

| Extra | Packages | Purpose |
|-------|----------|---------|
| `analysis` | scikit-learn | Statistical/NLP analysis modules |
| `korean` | kiwipiepy, rank-bm25, sentence-transformers | Korean tokenization & retrieval |
| `web` | streamlit, plotly | Streamlit Web UI |
| `postgres` | psycopg | PostgreSQL storage |
| `mlflow` | mlflow | MLflow tracker |
| `phoenix` | arize-phoenix + OpenTelemetry exporters | Phoenix tracing, dataset/experiment sync |
| `anthropic` | anthropic | Anthropic LLM adapter |

`uv` automatically downloads Python 3.12 based on `.python-version`.

---

## Quick Usage

1. **Configure**
   ```bash
   cp .env.example .env
   # set OPENAI_API_KEY or OLLAMA settings, LANGFUSE/PHOENIX keys, etc.
   ```
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

2. **Run the API + React frontend (dev)**
   ```bash
   # API
   uv run evalvault serve-api --reload

   # Frontend
   cd frontend
   npm install
   npm run dev
   ```

3. **Run an evaluation**
   ```bash
   uv run evalvault run tests/fixtures/sample_dataset.json \
     --metrics faithfulness,answer_relevancy \
     --profile dev \
     --tracker phoenix \
     --db evalvault.db
   ```

4. **Inspect history**
   ```bash
   uv run evalvault history --db evalvault.db
   ```

5. **Launch the Web UI**
   ```bash
   uv run evalvault web --browser
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

- `uv run evalvault history --mode simple` (또는 `full`) keeps CLI reports focused.
- Streamlit **📊 Evaluate** now includes the same mode toggle and surfaces a “Mode” pill on **📄 Reports** to make comparisons obvious.

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
