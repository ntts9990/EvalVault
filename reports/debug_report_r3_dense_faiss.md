# Debug Report

## Run Summary
- run_id: r3-dense-faiss-1767506494
- dataset: r3_bm25_smoke (1.0)
- model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- started_at: 2026-01-04T15:01:34.800514
- finished_at: 2026-01-04T15:01:34.800514
- duration_seconds: 0.0
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
  - retrieval: 724.669
  - output: 0.000

## Bottlenecks
- missing_stage: system_prompt
- latency: retrieval avg_duration_ms=724.669
- latency: output avg_duration_ms=0.0

## Recommendations
- [p2_medium] retriever: Review stage metrics - Inspect parameters or models for the affected stage.

## Failing Stage Metrics
- retrieval.latency_ms: score=724.6685000136495 threshold=500.0 stage_id=205a6579-835f-42f7-9bde-cf21ac3ed2ff
