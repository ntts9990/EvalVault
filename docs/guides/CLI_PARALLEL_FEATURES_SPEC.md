# CLI Parallel Features Spec (Draft)

> Audience: CLI/Platform contributors
> Purpose: Future CLI features aligned with SOLID, BDD, hexagonal & clean architecture
> Last Updated: 2026-01-18

## 1. Overview

This document specifies new CLI features that are parallel-by-default, deterministic, and cleanly separated by ports/adapters. The scope is design-level documentation with stable JSON outputs and BDD scenarios.

Design goals:
- SOLID: each command = one use-case orchestrator; dependencies injected via ports
- Clean/Hexagonal: CLI is an inbound adapter; domain services depend on outbound ports only
- Parallel execution: bounded concurrency with deterministic aggregation
- BDD: user-visible behavior is defined via Gherkin scenarios

Collaboration rules (conflict avoidance):
- Each stream modifies different files only.
- Shared schemas or interfaces change only after explicit agreement.
- Documentation edits are assigned to a single owner to avoid merge conflicts.

## 1.1 Parallel Agent Implementation Plan (Execution)

Scope:
- Implement all commands below in parallel (CLI + domain services + ports + adapters).
- Each command is owned by exactly one agent end-to-end.

Ownership:
- Agent Compare: `evalvault compare`
- Agent Calibrate: `evalvault calibrate-judge`
- Agent Difficulty: `evalvault profile-difficulty`
- Agent Regress: `evalvault regress`
- Agent Artifacts: `evalvault artifacts lint`
- Agent Ops: `evalvault ops snapshot`

File boundaries (default):
- CLI command module for the command
- Domain service (one use-case service per command)
- Outbound port interfaces needed by that service
- Outbound adapters for storage/reporting/FS as needed
- Tests for the command/service

Shared files (change only with explicit agreement):
- `adapters/inbound/cli/app.py`
- `adapters/inbound/cli/commands/__init__.py`
- Common JSON envelope schema or report templates
- `domain/services/async_batch_executor.py`

Definition of done (per agent):
- CLI command registered and functional with `--help` and a basic run path
- Domain service + ports/adapters implemented for the use-case
- Tests added for core logic and CLI wiring
- Tests and lint pass with the standard project commands

Test commands (standard project flow):
- `uv run ruff check src/ tests/`
- `uv run ruff format src/ tests/`
- `uv run pytest tests -v`

## 2. Command Specs

### 2.1 `evalvault compare`

Purpose:
- Compare two runs (metrics, prompts/config diffs, difficulty distribution) and output a unified report.

Synopsis:
```
uv run evalvault compare RUN_A RUN_B \
  --db data/db/evalvault.db \
  --metrics faithfulness,answer_relevancy \
  --test t-test \
  --format table \
  --output reports/comparison/comparison_RUNA_RUNB.json \
  --report reports/comparison/comparison_RUNA_RUNB.md \
  --output-dir reports/comparison \
  --artifacts-dir reports/comparison/artifacts/comparison_RUNA_RUNB \
  --parallel --concurrency 8
```

Options:
- `--db, -D <path>`: sqlite db path
- `--metrics, -m <csv>`: allowlist of metrics
- `--test, -t <t-test|mann-whitney>`
- `--format, -f <table|json>`
- `--output, -o <path>`
- `--report <path>`
- `--output-dir <path>`
- `--artifacts-dir <path>`
- `--parallel/--no-parallel`, `--concurrency <int>`

Exit codes:
- `0`: success
- `1`: invalid args or missing run
- `2`: report generation degraded

### 2.2 `evalvault calibrate-judge`

Purpose:
- Calibrate judge scores and emit reliability summary.

Synopsis:
```
uv run evalvault calibrate-judge RUN_ID \
  --db data/db/evalvault.db \
  --labels-source feedback \
  --method isotonic \
  --metric faithfulness \
  --holdout-ratio 0.2 \
  --seed 42 \
  --write-back \
  --output reports/calibration/judge_calibration_RUNID.json \
  --parallel --concurrency 8
```

Options:
- `--labels-source <feedback|gold|hybrid>`
- `--method <platt|isotonic|temperature|none>`
- `--metric <name>` (repeatable)
- `--holdout-ratio <float>`
- `--seed <int>`
- `--write-back`
- `--output, -o <path>`
- `--artifacts-dir <path>`
- `--parallel/--no-parallel`, `--concurrency <int>`

Exit codes:
- `0`: success
- `1`: labels missing / invalid args
- `2`: calibration quality below gate

### 2.3 `evalvault profile-difficulty`

Purpose:
- Compute difficulty buckets for a dataset or a run.

Synopsis:
```
uv run evalvault profile-difficulty \
  --db data/db/evalvault.db \
  --dataset-name insurance-qa \
  --limit-runs 50 \
  --metrics faithfulness,answer_relevancy \
  --bucket-count 5 \
  --output reports/difficulty/difficulty_insurance-qa.json \
  --parallel --concurrency 8
```

