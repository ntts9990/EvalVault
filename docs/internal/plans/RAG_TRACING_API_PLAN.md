# RAG 시스템 실시간 트레이싱 API 계획

> **작성일**: 2026-01-07
> **목적**: 외부 RAG 시스템에서 실시간으로 StageEvent를 전송하고 디버깅할 수 있는 API 및 SDK 제공

---

## 개요

현재 EvalVault는 평가 실행 시점에만 StageEvent를 수집합니다. 실제 운영 중인 RAG 시스템(LangChain, LlamaIndex, Custom RAG 등)에서 실시간으로 트레이싱 데이터를 전송하고 분석할 수 있도록 **FastAPI 엔드포인트**와 **Python SDK**를 추가합니다.

---

## 현재 상태

### 기존 인프라 활용

- ✅ `StageEvent` 엔티티: 유연한 구조 (`stage_type` 문자열, `attributes` dict)
- ✅ `StageStoragePort`: StageEvent 저장/조회 인터페이스
- ✅ `StageMetricService`: 자동 메트릭 계산
- ✅ `StageSummaryService`: 단계별 요약 생성
- ✅ `DebugReportService`: 디버깅 리포트 생성
- ✅ CLI ingestion: `evalvault stage ingest events.jsonl` (파일 기반)

### 제한사항

- ❌ 실시간 API 부재: RAG 시스템에서 직접 전송 불가
- ❌ Python SDK 부재: RAG 시스템에 통합하기 어려움
- ⚠️ 범용 메트릭 계산 미흡: 알 수 없는 `stage_type`에 대한 기본 메트릭만 제공

---

## 요구사항

### 1. 실시간 트레이싱

- RAG 시스템이 HTTP API로 StageEvent를 실시간 전송
- 배치 전송 지원 (여러 이벤트 한 번에)
- 비동기 처리로 성능 최적화

### 2. Python SDK

- 간단한 API로 StageEvent 기록
- 컨텍스트 매니저로 자동 타이밍 측정
- RAG 시스템별 통합 예시 제공

### 3. 유연한 모듈 지원

- RAG 시스템 구조를 미리 알 필요 없음
- 선택적 모듈만 트레이싱 가능
- 알 수 없는 `stage_type`도 유용한 메트릭 자동 계산

### 4. 기존 시스템과의 호환성

- 기존 CLI ingestion 유지
- 기존 StageEvent 스키마 호환
- 기존 분석 도구(DebugReport 등) 재사용

---

## 아키텍처 설계

### 1. 전체 구조

```
┌─────────────────────────────────────────┐
│      RAG 시스템 (다양한 구조)              │
│  - LangChain                            │
│  - LlamaIndex                           │
│  - Custom RAG                           │
└──────────────┬──────────────────────────┘
               │
               │ StageEvent 전송
               │ (선택적 모듈만)
               ▼
┌─────────────────────────────────────────┐
│   EvalVault 트레이싱 레이어               │
│                                          │
│  1. FastAPI /api/stage/events          │
│  2. Python SDK (evalvault-sdk)          │
│  3. JSONL 파일 ingestion (기존)         │
│  4. OpenTelemetry (Phoenix, 기존)       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   StageEvent 저장소                      │
│   - SQLiteStorageAdapter (기존)         │
│   - PostgreSQLStorageAdapter (기존)      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   자동 분석 & 디버깅 (기존)              │
│   - StageMetricService                  │
│   - DebugReportService                  │
│   - StageMetricGuideService             │
└─────────────────────────────────────────┘
```

### 2. FastAPI 엔드포인트

**파일**: `src/evalvault/adapters/inbound/api/routers/stage.py` (신규)

**엔드포인트**:

1. `POST /api/stage/events` - 단일/배치 StageEvent 전송
2. `GET /api/stage/events/{run_id}` - StageEvent 조회
3. `GET /api/stage/metrics/{run_id}` - StageMetric 조회
4. `GET /api/stage/summary/{run_id}` - StageSummary 조회
5. `GET /api/stage/debug/{run_id}` - DebugReport 조회

### 3. Python SDK

**패키지**: `evalvault-sdk` (별도 패키지 또는 `evalvault` 내부 모듈)

**주요 클래스**:

- `StageTracer`: StageEvent 기록 헬퍼
- `StageContext`: 컨텍스트 매니저로 자동 타이밍
- `StageEventBuilder`: 편의 빌더 클래스

### 4. 범용 메트릭 계산 강화

**파일**: `src/evalvault/domain/services/stage_metric_service.py` (수정)

