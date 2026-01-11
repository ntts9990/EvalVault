# Inbound Adapters

Inbound adapters implement the interfaces defined by inbound ports, providing concrete entry points for users and systems.

## CLI Adapter

Command-line interface built with Typer.

The CLI provides various commands for evaluation, analysis, and management:

- **run** - Execute RAG evaluations with various options
- **history** - View evaluation history
- **config** - Manage configuration
- **generate** - Generate test cases
- **pipeline** - Run analysis pipelines
- **benchmark** - Performance benchmarking
- **domain** - Domain memory management
- **phoenix** - Phoenix integration
- **gate** - Quality gates
- **experiment** - A/B testing

For detailed CLI usage, see the [User Guide](../../guides/USER_GUIDE.md).

## Web API Adapter + React Frontend

FastAPI endpoints power the React UI for interactive evaluation and analysis.

The web UI provides:

- **Evaluation Studio**: Run evaluations with real-time progress
- **History**: View past evaluation runs
- **Analysis Lab**: Save and reload analysis results
- **Settings**: Configure LLM providers and trackers

The FastAPI routes live in `src/evalvault/adapters/inbound/api/`, and the web adapter implementation is in `src/evalvault/adapters/inbound/api/adapter.py`. The React frontend is under `frontend/`.

## Usage Examples

### CLI

```bash
# Run evaluation
uv run evalvault run data.csv --metrics faithfulness,answer_relevancy

# View metrics
uv run evalvault metrics

# Compare runs
uv run evalvault compare RUN_ID_A RUN_ID_B
```

### Web UI (React + FastAPI)

```bash
# Start the API
uv run evalvault serve-api --reload

# Start the frontend
cd frontend
npm install
npm run dev
```

For detailed CLI usage, see the [User Guide](../../guides/USER_GUIDE.md).
