# O1 전달용 D1 DebugReport 요약

> **작성일**: 2026-01-04
> **목적**: R1/R2/R3 DebugReport 결과를 오케스트레이터에 공유
> **SSoT**: `docs/internal/status/STATUS.md` (최신 상태는 STATUS 기준)

---

## R1 (Retriever Smoke)

- run_id: `3dcb2b80-1744-4efd-837c-d7aea9348ebe`
- DB: `scratch/r1_smoke/evalvault.db`
- stage_events: `scratch/r1_smoke/stage_events.jsonl`
- stage_report: `scratch/r1_smoke/stage_report.txt`
- DebugReport:
  - `reports/debug_report_r1_smoke.md`
  - `reports/debug_report_r1_smoke.json`
- run 요약
  - dataset: `retriever-smoke`
  - model: `ollama/gemma3:1b`
  - total_test_cases: 1, pass_rate: 1.0
- Stage metrics: 7개 (실패 1개)
- bottlenecks
  - latency: retrieval avg_duration_ms=0.271
  - latency: output avg_duration_ms=0.126
- recommendations
  - `[p2_medium] retriever: Review stage metrics - Inspect parameters or models for the affected stage.`

---

## R2 (GraphRAG Smoke)

- run_id: `d60bce6a-ce38-4210-a63e-c8d73d9ecfe7`
- DB: `reports/r2_graphrag.db`
- stage_events: `reports/r2_graphrag_stage_events.jsonl`
- stage_report: `reports/r2_graphrag_stage_report.txt`
- DebugReport:
  - `reports/debug_report_r2_graphrag.md`
  - `reports/debug_report_r2_graphrag.json`
- run 요약
  - dataset: `graphrag-smoke`
  - model: `ollama/gemma3:1b`
  - total_test_cases: 1, pass_rate: 0.0
- Stage metrics: 7개 (실패 3개)
- missing_required_stage_types: `system_prompt`
- bottlenecks
  - missing_stage: system_prompt
  - latency: retrieval avg_duration_ms=1415.969
  - latency: output avg_duration_ms=371.0
- recommendations
  - `[p1_high] retriever: Review stage metrics - Inspect parameters or models for the affected stage.`
- 비교 샘플(openai)
  - run_id: `fd810155-d69f-4c2c-944a-be960a32aa62`
  - DebugReport: `reports/debug_report_r2_graphrag_openai.md`, `reports/debug_report_r2_graphrag_openai.json`

---

## R3 (BM25 evalvault run)

- run_id: `3fd2f7e6-98ba-4d7b-9b1d-2760aade541d`
- DB: `reports/r3_bm25.db`
- stage_events: `reports/r3_bm25_stage_events.jsonl`
- stage_report: `reports/r3_bm25_stage_report.txt`
- DebugReport:
  - `reports/debug_report_r3_bm25.md`
  - `reports/debug_report_r3_bm25.json`
- run 요약
  - dataset: `r3_bm25_smoke`
  - model: `gpt-5-nano`
  - total_test_cases: 1, pass_rate: 1.0
- Stage metrics: 6개 (실패 2개)
- missing_required_stage_types: `system_prompt`
- bottlenecks
  - missing_stage: system_prompt
  - latency: retrieval avg_duration_ms=0.429
- recommendations
  - `[p1_high] retriever: Review stage metrics - Inspect parameters or models for the affected stage.`

---

## 공통 메모

- DebugReport는 StageEvent가 누락된 경우 `missing_stage`로 기록됨 (system_prompt).
- trace_links 표기는 `langfuse_trace_url=...` / `phoenix_trace_url=...` 형식으로 통일됨.
- 추천 문구는 StageMetricGuideService의 기본 fallback을 사용 중.