- 알 수 없는 `stage_type`에 대해 `attributes`에서 자동으로 숫자 값 추출
- 커스텀 메트릭 이름 패턴 지원

---

## 구현 계획

### Phase 1: FastAPI 엔드포인트 구현

**파일**:
- `src/evalvault/adapters/inbound/api/routers/stage.py` (신규)
- `src/evalvault/adapters/inbound/api/main.py` (수정: router 등록)

**작업**:
- [ ] `POST /api/stage/events` 엔드포인트 구현
  - 단일 이벤트: `{"run_id": "...", "stage_type": "...", ...}`
  - 배치 이벤트: `{"events": [...]}`
  - 유효성 검증 (`StageEvent.from_dict()`)
  - 저장 및 응답
- [ ] `GET /api/stage/events/{run_id}` 엔드포인트 구현
  - 필터링 옵션 (`stage_type`, `limit`)
  - JSON 응답
- [ ] `GET /api/stage/metrics/{run_id}` 엔드포인트 구현
- [ ] `GET /api/stage/summary/{run_id}` 엔드포인트 구현
- [ ] `GET /api/stage/debug/{run_id}` 엔드포인트 구현
- [ ] 에러 핸들링 및 로깅
- [ ] API 문서화 (OpenAPI/Swagger)

**의존성**:
- 기존 `StageStoragePort` 구현체 재사용
- 기존 `DebugReportService` 재사용

**테스트**:
- 단위 테스트: 각 엔드포인트
- 통합 테스트: 실제 DB 연동

---

### Phase 2: Python SDK 구현

**파일**:
- `src/evalvault/sdk/__init__.py` (신규)
- `src/evalvault/sdk/tracer.py` (신규)
- `src/evalvault/sdk/context.py` (신규)
- `src/evalvault/sdk/client.py` (신규)

**작업**:
- [ ] `StageTracer` 클래스 구현
  - `record_stage()`: StageEvent 기록
  - `record_batch()`: 배치 기록
  - HTTP 클라이언트 또는 직접 DB 저장 옵션
- [ ] `StageContext` 컨텍스트 매니저 구현
  - 자동 `started_at`/`finished_at` 기록
  - 자동 `duration_ms` 계산
  - 예외 처리 시 `status="error"` 기록
- [ ] `StageEventBuilder` 편의 빌더 구현
- [ ] 설정 관리 (API URL, DB 경로 등)
- [ ] 예외 처리 및 재시도 로직
- [ ] SDK 문서화 및 예시

**사용 예시**:

```python
from evalvault.sdk import StageTracer

tracer = StageTracer(run_id="rag-001", api_url="http://localhost:8000")

# 단일 이벤트 기록
tracer.record_stage(
    stage_type="query_rewrite",
    attributes={"original": "...", "rewritten": "..."},
    duration_ms=45.2
)

# 컨텍스트 매니저로 자동 타이밍
with tracer.stage("retrieval", parent_stage_id=parent_id) as stage:
    # RAG 시스템의 retrieval 로직
    results = retrieve(query)
    stage.attributes = {
        "doc_ids": [r.id for r in results],
        "scores": [r.score for r in results],
        "top_k": len(results)
    }
```

---

### Phase 3: 범용 메트릭 계산 강화

**파일**:
- `src/evalvault/domain/services/stage_metric_service.py` (수정)

**작업**:
- [ ] `_generic_metrics()` 메서드 추가
  - 알 수 없는 `stage_type`에 대한 범용 메트릭 계산
  - `attributes`에서 숫자 값 자동 추출
  - 메트릭 이름: `{stage_type}.{attribute_key}`
- [ ] 커스텀 메트릭 패턴 지원
  - 설정 파일로 메트릭 추출 규칙 정의 (선택)
- [ ] 기존 특화 메트릭과의 충돌 방지
- [ ] 테스트 추가

**예시**:

```python
# stage_type="custom_module"인 경우
# attributes={"throughput": 100, "error_rate": 0.05}
# → 자동으로 다음 메트릭 생성:
# - custom_module.throughput: 100.0
# - custom_module.error_rate: 0.05
```

---

### Phase 4: RAG 시스템 통합 예시

**파일**:
- `docs/guides/RAG_TRACING_INTEGRATION.md` (신규)
- `examples/rag_tracing/` (신규 디렉토리)

**작업**:
- [ ] LangChain 통합 예시
  - Callback handler 구현
  - 주요 단계 자동 트레이싱
- [ ] LlamaIndex 통합 예시
  - Callback handler 구현
- [ ] Custom RAG 통합 예시
  - 수동 트레이싱 패턴
- [ ] 통합 가이드 문서 작성

**예시 구조**:

