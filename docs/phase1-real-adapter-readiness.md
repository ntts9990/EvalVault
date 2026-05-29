# Phase 1 Real Adapter Readiness

Status: **PARTIAL / BLOCKED**

This note records the narrow readiness finding for replacing a Phase 0 thin
EvalVault adapter with a real adapter. It intentionally does not claim
multi-user readiness: project isolation is not enforced today.

## What Is Scoped Today

- API network exposure has a fail-closed guard for non-loopback binds without
  `API_AUTH_TOKENS`.
- Most API file inputs are path-confined to allowed local roots; dataset upload,
  retriever-doc upload, and knowledge upload reject path traversal filenames.
- Knowledge endpoints can require shared read/write bearer tokens via
  `KNOWLEDGE_READ_TOKENS` and `KNOWLEDGE_WRITE_TOKENS`.
- `RegressionGateReport` output is T2-only: `evalvault regress --format json`
  emits `passed` / `failed` / error envelope states, not T3 release decisions.
- The `regress --format json` error envelope carries a **stable machine-readable
  taxonomy**: `error_code` (UPPER_SNAKE — `EVAL_INCOMPLETE_PROVENANCE`,
  `EVAL_RUN_NOT_FOUND`, `EVAL_INVALID_INPUT`, `EVAL_INTERNAL_ERROR`) plus
  `error_category` (`provenance` / `input` / `internal`). The legacy
  `error_type` (Python class name) is retained for backward compatibility but is
  no longer the contract — adapters switch on `error_code`.
- Numeric report fields (`baseline_score`, `candidate_score`, `diff`,
  `diff_percent`, `p_value`, `effect_size`) are **canonicalized** with
  6-decimal rounding (`-0.0` normalized), so the JSON serialization is
  deterministic across platforms and stable to hash. Verdict computation is
  unchanged.

## What Is Not Project-Isolated

- Auth foundation exists as domain entities (`User`, `Project`, `Membership`,
  `Role`) and token services, but FastAPI routes do not resolve a current user,
  project membership, or project-scoped role.
- Run start accepts `project_name`, but it is stored as metadata only. There is
  no `project_id` on `evaluation_runs`, no storage-level project filter, and no
  membership check.
- Run list/get/query surfaces are keyed by raw `run_id` or global filters:
  `/api/v1/runs/`, `/api/v1/runs/{run_id}`, compare, visual-space, prompt diff,
  stage events/metrics, quality gate, debug/analysis/dashboard/report, feedback,
  and cluster-map endpoints are not scoped by authenticated project membership.
- Dataset upload/read is global: files are saved under `data/datasets`, and
  listing reads `data/datasets`, `data/inputs`, and the repository root.
- Retriever-doc upload/read is global: files are saved under
  `data/retriever_docs`, and evaluation can read any allowed-root docs path.
- Knowledge upload/read is global: uploads go to `data/raw`, graph output goes
  to `data/kg`, and in-memory `KG_JOBS` is shared process state. Shared
  read/write tokens are not project membership.
- SQLite/Postgres schemas and `StoragePort` do not expose `project_id` as a
  first-class isolation key.

## Stable Output Seam

The stable candidate seam for solution-platform integration is:

```bash
uv run evalvault regress <candidate_run_id> \
  --baseline <baseline_run_id> \
  --format json \
  --output <path> \
  --db <db_path>
```

The JSON envelope has `command: "regress"`, `version: 1`, `status`, runtime
timestamps, and `data` containing the `RegressionGateReport` fields documented
in `docs/adapter-contract.md`. On the error/abstain path (`status: "error"`,
`data: null`) the envelope additionally carries `message`, `error_type` (legacy,
compat-only), and the stable `error_code` / `error_category`.

Contract fixtures and executable examples live in:

- `tests/fixtures/e2e/regression_gate/`
- `tests/unit/test_regression_gate_fixtures.py`

## Blockers Before Real Adapter Replacement

1. **Project isolation blocker:** every run/dataset/retriever/knowledge route
   that can read or mutate tenant data needs authenticated `project_id`
   resolution, membership enforcement, and storage-level filtering.
2. **Role gate blocker:** route-level viewer/editor/admin checks are not wired
   to `Membership.role`; only shared API or knowledge tokens are enforced.
3. **Evidence hash blocker (partially addressed):** numeric serialization is now
   canonical/deterministic (see above), which removes the cross-platform
   float-noise obstacle to hashing the report. Two gaps remain: (a)
   `RegressionGateReport` still does not emit the Phase 1 evidence/source hash
   fields expected by downstream reference integrity (`content_hash`,
   `source_hash`, or `evidence_refs`), and (b) `p_value` / `effect_size` are
   scipy-derived, so byte-for-byte reproducibility across **scipy versions** also
   requires version pinning, not just serialization canonicalization. The seam is
   stable and hash-anchorable for the deterministic arithmetic fields
   (scores/diffs); the statistical fields are stable in representation but need
   scipy pinning for cross-version hash equality.

Readiness remains **PARTIAL** for local/offline single-tenant regression-gate
consumption and **BLOCKED** for multi-user project-scoped replacement.