Options:
- `--dataset-name <string>` or `--run-id <id>`
- `--limit-runs <int>`
- `--metrics, -m <csv>`
- `--bucket-count <int>`
- `--min-samples <int>`
- `--output, -o <path>`
- `--artifacts-dir <path>`
- `--parallel/--no-parallel`, `--concurrency <int>`

Exit codes:
- `0`: success
- `1`: insufficient history or invalid args

### 2.4 `evalvault regress`

Purpose:
- CI-grade regression gate vs baseline run.

Synopsis:
```
uv run evalvault regress RUN_CANDIDATE \
  --db data/db/evalvault.db \
  --baseline RUN_BASELINE \
  --fail-on-regression 0.05 \
  --test t-test \
  --metrics faithfulness,answer_relevancy \
  --format github-actions \
  --output reports/regress/regress_RUNCAND.json \
  --parallel --concurrency 8
```

Exit codes:
- `0`: pass
- `1`: invalid input
- `2`: regression detected
- `3`: internal error

### 2.5 `evalvault artifacts lint`

Purpose:
- Validate required artifacts and schema invariants.

Synopsis:
```
uv run evalvault artifacts lint ARTIFACT_DIR \
  --strict \
  --format json \
  --output reports/artifacts_lint/lint_RUNID.json \
  --parallel --concurrency 16
```

Checks:
- `index.json` presence
- required paths exist
- JSON schema validation

### 2.6 `evalvault ops snapshot`

Purpose:
- Collect reproducibility metadata (profile, model config, env redactions).

Synopsis:
```
uv run evalvault ops snapshot \
  --profile dev \
  --db data/db/evalvault.db \
  --run-id RUN_ID \
  --include-model-config \
  --include-env \
  --redact OPENAI_API_KEY \
  --output reports/ops/snapshot_RUNID.json
```

## 3. Architecture Alignment

### 3.1 SOLID
- SRP: each command orchestrates a single use-case service
- OCP: add new commands via new registrars without modifying core command modules
- DIP: domain services depend on ports (StoragePort, ReportPort, FileSystemPort)

### 3.2 Hexagonal/Clean
- Inbound adapter: `adapters/inbound/cli/commands/*`
- Domain services: `domain/services/*` for use-cases
- Outbound ports: `ports/outbound/*`
- Outbound adapters: sqlite storage, report writers, LLM providers

### 3.3 Proposed Services (Draft)
- `RunComparisonService`
- `JudgeCalibrationService`
- `DifficultyProfilingService`
- `RegressionGateService`
- `ArtifactLintService`
- `OpsSnapshotService`

## 4. Parallel Execution Model

- Use bounded concurrency (`--concurrency`) and deterministic aggregation.
- Candidate base utility: `domain/services/async_batch_executor.py`.
- Parallelize per-metric/per-case computations; merge results with stable sorting.
- LLM calls default to sequential unless explicitly enabled.

## 5. JSON Output Envelope

Common envelope (recommended):
```
{
  "command": "compare",
  "version": 1,
  "status": "ok",
  "started_at": "2026-01-18T00:00:00Z",
  "finished_at": "2026-01-18T00:00:05Z",
  "duration_ms": 5000,
  "artifacts": {
    "dir": "reports/.../artifacts/...",
    "index": "reports/.../artifacts/.../index.json"
  },
  "data": {}
}
```

## 6. BDD Scenarios (Gherkin)

### compare
```
Feature: Compare two evaluation runs
  Scenario: Compare two runs with shared metrics
    Given a database with runs "run_a" and "run_b"
    When I run "evalvault compare run_a run_b --format json"
    Then the command exits with code 0
    And the JSON output contains "run_ids" ["run_a", "run_b"]
```

### calibrate-judge
```
Feature: Calibrate judge scoring
  Scenario: Calibrate judge scores using feedback labels
    Given a run "run_x" with feedback labels in storage
    When I run "evalvault calibrate-judge run_x --labels-source feedback"
    Then the command exits with code 0
```

### regress
```
Feature: Regression gate for CI
  Scenario: Regression detected
    Given a candidate run "run_new" and baseline "run_base"
    When I run "evalvault regress run_new --baseline run_base"
    Then the command exits with code 2
```

## 7. Non-goals
- No distributed execution or multi-node scheduling
- No new scoring algorithms; only orchestration and reporting
- No breaking change to existing CLI

## 8. Risks
- Provider rate limits with parallel LLM calls
- DB contention under high concurrency
- Schema drift in artifacts without linting

## 9. Mapping to Existing Modules (Evidence)
- CLI app: `adapters/inbound/cli/app.py`
- Command registration: `adapters/inbound/cli/commands/__init__.py`
- Existing compare pipeline: `adapters/inbound/cli/commands/analyze.py`
- Artifact utilities: `adapters/inbound/cli/utils/analysis_io.py`
- Async batch executor: `domain/services/async_batch_executor.py`
