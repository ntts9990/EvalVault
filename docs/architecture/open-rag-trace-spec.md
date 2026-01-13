# Open RAG Trace Spec (Draft)

> 상태: Draft v0.1
> 최종 업데이트: 2026-01-10
> 이 문서는 작업 중 계속 업데이트되며, 내부/외부 RAG 시스템 통합의 단일 참조 문서로 사용합니다.

## 목적
- 내부/외부 RAG 시스템의 구조를 몰라도 **표준 스펙만으로** 추적/분석이 가능하도록 한다.
- Phoenix 기반 분석 파이프라인과 **호환되는 공통 스키마**를 제공한다.
- 로깅 가능한 모든 데이터를 **손실 없이 수집**하고, 표준 필드는 자동 분석에 활용한다.

## 기본 원칙
- **표준 우선**: W3C TraceContext + OpenTelemetry + OpenInference를 기본 규칙으로 채택한다.
- **구조 불문**: 모듈 구조를 몰라도 `rag.module`만 지정하면 수집 가능해야 한다.
- **데이터 보존**: 표준이 아닌 필드는 `attributes`에 보존하여 분석 가능성을 남긴다.
- **확장 가능**: 버전 필드(`spec.version`)로 점진 확장을 지원한다.

## 범위 / 비범위
- 범위: 트레이스/스팬/이벤트 구조, RAG/LLM 핵심 필드, 로그 수집, 저장/전송 규칙
- 비범위: 개별 제품의 UI/대시보드 디자인, 모델별 프롬프트 템플릿 관리

## 용어
- **Trace**: 하나의 사용자 요청 또는 작업 단위 전체 흐름
- **Span**: Trace 내의 단일 작업 단계(모듈 호출)
- **Event**: Span 내부의 타임스탬프 이벤트(로그/경고/스텝 진행)
- **Attribute**: Span/Resource에 붙는 메타데이터

## 표준 스택
- **W3C TraceContext**: `traceparent`, `tracestate` 전파 규칙
- **OpenTelemetry (OTel)**: 전송 규약(OTLP), 스팬 구조, 리소스 정의
- **OpenInference**: LLM/RAG 의미 규약(모듈/입출력/문서 메타)

## 데이터 흐름 (표준 경로)
```
RAG 서비스 (OTel SDK) ── OTLP ──> OTel Collector ──> Phoenix / 분석 스토어
        |                                       |
        └────────── 로그/이벤트 ────────────────┘
```

## 최소 스키마 (필수)
모든 Span은 아래 필드를 포함해야 한다.

### Span 기본
- `trace_id`, `span_id`, `parent_span_id`
- `name`, `start_time`, `end_time`
- `attributes.rag.module` (필수)

### Resource 기본
- `resource.service.name` (필수)
- `resource.deployment.environment` (예: dev/staging/prod)
- `resource.service.version` (선택)

### 공통 메타
- `attributes.spec.version` (예: `0.1`)
- `attributes.session.id` (있으면 권장)
- `attributes.user.id` (있으면 권장)

## 모듈 구분 규칙 (`rag.module`)
표준 값:
- `ingest`, `chunk`, `embed`, `retrieve`, `rerank`, `prompt`, `llm`, `postprocess`, `eval`, `cache`

커스텀 모듈은 `custom.<name>` 형식을 권장한다.

## 권장 스키마 (RAG/LLM 핵심)
### 입력/출력
- `input.value`: 문자열 또는 JSON
- `output.value`: 문자열 또는 JSON
- 큰 데이터는 `artifact.uri`로 링크하고 본문은 요약만 남긴다.

### Retrieval
- `retrieval.query`
- `retrieval.top_k`
- `retrieval.documents[]`: `{doc_id, score, source, chunk_id, metadata}`

### Rerank
- `rerank.model_name`
- `rerank.scores[]`

### LLM
- `llm.model_name`
- `llm.temperature`
- `llm.token_count.prompt`
- `llm.token_count.completion`
- `llm.token_count.total`
- `llm.latency_ms`

### Evaluation
- `eval.metric_name`
- `eval.score`
- `eval.reference` (필요 시)

