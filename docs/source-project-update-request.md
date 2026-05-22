# Source Project Update Request

Status date: 2026-05-21

## Purpose

AI Tool Suite is becoming the closed-network-first, output-first evaluation
operating system for the sibling tool ecosystem.

Each source project should continue developing independently. This request asks
each project to publish a small, stable project-state handoff so AI Tool Suite
can integrate the project through adapters and so other sibling projects can
reuse useful patterns without copying internal code.

## Common Message To Send To Every Source Project

Please update your project with an AI Tool Suite handoff packet.

Target outcome:

- make your current development status machine-readable
- expose stable artifacts, commands, and schemas for adapter integration
- document which parts work in closed-network/default mode
- identify reusable patterns that other tools can learn from
- identify risks, gaps, and source changes that may affect AI Tool Suite

Do not move your internal implementation into AI Tool Suite. Keep improving in
your own repo. AI Tool Suite will integrate through certified adapters, stable
artifacts, CLI commands, local APIs, and documented contracts.

Please add or update these files in your repo:

```text
.ai-tool-suite/project-state.json
docs/adapter-contract.md
docs/development-journal.md
```

If your repo already has equivalent documents, keep them and add the missing
fields instead of duplicating content.

## Required `.ai-tool-suite/project-state.json`

Use this shape:

```json
{
  "project_id": "replace-with-project-id",
  "project_name": "Replace With Project Name",
  "source_path": "/Users/sungyub/Documents/Projects/replace-with-project",
  "source_commit": "git-commit-or-unknown",
  "updated_at": "2026-05-21T00:00:00Z",
  "classification": "trusted-runtime | trusted-artifact | policy-source | experimental",
  "development_status": {
    "summary": "",
    "recent_changes": [],
    "active_work": [],
    "next_priorities": []
  },
  "stable_surfaces": [
    {
      "kind": "json-artifact | jsonl-artifact | cli | local-api | local-http | report-sidecar",
      "name": "",
      "command_or_path": "",
      "schema_version": "",
      "network_posture": "offline | local-service | cloud-opt-in",
      "required_secrets": [],
      "stability": "stable | beta | experimental",
      "notes": ""
    }
  ],
  "verification_commands": {
    "install": "",
    "fast": "",
    "full": "",
    "closed_network": "",
    "artifact_generation": ""
  },
  "runtime_outputs": {
    "generated_paths": [],
    "fixture_paths": [],
    "gitignored_paths": []
  },
  "adapter_impact": {
    "breaking_changes_since_last_update": [],
    "new_adapter_opportunities": [],
    "fields_safe_to_rely_on": [],
    "fields_experimental": []
  },
  "reusable_patterns": [
    {
      "name": "",
      "description": "",
      "where_to_look": "",
      "why_it_may_help_other_tools": ""
    }
  ],
  "known_risks": [],
  "requests_to_ai_tool_suite": []
}
```

Rules:

- Default mode must be closed-network or explicitly marked otherwise.
- Machine-readable artifacts must include schema versions.
- Do not store raw chain-of-thought or private reasoning traces.
- Final outputs and decision artifacts must be separate from diagnostic traces.
- Generated runtime output must stay separate from curated fixtures.
- Non-interactive CLI commands are preferred.
- Structured JSON output is preferred whenever an agent may call the tool.

## Required `docs/adapter-contract.md`

Please document:

- stable command(s)
- stable artifact(s)
- schema examples
- field meanings
- fields safe to rely on
- experimental fields
- required secrets
- network posture
- generated output paths
- fixture paths
- structured error behavior
- rollback path
- command to regenerate a representative artifact

Keep this contract short and operational. It should let an adapter author work
without reverse-engineering the whole source repo.

## Required `docs/development-journal.md`

Please document:

- what changed recently
- why it changed
- what remains unstable
- what other tools may learn from it
- what AI Tool Suite should not rely on yet
- what should be promoted into a shared contract later

This can be narrative. The authoritative machine-readable state should still be
`.ai-tool-suite/project-state.json`.

## Project-Specific Requests

### EvalVault

Please prioritize:

- stable regression gate JSON artifact with schema version
- fixture-only regression gate examples for pass, fail, and incomplete provenance
- documented closed-network command that does not require OpenAI, MLflow,
  Phoenix, Langfuse, or hosted trackers
- CLI help and command registration alignment
- structured error output for failed runs
- explicit distinction between RAG evaluation outputs, tracing outputs, and
  regression-gate decisions

Useful patterns to report back:

- regression gate report shape
- RAG metric aggregation
- artifact storage layout
- local CLI invocation assumptions

Current AI Tool Suite target:

- Level 2 adapter exists.
- Next useful target is Level 3 local invocation with no-network guard.

### Reverra-Gate

Please prioritize:

- file-only decision summary artifact for `promote`, `hold`, and `rollback`
- stable schema version for decision summary and run-history output
- clear separation between core quality decision and gate trust decision
- no-network/default verification command
- raw reasoning retention policy confirmation
- representative fixtures for promote, hold, rollback, and incomplete provenance

Useful patterns to report back:

- output-first decision rule
- paired baseline/current comparison fields
- HMAC/audit/event design
- no-network regression testing
- Korean/English evaluation guidance

Current AI Tool Suite target:

- Level 2 adapter exists.
- Next useful target is Level 3 local invocation with no-network guard.

### local-llm-bench

Please prioritize:

- reproducibility manifest for every benchmark run
- hardware, engine, model, quantization, dataset, timestamp, and seed metadata
- compact fixture outputs for adapter tests
- metric parser tests
- generated benchmark output path separation
- closed-network benchmark smoke command

