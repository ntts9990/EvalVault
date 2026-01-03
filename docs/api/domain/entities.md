# Domain Entities

This module contains the core domain entities of EvalVault. These entities represent the fundamental business objects and data structures used throughout the system.

## Core Entities

### TestCase & Dataset

::: evalvault.domain.entities.dataset
    options:
      show_root_heading: false
      members:
        - TestCase
        - Dataset

### Evaluation Results

::: evalvault.domain.entities.result
    options:
      show_root_heading: false
      members:
        - MetricType
        - MetricScore
        - TestCaseResult
        - EvaluationRun

### Experiments

::: evalvault.domain.entities.experiment
    options:
      show_root_heading: false

### Knowledge Graph

::: evalvault.domain.entities.kg
    options:
      show_root_heading: false

### RAG Tracing

::: evalvault.domain.entities.rag_trace
    options:
      show_root_heading: false

### Analysis

::: evalvault.domain.entities.analysis
    options:
      show_root_heading: false
