# Agent Work Playbook (Parallel Execution)

## Overview
This document defines the agent responsibilities, checklists, and logging requirements for the structure-only refactor. All agents must document work in logs under `docs/refactor/logs/` before and after changes.

---

## General Rules
- No behavior change; structure-only refactor.
- Log before starting and after finishing each task.
- Keep changes scoped to assigned module/phase.
- Update imports, references, and registries as needed.

---

## Agent Roles

### Agent A: Evaluator Refactor
**Scope**: `src/evalvault/domain/services/evaluator.py`

**Checklist**
- [ ] Inventory evaluator responsibilities (orchestration, metric selection, execution, post-processing, fallbacks)
- [ ] Draft new file layout under `domain/services/evaluation/`
- [ ] Move functions by responsibility into new modules
- [ ] Update import paths and references
- [ ] Verify no behavior change with smoke checks
- [ ] Log changes and decisions

**Deliverables**
- New module layout and updated imports
- Updated log entry
- Confirmation that behavior is unchanged

**Required Logs**
- `docs/refactor/logs/phase-1-evaluator.md`

---

### Agent B: CLI Run Refactor
**Scope**: `src/evalvault/adapters/inbound/cli/commands/run.py`

**Checklist**
- [ ] Map CLI options and default behaviors
- [ ] Draft `run/` module layout
- [ ] Move option definitions to `options.py`
- [ ] Move execution flow to `orchestrator.py`
- [ ] Move output and artifact logic to `io.py`
- [ ] Preserve help text, exit codes, error messages
- [ ] Log changes and decisions

**Deliverables**
- New run module layout
- Updated `commands/__init__.py` references
- Updated log entry

**Required Logs**
- `docs/refactor/logs/phase-2-cli-run.md`

---

### Agent C: Analysis Refactor
**Scope**: `src/evalvault/adapters/outbound/analysis/`

**Checklist**
- [ ] Inventory analysis modules and responsibilities
- [ ] Classify modules into categories (core, analyzers, retrievers, reporters, comparators, search)
- [ ] Move files into new structure
- [ ] Update registry/import paths
- [ ] Validate any load-order assumptions
- [ ] Log changes and decisions

**Deliverables**
- New analysis folder structure
- Updated registry and imports
- Updated log entry

**Required Logs**
- `docs/refactor/logs/phase-3-analysis.md`

---

## Logging Rules
Each agent must write a log before and after changes using the template in `REFAC_020_logging_policy.md`.
