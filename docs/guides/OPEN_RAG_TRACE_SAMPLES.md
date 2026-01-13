# Open RAG Trace 최소 계측 샘플

> 상태: Draft v0.1
> 최종 업데이트: 2026-01-10
> 이 문서는 Open RAG Trace Spec 기준으로 최소 계측을 빠르게 적용하기 위한 샘플을 제공합니다.

## 공통 환경 변수
```bash
# 표준 OTLP 엔드포인트 (HTTP)
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://localhost:6006/v1/traces"

# 서비스 메타데이터
export OTEL_RESOURCE_ATTRIBUTES="service.name=rag-service,deployment.environment=dev"
```

## Collector 실행 (샘플)
```bash
docker run --rm \
  -p 4317:4317 \
  -p 4318:4318 \
  -e PHOENIX_OTLP_ENDPOINT=http://host.docker.internal:6006 \
  -v "$(pwd)/scripts/dev/otel-collector-config.yaml:/etc/otelcol/config.yaml" \
  otel/opentelemetry-collector:latest \
  --config=/etc/otelcol/config.yaml
```
> `http://localhost:4318/v1/traces` 는 **POST 전용**이라 GET 405는 정상입니다.

## Python (OpenTelemetry)
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
```

```python
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:6006/v1/traces")
resource = Resource.create({"service.name": "rag-service", "deployment.environment": "dev"})

trace.set_tracer_provider(TracerProvider(resource=resource))
provider = trace.get_tracer_provider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))

tracer = trace.get_tracer("rag-tracing")

query = "보험금 지급 조건"
from evalvault.adapters.outbound.tracer.open_rag_trace_helpers import build_retrieval_attributes

with tracer.start_as_current_span("retrieve_documents") as span:
    span.set_attribute("spec.version", "0.1")
    span.set_attribute("rag.module", "retrieve")
    attrs = build_retrieval_attributes(query, top_k=5, documents=[{"doc_id": "policy_01"}])
    for key, value in attrs.items():
        span.set_attribute(key, value)
    span.add_event("log", {"log.level": "info", "log.message": "retrieval complete"})
```

## Node.js (TypeScript)
```bash
npm install @opentelemetry/sdk-node @opentelemetry/exporter-trace-otlp-http @opentelemetry/api @opentelemetry/resources
```

```ts
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { Resource } from "@opentelemetry/resources";
import { trace } from "@opentelemetry/api";

const endpoint = process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT ?? "http://localhost:6006/v1/traces";

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({ url: endpoint }),
  resource: new Resource({
    "service.name": "rag-service",
    "deployment.environment": "dev",
  }),
});

await sdk.start();

const tracer = trace.getTracer("rag-tracing");
const span = tracer.startSpan("generate_answer");
span.setAttribute("spec.version", "0.1");
span.setAttribute("rag.module", "llm");
span.setAttribute("llm.model_name", "gpt-4o-mini");
span.setAttribute("llm.temperature", 0.2);
span.addEvent("log", { "log.level": "info", "log.message": "llm complete" });
span.end();

await sdk.shutdown();
```

## 계측 체크리스트
- `rag.module` 필수 입력
- `spec.version` 입력
- 입력/출력은 `input.value`, `output.value`에 기록
- 큰 데이터는 `artifact.uri`로 분리
- 객체 배열은 `*_json` 키로 JSON 직렬화 (예: `retrieval.documents_json`)
- 로그는 `span.add_event("log", ...)`로 이벤트화

## 검증 도구
```bash
python scripts/dev/validate_open_rag_trace.py --input traces.json
```

## 데모 스크립트
`retrieve/llm/eval` 모듈을 데코레이터로 감싸고 로그 이벤트를 자동 수집합니다.
```bash
python3 scripts/dev/open_rag_trace_demo.py --endpoint http://localhost:6006/v1/traces
```
```bash
python3 scripts/dev/open_rag_trace_demo.py --endpoint http://localhost:4318/v1/traces
```

## 내부 시스템 통합 템플릿
```bash
python3 scripts/dev/open_rag_trace_integration_template.py
```

---

## 변경 이력
- 2026-01-10: Draft v0.1 최초 작성
