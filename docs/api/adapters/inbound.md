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

For detailed CLI usage, see the [CLI Guide](../../guides/CLI_GUIDE.md).

## Web UI Adapter

Streamlit-based web interface for interactive evaluation.

The web UI consists of several pages:

- **Evaluate**: Run evaluations with real-time progress
- **History**: View past evaluation runs
- **Reports**: Generate and download reports
- **Settings**: Configure LLM providers and trackers

The web UI is located in `src/evalvault/adapters/inbound/web/` and includes reusable components for metrics display, dataset uploading, and visualization.

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

### Web UI

```bash
# Launch web interface
uv run evalvault web

# Or directly
uv run evalvault-web
```

For detailed CLI usage, see the [CLI Guide](../../guides/CLI_GUIDE.md).
