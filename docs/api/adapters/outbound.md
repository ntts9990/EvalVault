# Outbound Adapters

Outbound adapters provide concrete implementations for external system integrations.

## LLM Adapters

### OpenAI Adapter

::: evalvault.adapters.outbound.llm.openai_adapter.OpenAIAdapter
    options:
      show_root_heading: true
      show_source: true

### Azure OpenAI Adapter

::: evalvault.adapters.outbound.llm.azure_adapter.AzureOpenAIAdapter
    options:
      show_root_heading: true
      show_source: true

### Anthropic Adapter

::: evalvault.adapters.outbound.llm.anthropic_adapter.AnthropicAdapter
    options:
      show_root_heading: true
      show_source: true

### Ollama Adapter

::: evalvault.adapters.outbound.llm.ollama_adapter.OllamaAdapter
    options:
      show_root_heading: true
      show_source: true

## Dataset Loaders

### CSV Loader

::: evalvault.adapters.outbound.dataset.csv_loader.CSVDatasetLoader
    options:
      show_root_heading: true
      show_source: true

### Excel Loader

::: evalvault.adapters.outbound.dataset.excel_loader.ExcelDatasetLoader
    options:
      show_root_heading: true
      show_source: true

### JSON Loader

::: evalvault.adapters.outbound.dataset.json_loader.JSONDatasetLoader
    options:
      show_root_heading: true
      show_source: true

## Storage Adapters

### SQLite Adapter

::: evalvault.adapters.outbound.storage.sqlite_adapter.SQLiteStorageAdapter
    options:
      show_root_heading: true
      show_source: true

### PostgreSQL Adapter

::: evalvault.adapters.outbound.storage.postgres_adapter.PostgreSQLStorageAdapter
    options:
      show_root_heading: true
      show_source: true

## Tracker Adapters

### Langfuse Adapter

::: evalvault.adapters.outbound.tracker.langfuse_adapter.LangfuseAdapter
    options:
      show_root_heading: true
      show_source: true

### MLflow Adapter

::: evalvault.adapters.outbound.tracker.mlflow_adapter.MLflowAdapter
    options:
      show_root_heading: true
      show_source: true

### Phoenix Adapter

::: evalvault.adapters.outbound.tracker.phoenix_adapter.PhoenixAdapter
    options:
      show_root_heading: true
      show_source: true

## Configuration Examples

### OpenAI

```python
from evalvault.adapters.outbound.llm import OpenAIAdapter

adapter = OpenAIAdapter(
    api_key="sk-...",
    model="gpt-5-nano",
    temperature=0.0
)
```

### Langfuse

```python
from evalvault.adapters.outbound.tracker import LangfuseAdapter

tracker = LangfuseAdapter(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="https://cloud.langfuse.com"
)
```

### PostgreSQL

```python
from evalvault.adapters.outbound.storage import PostgreSQLStorageAdapter

storage = PostgreSQLStorageAdapter(
    host="localhost",
    port=5432,
    database="evalvault",
    user="postgres",
    password="secret"
)
```
