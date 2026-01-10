# Open RAG Trace Collector 구성 (Draft)

> 상태: Draft v0.1
> 최종 업데이트: 2026-01-10
> 본 문서는 Open RAG Trace Spec 기준으로 **OTel Collector**를 구성하는 방법을 정리합니다.

## 목적
- 내부/외부 RAG 시스템에서 생성된 트레이스를 표준 OTLP로 수집한다.
- Phoenix 및 분석 스토어로 **동시 export**가 가능하도록 구성한다.
- 표준 필드가 누락되어도 **Collector에서 보완**할 수 있도록 한다.

## 권장 아키텍처
### 1) 직접 수집
```
RAG 서비스 (OTel SDK) --> OTel Collector --> Phoenix / 분석 스토어
```

### 2) 게이트웨이 수집 (내부망/중국 클라우드 대응)
```
RAG 서비스 (OTel SDK) --> 내부 Collector(게이트웨이) --> 외부 Collector --> Phoenix/스토어
```

## 최소 구성 예시 (Phoenix 단일 Export)
`scripts/dev/otel-collector-config.yaml`
```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: "0.0.0.0:4318"
      grpc:
        endpoint: "0.0.0.0:4317"

processors:
  batch:
  attributes/spec_version:
    actions:
      - key: spec.version
        action: insert
        value: "0.1"

exporters:
  otlphttp/phoenix:
    endpoint: "http://host.docker.internal:6006"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [attributes/spec_version, batch]
      exporters: [otlphttp/phoenix]
```

## 멀티 Export 구성 (Phoenix + 파일 백업)
```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: "0.0.0.0:4318"
      grpc:
        endpoint: "0.0.0.0:4317"

processors:
  batch:
  attributes/spec_version:
    actions:
      - key: spec.version
        action: insert
        value: "0.1"

exporters:
  otlphttp/phoenix:
    endpoint: ${env:PHOENIX_OTLP_ENDPOINT}
  file/backup:
    path: /var/log/otel/rag-traces.json

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [attributes/spec_version, batch]
      exporters: [otlphttp/phoenix, file/backup]
```

## 실행 예시 (Docker)
```bash
docker run --rm \
  -p 4317:4317 \
  -p 4318:4318 \
  -e PHOENIX_OTLP_ENDPOINT=http://host.docker.internal:6006 \
  -v "$(pwd)/scripts/dev/otel-collector-config.yaml:/etc/otelcol/config.yaml" \
  otel/opentelemetry-collector:latest \
  --config=/etc/otelcol/config.yaml
```
> `http://localhost:4318/v1/traces` 는 **POST 전용**입니다. 브라우저에서 GET 요청 시 405가 정상이며, 전송 여부는 데모 스크립트나 Collector 로그로 확인하세요.

## 환경 변수 가이드
- `PHOENIX_ENDPOINT`: Phoenix OTLP HTTP 엔드포인트 (클라이언트 직접 전송용, 예: `http://localhost:6006/v1/traces`)
- `PHOENIX_OTLP_ENDPOINT`: Collector exporter가 사용할 Phoenix base URL (**필수**, 예: `http://host.docker.internal:6006`)
- Collector exporter는 `/v1/traces`를 자동으로 붙이므로 **base URL**을 사용합니다.
- Docker 내부에서 host Phoenix에 붙을 때는 `host.docker.internal`을 권장합니다.
- `OTEL_EXPORTER_OTLP_ENDPOINT`: 기본 OTLP 수신/송신 엔드포인트
- `OTEL_RESOURCE_ATTRIBUTES`: `service.name`, `deployment.environment` 등 리소스 메타데이터 지정

## 운영 팁
- **대용량 로그/이벤트**는 `artifact.uri`로 분리 저장하고 Span에는 요약만 남긴다.
- **민감 데이터**는 수집 전 마스킹/해싱 정책을 적용한다.
- 내부망 게이트웨이는 **단방향 outbound**만 허용해도 동작하도록 설계한다.

## 검증
Collector로 수집된 데이터는 아래 스크립트로 최소 스키마를 검사할 수 있다.
```
python scripts/dev/validate_open_rag_trace.py --input traces.json
```

---

## 변경 이력
- 2026-01-10: Draft v0.1 최초 작성
