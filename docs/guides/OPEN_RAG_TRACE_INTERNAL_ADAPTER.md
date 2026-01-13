# Open RAG Trace 내부 시스템 최소 계측 래퍼

> 상태: Draft v0.1
> 최종 업데이트: 2026-01-10
> 이 문서는 내부 RAG 시스템에 빠르게 붙일 수 있는 **최소 계측 래퍼** 가이드를 제공합니다.

## 목표
- 내부 구조를 몰라도 `rag.module` 중심으로 트레이스를 생성한다.
- 기존 로깅을 span event로 흡수한다.
- 표준 스키마에 없는 필드는 `custom.*`로 보존한다.

## 설계 원칙
- **얕은 래핑**: 모듈 호출부에만 최소 계측을 추가한다.
- **관용적 매핑**: 기존 로그/메트릭을 최대한 그대로 담는다.
- **표준 보장**: `spec.version` + `rag.module`은 항상 기록한다.

## 공통 규약 (필수)
- `spec.version`: `"0.1"`
- `rag.module`: `ingest|chunk|embed|retrieve|rerank|prompt|llm|postprocess|eval|cache`
- 큰 데이터는 `artifact.uri`로 분리 저장
- 로그는 span event로 기록
- 객체 배열은 JSON 문자열로 직렬화 (`*_json`)

## EvalVault 제공 래퍼 사용 (Python)
```python
from evalvault.adapters.outbound.tracer.open_rag_trace_adapter import OpenRagTraceAdapter
from evalvault.adapters.outbound.tracer.open_rag_trace_helpers import build_retrieval_attributes

adapter = OpenRagTraceAdapter()

attrs = build_retrieval_attributes("보험금 지급 조건", top_k=5, documents=[{"doc_id": "policy_01"}])

with adapter.span("retrieve_documents", "retrieve", attrs):
    # ... 실제 검색 수행 ...
    pass
```
> `opentelemetry-sdk`/exporter가 설치되지 않은 경우 `OpenRagTraceAdapter`는 no-op으로 동작합니다.
> 실제 전송을 위해서는 OTel 초기화와 exporter 설정이 필요합니다.

## 데코레이터로 간단 적용 (Python)
```python
from evalvault.adapters.outbound.tracer.open_rag_trace_decorators import trace_module
from evalvault.adapters.outbound.tracer.open_rag_trace_helpers import build_llm_attributes

@trace_module("llm", attributes_builder=lambda prompt: build_llm_attributes("gpt-4o-mini"))
def generate_answer(prompt: str) -> str:
    # ... 실제 생성 수행 ...
    return "answer"
```

## 기존 로깅 흡수 (Python)
```python
import logging
from evalvault.adapters.outbound.tracer.open_rag_log_handler import install_open_rag_log_handler

logger = logging.getLogger("rag")
install_open_rag_log_handler(logger)
```
> 로그 핸들러는 **현재 활성 span**에 이벤트를 붙입니다.
> `adapter.span(...)` 또는 `@trace_module`로 span 컨텍스트를 활성화해야 로그가 수집됩니다.

## 통합 템플릿 (샘플 파일)
실제 내부 파이프라인에 붙일 때는 아래 템플릿을 시작점으로 사용하세요.
```
scripts/dev/open_rag_trace_integration_template.py
```

## Python 래퍼 (예시)
```python
from opentelemetry import trace

class RagTraceAdapter:
    def __init__(self, tracer=None, spec_version: str = "0.1"):
        self.tracer = tracer or trace.get_tracer("open-rag-trace")
        self.spec_version = spec_version

    def start_span(self, name: str, module: str, **attrs):
        span = self.tracer.start_span(name)
        span.set_attribute("spec.version", self.spec_version)
        span.set_attribute("rag.module", module)
        for key, value in attrs.items():
            span.set_attribute(key, value)
        return span

    @staticmethod
    def add_log(span, level: str, message: str, **data):
        span.add_event("log", {"log.level": level, "log.message": message, "log.data": data})

    @staticmethod
    def add_custom(span, **attrs):
        for key, value in attrs.items():
            span.set_attribute(f"custom.{key}", value)


def retrieve_documents(adapter: RagTraceAdapter, query: str, top_k: int):
    span = adapter.start_span(
        "retrieve_documents",
        "retrieve",
        **{
            "retrieval.query": query,
            "retrieval.top_k": top_k,
        },
    )
    try:
        adapter.add_log(span, "info", "retrieval start", query=query)
        # ... 실제 검색 수행 ...
        documents = []
        span.set_attribute("retrieval.documents", documents)
        adapter.add_log(span, "info", "retrieval complete", count=len(documents))
        return documents
    except Exception as exc:
        adapter.add_log(span, "error", "retrieval failed", error=str(exc))
        raise
    finally:
        span.end()
```

## Node.js 래퍼 (예시)
```ts
import { trace } from "@opentelemetry/api";

export class RagTraceAdapter {
  private tracer = trace.getTracer("open-rag-trace");
  private specVersion = "0.1";

  startSpan(name: string, module: string, attrs: Record<string, unknown> = {}) {
    const span = this.tracer.startSpan(name);
    span.setAttribute("spec.version", this.specVersion);
    span.setAttribute("rag.module", module);
    Object.entries(attrs).forEach(([key, value]) => span.setAttribute(key, value));
    return span;
  }

  addLog(span: any, level: string, message: string, data: Record<string, unknown> = {}) {
    span.addEvent("log", { "log.level": level, "log.message": message, "log.data": data });
  }

  addCustom(span: any, attrs: Record<string, unknown>) {
    Object.entries(attrs).forEach(([key, value]) =>
      span.setAttribute(`custom.${key}`, value),
    );
  }
}
```

## 로그 흡수 전략
- 기존 로거의 레벨/메시지를 그대로 이벤트로 변환한다.
- 예: `logger.info("retrieval start", extra={"query": query})` → span event
- 구조화 로그 데이터는 JSON 문자열로 직렬화한다.

## 외부/레거시 메트릭 대응
- 표준 필드에 매핑하기 애매한 값은 `custom.*`로 보관한다.
- 추후 매핑 규칙이 확정되면 `custom.*` → 표준 필드로 이행한다.

## 적용 순서 (권장)
1. 모듈 식별: retrieval/llm/eval 등 핵심 모듈 먼저 래핑
2. 표준 필드 확보: `rag.module`, `spec.version`
3. 데이터 확장: 문서/스코어/모델 파라미터 추가
4. 로그 흡수: 단계별 로그 이벤트화

---

## 변경 이력
- 2026-01-10: Draft v0.1 최초 작성
