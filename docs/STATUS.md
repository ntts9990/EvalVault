# EvalVault Implementation Status

> Last Updated: 2024-12-24

---

## Quick Summary

| Category | Status | Details |
|----------|--------|---------|
| **Overall Progress** | Phase 3 Complete | Core system fully implemented |
| **Total Tests** | 118 passing | 100 unit + 18 integration |
| **Architecture** | Hexagonal | Ports & Adapters pattern |
| **Python Version** | 3.12+ | Type hints required |

---

## Component Status

### Domain Layer

| Component | Status | Tests | Notes |
|-----------|--------|-------|-------|
| TestCase | ✅ Complete | 19 | Ragas format conversion |
| Dataset | ✅ Complete | 19 | Iterable, length support |
| MetricType | ✅ Complete | 19 | 4 metrics defined |
| MetricScore | ✅ Complete | 19 | Threshold-based pass logic |
| TestCaseResult | ✅ Complete | 19 | Token/latency tracking |
| EvaluationRun | ✅ Complete | 19 | Full aggregation |
| RagasEvaluator | ✅ Complete | 11 | Async, token tracking |

### Ports Layer

| Port | Type | Status | Tests |
|------|------|--------|-------|
| EvaluatorPort | Inbound | ✅ Complete | 24 |
| LLMPort | Outbound | ✅ Complete | 24 |
| DatasetPort | Outbound | ✅ Complete | 24 |
| TrackerPort | Outbound | ✅ Complete | 24 |
| StoragePort | Outbound | ⏳ Interface Only | 0 |

### Adapters Layer

| Adapter | Port | Status | Tests |
|---------|------|--------|-------|
| CLI (Typer) | Inbound | ✅ Complete | 7 |
| OpenAIAdapter | LLMPort | ✅ Complete | 4 |
| CSVDatasetLoader | DatasetPort | ✅ Complete | 21 |
| ExcelDatasetLoader | DatasetPort | ✅ Complete | 21 |
| JSONDatasetLoader | DatasetPort | ✅ Complete | 21 |
| LangfuseAdapter | TrackerPort | ✅ Complete | 18 |
| SQLiteAdapter | StoragePort | ❌ Not Implemented | 0 |

---

## Recent Changes (2024-12-24)

### Langfuse Trace Metadata Fix

**Problem**: Langfuse trace name과 metadata가 저장되지 않음

**Root Cause**: Langfuse 3.x (OTEL 기반)에서는 `span.end()` 호출 전까지 데이터가 전송되지 않음

**Solution**: `log_evaluation_run()` 메서드에서 flush 전 `span.end()` 호출 추가

```python
# langfuse_adapter.py (line 317-327)
# End the root span and flush
trace_or_span = self._traces.get(trace_id)
if trace_or_span and hasattr(trace_or_span, "end"):
    trace_or_span.end()

self._client.flush()

# Remove from active traces
if trace_id in self._traces:
    del self._traces[trace_id]
```

### Token Tracking Implementation

**Added**: `TestCaseEvalResult` dataclass for holding scores + tokens

```python
@dataclass
class TestCaseEvalResult:
    """Ragas 평가 결과 (토큰 사용량 포함)."""
    scores: dict[str, float]
    tokens_used: int = 0
```

**Implementation**: LangChain `get_openai_callback()` 사용

```python
from langchain_community.callbacks import get_openai_callback

with get_openai_callback() as cb:
    score = await metric.single_turn_ascore(sample)
    test_case_tokens += cb.total_tokens
```

### Langfuse 2.x/3.x API Compatibility

**Feature Detection**:
```python
if hasattr(self._client, "start_span"):
    # Langfuse 3.x API
    span = self._client.start_span(name=name)
else:
    # Langfuse 2.x API
    trace = self._client.trace(name=name)
```

---

## Test Coverage

### Unit Tests (100)

```
tests/unit/
├── test_entities.py      # 19 tests - Domain entities
├── test_data_loaders.py  # 21 tests - CSV/Excel/JSON
├── test_evaluator.py     # 11 tests - RagasEvaluator
├── test_langfuse_tracker.py # 18 tests - Langfuse adapter
├── test_openai_adapter.py # 4 tests - OpenAI adapter
├── test_ports.py         # 24 tests - Port interfaces
└── test_cli.py           # 7 tests - CLI commands
```

### Integration Tests (18)

```
tests/integration/
├── test_evaluation_flow.py  # End-to-end evaluation
├── test_data_flow.py        # Dataset loading flow
└── test_langfuse_flow.py    # Langfuse integration
```

### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Unit tests only
uv run pytest tests/unit/ -v

# Skip API-dependent tests
uv run pytest tests/ -m "not requires_openai and not requires_langfuse"

# With coverage
uv run pytest tests/ --cov=src/evalvault
```

---

## Directory Structure

```
src/evalvault/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── dataset.py      # TestCase, Dataset
│   │   └── result.py       # MetricScore, TestCaseResult, EvaluationRun
│   └── services/
│       ├── __init__.py
│       └── evaluator.py    # RagasEvaluator, TestCaseEvalResult
├── ports/
│   ├── __init__.py
│   ├── inbound/
│   │   ├── __init__.py
│   │   └── evaluator_port.py
│   └── outbound/
│       ├── __init__.py
│       ├── llm_port.py
│       ├── dataset_port.py
│       ├── tracker_port.py
│       └── storage_port.py
├── adapters/
│   ├── __init__.py
│   ├── inbound/
│   │   ├── __init__.py
│   │   └── cli.py          # Typer CLI
│   └── outbound/
│       ├── __init__.py
│       ├── llm/
│       │   ├── __init__.py
│       │   └── openai_adapter.py
│       ├── dataset/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── csv_loader.py
│       │   ├── excel_loader.py
│       │   ├── json_loader.py
│       │   └── loader_factory.py
│       ├── tracker/
│       │   ├── __init__.py
│       │   └── langfuse_adapter.py
│       └── storage/
│           └── __init__.py  # (Empty - Phase 5)
└── config/
    ├── __init__.py
    └── settings.py
```

---

## Metrics Supported

| Metric | Ragas Class | Ground Truth Required | Embeddings Required |
|--------|-------------|----------------------|---------------------|
| `faithfulness` | Faithfulness | No | No |
| `answer_relevancy` | AnswerRelevancy | No | Yes |
| `context_precision` | ContextPrecision | Yes | No |
| `context_recall` | ContextRecall | Yes | No |

### Planned Metrics (Phase 4)

| Metric | Status | Notes |
|--------|--------|-------|
| `factual_correctness` | Pending | Ragas FactualCorrectness |
| `semantic_similarity` | Pending | Ragas SemanticSimilarity |

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano

# Optional
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_BASE_URL=https://api.openai.com/v1

# Langfuse (Optional)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# Thresholds
THRESHOLD_FAITHFULNESS=0.7
THRESHOLD_ANSWER_RELEVANCY=0.7
THRESHOLD_CONTEXT_PRECISION=0.7
THRESHOLD_CONTEXT_RECALL=0.7
```

---

## Known Issues

1. **No Persistent Storage**: Evaluation results are only logged to Langfuse, no local storage (Phase 5)
2. **English-only Prompts**: Ragas uses English prompts by default, may affect Korean text accuracy (Phase 4)
3. **Single LLM Provider**: Only OpenAI supported currently (Phase 4 optional)

---

## Next Steps

See [ROADMAP.md](./ROADMAP.md) for detailed implementation plan.

**Phase 4 Priorities**:
1. Language detection utility
2. Korean prompt customization
3. FactualCorrectness metric
4. SemanticSimilarity metric
