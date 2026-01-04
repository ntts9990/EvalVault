# D1 디버깅 레이어 R2/R3 업데이트 정리

> **작성일**: 2026-01-07
> **작성자**: D1 에이전트
> **범위**: R2(GraphRAG), R3(대용량 최적화) 디버깅 레이어 반영 가이드

---

## 배경 요약

- R1에서 retriever 옵션/StageEvent 연동이 완료됨.
- R2/R3는 디버깅 레이어의 메타데이터 계약과 레이턴시 기록을 보강해야 함.
- CLI 추가 변경은 P4.1 트랙 이후로 미룸(충돌 방지).

---

## R1 상태 확인 (기준선)

- `StageEvent`에 `doc_ids/scores/top_k`가 기록됨.
- `retrieval_time_ms`가 best-effort로 기록됨 (retriever 경로에서 측정).
- `stage report`에서 retrieval 관련 메트릭 출력 확인.
- smoke 스크립트로 스테이지/메트릭 검증 완료.
- ground_truth doc_id 매핑 검증은 R4 fixture 기준으로 진행 필요.

참고:
- `src/evalvault/domain/services/stage_event_builder.py`
- `src/evalvault/adapters/inbound/cli/commands/run_helpers.py`
- `scripts/tests/run_retriever_stage_report_smoke.sh`
- `docs/internal/R1_COMPLETION_REPORT.md`

---

## R2 디버깅 레이어 보강 (GraphRAG)

### 현재 상태

- GraphRAG retriever/KG builder 구현 및 `evalvault run --retriever graphrag` 연결 완료.
- StageEvent 확장 메타데이터/레이턴시 기록까지 반영 완료.

참고:
- `src/evalvault/adapters/outbound/kg/graph_rag_retriever.py`
- `src/evalvault/adapters/outbound/kg/parallel_kg_builder.py`
- `tests/unit/adapters/outbound/kg/test_graph_rag_retriever.py`
- `docs/internal/R2_COMPLETION_REPORT.md`

### R2가 해야 할 디버깅 레이어 반영

- **Retrieval 메타데이터 계약 준수**
  - `doc_ids`, `scores`, `top_k`는 기존 규약 유지
- GraphRAG 추가 메타데이터는 `attributes`에 확장
  (예: `graph.hops`, `graph.nodes`, `graph.edges`, `rerank.method`)
- **레이턴시 기록**
  - GraphRAG search 타이밍 측정 → `retrieval_time_ms`로 기록
- **Observability(스팬)**
  - `retriever.graphrag.*` 형태로 span attribute 추가
  - 예: `retriever.graphrag.candidate_multiplier`, `retriever.graphrag.rrf_k`

### 충돌 회피 가이드

- R2 트랙은 `adapters/outbound/kg/` 중심 변경 유지.
- CLI 추가 변경은 P4.1 이후/조율 사항으로 남겨둠.

---

## R3 업데이트 반영 (대용량 최적화)

### 현재 상태

- 성능 스모크 스크립트에서 p95/p99까지 측정 가능.
- `retrieval_time_ms` → `duration_ms` 반영 경로 보강 완료.
- 성능 attributes pass-through 및 span 보강 완료.
- JSONL ↔ StageEvent 매핑 가이드 추가 완료 (`docs/internal/R3_PROGRESS_REPORT.md`).

참고:
- `scripts/perf/r3_dense_smoke.py`

### R3 반영 완료 항목

- **StageEvent 레이턴시 연결**
  - `StageMetricService`는 `StageEvent.duration_ms` 기반으로 latency 메트릭 계산함.
  - retrieval 타이밍을 `duration_ms`에 반영하도록 보강 완료.
- **메타데이터 확장**
  - `attributes`에 `total_docs_searched`, `index_size`, `cache_hit` 등 추가.
- **스팬 보강**
  - Dense retriever span에 성능 attributes 기록 완료.

참고:
- `src/evalvault/domain/services/stage_metric_service.py`
- `src/evalvault/adapters/outbound/nlp/korean/dense_retriever.py`
- `src/evalvault/adapters/outbound/nlp/korean/hybrid_retriever.py`

---

## 공통 우선 과제 (R2/R3 공통)

1) **StageEvent 메타데이터 계약 확정**
   - 최소 필드: `doc_ids`, `scores`, `top_k`, `retrieval_time_ms`
   - `doc_ids`는 dataset `doc_id` 우선, 없으면 `doc_<index>` 대체
2) **StageEventBuilder 통과 규칙 확장**
   - 현재는 `doc_ids/scores/top_k/retrieval_time_ms`만 통과 → 확장 메타데이터 보존 필요
3) **p95 요약 지표**
   - StageSummary는 평균 중심이므로, p95는 스모크/리포트에서 별도 계산 유지

---

## 전달용 체크리스트 (에이전트 공유)

### R2 체크리스트

- [x] GraphRAG retrieval 타이밍 측정 → `retrieval_time_ms` 기록
- [x] `doc_ids/scores/top_k` 필드 유지
- [x] GraphRAG 메타데이터를 attributes에 추가
- [x] span attributes 보강

### R3 체크리스트

- [x] 대용량 경로에서 StageEvent `duration_ms` 채우기
- [x] 검색/캐시/인덱스 관련 메타데이터 추가
- [x] span attributes에 레이턴시/캐시 지표 추가
- [x] JSONL ↔ StageEvent 매핑 가이드 정리

---

## 참고 문서

- `docs/internal/DEBUG_TOOL_PLAN.md`
- `docs/internal/PARALLEL_WORK_PLAN.md`
