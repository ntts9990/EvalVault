# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EvalVault is a RAG (Retrieval-Augmented Generation) evaluation system for Korean/English insurance documents. Built on Ragas + Langfuse for evaluation and tracking.

**Core Flow:**
```
Input (CSV/Excel/JSON) → Ragas Evaluation → Langfuse Trace/Score → Analysis
```

**Supported Metrics:**
- `faithfulness` - 답변이 컨텍스트에 충실한지
- `answer_relevancy` - 답변이 질문과 관련있는지
- `context_precision` - 검색된 컨텍스트의 정밀도
- `context_recall` - 필요한 정보가 검색되었는지

## Architecture

**Hexagonal Architecture (Ports & Adapters)**

```
src/evalvault/
├── domain/
│   ├── entities/         # TestCase, Dataset, EvaluationRun, MetricScore
│   └── services/         # RagasEvaluator
├── ports/
│   ├── inbound/          # EvaluatorPort
│   └── outbound/         # LLMPort, DatasetPort, StoragePort, TrackerPort
├── adapters/
│   ├── inbound/          # CLI (Typer)
│   └── outbound/
│       ├── dataset/      # CSV, Excel, JSON loaders
│       ├── llm/          # OpenAIAdapter
│       ├── storage/      # (미구현 - Phase 5 예정)
│       └── tracker/      # LangfuseAdapter
└── config/               # Settings (pydantic-settings)
```

### Port/Adapter 구현 현황

| Port | Adapter | Status |
|------|---------|--------|
| LLMPort | OpenAIAdapter | ✅ 구현됨 |
| DatasetPort | CSV/Excel/JSON Loaders | ✅ 구현됨 |
| TrackerPort | LangfuseAdapter | ✅ 구현됨 |
| StoragePort | - | ⏳ 미구현 (Phase 5) |
| EvaluatorPort | RagasEvaluator | ✅ 구현됨 |

## External Services Configuration

### OpenAI
- **Model**: `gpt-5-nano` (default, configurable via OPENAI_MODEL)
- **Note**: `gpt-5-nano`는 실제 사용 가능한 모델입니다. 변경하지 마세요.
- **Usage**: Ragas metric evaluation via LangChain

### Langfuse (Self-hosted)
- **Organization**: BGK
- **Project**: RAGAS
- **Host**: Set via `LANGFUSE_HOST` environment variable
- **Purpose**: Trace logging, score tracking, evaluation history

## Development Commands

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest tests/ -v --tb=short

# Skip tests requiring API keys
pytest tests/ -v -m "not requires_openai and not requires_langfuse"

# Lint
ruff check src/
ruff format src/

# CLI usage
evalvault run data.csv --metrics faithfulness,answer_relevancy
evalvault metrics
evalvault config
```

## Development Practices

### TDD (Test-Driven Development)
- **Always write tests first** before implementation
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Use `@pytest.mark.requires_openai` for tests needing real API
- Use `@pytest.mark.requires_langfuse` for tests needing Langfuse

### Code Style
- Python 3.12+ features encouraged
- Type hints required
- Korean docstrings allowed for domain-specific comments
- English for public API documentation

## Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
# OpenAI (required)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
# OPENAI_BASE_URL=https://api.openai.com/v1  # optional

# Langfuse (self-hosted)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://your-langfuse-host:port

# Metric Thresholds (SLA)
THRESHOLD_FAITHFULNESS=0.7
THRESHOLD_ANSWER_RELEVANCY=0.7
THRESHOLD_CONTEXT_PRECISION=0.7
THRESHOLD_CONTEXT_RECALL=0.7
```

## Data Format

### Input Dataset (JSON)
```json
{
  "name": "insurance-qa-dataset",
  "version": "1.0.0",
  "test_cases": [
    {
      "id": "tc-001",
      "question": "이 보험의 보장금액은 얼마인가요?",
      "answer": "보장금액은 1억원입니다.",
      "contexts": ["해당 보험의 사망 보장금액은 1억원입니다."],
      "ground_truth": "1억원"
    }
  ]
}
```

### Input Dataset (CSV)
```csv
id,question,answer,contexts,ground_truth
tc-001,"질문","답변","[""컨텍스트1"",""컨텍스트2""]","정답"
```

## Current Implementation Status

| Component | Status | Unit Tests | Integration Tests |
|-----------|--------|------------|-------------------|
| Domain Entities | ✅ Complete | 19 | - |
| Port Interfaces | ✅ Complete | 24 | - |
| Data Loaders | ✅ Complete | 21 | 8 |
| RagasEvaluator | ✅ Complete | 7 | 6 |
| OpenAIAdapter | ✅ Complete | 4 | - |
| LangfuseAdapter | ✅ Complete | 18 | 5 |
| CLI | ✅ Complete | 7 | - |

**Test Summary:**
- Unit Tests: 100
- Integration Tests: 18
- **Total: 118 tests passing**

## Roadmap

### Phase 1-3: Core System (Completed)
- [x] Domain Entities (TestCase, Dataset, EvaluationRun, MetricScore)
- [x] Port Interfaces (LLMPort, DatasetPort, StoragePort, TrackerPort, EvaluatorPort)
- [x] Data Loaders (CSV, Excel, JSON)
- [x] RagasEvaluator with async evaluation (4 metrics)
- [x] OpenAI Adapter (LangChain integration)
- [x] Langfuse Adapter (trace/score logging)
- [x] CLI Interface (run, metrics, config commands)
- [x] Configuration via pydantic-settings
- [ ] ~~StorageAdapter~~ → Phase 5로 이동

### Phase 4: Foundation Enhancement (P0 - Next)
- [ ] Language detection utility (`langdetect`)
- [ ] Korean prompt customization for Ragas
- [ ] FactualCorrectness metric
- [ ] SemanticSimilarity metric
- [ ] Azure OpenAI Adapter (선택)
- [ ] Anthropic Claude Adapter (선택)

### Phase 5: Storage & Domain (P1)
- [ ] SQLite storage adapter (StoragePort 구현)
- [ ] Evaluation history 조회/비교 기능
- [ ] InsuranceTermAccuracy metric
- [ ] Basic Testset Generation

### Phase 6: Advanced Features (P2)
- [ ] Knowledge Graph-based testset generation
- [ ] Experiment management system
- [ ] Multilingual prompt expansion
- [ ] PostgreSQL storage adapter (선택)
- [ ] MLflow Tracker adapter (선택)
