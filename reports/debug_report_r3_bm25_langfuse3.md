# Debug Report

## Run Summary
- run_id: 3ab112c4-f0ae-447d-ab2e-1a4f30e2e114
- dataset: r3_bm25_smoke (1.0)
- model: gpt-5-nano
- started_at: 2026-01-04T15:18:56.894222
- finished_at: 2026-01-04T15:18:56.894259
- duration_seconds: 3.7e-05
- total_test_cases: 1
- pass_rate: 1.0
- total_tokens: 0
- total_cost_usd: None
- trace_links: langfuse_trace_url=http://localhost:3000/project/cmjixj06j0006nq07ys4tz9i2/traces/73eea26251f01a2b352d17842887f98a

## Stage Summary
- total_events: 3
- missing_required_stage_types: system_prompt
- stage_type_counts:
  - input: 1
  - retrieval: 1
  - output: 1
- stage_type_avg_durations_ms:
  - retrieval: 0.526

## Bottlenecks
- missing_stage: system_prompt
- latency: retrieval avg_duration_ms=0.526

## Recommendations
- [p1_high] retriever: Review stage metrics - Inspect parameters or models for the affected stage.

## Failing Stage Metrics
- retrieval.avg_score: score=0.0 threshold=0.2 stage_id=c66c049c-2e92-4e2a-ba3c-8e966101363a
- retrieval.score_gap: score=0.0 threshold=0.1 stage_id=c66c049c-2e92-4e2a-ba3c-8e966101363a
