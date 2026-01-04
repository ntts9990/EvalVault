# O1 병렬 진행 현황 (요약)

> **작성일**: 2026-01-04
> **SSoT**: `docs/internal/STATUS.md`
> **작업 기준**: `docs/internal/PARALLEL_WORK_PLAN.md`

---

## 핵심 링크

- 진행 상태: `docs/internal/STATUS.md`
- 문서 정비 계획: `docs/internal/DOCS_REFACTOR_PLAN.md`
- D1 DebugReport 요약: `docs/internal/O1_D1_DEBUG_REPORT_SUMMARY.md`
- R1 보고서: `docs/internal/R1_COMPLETION_REPORT.md`
- R2 보고서: `docs/internal/R2_COMPLETION_REPORT.md`
- R3 보고서: `docs/internal/R3_PROGRESS_REPORT.md`
- R4 보고서: `docs/internal/R4_PROGRESS_REPORT.md`

---

## 요약 스냅샷 (run_id 기준)

| 트랙 | 상태 | run_id | 비고 |
|------|------|--------|------|
| R1 | 완료 | `3dcb2b80-1744-4efd-837c-d7aea9348ebe` | retriever smoke |
| R2 (dev) | 완료(샘플) | `d60bce6a-ce38-4210-a63e-c8d73d9ecfe7` | graphrag dev |
| R2 (openai) | 비교 샘플 | `fd810155-d69f-4c2c-944a-be960a32aa62` | graphrag openai |
| R3 | 중간 완료 | `3fd2f7e6-98ba-4d7b-9b1d-2760aade541d` | bm25 smoke |
| R4 | 완료 | - | benchmark 결과 확보 |
| D1 | 완료 | - | DebugReport 3종 검증 |

---

## 상세 경로 (요약)

### R2 (GraphRAG)
- dev DB: `reports/r2_graphrag.db`
- openai DB: `reports/r2_graphrag_openai.db`
- stage_events: `reports/r2_graphrag_stage_events.jsonl`, `reports/r2_graphrag_openai_stage_events.jsonl`
- stage_report: `reports/r2_graphrag_stage_report.txt`, `reports/r2_graphrag_openai_stage_report.txt`
- DebugReport: `reports/debug_report_r2_graphrag.md`, `reports/debug_report_r2_graphrag_openai.md`

---

상세 내용과 최신 링크는 `docs/internal/STATUS.md`를 기준으로 합니다.
