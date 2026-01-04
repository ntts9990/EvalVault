# EvalVault 내부 작업 상태 보드

> 업데이트: 2026-01-07
> 목적: R1~R4/D1 진행 현황과 산출물 위치를 단일 문서로 집약

---

## 사용 방법

- 최신 상태/요청 사항은 본 문서가 **단일 진실(Single Source of Truth)**입니다.
- 상세 구현/검증 기록은 각 완료/진행 보고서로 이동합니다.
- 상충하는 정보가 발견되면 **본 문서 기준으로 정리**하고, 원문은 보관/정정 표시합니다.
- 문서 통합/최신화 계획은 `docs/internal/plans/DOCS_REFACTOR_PLAN.md`에 기록합니다.

---

## R1~R4/D1 상태 요약

| ID | 상태 | 핵심 산출물 | 다음 액션 |
|----|------|------------|-----------|
| R1 | 완료 | run_id, stage report, stage_events JSONL | - |
| R2 | 완료(샘플 확보) | GraphRAG 구현 + run_id/DB/stage_events | 확장 attributes 예시 확인/정리 |
| R3 | 중간 완료 | performance JSONL + stage_events + DB run + debug report | - |
| R4 | 완료 | 벤치마크 스모크 결과/리포트 | 오케스트레이터 공유 |
| D1 | 구현 완료(샘플 3종 검증 완료) | DebugReportService + R1/R2/R3 리포트 | - |

---

## 상세 상태 및 산출물

### R1 (하이브리드 서치 파이프라인 통합)

- 상태: 완료
- run_id: `3dcb2b80-1744-4efd-837c-d7aea9348ebe`
- DB 경로: `scratch/r1_smoke/evalvault.db`
- stage_events: `scratch/r1_smoke/stage_events.jsonl`
- stage report: `scratch/r1_smoke/stage_report.txt`
- 확인 포인트
  - StageEvent에 `doc_ids/scores/top_k/retrieval_time_ms` 기록
  - `doc_ids`는 retriever doc_id 우선, 없으면 `doc_<index>` fallback
- 요청 사항
  - 없음

참고 문서: `docs/internal/reports/R1_COMPLETION_REPORT.md`

---

### R2 (GraphRAG 검색 최적화)

- 상태: 완료
- run_id: `d60bce6a-ce38-4210-a63e-c8d73d9ecfe7`
- DB 경로: `reports/r2_graphrag.db`
- stage_events: `reports/r2_graphrag_stage_events.jsonl`
- stage report: `reports/r2_graphrag_stage_report.txt`
- DebugReport 샘플:
  - `reports/debug_report_r2_graphrag.md`
  - `reports/debug_report_r2_graphrag.json`
- openai 비교 샘플:
  - run_id: `fd810155-d69f-4c2c-944a-be960a32aa62`
  - DB: `reports/r2_graphrag_openai.db`
  - stage_events: `reports/r2_graphrag_openai_stage_events.jsonl`
  - stage_report: `reports/r2_graphrag_openai_stage_report.txt`
  - DebugReport:
    - `reports/debug_report_r2_graphrag_openai.md`
    - `reports/debug_report_r2_graphrag_openai.json`
- KG fixture: `tests/fixtures/kg/minimal_graph.json`
- smoke 데이터셋 후보:
  - `tests/fixtures/e2e/graphrag_smoke.json`
  - `tests/fixtures/e2e/graphrag_retriever_docs.json`
- 요청 사항
  - 확장 attributes 예시 문서화 완료 (`graph_nodes/graph_edges/community_id/subgraph_size`)

참고 문서: `docs/internal/reports/R2_COMPLETION_REPORT.md`

---

### R3 (대용량 처리 최적화)

- 상태: 중간 완료
- 성능 JSONL: `scripts/perf/r3_smoke_real.jsonl`
- run_id(성능 로그): `r3-smoke-1767502115`
- stage_events 샘플: `scripts/perf/r3_stage_events_sample.jsonl`
  - `duration_ms` 포함, retrieval stage 메타데이터 예시 제공
- evalvault run 샘플
  - run_id: `3fd2f7e6-98ba-4d7b-9b1d-2760aade541d`
  - DB 경로: `reports/r3_bm25.db`
  - stage_events: `reports/r3_bm25_stage_events.jsonl`
  - stage report: `reports/r3_bm25_stage_report.txt`
  - DebugReport 샘플:
    - `reports/debug_report_r3_bm25.md`
    - `reports/debug_report_r3_bm25.json`
  - fixtures:
    - `scripts/perf/r3_evalvault_run_dataset.json`
    - `scripts/perf/r3_retriever_docs.json`
- dense/FAISS run 샘플
  - run_id: `r3-dense-faiss-1767506494`
  - DB 경로: `reports/r3_dense_faiss.db`
  - stage_events: `reports/r3_dense_faiss_stage_events.jsonl`
  - stage report: `reports/r3_dense_faiss_stage_report.txt`
  - DebugReport 샘플:
    - `reports/debug_report_r3_dense_faiss.md`
    - `reports/debug_report_r3_dense_faiss.json`
