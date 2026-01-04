# Debug Report

## Run Summary
- run_id: 3dcb2b80-1744-4efd-837c-d7aea9348ebe
- dataset: retriever-smoke (1.0.0)
- model: ollama/gemma3:1b
- started_at: 2026-01-04T14:47:48.046591
- finished_at: 2026-01-04T14:47:48.047067
- duration_seconds: 0.000476
- total_test_cases: 1
- pass_rate: 1.0
- total_tokens: 0
- total_cost_usd: None

## Stage Summary
- total_events: 4
- stage_type_counts:
  - system_prompt: 1
  - input: 1
  - retrieval: 1
  - output: 1
- stage_type_avg_durations_ms:
  - retrieval: 0.271
  - output: 0.126

## Bottlenecks
- latency: retrieval avg_duration_ms=0.271
- latency: output avg_duration_ms=0.126

## Recommendations
- [p2_medium] retriever: Review stage metrics - Inspect parameters or models for the affected stage.

## Failing Stage Metrics
- retrieval.score_gap: score=0.08292250839768633 threshold=0.1 stage_id=423de2bd-1b6c-4b6c-bd44-33a36e7e6da9
