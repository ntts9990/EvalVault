# Configuration

Configuration management using pydantic-settings for type-safe environment variable handling.

## Settings

Main application settings loaded from environment variables.

::: evalvault.config.settings.Settings
    options:
      show_root_heading: true
      show_source: true

## Model Configuration

Configuration for LLM model parameters.

::: evalvault.config.model_config.ModelConfig
    options:
      show_root_heading: true
      show_source: true

## Playbooks

Pre-configured settings for common use cases defined in YAML files.

See `src/evalvault/config/playbooks/` for available playbook configurations.

## Environment Variables

Create a `.env` file in your project root:

```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
# OPENAI_BASE_URL=https://api.openai.com/v1  # Optional

# Langfuse Configuration (Optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Phoenix Configuration (Optional)
PHOENIX_ENABLED=true
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006

# Database Configuration (Optional)
DATABASE_URL=sqlite:///./evalvault.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/evalvault

# MLflow Configuration (Optional)
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=evalvault-experiments
```

## Configuration Loading

```python
from evalvault.config import Settings

# Load from environment variables
settings = Settings()

# Access configuration
print(settings.openai_api_key)
print(settings.openai_model)
print(settings.langfuse_enabled)
```

## Playbook Usage

Playbooks can be specified via CLI:

```bash
# Use simple playbook (fast, basic metrics)
uv run evalvault run data.csv --mode simple

# Use full playbook (comprehensive evaluation)
uv run evalvault run data.csv --mode full
```

## Configuration Validation

All configuration is validated at startup using Pydantic:

- Type checking
- Required field validation
- Range validation for numeric values
- URL format validation

Invalid configuration will raise a clear error message at startup.
