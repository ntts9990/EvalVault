# Regression-Gate Fixture Examples

> Fixture-only, **no-network** examples of the `evalvault regress` decision contract,
> covering the three decision classes an adapter must handle: **pass**, **fail**, and
> **incomplete provenance**. Requested by AI Tool Suite in
> [`docs/source-project-update-request.md`](../../../../docs/source-project-update-request.md) §EvalVault.
> Schema contract: [`docs/adapter-contract.md`](../../../../docs/adapter-contract.md) §2.1.

These fixtures require **no OpenAI / MLflow / Phoenix / Langfuse / hosted tracker** —
they exercise the local SQLite + scipy path only. The matching test
(`tests/unit/test_regression_gate_fixtures.py`) seeds a temp SQLite DB, invokes the
real `regress` CLI end-to-end, and asserts the contract.

## Layout

```
regression_gate/
├── runs/                       # input EvaluationRun fixtures (seedable, offline)
│   ├── pass_baseline.json      pass_candidate.json
│   ├── fail_baseline.json      fail_candidate.json
│   └── incomplete_baseline.json incomplete_candidate.json
└── expected/                   # golden output envelopes (representative artifacts)
    ├── pass.json
    ├── fail.json
    └── incomplete_provenance.json
```

## Run fixture schema

A compact, storage-agnostic shape that the test loader turns into an `EvaluationRun`:

```json
{
  "run_id": "candidate-pass",
  "dataset_name": "regression-gate-fixture",
  "model_name": "fixture-model",
  "metrics_evaluated": ["faithfulness", "answer_relevancy"],
  "thresholds": {"faithfulness": 0.8, "answer_relevancy": 0.7},
  "cases": [
    {"test_case_id": "tc-1", "scores": {"faithfulness": 0.89, "answer_relevancy": 0.86}}
  ]
}
```

## The three scenarios

| Scenario | Setup | Envelope `status` | `data.status` | exit code |
|---|---|---|---|---|
| **pass** | candidate ≈ baseline (within `fail_on_regression` 0.05) | `ok` | `passed` | `0` |
| **fail** | candidate faithfulness drops 0.21 (> 0.05) | `ok` | `failed` | `2` |
| **incomplete provenance** | baseline & candidate share **no** `metrics_evaluated` | `error` | — (`data` is null) | `1` |

**Incomplete provenance** is the decision class adapters most often forget: the gate
*cannot render a verdict* because the two runs have nothing comparable. The envelope
reports `status: "error"` + `error_type: "ValueError"` + a human-readable `message`,
never `"passed"`/`"failed"`. Treat it as "abstain", not "pass".

## What is asserted (and what is not)

The golden envelopes contain representative values, but the test asserts at the right
granularity — because this is a **contract** test, not a bit-for-bit snapshot:

- **Exact equality** — the contract: `command`, `version`, envelope `status`,
  `data.status`, `data.regression_detected`, `data.fail_on_regression`, `data.test`,
  `data.metrics`, per-result `metric` + `regression`, and the **exit code**.
- **Tight tolerance (3 decimals)** — `baseline_score`, `candidate_score`, `diff`,
  `diff_percent`. These are simple arithmetic but may vary by ~1 ULP across the
  Ubuntu/macOS/Windows CI matrix; 3-decimal tolerance catches real regressions while
  ignoring sub-noise platform jitter.
- **Range / sign only** — `p_value` (∈ [0,1]), `effect_size`, `effect_level`,
  `is_significant`. These are scipy-derived and classified `fields_experimental` in the
  adapter contract; their *meaning* is asserted (e.g. fail → faithfulness `regression`
  true, `is_significant` true), not their exact float.
- **Not asserted** — `started_at`, `finished_at`, `duration_ms` (wall-clock runtime).

The `_meta` block in each golden file documents `exit_code`, runtime fields, and
environment-sensitive fields. `_meta` is fixture metadata, not part of the CLI output.

## Regenerate

```bash
uv run pytest tests/unit/test_regression_gate_fixtures.py -q
```

The test is the executable spec. If the regression-gate envelope schema changes,
this test fails first — update the golden files deliberately and bump
`schema_version` in `docs/adapter-contract.md` §2.1 per the stability policy.
