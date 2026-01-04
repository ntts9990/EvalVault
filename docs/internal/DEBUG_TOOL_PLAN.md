# 디버깅 툴 통합 계획

> **작성일**: 2026-01-07
> **목적**: 각 단계별 데이터 흐름, 레이턴시, 정확도 추적 및 분석

---

## 개요

평가 파이프라인의 각 단계에서 데이터 흐름, 레이턴시, 정확도를 추적하고 분석하는 디버깅 툴을 추가합니다.

---

## 현재 상태

> 최신 진행 상태/샘플 경로는 `docs/internal/STATUS.md`에서 관리합니다.

### 기존 인프라 활용

- ✅ `StageEvent`/`StageMetricService`/`StageSummaryService`: 단계별 이벤트 및 요약
- ✅ 평가 결과(`EvaluationRun`) 저장/조회 포트 존재
- ✅ 레이턴시 측정: `latency_ms` 필드 (StageEvent 채움은 부분적)
- ✅ Phoenix 기반 관측성: OpenTelemetry 트레이싱
- ✅ CLI 명령어: `evalvault stage` 명령어 존재

### 추가 필요 기능

- 🔄 StageEvent 메타데이터 계약 정의 및 R1~R3 연동 (doc_ids, scores, top_k, retrieval_time_ms 등)
- 🔄 평가 결과(EvaluationRun)와 StageEvent 결합 분석(품질/정확도 패턴)
- 🔄 디버깅 리포트(요약/권장사항) 생성 및 내보내기
- 🔄 (선택) 외부 시각화용 CSV/JSON export, Plotly는 후순위

### 병렬 작업 상태 (요약)

- R1: 완료
- R2: 완료
- R3: 중간 완료
- R4: 진행 중
- D1: 계획 확정 (샘플 수집 대기)

---

## R4/D1 연동 준비 체크리스트 (R1~R3)

### 공통 (R1~R3)

- `doc_ids`의 기준 문서 ID 규칙을 공유 (dataset doc_id 우선, 없으면 `doc_<index>`)
- `doc_ids`와 `scores` 배열 길이/순서 일치 보장
- StageEvent `stage_name`/`stage_type` 명명 규칙 합의 (retrieval/graph/rerank 등)
- 디버깅/벤치마크 재현용 `run_id`/샘플 경로는 `docs/internal/STATUS.md`에 기록

### R1 (완료 후 정리)

- retrieval StageEvent 예시(run_id + stage report 출력) D1에 전달
- `retrieval_time_ms`는 없을 경우 누락 가능하지만, 측정 경로를 문서화
- R4 대비: `doc_ids`가 ground_truth doc_id와 동일한지 점검

### R2 (완료, 디버깅 레이어 반영 완료)

- GraphRAG StageEvent 확장 메타데이터 반영
  - `graph_nodes`, `graph_edges`, `community_id`, `subgraph_size`
  - `retrieval_time_ms` (KG 탐색+retrieval 합산 시간)
- GraphRAG 결과의 `doc_ids` 정규화 규칙 문서화 (R2 완료 보고서 반영)
- 샘플 run_id/DB/stage_events 경로는 `docs/internal/STATUS.md`에서 관리

### R3 (중간 완료)

- 성능 최적화 메타데이터 StageEvent 확장 반영
  - `index_build_time_ms`, `batch_size`, `cache_hit`, `faiss_gpu_active`
  - `total_docs_searched`, `index_size`
- retrieval 단계 `retrieval_time_ms` → `duration_ms` 반영 보강 완료
- JSONL 성능 로그와 StageEvent/StageMetric 값 매핑 가이드 제공
- R4 대비: 대용량 데이터셋의 doc_id 안정성/샘플링 기준 명시
- 샘플 JSONL/StageEvent 경로는 `docs/internal/STATUS.md`에서 관리

---

## 아키텍처 설계

### 1. 포트 재사용 (DebugPort 제거)

- `StageStoragePort`로 StageEvent/StageMetric 조회
- `StoragePort`로 EvaluationRun 조회
- Phoenix trace URL은 tracker metadata에서 링크 제공

