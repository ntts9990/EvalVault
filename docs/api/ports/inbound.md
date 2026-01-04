# Inbound Ports

Inbound ports define the interfaces through which external actors (users, systems) interact with the application.

## EvaluatorPort

Primary interface for running evaluations.

::: evalvault.ports.inbound.evaluator_port.EvaluatorPort
    options:
      show_root_heading: true
      show_source: true

## AnalysisPipelinePort

Interface for building and executing analysis pipelines.

::: evalvault.ports.inbound.analysis_pipeline_port.AnalysisPipelinePort
    options:
      show_root_heading: true
      show_source: true

## DomainLearningHookPort

Interface for forming domain memories after evaluation.

::: evalvault.ports.inbound.learning_hook_port.DomainLearningHookPort
    options:
      show_root_heading: true
      show_source: true

## WebUIPort

Interface for web UI-driven evaluation and reporting.

::: evalvault.ports.inbound.web_port.WebUIPort
    options:
      show_root_heading: true
      show_source: true

## Hexagonal Architecture

These ports follow the **Hexagonal Architecture** (Ports & Adapters) pattern:

```
┌─────────────────────────────────────┐
│      Inbound Adapters               │
│   (CLI, Web UI, API)                │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────┐
        │   Inbound   │
        │    Ports    │ ◄── You are here
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │   Domain    │
        │   Services  │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │  Outbound   │
        │    Ports    │
        └──────┬──────┘
               │
┌──────────────▼──────────────────────┐
│     Outbound Adapters               │
│  (LLM, Storage, Tracker)            │
└─────────────────────────────────────┘
```

### Benefits

- **Testability**: Easy to mock ports for unit testing
- **Flexibility**: Swap implementations without changing domain logic
- **Isolation**: Domain logic independent of external dependencies
