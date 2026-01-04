# Configuration

Pydantic Settings 기반의 환경 변수 설정 레퍼런스입니다.

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
# Profile / Provider (Optional)
EVALVAULT_PROFILE=dev
LLM_PROVIDER=openai
TRACKER_PROVIDER=langfuse

# OpenAI Configuration (Required when provider=openai)
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
PHOENIX_ENDPOINT=http://localhost:6006/v1/traces
PHOENIX_SAMPLE_RATE=1.0

# PostgreSQL Configuration (Optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=evalvault
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret
# POSTGRES_CONNECTION_STRING=postgresql://user:pass@localhost:5432/evalvault

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
print(settings.phoenix_enabled)
print(settings.tracker_provider)
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
