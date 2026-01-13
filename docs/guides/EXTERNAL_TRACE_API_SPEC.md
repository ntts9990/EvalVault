# 외부 로그 연동 API 규격 (OpenTelemetry + OpenInference)

> 상태: Draft v0.1
> 목적: 외부 파이프라인이 EvalVault로 **OTel/OpenInference 트레이스를 전송**하고,
>       EvalVault가 이를 **트레이싱/분석 파이프라인으로 전환**하기 위한 규격을 제공합니다.

## 1) 전송 방식 (권장)

### 1.1 OTLP HTTP (Phoenix/Collector)
- **엔드포인트**: `http://<host>:6006/v1/traces`
- **프로토콜**: OpenTelemetry OTLP HTTP
- **포맷**: OTLP Trace (protobuf/json)
- **특징**: Phoenix UI와 자동 연결되며, EvalVault가 Phoenix 메타데이터를 수집/노출할 수 있음

> Collector 사용 시:
> - `http://<collector-host>:4318/v1/traces`로 전송
> - Collector가 Phoenix로 전달

## 2) EvalVault Ingest API (Draft)

> 아래는 외부 시스템이 EvalVault에 직접 전송할 때의 **목표 규격(초안)**입니다.
> 실제 구현은 이 스펙을 기준으로 진행합니다.

### 2.1 `POST /api/v1/ingest/otel-traces`
- **설명**: OpenTelemetry OTLP JSON 기반 Trace 입력
- **Content-Type**: `application/json`
- **요청 본문(요약)**:
  ```json
  {
    "resourceSpans": [
      {
        "resource": { "attributes": [ { "key": "service.name", "value": { "stringValue": "rag-service" } } ] },
        "scopeSpans": [
          {
            "spans": [
              {
                "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                "spanId": "00f067aa0ba902b7",
                "parentSpanId": "",
                "name": "retrieve",
                "startTimeUnixNano": 1730000000000000000,
                "endTimeUnixNano": 1730000000500000000,
                "attributes": [
                  { "key": "rag.module", "value": { "stringValue": "retrieve" } },
                  { "key": "spec.version", "value": { "stringValue": "0.1" } },
                  { "key": "input.value", "value": { "stringValue": "보험금 지급 조건" } },
                  { "key": "retrieval.documents_json", "value": { "stringValue": "[{\"doc_id\":\"policy_01\",\"score\":0.91}]" } }
                ]
              },
              {
                "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
                "spanId": "b9c7c989f97918e1",
                "parentSpanId": "00f067aa0ba902b7",
                "name": "llm",
                "startTimeUnixNano": 1730000000600000000,
                "endTimeUnixNano": 1730000002000000000,
                "attributes": [
                  { "key": "rag.module", "value": { "stringValue": "llm" } },
                  { "key": "spec.version", "value": { "stringValue": "0.1" } },
                  { "key": "input.value", "value": { "stringValue": "보험금 지급 조건을 요약해줘" } },
                  { "key": "output.value", "value": { "stringValue": "보험금 지급 조건은 약관과 보장 범위에 따릅니다." } },
                  { "key": "llm.model_name", "value": { "stringValue": "gemma3:1b" } },
                  { "key": "llm.temperature", "value": { "doubleValue": 0.2 } }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
  ```

### 2.2 `POST /api/v1/ingest/stage-events`
- **설명**: Stage Event(JSONL) 기반 입력
- **Content-Type**: `application/jsonl`
- **요청 본문(줄 단위 JSON)**:
  ```jsonl
  {"run_id":"run_20260103_001","stage_id":"stg_sys_01","stage_type":"system_prompt","stage_name":"system_prompt_v1","duration_ms":18,"attributes":{"prompt_id":"sys-01"}}
  {"run_id":"run_20260103_001","stage_id":"stg_input_01","parent_stage_id":"stg_sys_01","stage_type":"input","stage_name":"user_query","duration_ms":6,"attributes":{"query":"보험금 지급 조건","language":"ko"}}
  {"run_id":"run_20260103_001","stage_id":"stg_retrieval_01","parent_stage_id":"stg_input_01","stage_type":"retrieval","stage_name":"hybrid_retriever","duration_ms":120,"attributes":{"top_k":3,"doc_ids":["doc-1","doc-7","doc-9"],"scores":[0.91,0.72,0.45]}}
  ```

### 2.3 응답 예시 (성공/실패)

**성공(OTLP)**
```json
{
  "status": "ok",
  "ingested": 12,
  "trace_ids": ["4bf92f3577b34da6a3ce929d0e0e4736"],
  "message": "ingested otlp traces"
}
```

**성공(Stage Events)**
```json
{
  "status": "ok",
  "run_id": "run_20260103_001",
  "ingested": 5,
  "message": "stored stage events"
}
```

**실패(공통)**
```json
{
  "status": "error",
  "error_code": "invalid_payload",
  "message": "missing required attribute: rag.module"
}
```

### 2.4 HTTP 상태 코드 규칙
- `200 OK`: 정상 수집
- `400 Bad Request`: JSON/JSONL 파싱 실패
- `422 Unprocessable Entity`: 필수 필드 누락 또는 스키마 불일치
- `500 Internal Server Error`: 저장/파이프라인 내부 오류

## 3) OpenInference 필수/권장 속성

| 구분 | 키 | 설명 |
|---|---|---|
| 필수 | `rag.module` | 단계 유형(`retrieve`, `rerank`, `llm`, `eval` 등) |
| 필수 | `spec.version` | Open RAG Trace 스펙 버전 |
| 권장 | `input.value` | 입력 텍스트 |
| 권장 | `output.value` | 출력 텍스트 |
| 권장 | `llm.model_name` | 사용한 LLM 모델명 |
| 권장 | `retrieval.documents_json` | 검색 문서 JSON 문자열 |

> 전체 규격은 `docs/architecture/open-rag-trace-spec.md` 참고

## 4) 예시 파일

- OTLP/OpenInference 샘플: `docs/templates/otel_openinference_trace_example.json`
- Stage Event 샘플: `examples/stage_events.jsonl`
- RAGAS 데이터셋 샘플: `docs/templates/ragas_dataset_example_ko90_en10.json`

## 5) 분석 전환 규칙(요약)

- **RAGAS 형식 데이터셋**이면 `evalvault run` 기반 평가/분석
- **OTel/OpenInference 트레이스**는 Phoenix로 트레이싱 연결
- **비정형 로그(Stage Event)**는 `stage ingest` → `stage summary` → 분석 모듈로 전환
