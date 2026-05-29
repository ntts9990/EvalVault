# EvalVault Security & Multi-tenancy Track (EvalVault Phase 1) — Implementation Plan

> **Status date**: 2026-05-29
> **Branch**: `feat/multiuser-auth`
> **Driver**: EvalVault is moving from a single-user / localhost tool to a **networked, multi-user solution**. The API currently ships **unauthenticated by default** (`api_auth_tokens` empty ⇒ `require_api_token` is a no-op) and has **no concept of users, sessions, or data ownership** — every caller can read and mutate every run/dataset.
> **Scope**: Backend authentication + authorization with **project-scoped data isolation**, per-project tracker segmentation, and a fail-closed network posture. The web frontend is being rewritten separately; this plan delivers the **API contract** it will consume.

> ⚠️ **Roadmap naming — read this first.** This is the **EvalVault security/multi-tenancy track**, internally sub-phased **P1.0 → P1.5**. It is **not** the *solution-platform* "Phase 1 (real adapter integration)". Always refer to the steps here as **EvalVault Auth P1.x** to avoid conflating the two tracks on the shared roadmap.
>
> 🎯 **Readiness gate.** The integration/demo roadmap milestone is **"project isolation enforced" (end of P1.3)** — *not* "auth-ready". P1.1–P1.2 are foundation work; **P1.3 is the actual security completion point** (data is actually isolated). Do not advertise readiness before P1.3.

---

## 0. Threat model & decisions

EvalVault must keep working **air-gapped / offline** (Docker offline bundle is a core scenario), so authentication cannot depend on an external IdP by default.

| Concern | Decision | Rationale |
|---|---|---|
| Identity source | **Built-in accounts** (username/password) with server-issued sessions; **OIDC later** via a pluggable adapter | Self-contained, works offline. OIDC (Authlib) added behind the same port when needed. |
| Password hashing | **`pwdlib[argon2]`** | `passlib` is effectively unmaintained (breaks on Python 3.13+); Argon2 is the current standard; FastAPI docs migrated to pwdlib. |
| Session transport (browser) | **httpOnly + Secure cookie** carrying a short-lived **access JWT** + rotating **refresh** token; CSRF via SameSite=Strict + double-submit token | Frontend is greenfield, so best-practice is applied directly. httpOnly keeps tokens out of JS ⇒ XSS cannot exfiltrate them. |
| Programmatic access (CLI/MCP/CI) | **Per-user API keys** (`Authorization: Bearer <key>`) | Browser flow is unsuitable for headless callers. The legacy shared `api_auth_tokens` becomes a deprecated transition "service token", then removed. |
| Authorization / isolation | **Project-scoped** (users belong to projects; data is scoped to a project) | EvalVault already uses a `project_name` concept; team/project is the natural boundary for a multi-user solution. Lighter than per-user ownership, gives real isolation. |
| Network exposure | **Conditional fail-closed** (P1.0): a non-loopback bind (`0.0.0.0`) with no auth configured **refuses to boot** | The real risk is network exposure, not "no token" per se. Localhost-only dev stays frictionless. |
| Trackers | **Per-project** MLflow experiment / Phoenix project / Langfuse project mapping | Without this, a shared tracker UI is a side channel that defeats in-app isolation (see §1). |

### Defaults (applied unless changed)
- **JWT signing**: HS256 (single node / shared secret). RS256 option for multi-node.
- **Registration**: **admin-invite only** (no self-service signup).
- **Email verification / password reset**: admin-issued/reset initially (SMTP is air-gap-unfriendly; deferred).

---

## 1. Relationship to the experiment trackers (MLflow / Phoenix / Langfuse)

The trackers are **a mostly-separate concern** from user auth, with two real intersections:

1. **Different auth domains.** User auth governs "who logs into EvalVault". Trackers are *outbound* services EvalVault pushes to using **service credentials** (`MLFLOW_TRACKING_URI`, `LANGFUSE_*`, `PHOENIX_*`) — admin/global config, not per-user. Building user auth does **not** change tracker connections.
2. **Isolation leakage (P1.4).** If runs are isolated per project in EvalVault but all log to **one shared** MLflow experiment / Phoenix project / Langfuse project, the tracker UI becomes a side channel (user A sees user B's traces). End-to-end isolation therefore requires mapping **EvalVault project → per-project tracker experiment/project**, and constraining request-supplied `tracker_config` so a user cannot redirect logging or read another project.

> Residual risk: the external tracker UIs enforce their **own** access control. Per-project segmentation aligns EvalVault's boundary with the trackers, but operators are still responsible for the trackers' own auth.

---

## 2. Sub-phases (EvalVault Auth P1.0 → P1.5)

### P1.0 — Security hotfix (independent of multi-user) · partly DONE
The basic defense line, decoupled from identity. **Stays in place regardless of auth.**
- ✅ **Path-traversal hardening** of all upload/eval file sinks via `api/path_safety.py` (`safe_upload_filename` + `resolve_user_path`), confined to the allow-list the MCP boundary already uses (`data/`, `tests/fixtures/`, `reports/`). Closes arbitrary file read/write on `/knowledge/upload`, `/runs/options/datasets`, `/runs/options/retriever-docs`, `/runs/start` (`dataset_path`), retriever `docs_path`.
- ⏳ **Fail-closed network bind**: a non-loopback bind (`--host 0.0.0.0`) with no auth configured **refuses to boot** (escape hatch `EVALVAULT_ALLOW_INSECURE_NETWORK=1`). Localhost-only keeps the existing info warning.
- Tests: traversal regressions (done) + fail-closed boot guard.

### P1.1 — Identity foundation (backend, no enforcement yet) · L
- Domain entities (`domain/entities/auth.py`, dataclasses): `User`, `Project`, `Membership` (`Role` = admin/editor/viewer), `ApiKey`, `RefreshToken`.
- Ports (`ports/outbound/auth_port.py`): `PasswordHasherPort`, `TokenServicePort`, `IdentityStoragePort`.
- Adapters (`adapters/outbound/auth/`): `Argon2PasswordHasher` (pwdlib), `JwtTokenService` (PyJWT, access+refresh).
- Storage: new tables (`users`, `projects`, `memberships`, `api_keys`, `refresh_tokens`) in SQLite + PostgreSQL adapters (additive, `CREATE TABLE IF NOT EXISTS`).
- Bootstrap: seed admin from env (`EVALVAULT_ADMIN_EMAIL` / `_PASSWORD`) on first run.
- Settings: `auth_secret_key`, `auth_access_ttl`, `auth_refresh_ttl`, `auth_cookie_secure`.
- Tests: hashing, token issue/verify/expiry/rotation, identity store CRUD, bootstrap. **No API enforcement yet.**

### P1.2 — Auth session · M
- Routers: `/api/v1/auth/login`, `/refresh`, `/logout`, `/me`; cookie set/clear + CSRF; API key issue/list/revoke.
- `get_current_principal` dependency: resolves a principal from **cookie JWT** (browser) or **Bearer API key** (programmatic CLI/MCP/CI).
- **Fail-closed refined**: non-loopback bind + no admin/secret ⇒ refuse (extends the P1.0 token check to admin existence), folded into prod-profile validation.
- Legacy `api_auth_tokens` kept as a flagged transition service-token path.
- Tests: login, refresh rotation, CSRF, API-key auth, fail-closed boot.

### P1.3 — Project authorization enforcement · L — 🎯 **READINESS GATE (security complete here)**
- Promote `project` to a first-class entity; replace free-text `project_name` with `Project`/`project_id` on runs/datasets/uploads (migration backfills existing rows to a `default` project).
- Add a `project_id` filter to `save`/`list`/`get`/query in both storage adapters.
- Enforce on **all 9 routers**: authenticated principal + project membership; list/query filtered to the principal's projects; mutations gated by role (editor↑ write, viewer read).
- Admin membership/role management endpoints.
- Tests: cross-project isolation (A cannot read/list/mutate B's runs), role gating, IDOR ⇒ 403/404.

### P1.4 — Tracker per-project segmentation · M
- Map project → per-project MLflow experiment / Phoenix project / Langfuse project (or tags) in the tracker adapters (currently global).
- Validate/restrict request `tracker_config` so a user cannot redirect logging or target another project.
- Tests: run in project X logs to experiment X; `tracker_config` override constrained.

### P1.5 — Cutover · M
- Deliver the API contract (login/refresh/logout/me, CSRF, API-key mgmt, project switching, 401/403 semantics) + OpenAPI + reference client snippet for the new frontend.
- Update `.env.example`, `docker-compose.offline.yml` (admin bootstrap, secret key, cookie/secure, fail-closed), OFFLINE docs, `PROJECT_STATE.md`.
- Remove the deprecated shared-token path; full test + security regression pass; migration guide.

---

## 3. Cross-cutting concerns
- **MCP** shares `WebUIAdapter.run_evaluation` ⇒ must carry a principal/project context; resolved via an **API-key principal** (MCP already has its own token scheme).
- **CLI** is operator-trusted and local ⇒ keeps working (local/service principal); must not break.
- **DB migrations**: adapters use `CREATE TABLE IF NOT EXISTS` ⇒ additive schema + backfill; preserve existing runs.
- **Reuse**: existing rate-limiting, CORS, and prod-profile validation are extended (auth secret + admin required).
- **Path-traversal fixes (P1.0)** remain a defense-in-depth layer independent of auth.

---

## 4. Out of scope (for now)
- Full OIDC/SSO (designed-for via the port; implemented when required).
- Self-service registration, email verification, SMTP-based password reset.
- Per-user (sub-project) ownership/ACLs — project is the isolation unit.