Useful patterns to report back:

- local model benchmark evidence
- reproducibility metadata model
- hardware-aware comparison caveats

Current AI Tool Suite target:

- Level 1 benchmark evidence adapter after metadata and fixtures stabilize.

### aia-awesome-novel-studio Eval Toolkit

Please prioritize:

- stable domain evaluation artifacts for Korean dialogue, narration, and STT
- clear scoring rubric and schema version
- curated small fixtures separate from generated local outputs
- closed-network/default verification command
- structured per-sample outputs and aggregate report sidecar

Useful patterns to report back:

- Korean dialogue quality dimensions
- STT/domain-specific evaluation cases
- genre/style evaluation constraints

Current AI Tool Suite target:

- Level 1 domain evidence adapter after fixture and schema audit.

### ai-agent-opt

Please prioritize:

- policy and methodology notes rather than runtime integration
- statistical test assumptions
- benchmark comparison methodology
- risk notes for paired tests, variance, stochastic runs, and multiple testing
- examples of decision thresholds that should or should not be generalized

Useful patterns to report back:

- statistical gate design
- optimization/evaluation loop design
- confidence and uncertainty handling

Current AI Tool Suite target:

- Policy source. No runtime adapter until executable surfaces are stable.

### CSWind PoC Eval

Please prioritize:

- compact promote/hold/rollback fixture examples
- Korean rationale examples
- exact gate rule summary
- clear boundary between business-specific assumptions and reusable evaluation
  logic
- closed-network/default verification command if available

Useful patterns to report back:

- small decision gate implementation
- paired McNemar/bootstrap use
- Korean operator-facing rationale language

Current AI Tool Suite target:

- Level 1 fixture/policy extraction, not primary runtime integration yet.

### Grounded Workspace OS

Please prioritize:

- evidence reference schema
- claim taxonomy
- policy gateway rules
- permission/scope classification
- examples that do not require Google Workspace or cloud services
- notes on what is generic versus workspace-specific

Useful patterns to report back:

- EvidenceRef and Claim model
- approval/policy gateway design
- permission-aware agent operation

Current AI Tool Suite target:

- Policy/schema source. Avoid direct runtime integration for now.

### Verbera

Please prioritize:

- stable local validation JSON
- retrieval/workflow evidence schema
- graph-grounded evidence references
- closed-network validation command
- fixture examples for pass/fail/ambiguous retrieval evidence
- generated output and fixture separation

Useful patterns to report back:

- retrieval evidence structure
- graph-grounded validation
- workflow-level evidence contracts

Current AI Tool Suite target:

- Level 1 retrieval/workflow evidence adapter after local validation JSON is
  stable.

### LLM Research Vault

Please prioritize:

- research artifact metadata
- source/citation provenance
- claim levels: observation, pattern, bridge-candidate, mechanism-claim
- reproducible search or ingestion notes
- sensitive-data and copyright handling notes
- stable export format for research summaries

Useful patterns to report back:

- research evidence organization
- citation/provenance rules
- uncertainty handling

Current AI Tool Suite target:

- Policy and evidence source unless stable machine-readable exports exist.

### NTTS Flightlog

Please prioritize:

- stable progress/log event schema
- local-only operation mode
- structured session summaries
- agent-readable status snapshots
- generated log output paths and retention policy

Useful patterns to report back:

- live progress capture
- session handoff summaries
- task lifecycle status vocabulary

Current AI Tool Suite target:

- Agent operation evidence source after event schema is stable.

### Realtime Translation

Please prioritize:

- translation quality output artifacts
- latency and streaming metrics
- closed-network/local-service mode if available
- fixtures for source, translation, reference, and evaluation result
- privacy/sensitive-audio handling notes

Useful patterns to report back:

- multilingual output evaluation
- latency-aware quality metrics
- streaming artifact boundaries

Current AI Tool Suite target:

- Evidence adapter only after artifact schema and privacy policy are clear.

### AIA Classification

Please prioritize:

- classification result schema
- label taxonomy versioning
- confusion/error analysis artifacts
- deterministic fixture set
- closed-network/default verification command

Useful patterns to report back:

- label taxonomy management
- per-class evidence reporting
- classification regression checks

Current AI Tool Suite target:

- Level 1 evidence adapter after schema and fixtures stabilize.

### Amorepacific AIM

Please prioritize:

- domain-specific artifact contracts
- sensitive-data handling policy
- closed-network/default operation notes
- stable JSON sidecars for any reports
- fixture examples that contain no confidential data

Useful patterns to report back:

- enterprise/domain evaluation constraints
- sensitive-data policy examples
- operator-facing reporting patterns

Current AI Tool Suite target:

- Inspect/profile only until safe fixtures and integration surfaces are clear.

### Reverra Lab

Please prioritize:

- which experiments are candidates for Reverra-Gate or AI Tool Suite promotion
- experimental artifact schemas
- stable versus exploratory boundaries
- reusable evaluation methods
- no-network/default experiment reproduction commands where possible

Useful patterns to report back:

- experiment-to-product promotion criteria
- evaluation method prototypes
- decision-policy experiments

Current AI Tool Suite target:

- Policy/method source unless a stable artifact emerges.

## How AI Tool Suite Will Use The Update

AI Tool Suite will ingest the project-state packet and use it to update:

- `docs/project-profiles/<project>.md`
- `docs/adapter-certification-matrix.md`
- adapter manifests
- fixture requirements
- source-specific advisories
- future MCP resources for agent access

The goal is not centralized control. The goal is shared operational memory:
each project stays independent, but useful contracts, evidence patterns, and
development lessons become available to the rest of the ecosystem.