```
examples/rag_tracing/
├── langchain_example.py
├── llamaindex_example.py
├── custom_rag_example.py
└── README.md
```

---

### Phase 5: 성능 최적화 및 모니터링

**작업**:
- [ ] 배치 전송 최적화
  - 큐잉 및 배치 처리
  - 비동기 저장
- [ ] API 레이트 리밋 (선택)
- [ ] 메트릭 수집 (API 호출 수, 레이턴시 등)
- [ ] 로깅 및 모니터링

---

## API 스펙

### POST /api/stage/events

**요청 본문** (단일 이벤트):

```json
{
  "run_id": "rag-001",
  "stage_type": "query_rewrite",
  "stage_name": "query_rewriter_v2",
  "parent_stage_id": "input-123",
  "status": "success",
  "started_at": "2026-01-07T10:00:00Z",
  "finished_at": "2026-01-07T10:00:00.045Z",
  "duration_ms": 45.2,
  "attributes": {
    "original": "보험 보장금액은?",
    "rewritten": "보험 보장금액이 얼마인지 알려주세요"
  },
  "metadata": {
    "model": "gpt-4",
    "temperature": 0.7
  },
  "trace_id": "trace-456",
  "span_id": "span-789"
}
```

**요청 본문** (배치 이벤트):

```json
{
  "events": [
    { "run_id": "rag-001", "stage_type": "input", ... },
    { "run_id": "rag-001", "stage_type": "retrieval", ... }
  ]
}
```

**응답**:

```json
{
  "stored": 1,
  "run_id": "rag-001",
  "stage_ids": ["stage-abc-123"]
}
```

**에러 응답**:

```json
{
  "error": "Invalid stage event",
  "details": "stage_type is required",
  "index": 0
}
```

### GET /api/stage/events/{run_id}

**쿼리 파라미터**:
- `stage_type` (선택): 필터링
- `limit` (선택, 기본값: 200): 최대 반환 개수

**응답**:

```json
{
  "run_id": "rag-001",
  "events": [
    {
      "stage_id": "stage-abc-123",
      "stage_type": "input",
      "stage_name": "user_query",
      "status": "success",
      "duration_ms": 12.5,
      "started_at": "2026-01-07T10:00:00Z",
      "attributes": { "query": "..." }
    }
  ],
  "total": 5,
  "returned": 5
}
```

### GET /api/stage/debug/{run_id}

**응답**: `DebugReport` JSON (기존 `DebugReportService` 재사용)

---

## 사용 예시

### 1. FastAPI 직접 호출

```python
import requests

# 단일 이벤트 전송
response = requests.post(
    "http://localhost:8000/api/stage/events",
    json={
        "run_id": "rag-001",
        "stage_type": "query_rewrite",
        "attributes": {"original": "...", "rewritten": "..."},
        "duration_ms": 45.2
    }
)
```

### 2. Python SDK 사용

```python
from evalvault.sdk import StageTracer

tracer = StageTracer(
    run_id="rag-001",
    api_url="http://localhost:8000"
)

# 단일 이벤트
tracer.record_stage(
    stage_type="query_rewrite",
    attributes={"original": "...", "rewritten": "..."},
    duration_ms=45.2
)

# 컨텍스트 매니저
with tracer.stage("retrieval", parent_stage_id=parent_id) as stage:
    results = retrieve(query)
    stage.attributes = {
        "doc_ids": [r.id for r in results],
        "scores": [r.score for r in results]
    }
```

### 3. LangChain 통합

```python
from langchain.callbacks import BaseCallbackHandler
from evalvault.sdk import StageTracer

class EvalVaultTracer(BaseCallbackHandler):
    def __init__(self, run_id: str):
        self.tracer = StageTracer(run_id=run_id)
        self.current_stage = None

    def on_retriever_start(self, query: str, **kwargs):
        self.current_stage = self.tracer.stage("retrieval")
        self.current_stage.__enter__()
        self.current_stage.attributes["query"] = query

    def on_retriever_end(self, documents, **kwargs):
        if self.current_stage:
            self.current_stage.attributes["doc_ids"] = [d.id for d in documents]
            self.current_stage.__exit__(None, None, None)
```

---

## 마이그레이션 가이드

### 기존 JSONL ingestion 사용자

기존 방식은 계속 지원됩니다:

```bash
# 기존 방식 (계속 사용 가능)
evalvault stage ingest events.jsonl --db eval.db

# 새로운 방식 (실시간)
curl -X POST http://localhost:8000/api/stage/events \
  -H "Content-Type: application/json" \
  -d @events.json
```

### 점진적 마이그레이션

