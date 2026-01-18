# Logging Policy and Templates

## Purpose
All refactor work must be logged to ensure traceability, safety, and clear audit history. Logs are mandatory and must be updated before and after each refactor task.

---

## Logging Rules
- Log entry required before any structural change.
- Log entry must be updated after changes are completed.
- Include file lists, module moves, and verification steps.
- Explicitly confirm "behavior unchanged".

---

## Log File Naming
- `docs/refactor/logs/phase-1-evaluator.md`
- `docs/refactor/logs/phase-2-cli-run.md`
- `docs/refactor/logs/phase-3-analysis.md`
- `docs/refactor/logs/phase-0-baseline.md`

---

## Standard Log Template
```markdown
# Refactor Log: <phase>

## Pre-Change Snapshot
- Date:
- Owner:
- Scope:
- Files:
- Risks:

## Planned Changes
- Responsibility split:
- New modules:
- Dependency updates:

## Post-Change Summary
- Changes applied:
- Behavior change: No
- Updated imports:

## Verification
- ruff check:
- pytest tests/unit -v:
- Additional checks:

## Notes
- Follow-ups:
```

---

## Behavior-Change Guardrail
If any behavior change is detected or suspected, update the log with:
- Description of change
- Impacted commands or API endpoints
- Mitigation or rollback plan
- Request for explicit approval