### 2. 디버깅 리포트 서비스

```python
# domain/entities/debug.py
@dataclass
class DebugReport:
    """Stage/Event + EvaluationRun을 묶은 디버깅 리포트."""

    run_summary: dict[str, Any]
    stage_summary: StageSummary
    stage_metrics: list[StageMetric]
    bottlenecks: list[dict[str, Any]]
    recommendations: list[str]
    phoenix_trace_url: str | None = None
```

```python
# domain/services/debug_report_service.py
class DebugReportService:
    """디버깅 분석 서비스."""

    def build_report(
        self,
        run_id: str,
        storage: StoragePort,
        stage_storage: StageStoragePort,
    ) -> DebugReport:
        # 1. EvaluationRun + StageEvent/StageMetric 수집
        # 2. StageSummary/StageMetric 계산
        # 3. 병목/품질 패턴 추론
        # 4. 리포트 생성
```

### 3. 데이터 흐름 추적

- StageEvent.parent_stage_id 기반으로 트리 구성
- 별도 DataFlowTrace 엔티티는 필요 시점에만 추가

### 4. 레이턴시 분석

- StageEvent.duration_ms 우선 사용
- 누락된 경우 attributes의 retrieval_time_ms/rerank_time_ms를 사용
- EvaluationRun.duration_seconds와 비교해 병목 식별

### 5. 품질/정확도 분석

- EvaluationRun 평균 메트릭/통과율을 기본 품질 지표로 사용
- StageMetricService의 retrieval precision/recall, citation_count 등으로 단계별 품질 보강
- StageMetricGuideService로 개선 권장사항 도출

---

## 구현 계획

### Phase 0: StageEvent 메타데이터 계약 정리 (R1~R3 연동)

**파일**:
- R1~R3 작업 범위 (retriever/graph 단계 메타데이터 채움)

**작업**:
- [x] StageEvent attributes 스키마 문서화 (doc_ids, scores, top_k, retrieval_time_ms 등)
- [x] R1의 retrieval 메타데이터 채움 완료
- [x] R2 확장 필드 구현 완료
- [x] R3 확장 필드 반영 완료 (샘플 검증은 STATUS에서 추적)
- [x] R2 예시 run_id/stage report 샘플 확보 (경로는 STATUS에서 관리)
- [ ] R3 예시 run_id 및 stage report 샘플 확보
- [x] R4 벤치마크 doc_id 규칙과 StageEvent doc_ids 매핑 확인 (`docs/internal/R4_PROGRESS_REPORT.md`)

**R1 기준 계약 (retrieval stage attributes)**
- `doc_ids`: 문서 식별자 배열 (필수)
- `scores`: 문서 점수 배열 (선택)
- `top_k`: 반환 건수 (필수)
- `retrieval_time_ms`: 검색 소요 시간 (R1에서 best-effort 기록, R2/R3에서 보강)

**R2 확장 (GraphRAG)**
- `graph_nodes`: 사용된 노드 수 (선택)
- `graph_edges`: 사용된 엣지 수 (선택)
- `community_id`: 커뮤니티/클러스터 ID (선택)
- `subgraph_size`: 서브그래프 크기 (선택)

**R3 예정 확장 (대용량 최적화)**
- `index_build_time_ms`: 인덱스 구축 시간 (선택)
- `cache_hit`: 캐시 히트 여부 (선택)
- `batch_size`: 배치 크기 (선택)

### Phase 1: 리포트 엔티티/서비스 구현

**파일**:
- `src/evalvault/domain/entities/debug.py` (신규)
- `src/evalvault/domain/services/debug_report_service.py` (신규)

**작업**:
- [ ] `DebugReport` 정의
- [ ] `DebugReportService` 구현 (StageSummary/StageMetric/EvaluationRun 결합)

### Phase 2: 리포트 렌더러 구현

**파일**:
- `src/evalvault/adapters/outbound/debug/report_renderer.py` (신규)

**작업**:
- [ ] Markdown 리포트 생성
- [ ] JSON 리포트 생성
- [ ] Phoenix 링크 포함

