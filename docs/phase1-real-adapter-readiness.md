# Phase 1 Real Adapter Readiness

Status: **PARTIAL / BLOCKED**

This note records the narrow readiness finding for replacing a Phase 0 thin
EvalVault adapter with a real adapter. It intentionally does not claim full
production multi-user readiness yet: the SQLite-backed project isolation path is
now exercised across the live HTTP and MCP surfaces, but Postgres identity
storage parity and downstream evidence-hash fields are still open.

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
  `Role`) and token services. Live run routes now resolve a current user,
  project membership, and project-scoped role; file-backed HTTP tenant surfaces
  now use the same denial policy when a project context is supplied.
- (RESOLVED this pass for run routes) Run routes now resolve a principal +
  current project and enforce project scope when a project context is supplied —
  see "Live Run-Route Wiring" below. Without a project context, legacy/default
  behavior is preserved.
- (RESOLVED this pass for dataset upload/list/read + retriever-doc upload/read) These now
  isolate into project-owned subdirectories when a project context is supplied —
  see "Non-Run Surface Isolation" below. No project context keeps the legacy
  global behavior.
- (RESOLVED this pass for knowledge upload/list/build/jobs/stats) These now
  isolate into `data/raw/<project_id>` and `data/kg/<project_id>`, and `KG_JOBS`
  entries carry `project_id` so project-scoped job/status reads cannot reveal
  another project's jobs — see "Knowledge Surface Isolation" below. No project
  context keeps the legacy global dirs + shared `KNOWLEDGE_*_TOKENS` behavior.
- (RESOLVED this pass for MCP run tools) The MCP JSON-RPC endpoint now accepts a
  real identity principal (session JWT or per-user API key) from the HTTP bearer
  token and passes that principal into all run tools. Project-scoped MCP calls
  enforce membership/role and storage filtering; shared MCP/API service tokens
  keep only the legacy no-project behavior — see "MCP Surface Isolation" below.
- Run storage now has a first-class `project_id` isolation key. The remaining
  gap for auth/backend parity is a Postgres `IdentityStoragePort` adapter, not
  run storage, HTTP file-backed surfaces, or MCP run tools.

## G4 Project Isolation — Landed This Pass (storage-enforced foundation)

Implemented as a coherent, test-backed vertical slice honoring Principle 2
(storage-enforced isolation, not route-only checks):

- **`project_id` on `evaluation_runs`** (SQLite + Postgres; additive ALTER
  migration; legacy rows backfilled to the deterministic default project).
  `StoragePort` exposes it as a first-class isolation key: `get_run(run_id,
  project_id=...)` refuses cross-project reads (raises `KeyError`, no existence
  leak) and `list_runs(..., project_id=...)` is storage-filtered. Unscoped saves
  normalize to `DEFAULT_PROJECT_ID`.
- **Identity storage** (`IdentityStoragePort` + `SqliteIdentityStorageAdapter`):
  users, projects, memberships, API keys, refresh tokens; idempotent admin
  bootstrap (`bootstrap_admin`, env `EVALVAULT_ADMIN_EMAIL` / `_PASSWORD`).
- **Authorization** (`domain/services/authorization.py`): `Principal` + role
  ordering (admin > editor > viewer); membership/role resolution.
- **API principal primitives** (`adapters/inbound/api/principal.py`): resolve a
  principal from a session access JWT or per-user API key; current-project
  precedence (`X-Project-Id` header → `project_id` query → body); denial policy.

### Denial policy (authored for G4)
- Unresolvable principal where auth is required → **401**.
- Authenticated **non-member** of the target project → **404** (do not leak the
  existence of foreign projects/runs).
- Member with **insufficient role** for a write → **403**.

Proof: `tests/integration/test_run_project_isolation.py` (end-to-end: real
identity + run storage + JWT + authz), `tests/unit/test_storage_project_isolation.py`,
`tests/unit/test_identity_storage.py`, `tests/unit/test_authorization.py`.

## Live Run-Route Wiring — Landed This Pass

The principal/denial primitives are now wired into the live FastAPI **run**
routes (`/api/v1/runs`):

