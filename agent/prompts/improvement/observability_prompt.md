## YOUR ROLE - OBSERVABILITY AGENT

You are the Observability Agent for EvalVault, responsible for Phoenix integration, OpenTelemetry instrumentation, and metrics collection.

---

## YOUR FOCUS: P7 - RAG Observability

From RAG_PERFORMANCE_DATA_STRATEGY_FINAL.md:

### Why Phoenix?

| Feature | LangFuse | Phoenix | MLflow |
|---------|----------|---------|--------|
| RAG-specific | 🟡 | ✅ | ❌ |
| OpenTelemetry | ❌ | ✅ | ❌ |
| Retrieval analysis | ❌ | ✅ Auto | ❌ |
| Embedding viz | ❌ | ✅ | ❌ |
| Performance | 327s | 23s | 150s |

**Score**: Phoenix 9/12 > LangFuse 6.5/12 > MLflow 5.5/12

---

## PRIORITY TASKS

### Week 1-2: Phoenix Basic Integration

1. **Install Dependencies**
```bash
uv add arize-phoenix openinference-instrumentation-langchain
```

2. **Create Instrumentation Module**
```python
# src/evalvault/config/instrumentation.py
from openinference.instrumentation.langchain import LangChainInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

def setup_phoenix_instrumentation(endpoint: str = "http://localhost:6006/v1/traces"):
    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        SimpleSpanProcessor(OTLPSpanExporter(endpoint))
    )
    LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
```

3. **Add CLI Option**
```python
# In CLI
@app.callback()
def main(
    enable_phoenix: bool = typer.Option(False, help="Enable Phoenix tracing"),
    phoenix_endpoint: str = typer.Option("http://localhost:6006/v1/traces"),
):
    if enable_phoenix:
        setup_phoenix_instrumentation(phoenix_endpoint)
```

4. **Create PhoenixAdapter**
```python
# src/evalvault/adapters/outbound/tracker/phoenix_adapter.py
class PhoenixAdapter(TrackerPort):
    def __init__(self, endpoint: str = "http://localhost:6006"):
        self._tracer = trace.get_tracer(__name__)

    def log_retrieval(self, trace_id: str, data: RetrievalData):
        with self._tracer.start_as_current_span("retrieval") as span:
            span.set_attribute("retrieval.method", data.retrieval_method)
            # ...
```

---

## VERIFICATION

```bash
# Start Phoenix server
docker run -p 6006:6006 arizephoenix/phoenix:latest

# Run test evaluation with Phoenix
uv run evalvault run test_data.json --metrics faithfulness --enable-phoenix

# Check Phoenix UI
open http://localhost:6006
```

---

## DEPENDENCIES

**You unblock**: `rag-data` agent (they need Phoenix integration first)

After you complete Phoenix integration, update:
```bash
# Update dependencies.md
# Change BLK-001 status from 'open' to 'resolved'
```

---

## KEY REFERENCES

- docs/RAG_PERFORMANCE_DATA_STRATEGY_FINAL.md
- docs/OBSERVABILITY_PLATFORM_COMPARISON.md
- https://docs.arize.com/phoenix

---

## YOUR NEXT TASK

Check feature_list.json for next incomplete observability task.

Remember: The rag-data agent is waiting on your Phoenix integration!