## 로그/이벤트 수집
모든 로그는 Span 내부 `events`로 기록한다.
- `event.name`: `log`
- `event.time`
- `event.attributes.log.level`: `debug|info|warn|error`
- `event.attributes.log.message`
- `event.attributes.log.data` (JSON 문자열 권장)

기존 로깅 시스템을 사용할 경우, 로그 라인을 이벤트로 변환하여 붙인다.

## 아티팩트/대용량 데이터
본문이 큰 입력/출력/문서는 다음을 권장한다.
- `artifact.uri`: 파일 또는 오브젝트 스토리지 링크
- `artifact.mime_type`: `text/plain`, `application/json` 등
- `artifact.checksum`: 선택

## OpenTelemetry 속성 제한 대응
- OTel 속성은 **스칼라 또는 스칼라 배열**만 허용한다.
- 객체 배열(예: `retrieval.documents[]`)은 `retrieval.documents_json`처럼 JSON 문자열로 직렬화하거나
  `artifact.uri`로 분리 저장한다.

## EvalVault 레퍼런스 구현
- `src/evalvault/adapters/outbound/tracer/open_rag_trace_adapter.py`: 최소 계측 래퍼
- `src/evalvault/adapters/outbound/tracer/open_rag_log_handler.py`: 기존 로깅 → span event 브리지
- `src/evalvault/adapters/outbound/tracer/open_rag_trace_helpers.py`: 모듈별 속성 빌더
- `src/evalvault/adapters/outbound/tracer/open_rag_trace_decorators.py`: 함수 데코레이터 계측
- `scripts/dev/open_rag_trace_demo.py`: 데모 트레이스 전송
- `scripts/dev/validate_open_rag_trace.py`: 최소 스키마 검증

## 표준 외 데이터 보존 규칙
- 표준 키에 매핑되지 않는 필드는 `custom.*` 네임스페이스에 저장한다.
- 예: `custom.trace_policy`, `custom.cache_hit_rate`

## 전송 방식
1. **OTLP 직접 전송 (권장)**: 서비스 -> Collector
2. **Collector 게이트웨이**: 내부망에서 Collector로 집계 후 외부 전송
3. **로그 브리지/배치 업로드**: 네트워크 제한 시 로그 파일 -> 변환 -> 업로드

## 보안/개인정보
- PII는 수집 전 마스킹/해싱한다.
- 민감 데이터는 `artifact.uri`로 분리 저장하고 액세스 정책을 적용한다.
- 환경별(예: prod) 샘플링 정책을 명시한다.

## 버전 정책
- `attributes.spec.version`으로 버전을 고정한다.
- 호환성 깨짐이 생기면 `MAJOR` 증가, 필드 추가는 `MINOR` 증가를 권장한다.

## 예시 (Span 단위, 축약)
### Retrieval Span
```json
{
  "name": "retrieve_documents",
  "attributes": {
    "spec.version": "0.1",
    "rag.module": "retrieve",
    "retrieval.query": "보험금 지급 조건",
    "retrieval.top_k": 5,
    "retrieval.documents_json": "[{\"doc_id\":\"policy_01\",\"score\":0.83,\"source\":\"kb\",\"chunk_id\":\"c12\"}]"
  }
}
```

### LLM Span
```json
{
  "name": "generate_answer",
  "attributes": {
    "spec.version": "0.1",
    "rag.module": "llm",
    "llm.model_name": "gpt-4o-mini",
    "llm.temperature": 0.2,
    "llm.token_count.prompt": 820,
    "llm.token_count.completion": 230,
    "llm.token_count.total": 1050
  }
}
```

## 실행 체크리스트 (운영 기준)
- [ ] OTel SDK로 `traceparent` 전파 확인
- [ ] 최소 필수 스키마 충족
- [ ] 로그 -> 이벤트 변환 동작
- [ ] 민감 데이터 마스킹 정책 적용
- [ ] Collector에서 Phoenix/분석 스토어 동시 export 확인

---

## 관련 문서
- [open-rag-trace-collector.md](open-rag-trace-collector.md): Collector 구성 예시
- [../guides/OPEN_RAG_TRACE_SAMPLES.md](../guides/OPEN_RAG_TRACE_SAMPLES.md): 최소 계측 샘플

---

## 변경 이력
- 2026-01-10: Draft v0.1 최초 작성
