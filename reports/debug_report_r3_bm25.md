# Debug Report

## Run Summary
- run_id: 3fd2f7e6-98ba-4d7b-9b1d-2760aade541d
- dataset: r3_bm25_smoke (1.0)
- model: gpt-5-nano
- started_at: 2026-01-04T14:52:22.536392
- finished_at: 2026-01-04T14:52:22.536428
- duration_seconds: 3.6e-05
- total_test_cases: 1
- pass_rate: 1.0
- total_tokens: 0
- total_cost_usd: None

## Stage Summary
- total_events: 3
- missing_required_stage_types: system_prompt
- stage_type_counts:
  - input: 1
  - retrieval: 1
  - output: 1
- stage_type_avg_durations_ms:
  - retrieval: 0.429

## Bottlenecks
- missing_stage: system_prompt
- latency: retrieval avg_duration_ms=0.429

## Recommendations
- [p1_high] retriever: Review stage metrics - Inspect parameters or models for the affected stage.

## Failing Stage Metrics
- retrieval.avg_score: score=0.0 threshold=0.2 stage_id=5dfeebb1-5362-46c1-acbb-95860a51cc94
- retrieval.score_gap: score=0.0 threshold=0.1 stage_id=5dfeebb1-5362-46c1-acbb-95860a51cc94
