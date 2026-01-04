# R1 완료 보고서

> 업데이트: 2026-01-07
> 범위: R1 하이브리드 서치 평가 파이프라인 통합

---

## 1. 완료 요약

- `--retriever/--retriever-docs/--retriever-top-k` 옵션을 통해 contexts 자동 생성 경로를 통합
- StageEvent에 retrieval 메타데이터(`doc_ids/scores/top_k`) 기록
- `stage report`에서 retrieval 관련 메트릭 출력 확인
- 유닛/통합 테스트 및 스모크 스크립트 통과 확인

---

## 2. 구현 내역 (핵심 변경)

- CLI 옵션 추가: `evalvault run` / `run-simple` / `run-full`
- retriever 문서 로딩 + dataset contexts 채움 헬퍼 추가
- StageEventBuilder에 retrieval metadata 주입
- 문서/가이드 업데이트
- 스모크 스크립트 추가 및 실행

---

## 3. 검증 및 증거

### 3.1 스모크 스크립트

- 실행 스크립트: `scripts/tests/run_retriever_stage_report_smoke.sh`
- 최신 실행 결과:
  - run_id: `3dcb2b80-1744-4efd-837c-d7aea9348ebe`
  - stage_events: `scratch/r1_smoke/stage_events.jsonl`
  - stage report: `scratch/r1_smoke/stage_report.txt`
  - retrieval metrics: `avg_score/result_count/score_gap` 출력 확인
  - 산출물 위치: `scratch/r1_smoke`

### 3.2 테스트

- `uv run pytest tests/unit/test_run_memory_helpers.py -v`
- `uv run pytest tests/unit/domain/services/test_stage_event_builder.py -v`
- `uv run pytest tests/integration/test_cli_integration.py -v`

---

## 4. 사용자 가이드 반영

- CLI 가이드에 retriever 옵션 추가 (`docs/guides/CLI_GUIDE.md`)
- 개발 가이드에 StageEvent 규칙 및 retriever 자동 생성 규칙 추가 (`docs/internal/reference/DEVELOPMENT_GUIDE.md`)

---

## 5. D1 연동 체크 (요구사항 반영)

- **retrieval_time_ms 기록 경로**: `apply_retriever_to_dataset()`에서 `perf_counter()`로 측정 → StageEvent attributes에 기록
- **doc_ids 정합성**: retriever 문서의 `doc_id`를 우선 사용하며, 없으면 `doc_<index>`로 대체
- **doc_ids ↔ scores 순서**: 동일 순서로 유지(검색 결과 순서 보존)
- **ground_truth doc_id 매핑 확인**: R1 스모크 데이터셋에는 ground_truth doc_id가 없어 직접 검증 불가
  → R4 fixture 기준으로 추가 검증 필요

---

## 6. 미해결/후속 항목

- 디버깅 레이어 확장(입출력 payload 저장, p95 요약 지표)은 R2/R3 범위에서 논의 필요
- GraphRAG 단계의 StageEvent 연동 정의는 R2 범위에서 별도 정리 예정
- StageEvent retrieval 메타데이터 계약 문서화 완료 (`docs/internal/plans/DEBUG_TOOL_PLAN.md`)
- R1은 `retrieval_time_ms`를 best-effort로 기록하며, dataset 기반 contexts에는 미기록 가능
 - `doc_ids`는 retriever 문서의 `doc_id` 우선, 없으면 `doc_<index>`로 대체 (해시 규칙은 R2/R3에서 합의)
