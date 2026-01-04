# Debug Report

## Run Summary
- run_id: d60bce6a-ce38-4210-a63e-c8d73d9ecfe7
- dataset: graphrag-smoke (1.0.0)
- model: ollama/gemma3:1b
- started_at: 2026-01-04T16:12:08.399777
- finished_at: 2026-01-04T16:12:08.771204
- duration_seconds: 0.371427
- total_test_cases: 1
- pass_rate: 0.0
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
  - retrieval: 1415.969
  - output: 371.000

## Bottlenecks
- missing_stage: system_prompt
- latency: retrieval avg_duration_ms=1415.969
- latency: output avg_duration_ms=371.0

## Recommendations
- [p1_high] retriever: Review stage metrics - Inspect parameters or models for the affected stage.

## Failing Stage Metrics
- retrieval.latency_ms: score=1415.9693329129368 threshold=500.0 stage_id=89d58c61-1df9-4670-9776-b54b5adb68de
- retrieval.avg_score: score=0.016261237440507666 threshold=0.2 stage_id=89d58c61-1df9-4670-9776-b54b5adb68de
- retrieval.score_gap: score=0.00018508725542041443 threshold=0.1 stage_id=89d58c61-1df9-4670-9776-b54b5adb68de
