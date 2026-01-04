# D1 디버깅 레이어 에이전트 가이드

> **작성일**: 2026-01-07
> **목적**: R1~R4/D1이 동일한 메타데이터 계약과 샘플 수집 기준을 공유

---

## 참고 문서

- `docs/internal/status/STATUS.md` (최신 상태/샘플 단일 기준)
- `docs/internal/plans/DEBUG_TOOL_PLAN.md`
- `docs/internal/plans/PARALLEL_WORK_PLAN.md`
- `docs/internal/reports/R1_COMPLETION_REPORT.md`
- `docs/internal/reports/R2_COMPLETION_REPORT.md`
- `docs/internal/reports/R3_PROGRESS_REPORT.md`
- `docs/internal/reports/R4_PROGRESS_REPORT.md`

---

## 공통 계약 (R1~R4, D1 공용)

- StageEvent 최소 필드: `doc_ids`, `scores`, `top_k`, `retrieval_time_ms`
- StageMetricService는 `StageEvent.duration_ms`를 레이턴시 기준으로 사용
- `doc_ids` 순서와 `scores` 순서는 반드시 일치
- `doc_ids`는 dataset `doc_id` 우선, 없으면 `doc_<index>` 대체
- 확장 메타데이터는 `attributes`에 넣고 네이밍은 `snake_case` 유지
- StageEventBuilder가 확장 `attributes`를 누락하지 않도록 확인
- span attributes는 `retriever.*` 접두어 사용 (GraphRAG는 `retriever.graphrag.*`)
- CLI 변경은 P4.1 이후에만 수행

---

## R2/R3 보강 요약 (핵심만)

### R2 (GraphRAG)

- `doc_ids/scores/top_k` 규약 유지
- GraphRAG 추가 메타데이터는 `attributes`로 확장
  - 예: `graph_nodes`, `graph_edges`, `community_id`, `subgraph_size`
- GraphRAG 검색 레이턴시는 `retrieval_time_ms`로 기록
- span attributes 예시: `retriever.graphrag.candidate_multiplier`, `retriever.graphrag.rrf_k`

### R3 (대용량 최적화)

- retrieval 레이턴시를 `duration_ms`로 연결
- 성능 관련 메타데이터 확장
  - `index_build_time_ms`, `batch_size`, `cache_hit`
  - `total_docs_searched`, `index_size`, `faiss_gpu_active`
- JSONL ↔ StageEvent 매핑은 `docs/internal/reports/R3_PROGRESS_REPORT.md` 참고

---

## 에이전트별 준비 사항 (요약)

### R1

- run_id + stage report 로그 제공
- `doc_ids`와 ground_truth `doc_id` 매핑 확인
- `retrieval_time_ms` 측정 경로 기록

### R2

- GraphRAG run_id + stage_events 샘플 확보
- GraphRAG 확장 attributes 예시 수집

### R3

- `duration_ms` 포함 StageEvent 샘플 확보
- 성능 JSONL ↔ StageEvent 매핑 예시 제공

### R4

- ground_truth 스키마/fixture 유지
- 메트릭 유틸/테스트 추가 여부 확인

### D1

- DebugReportService MVP 범위 유지
- 샘플 수집 후 Markdown/JSON 렌더러 구현 착수

> 샘플 확보 현황과 경로는 `docs/internal/status/STATUS.md`에서 최신으로 관리합니다.

---

## D1 MVP 범위 (확정)

### 포함 범위

- 입력: `StoragePort.get_run(run_id)` + `StageStoragePort.list_stage_events/metrics`
- 출력: `DebugReport` (Markdown/JSON)
- 리포트 구성
  - run summary (EvaluationRun 요약)
  - stage summary (StageSummaryService)
  - stage metrics (StageMetricService 결과 또는 저장본)
  - 병목 추정: stage_type별 상위 latency, 누락된 required stage
  - 권장사항: StageMetricGuideService 기반
  - Phoenix trace URL (가능한 경우)

### 제외 범위

- CLI 연결 (`evalvault debug`/`evalvault stage report` 확장)
- Plotly 시각화, CSV export
- payload store/입출력 본문 저장
- p95 지표(리포트 외부 스모크/로그에서 산출)

---

## 샘플 요청 템플릿 (R1~R3 전달용)

```
[에이전트] R1 | R2 | R3
[run_id] <uuid or run_id>
[DB] <db_path> 또는 "없음"
[stage_events] <jsonl_path> 또는 "없음"
[stage_report] <출력 로그 경로 또는 캡처 요약>
[fixtures] <fixtures 경로 목록>
[추가 메타데이터 예시] <attributes 샘플 1~2개>
```

> 예시/확보 현황은 `docs/internal/status/STATUS.md`에서 최신으로 관리합니다.

---

## 산출물 체크리스트 (공유 기준)

| 에이전트 | 필수 산출물 | 예시/위치 |
|---------|-------------|-----------|
| R1 | run_id + stage report | `docs/internal/reports/R1_COMPLETION_REPORT.md` |
| R2 | run_id + KG fixture | `tests/fixtures/` |
| R3 | run_id + JSONL 로그 | `scripts/perf/` |
| R4 | ground_truth fixture | `tests/fixtures/` |
| D1 | DebugReport 샘플(초기) | `docs/internal/plans/DEBUG_TOOL_PLAN.md` |

---

## 충돌 방지 메모

- R2/R3는 `adapters/outbound/kg/`, `adapters/outbound/nlp/` 중심 변경 유지
- `adapters/inbound/cli/`는 P4.1 이후만 수정
- 공유 파일(`pyproject.toml`, `src/evalvault/__init__.py`) 변경 시 사전 조율

---

## 오케스트레이터 운영 포인트

- 진행 순서/상태 업데이트는 `docs/internal/status/STATUS.md`에만 반영
- 계획/설계 변경은 `docs/internal/plans/DEBUG_TOOL_PLAN.md`로 반영
