# Phase 0 Responsibility Map

## Purpose
Establish a shared understanding of responsibilities and boundaries for refactor targets before any structural changes. This document is the baseline for behavior-preserving refactor work.

---

## Target 1: Evaluator Service
**Path**: `src/evalvault/domain/services/evaluator.py`

### Responsibilities (Current)
- Evaluation flow orchestration
- Metric selection and configuration
- Metric execution and aggregation
- Score normalization and NaN handling
- Fallback/locale handling
- Result packaging and emission

### Boundary Notes
- Domain layer only; must not depend on adapter details
- Exposed to both CLI and API paths via services/ports

### Expected Refactor Boundaries
- Orchestration vs execution vs postprocess separated
- No change to metric behaviors or scoring logic

---

## Target 2: CLI Run Command
**Path**: `src/evalvault/adapters/inbound/cli/commands/run.py`

### Responsibilities (Current)
- CLI option definitions and validation
- Dataset loading and configuration
- Orchestration of evaluation run
- Output artifact writing
- Error handling and exit code mapping
- Logging and progress output

### Boundary Notes
- Inbound adapter; should not embed domain logic
- Must preserve Typer CLI interface and help text

### Expected Refactor Boundaries
- Options parsing separated from orchestration
- IO and artifact handling separated from orchestration
- Behavior identical for arguments and outputs

---

## Target 3: Analysis Adapters
**Path**: `src/evalvault/adapters/outbound/analysis/`

### Responsibilities (Current)
- NLP/Statistical/Causal analysis modules
- Reporting and summarization modules
- Retriever logic for analysis workflows
- Registry-like structures for analysis modules
- Analysis output shaping and file output

### Boundary Notes
- Outbound adapters; implement analysis capabilities
- Must preserve registry and load order behavior

### Expected Refactor Boundaries
- Split into functional categories (core/analyzers/retrievers/reporters/comparators/search)
- Preserve registry and API for analysis usage

---

## Behavior Preservation Checklist (Phase 0)
- CLI: Options, help text, exit codes unchanged
- API: Response schemas unchanged
- Evaluator: Scores, metrics, error semantics unchanged
- Analysis: Output formats unchanged

---

## Phase 0 Exit Criteria
- Responsibility map approved
- Logging templates ready
- WBS prepared for Phase 1-3