1. **Phase 1**: FastAPI 엔드포인트만 추가 (기존 시스템 영향 없음)
2. **Phase 2**: Python SDK 추가 (선택적 사용)
3. **Phase 3**: 범용 메트릭 강화 (기존 메트릭과 호환)
4. **Phase 4**: 통합 예시 제공 (참고용)

---

## 충돌 방지

### 수정 가능 영역

- `src/evalvault/adapters/inbound/api/routers/stage.py` (신규)
- `src/evalvault/adapters/inbound/api/main.py` (router 등록만)
- `src/evalvault/sdk/` (신규 디렉토리)
- `src/evalvault/domain/services/stage_metric_service.py` (범용 메트릭 추가)
- `docs/guides/RAG_TRACING_INTEGRATION.md` (신규)
- `examples/rag_tracing/` (신규)

### 조건부/조율 필요

- `pyproject.toml`: SDK 의존성 추가 시 (HTTP 클라이언트 등)
- `src/evalvault/__init__.py`: SDK 공개 API 노출 시

### 수정 금지 영역

- `src/evalvault/domain/entities/stage.py`: StageEvent 스키마 변경 없음
- `src/evalvault/ports/outbound/stage_storage_port.py`: 포트 인터페이스 변경 없음
- 기존 CLI 명령어: `evalvault stage ingest` 등 유지

---

## 완료 기준

### Phase 1 (FastAPI)

- [ ] `POST /api/stage/events` 엔드포인트 구현 및 테스트
- [ ] `GET /api/stage/events/{run_id}` 엔드포인트 구현 및 테스트
- [ ] `GET /api/stage/metrics/{run_id}` 엔드포인트 구현 및 테스트
- [ ] `GET /api/stage/summary/{run_id}` 엔드포인트 구현 및 테스트
- [ ] `GET /api/stage/debug/{run_id}` 엔드포인트 구현 및 테스트
- [ ] OpenAPI 문서 자동 생성 확인
- [ ] 통합 테스트 (실제 DB 연동)

### Phase 2 (Python SDK)

- [ ] `StageTracer` 클래스 구현 및 테스트
- [ ] `StageContext` 컨텍스트 매니저 구현 및 테스트
- [ ] SDK 문서화 및 예시 코드
- [ ] 배포 준비 (패키징 또는 모듈 통합)

### Phase 3 (범용 메트릭)

- [ ] `_generic_metrics()` 메서드 구현 및 테스트
- [ ] 알 수 없는 `stage_type`에 대한 메트릭 자동 계산 검증
- [ ] 기존 특화 메트릭과의 충돌 없음 확인

### Phase 4 (통합 예시)

- [ ] LangChain 통합 예시 작성
- [ ] LlamaIndex 통합 예시 작성
- [ ] Custom RAG 통합 예시 작성
- [ ] 통합 가이드 문서 작성

### Phase 5 (최적화)

- [ ] 배치 처리 최적화
- [ ] 성능 테스트
- [ ] 모니터링 도구 연동

---

## 참고 자료

- `docs/internal/plans/DEBUG_TOOL_PLAN.md` - 디버깅 툴 계획
- `src/evalvault/domain/entities/stage.py` - StageEvent 엔티티
- `src/evalvault/domain/services/stage_metric_service.py` - StageMetricService
- `src/evalvault/adapters/inbound/cli/commands/stage.py` - Stage CLI 명령어
- `src/evalvault/adapters/inbound/api/main.py` - FastAPI 앱 진입점
- `docs/internal/reference/DEVELOPMENT_GUIDE.md` - 개발 가이드 (Stage 섹션)

---

## 향후 확장 가능성

### 1. 실시간 스트리밍

- WebSocket 지원으로 실시간 이벤트 스트리밍
- 클라이언트가 실시간으로 StageEvent 수신

### 2. 분산 트레이싱

- OpenTelemetry 표준 완전 지원
- 분산 시스템 간 트레이스 연결

### 3. 자동 계측

- LangChain/LlamaIndex 자동 계측 플러그인
- 데코레이터 기반 자동 트레이싱

### 4. 클라우드 통합

- AWS X-Ray, Google Cloud Trace 연동
- SaaS 트레이싱 서비스 연동

---

## 오케스트레이터 TODO

- FastAPI 엔드포인트 구현 범위 합의 (Phase 1)
- Python SDK 패키징 전략 결정 (별도 패키지 vs 모듈 통합)
- 범용 메트릭 계산 규칙 문서화
- RAG 시스템 통합 예시 우선순위 결정
- 성능 요구사항 정의 (TPS, 레이턴시 목표)
