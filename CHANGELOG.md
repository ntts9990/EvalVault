# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> Note: v1.x release notes are tracked in GitHub Releases. This file keeps legacy 0.x history
> plus high-level highlights.

## [Unreleased]

### Phase 3 — refactor & hardening milestone

Consolidates the REFACTOR_DIAGNOSIS slice program landed on `main`.

#### Added
- `RetryPolicy` (timeout + backoff) across all five LLM adapters (A-S1).
- `BaseTrackerAdapter` with a unified error policy and a real `MultiTrackerAdapter`
  for MLflow + Phoenix dual-logging (A-S2/A-S3), replacing hand-synthesised
  dual-logging in the CLI/API.
- Initial public governance docs (Code of Conduct, Security Policy, CONTRIBUTING).
- GitHub templates for issues, pull requests, and automation policies.
- CI enhancements for coverage reporting, caching, and multi-Python support.

#### Changed
- `RagasEvaluator` narrowed from 1,951 → 971 lines: cost, faithfulness fallback,
  metric scoring, prompt catalog/overrides, Korean prompts, language detection,
  and claim-level conversion extracted into focused, independently-tested
  services (D-S2/D-S3/D-S4/D-S5).
- Domain no longer imports adapters (`DomainMemoryPort`, D-S1); reporting rebuilt
  on Builder/Renderer/Composer interfaces; pipeline templates split per category.
- Storage/domain drop the vendor-specific `langfuse_trace_id` in favour of a
  `tracker_trace_ids` map (A-S4).
- CI matrix slimmed (Windows moved to a nightly job), regression-gate job
  de-duplicated, lint job trimmed, docs absorbed into the handbook.
- README bilingual overview and refreshed badges.
- CLAUDE.md updated to remove internal-only references.

#### Removed
- The `agent/` autonomous-agent subsystem and its in-package `evalvault agent`
  CLI / `AgentType` config (X-S1).

#### Fixed
- `evalvault run` no longer aborts (exit 2) when the default `mlflow+phoenix`
  tracker is configured but Phoenix is unreachable: auto-derived Phoenix sync is
  now best-effort (open-circuit), while explicit `--phoenix-dataset` /
  `--phoenix-experiment` requests still fail loudly.
- Storage factory honours an explicit `--db` path instead of silently falling
  back to a settings-driven backend.

## [1.38.0] - 2026-01-04

### Changed
- See GitHub Releases for full notes.

## [0.4.0] - 2025-12-25

### Added
- Ollama support for air-gapped deployments.
- Profile-driven model configuration (`--profile` CLI flag).

## [0.3.0] - 2025-12-24

### Added
- Phase 6 completion with six evaluation metrics (Ragas v1.0 compatible).

## [0.2.0] - 2024-12-24

### Added
- SQLite persistence and evaluation history CLI commands.

## [0.1.0] - 2024-12-24

### Added
- Initial release with core CLI and evaluation pipeline.

[Unreleased]: https://github.com/ntts9990/EvalVault/compare/v1.38.0...HEAD
[1.38.0]: https://github.com/ntts9990/EvalVault/releases/tag/v1.38.0
[0.4.0]: https://github.com/ntts9990/EvalVault/releases/tag/v0.4.0
[0.3.0]: https://github.com/ntts9990/EvalVault/releases/tag/v0.3.0
[0.2.0]: https://github.com/ntts9990/EvalVault/releases/tag/v0.2.0
[0.1.0]: https://github.com/ntts9990/EvalVault/releases/tag/v0.1.0