### Phase 3: CLI 연결 (P4.1 이후)

**파일**:
- `src/evalvault/adapters/inbound/cli/commands/stage.py` (확장, P4.1 이후)

**작업**:
- [ ] `evalvault stage report <run_id> --export` 옵션 추가
- [ ] 필요 시 `evalvault debug report` 별도 명령어 추가 (후순위)

### Phase 4: 선택 기능

**파일**:
- `src/evalvault/adapters/outbound/debug/exports.py` (선택)

**작업**:
- [ ] CSV/JSON export (외부 분석 도구 연계)
- [ ] Plotly 시각화는 필요 시 `--extra web`와 함께 도입

---

## 충돌 방지

### 수정 가능 영역

- `domain/entities/debug.py` (신규)
- `domain/services/debug_report_service.py` (신규)
- `adapters/outbound/debug/` (신규)
- `docs/internal/DEBUG_TOOL_PLAN.md` (본 문서)

### 조건부/조율 필요

- R1~R3 트랙 파일 (StageEvent 메타데이터 채움)
- `adapters/inbound/cli/commands/stage.py` (P4.1 이후에만)
- Langfuse trace_url/CLI 표시 연동 (P4.1 이후에만)

### 수정 금지 영역

- `adapters/inbound/web/` (P2.2 작업 중)
- `domain/services/evaluator.py` (P3 작업 중)
- `adapters/inbound/cli/commands/run.py` (P4.1 작업 중)
- `tests/` (P5 작업 중, 읽기만)

### 공유 파일 (조율 필요)

- `pyproject.toml` - 의존성 추가 시
- `src/evalvault/__init__.py` - 공개 API 변경 시

---

## 사용 예시

### CLI 사용 (P4.1 이후 적용 예정)

```bash
# 디버깅 리포트 저장
evalvault stage report <run_id> --export debug_report.md
evalvault stage report <run_id> --format json --export debug_report.json
```

### 내부 API 사용 (초기)

```python
from evalvault.domain.services.debug_report_service import DebugReportService

service = DebugReportService()
report = service.build_report(run_id, storage, stage_storage)
```

### 리포트 내용

1. **데이터 흐름**
   - StageEvent 트리 기반 단계 흐름
   - 입력/출력 참조 및 주요 메타데이터

2. **레이턴시 분석**
   - 전체 레이턴시 분해
   - 단계별 레이턴시
   - 병목 지점 식별
   - 개선 권장사항

3. **정확도 분석**
   - EvaluationRun 평균 메트릭/통과율
   - Retrieval precision/recall, citation_count 등 단계 품질
   - 오류 패턴 및 개선 권장사항

4. **관측 링크**
   - Phoenix Trace URL (가능한 경우)

---

## 완료 기준

- [ ] StageEvent 메타데이터 계약 정리 및 R1~R3 연동 완료
- [ ] `DebugReportService` 구현 완료
- [ ] Markdown/JSON 리포트 생성 완료
- [ ] CLI export 옵션 추가 (P4.1 이후)
- [ ] 단위/통합 테스트는 P5 트랙과 조율
- [ ] 문서화 완료

---

## 오케스트레이터 TODO

- 샘플/산출물 경로는 `docs/internal/STATUS.md`에서 최신 유지
- R2/R3 확장 필드 검증 및 샘플 수집 일정 조율
- R4 벤치마크 스키마와 StageEvent doc_id 규칙 충돌 여부 점검
- 디버깅 리포트 MVP 범위 합의 (Markdown/JSON 우선, Plotly 후순위)
- 공유 파일 변경(`pyproject.toml`, `__init__.py`) 발생 시 충돌 조율

---

## 참고 자료

- `docs/internal/PARALLEL_WORK_PLAN.md` - 병렬 작업 계획
- `src/evalvault/domain/entities/stage.py` - StageEvent 엔티티
- `src/evalvault/domain/services/stage_metric_service.py` - StageMetricService
- `src/evalvault/adapters/inbound/cli/commands/stage.py` - Stage CLI 명령어
