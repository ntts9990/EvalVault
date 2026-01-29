# Outbound Ports

Outbound ports define the interfaces for interacting with external systems and infrastructure.

## LLMPort

Interface for Large Language Model providers.

::: evalvault.ports.outbound.llm_port.LLMPort
    options:
      show_root_heading: true
      show_source: true

## DatasetPort

Interface for loading and managing datasets.

::: evalvault.ports.outbound.dataset_port.DatasetPort
    options:
      show_root_heading: true
      show_source: true

## StoragePort

Interface for persistent storage operations.

::: evalvault.ports.outbound.storage_port.StoragePort
    options:
      show_root_heading: true
      show_source: true

## TrackerPort

Interface for tracking and observability systems.

::: evalvault.ports.outbound.tracker_port.TrackerPort
    options:
      show_root_heading: true
      show_source: true

## Available Adapters

### LLM Adapters

| Adapter | Status | Description |
|---------|--------|-------------|
| OpenAI | ✅ Complete | GPT-4, GPT-3.5, embeddings |
| Azure OpenAI | ✅ Complete | Azure-hosted OpenAI models |
| Anthropic | ✅ Complete | Claude models |
| Ollama | ✅ Complete | Local LLM inference |

### Storage Adapters

| Adapter | Status | Description |
|---------|--------|-------------|
| SQLite | ✅ Complete | Local file-based storage |
| PostgreSQL | ✅ Complete | Production database |

### Tracker Adapters

| Adapter | Status | Description |
|---------|--------|-------------|
| Langfuse | ✅ Complete | LLM observability platform |
| MLflow | ✅ Complete | ML experiment tracking |
| Phoenix | ✅ Complete | Arize Phoenix observability |

### Dataset Loaders

| Loader | Status | Formats |
|--------|--------|---------|
| CSV | ✅ Complete | `.csv` with auto-encoding detection |
| Excel | ✅ Complete | `.xlsx`, `.xls` |
| JSON | ✅ Complete | `.json` with validation |

## Implementation Guide

See the [Handbook Architecture chapter](../../handbook/CHAPTERS/01_architecture.md) for boundaries/ports/adapters when implementing custom adapters.
