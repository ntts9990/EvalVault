# Debug Report

## Run Summary
- run_id: fd810155-d69f-4c2c-944a-be960a32aa62
- dataset: graphrag-smoke (1.0.0)
- model: gpt-5-nano
- started_at: 2026-01-04T16:15:49.330233
- finished_at: 2026-01-04T16:16:22.376623
- duration_seconds: 33.04639
- total_test_cases: 1
- pass_rate: 1.0
- total_tokens: 6657
- total_cost_usd: None

## Stage Summary
- total_events: 3
- missing_required_stage_types: system_prompt
- stage_type_counts:
  - input: 1
  - retrieval: 1
  - output: 1
- stage_type_avg_durations_ms:
  - retrieval: 1474.456
  - output: 33046.000

## Bottlenecks
- missing_stage: system_prompt
- latency: output avg_duration_ms=33046.0
- latency: retrieval avg_duration_ms=1474.456

## Recommendations
- [p1_high] retriever: Review stage metrics - Inspect parameters or models for the affected stage.
- [p2_medium] generator: Review stage metrics - Inspect parameters or models for the affected stage.

## Failing Stage Metrics
- output.latency_ms: score=33046.0 threshold=3000.0 stage_id=972d6e13-bf1f-4e52-b1e9-76f969e268e0
- retrieval.latency_ms: score=1474.4563749991357 threshold=500.0 stage_id=0c97b847-2fee-4bb4-8b56-b24d6193b8c1
- retrieval.avg_score: score=0.016261237440507666 threshold=0.2 stage_id=0c97b847-2fee-4bb4-8b56-b24d6193b8c1
- retrieval.score_gap: score=0.00018508725542041443 threshold=0.1 stage_id=0c97b847-2fee-4bb4-8b56-b24d6193b8c1