- `get_principal` resolves a `Principal` from the bearer token (session JWT or
  per-user API key) via injected/lazily-built identity store + token service +
  hasher. `get_current_project_id` resolves the project with precedence
  `X-Project-Id` header → `project_id` query (request-body `project_id` for
  `start`). Both live in `adapters/inbound/api/main.py`.
- A router-level guard (`runs.enforce_run_path_access`) enforces, for any
  `{run_id}` route when a project context is supplied: membership (else 401/404)
  and storage-scoped existence via `adapter.get_run_details(run_id,
  project_id=...)` → `BaseSQLStorageAdapter.get_run(project_id=...)` (foreign /
  unknown run → 404, no existence leak). This covers get, feedback read,
  stage-events/metrics, quality-gate, debug/dashboard/report/improvement/
  analysis, and cluster-map reads with no per-handler code.
- Non-`{run_id}` and write routes are wired in-handler: `GET /runs/` lists only
  the member project via `adapter.list_runs(..., project_id=...)`; `compare` and
  `prompt-diff` validate BOTH runs; `visual-space` validates the optional
  `base_run_id`; **writes** (`start`, feedback save, cluster-map save/delete)
  require the **editor** role; `start` persists the resolved `project_id` onto
  the new `EvaluationRun`.
- The denial policy maps to HTTP via app exception handlers
  (`PrincipalRequiredError`→401, `ProjectAccessDeniedError`→404,
  `InsufficientRoleError`→403).
- **Backward compatible:** with no project context, routes behave exactly as
  before; the shared `API_AUTH_TOKENS` service token alone confers no project
  membership (a project-scoped request requires a real identity principal).

Proof: `tests/integration/test_run_route_isolation.py` (live TestClient over a
real adapter + real SQLite run storage + real identity + JWT): list scoping,
foreign-run 404, missing-principal 401, non-member 404, viewer-write 403, and
legacy no-project pass-through. Existing `tests/integration/test_pipeline_api_contracts.py`
remains green (no regression).

## Non-Run Surface Isolation — Landed This Pass (Block 1)

Dataset and retriever-doc HTTP surfaces are now project-scoped using
**project-owned subdirectories**, the smallest pattern consistent with the
file-backed storage:

- `GET /options/datasets`: with a project context the caller must be a member;
  listing is scoped to `data/datasets/<project_id>/` (only that project's
  datasets). No project context keeps the legacy global listing.
- `POST /options/datasets`: with a project context the caller must be an
  **editor**; the file is stored under `data/datasets/<project_id>/`.
- `POST /options/retriever-docs`: with a project context the caller must be an
  **editor**; the file is stored under `data/retriever_docs/<project_id>/`.
- `POST /start`: with a project context the supplied `dataset_path` must resolve
  inside `data/datasets/<project_id>/`, and `retriever_config.docs_path` must
  resolve inside `data/retriever_docs/<project_id>/`.
- The `project_id` directory segment is guarded by `safe_upload_filename`, and
  the existing per-file `safe_upload_filename` traversal guard is unchanged — a
  crafted filename (e.g. `../evil.json`) is still rejected with 400 even under a
  project context.
- Denial policy is identical to the run routes (401 / 404-non-member /
  403-insufficient-role), and legacy `API_AUTH_TOKENS` alone confers no
  membership.

Proof: `tests/integration/test_dataset_route_isolation.py` (live TestClient,
real adapter + identity + JWT): cross-project list isolation, non-member 404,
missing-principal 401, viewer-upload 403, path-traversal-still-400, legacy
pass-through, dataset read containment, retriever-doc read containment, and
retriever-doc editor/viewer/no-principal cases.

## Knowledge Surface Isolation — Landed This Pass (Phase 1-2C)

The knowledge endpoints (`/api/v1/knowledge/*`) are now project-scoped while
preserving the legacy shared-token path:

- `POST /upload` (write→**editor**), `GET /files` (read→**member**),
  `POST /build` (write→**editor**), `GET /jobs/{job_id}` (read→**member**),
  `GET /stats` (read→**member**).
