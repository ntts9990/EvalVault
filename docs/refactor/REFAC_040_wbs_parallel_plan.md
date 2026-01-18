# Work Breakdown Structure (WBS) and Parallel Plan

## Purpose
This WBS defines detailed tasks per track and rules for parallel execution. All tasks require logging before and after changes.

---

## Phase 0 - Baseline (Sequential)
**Goal**: establish baseline maps and safety checks.

### Tasks
1. Build responsibility map (evaluator, CLI run, analysis)
2. Identify module boundaries and dependency edges
3. Define behavior-preservation checklist
4. Prepare logging templates and log stubs

### Output
- `REFAC_030_phase0_responsibility_map.md`
- Log stub in `docs/refactor/logs/phase-0-baseline.md`

---

## Phase 1 - Evaluator Refactor (Track A)
**Owner**: Agent A

### Task A1: Responsibility Inventory
- List all functions and responsibilities in evaluator
- Group by category: orchestration, metric selection, execution, postprocess, fallbacks
- Log inventory summary

### Task A2: Target Structure Definition
- Define module layout for `domain/services/evaluation/`
- Map each function to a destination module
- Document any shared utilities

### Task A3: Safe Extraction
- Move functions to new modules incrementally
- Update imports in dependent modules
- Ensure no behavior changes or signature changes

### Task A4: Verification
- Run `ruff check src/ tests/`
- Run `pytest tests/unit -v`
- Document results

### Task A5: Post-Change Log Update
- Update `docs/refactor/logs/phase-1-evaluator.md`

---

## Phase 2 - CLI Run Refactor (Track B)
**Owner**: Agent B

### Task B1: CLI Option Map
- Enumerate all CLI options, defaults, help text
- Record error handling and exit code usage
- Log CLI option map

### Task B2: Target Structure Definition
- Define `commands/run/` module layout
- Map current sections to `cli.py`, `options.py`, `orchestrator.py`, `io.py`

### Task B3: Safe Extraction
- Move Typer option definitions to `options.py`
- Move orchestration flow to `orchestrator.py`
- Move output and artifact handling to `io.py`
- Preserve help text and option flags

### Task B4: Verification
- Run `ruff check src/ tests/`
- Run `pytest tests/unit -v`
- Document results

### Task B5: Post-Change Log Update
- Update `docs/refactor/logs/phase-2-cli-run.md`

---

## Phase 3 - Analysis Refactor (Track C)
**Owner**: Agent C

### Task C1: Analysis Module Inventory
- List analysis modules and categorize by responsibility
- Identify registry or load-order dependencies
- Log inventory and dependencies

### Task C2: Target Structure Definition
- Define category-based folder layout
- Map each module to a new location

### Task C3: Safe Moves
- Move files into new folders
- Update import paths and registry references
- Verify dynamic imports/load order

### Task C4: Verification
- Run `ruff check src/ tests/`
- Run `pytest tests/unit -v`
- Document results

### Task C5: Post-Change Log Update
- Update `docs/refactor/logs/phase-3-analysis.md`

---

## Parallel Execution Rules
- Track A (Evaluator) and Track B (CLI) can run in parallel after Phase 0.
- Track C (Analysis) should start after either A or B stabilizes to reduce conflicts.
- If a shared utility or registry is modified, serialize the dependent tasks.

---

## Logging Requirement
Each task step requires:
- Pre-change log entry
- Post-change update with files and verification
- Explicit "behavior unchanged" confirmation
