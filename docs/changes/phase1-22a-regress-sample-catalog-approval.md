# Approval: Phase 1-22A Regress Sample Catalog

- Work ID: phase1-22a-regress-sample-catalog
- Target File/Schema: `evalvault.regress-sample-catalog.v1`
- Approval Evidence: user-authorized Phase 1-22A direct repo-local work in this session, constrained by EvalVault AGENTS shared-schema workflow.
- Scope Approved:
  - Additive `evalvault regress-sample --list --format json` catalog output.
  - Forecast-only `data.evidence_diagnostics` metadata needed for platform catalog parity.
  - No change to the default quality `evalvault regress-sample` envelope.
  - No `promote`, `hold`, or `rollback` vocabulary in EvalVault-owned identifiers or output.
  - T2 status set remains `passed|failed` for this phase.
- Required Verification:
  - Focused regress sample tests pass.
  - Ruff passes on touched CLI/domain/tests.
  - Repeated catalog generation is deterministic.

This approval is limited to Phase 1-22A catalog listing. It does not approve future `inconclusive` emission or any release-decision vocabulary in EvalVault.
