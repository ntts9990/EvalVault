# Change Request: Phase 1-22A Regress Sample Catalog

- Work ID: phase1-22a-regress-sample-catalog
- Owner: EvalVault repo-local agent
- Target File/Schema: `evalvault regress-sample --list --format json`, `evalvault.regress-sample-catalog.v1`
- Reason: solution-platform needs an EvalVault-owned machine-readable list/hash surface for deterministic regress samples instead of treating catalog parity as a known migration gap. Forecast scenarios also need source-owned diagnostic fields so the platform can prove the catalog covers its required forecast diagnostics.
- Impacted Epics: Phase 1 real adapter demo readiness, source-owned forecast evidence catalog.
- Validation Plan:
  - `uv run pytest tests/unit/test_regress_sample.py tests/unit/test_readiness_proof_service.py -q`
  - `uv run ruff check src/evalvault/adapters/inbound/cli/commands/regress.py src/evalvault/domain/services/regress_sample.py tests/unit/test_regress_sample.py tests/unit/test_readiness_proof_service.py`
  - `uv run evalvault regress-sample --list --format json`
  - repeated catalog generation must be byte-stable.
- Rollback Plan: remove the `--list` branch, catalog helper, and catalog tests; existing scenario generation remains unchanged.

## Approval Request

This change adds an additive CLI JSON surface and adds forecast-only `data.evidence_diagnostics` metadata to the existing forecast samples. The default quality sample stays unchanged, no T3 release vocabulary is added, and Phase 1-22A allowed T2 statuses remain `passed|failed`.
