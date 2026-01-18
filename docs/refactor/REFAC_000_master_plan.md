# Refactoring Master Plan (Structure-Only)

## Problem 1-Pager: EvalVault Structure Refactor

### Background
EvalVault has grown quickly with a stable hexagonal architecture, but key modules have accumulated excessive complexity and size, notably in CLI run command, evaluator service, and analysis adapters. These modules now mix responsibilities, complicating maintenance and safe changes.

### Problem
- Core entry points are oversized and multi-responsibility, increasing risk of unintended changes.
- CLI and API rely on shared behaviors but are difficult to reason about due to monolithic command/router modules.
- Analysis adapters lack clear boundaries, causing ambiguity when adding or extending features.

### Goal
- Clarify responsibilities and boundaries without changing runtime behavior.
- Reduce module size and improve readability and testability.
- Preserve hexagonal architecture boundaries (Adapters -> Ports -> Domain).

### Non-goals
- No behavior change (CLI, API, output format, error semantics).
- No performance optimizations.
- No UI/UX changes.
- No external integration changes.

### Constraints
- Keep Ruff and type hints compliant.
- Maintain existing tests and avoid introducing breaking changes.
- Refactor by small, verifiable steps.

---

## Official Policy: Structure-Only Refactor
- No behavior change unless explicitly documented and approved.
- Any potential behavior change must be logged before implementation.
- Small PRs preferred, each scoped to a single refactor unit.

---

## Scope (Phase 1 Target)
1. `src/evalvault/domain/services/evaluator.py`
2. `src/evalvault/adapters/inbound/cli/commands/run.py`
3. `src/evalvault/adapters/outbound/analysis/`

---

## Sequence and Rationale
**Order: evaluator -> CLI -> analysis**
- Evaluator is the core domain logic used by both CLI and API.
- Stabilizing domain responsibilities first lowers risk when restructuring CLI and analysis.
- Analysis is largest and most interdependent; moving it last avoids churn.

---

## Phase Plan

### Phase 0 - Baseline and Safety
**Objective**: Establish guardrails and documentation before structural changes.
- Document current responsibilities for each target module.
- Identify call flow and dependencies (CLI -> Service -> Ports -> Adapters).
- Define behavior preservation checklist and required test runs.

**Exit Criteria**
- Responsibility maps complete for all three targets.
- Behavior preservation checklist defined.
- Logging template adopted.

---

### Phase 1 - Evaluator Refactor
**Objective**: Split evaluator responsibilities without changing behavior.

**Proposed Structure**
```
src/evalvault/domain/services/evaluation/
  __init__.py
  orchestrator.py
  metric_registry.py
  executors/
  postprocess.py
  fallbacks.py
```

**Refactor Actions**
- Extract orchestration flow to `orchestrator.py`.
- Move metric selection/registry logic to `metric_registry.py`.
- Separate scoring normalization and NaN handling to `postprocess.py`.
- Separate locale/language fallback logic to `fallbacks.py`.

**Exit Criteria**
- Behavior unchanged (scores, errors, logs, outputs).
- All imports updated and type hints preserved.
- Tests pass.

---

### Phase 2 - CLI Run Refactor
**Objective**: Split run command into parsing, orchestration, and IO.

**Proposed Structure**
```
src/evalvault/adapters/inbound/cli/commands/run/
  __init__.py
  cli.py
  orchestrator.py
  executors/
  options.py
  io.py
```

**Refactor Actions**
- Move option definitions and validation into `options.py`.
- Move execution flow into `orchestrator.py`.
- Move output and artifact handling into `io.py`.

**Exit Criteria**
- CLI help text and options unchanged.
- Exit codes and error handling unchanged.
- Same output structure for files and console.

---

### Phase 3 - Analysis Adapter Refactor
**Objective**: Organize analysis adapters into functional categories.

**Proposed Structure**
```
src/evalvault/adapters/outbound/analysis/
  core/
  analyzers/
  retrievers/
  reporters/
  comparators/
  search/
```

**Refactor Actions**
- Classify modules by function and move accordingly.
- Update imports and registry references.
- Ensure any load-order assumptions are preserved.

**Exit Criteria**
- Same analysis outputs and API behavior.
- Registry or dynamic import behavior preserved.

---

## Parallel Work Strategy
- Phase 0 runs sequentially to build shared context.
- Phase 1 and Phase 2 can run in parallel after Phase 0 completes.
- Phase 3 begins after Phase 1 or Phase 2 is stable to reduce churn.

---

## Verification Plan
- Run `ruff check src/ tests/` after each phase.
- Run `pytest tests/unit -v` after each phase.
- If any behavior change is observed, halt and document.

---

## Logging Requirement
Every refactor step must be logged in `docs/refactor/logs/` using standard template.