- Phoenix 로깅 확인 (BM25 스모크)
  - run_id: `d82e84fe-9b56-4b28-bde6-dad0f031f99a`
  - DB 경로: `reports/r3_bm25_phoenix.db`
  - stage_events: `reports/r3_bm25_phoenix_stage_events.jsonl`
  - 실행 로그: `reports/r3_bm25_phoenix_run.log`
  - Phoenix trace: `http://localhost:6006/#/traces/df215755-c975-4012-a6c1-ccb13d360453`
- Langfuse 로깅 확인 (BM25 스모크)
  - run_id: `3ab112c4-f0ae-447d-ab2e-1a4f30e2e114`
  - DB 경로: `reports/r3_bm25_langfuse3.db`
  - stage_events: `reports/r3_bm25_langfuse3_stage_events.jsonl`
  - 실행 로그: `reports/r3_bm25_langfuse3_run.log`
  - Langfuse trace_id: `73eea26251f01a2b352d17842887f98a`
  - Langfuse trace_url: `http://localhost:3000/project/cmjixj06j0006nq07ys4tz9i2/traces/73eea26251f01a2b352d17842887f98a`
  - DebugReport 샘플: `reports/debug_report_r3_bm25_langfuse3.md`, `reports/debug_report_r3_bm25_langfuse3.json`
  - tracker_metadata 저장 확인: `reports/r3_bm25_langfuse3.db`에 trace_id/host/trace_url 저장됨
  - backfill 스크립트: `scripts/perf/backfill_langfuse_trace_url.py` (기존 DB 업데이트 완료)
  - 전체 DB 스캔 완료 (metadata 없는 DB는 자동 스킵)
- 요청 사항
  - Langfuse trace_url/CLI 표시 연동은 P4.1 이후 CLI/로깅 조율 필요

참고 문서: `docs/internal/reports/R3_PROGRESS_REPORT.md`

---

### R4 (벤치마크 doc_id 스키마)

- 상태: 완료
- testset
  - `examples/benchmarks/korean_rag/retrieval_test.json`
- ground_truth fixture
  - `tests/fixtures/benchmark/retrieval_ground_truth_min.json`
  - `tests/fixtures/benchmark/retrieval_ground_truth_multi.json`
- 합의 스키마: `relevant_doc_ids` 우선, `relevant_docs` 레거시 허용
- 스모크 결과 파일
  - `reports/retrieval_benchmark_korean_rag_dev_k5_20260104.json`
  - `reports/retrieval_benchmark_graphrag_korean_rag_dev_k5_20260104.json`
- 참고
  - KG fixture doc_id 정합성 반영: `tests/fixtures/kg/minimal_graph.json`

참고 문서: `docs/internal/reports/R4_PROGRESS_REPORT.md`

---

### D1 (디버깅 레이어)

- 상태: 구현 완료(샘플 3종 검증 완료)
- MVP 범위: DebugReportService + Markdown/JSON 렌더러 (CLI 연결은 P4.1 이후)
- 완료 산출물
  - DebugReportService: `src/evalvault/domain/services/debug_report_service.py`
  - 렌더러: `src/evalvault/adapters/outbound/debug/report_renderer.py`
  - R1 리포트: `reports/debug_report_r1_smoke.md`, `reports/debug_report_r1_smoke.json`
  - R2 리포트: `reports/debug_report_r2_graphrag.md`, `reports/debug_report_r2_graphrag.json`
  - R3 리포트: `reports/debug_report_r3_bm25.md`, `reports/debug_report_r3_bm25.json`
  - R3 (dense/FAISS) 리포트: `reports/debug_report_r3_dense_faiss.md`, `reports/debug_report_r3_dense_faiss.json`
- DebugReport 샘플 재렌더링 완료 (trace_links 포맷 통일)
- 필요 샘플(템플릿)

```
[에이전트] R1 | R2 | R3
[run_id] <uuid or run_id>
[DB] <db_path> 또는 "없음"
[stage_events] <jsonl_path> 또는 "없음"
[stage_report] <출력 로그 경로 또는 캡처 요약>
[fixtures] <fixtures 경로 목록>
[추가 메타데이터 예시] <attributes 샘플 1~2개>
```

참고 문서: `docs/internal/plans/DEBUG_TOOL_PLAN.md`

---

## 충돌/리스크 메모

- retriever 미사용 시 `context_<n>` fallback으로 ground_truth 매핑 불가
- StageEventBuilder 확장 필드 통과 규칙 누락 시 메타데이터 손실 위험

---

## 문서 구조화 원칙

- 상태/요청 사항은 `docs/internal/status/STATUS.md`에만 갱신
- 상세 증거/로그는 각 `*_REPORT.md`에 유지
- 중복 문서는 archive로 이동하고, 본문에서 링크만 유지
- `docs/internal/status/O1_PARALLEL_STATUS.md`는 요약/포인터 문서로 유지
