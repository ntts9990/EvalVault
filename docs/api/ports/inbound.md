# Inbound Ports

Inbound ports define the interfaces through which external actors (users, systems) interact with the application.

## EvaluatorPort

Primary interface for running evaluations.

::: evalvault.ports.inbound.evaluator_port.EvaluatorPort
    options:
      show_root_heading: true
      show_source: true

## GeneratorPort

Interface for test case and knowledge graph generation.

::: evalvault.ports.inbound.generator_port.GeneratorPort
    options:
      show_root_heading: true
      show_source: true

## AnalyzerPort

Interface for query analysis operations.

::: evalvault.ports.inbound.analyzer_port.AnalyzerPort
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