- In **project mode** (`X-Project-Id` / `project_id`) identity auth is the sole
  authority (401 no-principal / 404 non-member / 403 viewer-write); the legacy
  `KNOWLEDGE_READ_TOKENS` / `KNOWLEDGE_WRITE_TOKENS` are **not** additionally
  required, and a shared knowledge token does not confer membership. In **legacy
  mode** (no project) the shared-token behavior is unchanged.
- Uploaded files live under `data/raw/<project_id>/`; graph output under
  `data/kg/<project_id>/`. The `project_id` segment is guarded by
  `safe_upload_filename` and per-file uploads keep the `safe_upload_filename`
  traversal guard (`../evil.txt` → 400).
- `KG_JOBS` entries carry `project_id`; `GET /jobs/{job_id}` and `GET /stats`
  return 404 / empty for jobs/graphs belonging to another project (or to the
  legacy global scope), so no cross-project job/status leak occurs.

Proof: `tests/integration/test_knowledge_route_isolation.py` (live TestClient,
real identity + JWT): cross-project upload/list isolation, non-member 404,
missing-principal 401, viewer upload/build 403, traversal-400, project-scoped
job-status 404, project-scoped stats dir, and legacy shared-token pass/deny.

## MCP Surface Isolation — Landed This Pass (Phase 1-2C)

The MCP JSON-RPC route (`/api/v1/mcp`) now has the same project-scoped authority
model as the live HTTP run routes:

- The router resolves a `Principal` from the HTTP `Authorization: Bearer` token
  using the existing identity path (session access JWT or per-user API key).
  That principal is passed to every MCP tool as a keyword-only argument.
- Shared `MCP_AUTH_TOKENS` / fallback `API_AUTH_TOKENS` remain valid for
  **legacy no-project** MCP calls, but they resolve to `principal=None` and
  therefore never satisfy project membership. A shared token plus `project_id`
  returns a structured MCP auth error instead of project data.
- `list_runs`, `get_run_summary`, `analyze_compare`, and `get_artifacts` require
  project membership when `project_id` is supplied and pass `project_id` into
  run storage reads (`list_runs(..., project_id=...)`,
  `get_run(..., project_id=...)`).
- `run_evaluation` requires the **editor** role when `project_id` is supplied,
  confines `dataset_path` to `data/datasets/<project_id>/`, and persists the
  resolved `project_id` onto the new `EvaluationRun`.
- Legacy tool calls without `project_id` preserve the existing shared-token /
  local behavior and direct tool unit-call compatibility.

Proof: `tests/unit/adapters/inbound/mcp/test_project_tools.py` and
`tests/integration/test_mcp_project_isolation.py`: project-scoped list/get/
compare/artifact checks, no-principal auth errors, viewer-write denial,
foreign dataset-path rejection, bearer API-key + JWT project scoping, shared
MCP-token legacy success, and shared MCP-token + `project_id` denial.

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

1. **Project isolation — run routes + dataset/retriever-doc + knowledge + MCP DONE; remaining
   backend parity:** the storage-enforced scoping, identity persistence,
   membership/role resolution, the principal/denial primitives, the live
   `/api/v1/runs` route wiring, **dataset upload/list/read + retriever-doc
   upload/read**, **knowledge upload/list/build/jobs/stats**, and **MCP run
   tools** are implemented and proven. **Remaining**: a **Postgres
   `IdentityStoragePort` adapter** (only SQLite identity exists today) is still
   needed for backend parity. Storage run-mutation methods (`delete_run`,
   `update_run_metadata`, `save_feedback`, cluster maps) remain scoped at the
   route layer via the `get_run(project_id=...)` membership chokepoint rather
   than being independently project-parameterized.
2. **Role gate — run + dataset/retriever-doc + knowledge + MCP writes DONE; remaining:**
   `require_role` / viewer-editor-admin is applied to run writes (start, feedback
   save, cluster-map save/delete), dataset/retriever-doc uploads, knowledge
   upload/build, and MCP `run_evaluation`, all proven (`test_run_route_isolation.py`,
   `test_dataset_route_isolation.py`, `test_knowledge_route_isolation.py`,
   `test_mcp_project_isolation.py`, `test_project_tools.py`).
   Admin membership-management endpoints are not yet introduced (conditional per
   the plan).
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
