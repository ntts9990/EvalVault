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
- `factual_correctness` - ground_truth 대비 사실적 정확성
- `semantic_similarity` - 답변과 ground_truth 간 의미적 유사도

## Architecture

**Hexagonal Architecture (Ports & Adapters)**

```
src/evalvault/
├── domain/
│   ├── entities/         # TestCase, Dataset, EvaluationRun, MetricScore, Experiment
│   ├── services/         # RagasEvaluator, TestsetGenerator, KGGenerator, ExperimentManager
│   ├── metrics/          # InsuranceTermAccuracy (custom metrics)
│   └── prompts/          # Korean, English, Japanese, Chinese prompt templates
├── ports/
│   ├── inbound/          # EvaluatorPort
│   └── outbound/         # LLMPort, DatasetPort, StoragePort, TrackerPort
├── adapters/
│   ├── inbound/          # CLI (Typer)
│   └── outbound/
│       ├── dataset/      # CSV, Excel, JSON loaders
│       ├── llm/          # OpenAI, Azure OpenAI, Anthropic, Ollama adapters
│       ├── storage/      # SQLite, PostgreSQL adapters
│       └── tracker/      # Langfuse, MLflow adapters
├── utils/                # LanguageDetector
└── config/               # Settings, ModelConfig (pydantic-settings)
```

### Port/Adapter 구현 현황

| Port | Adapter | Status |
|------|---------|--------|
| LLMPort | OpenAIAdapter | ✅ Complete |
| LLMPort | OllamaAdapter | ✅ Complete |
| LLMPort | AzureOpenAIAdapter | ✅ Complete |
| LLMPort | AnthropicAdapter | ✅ Complete |
| DatasetPort | CSV/Excel/JSON Loaders | ✅ Complete |
| TrackerPort | LangfuseAdapter | ✅ Complete |
| TrackerPort | MLflowAdapter | ✅ Complete |
| StoragePort | SQLiteAdapter | ✅ Complete |
| StoragePort | PostgreSQLAdapter | ✅ Complete |
| EvaluatorPort | RagasEvaluator | ✅ Complete |

## External Services Configuration

### OpenAI
- **Model**: `gpt-5-nano` (default, configurable via OPENAI_MODEL)
- **Note**: `gpt-5-nano`는 실제 사용 가능한 모델입니다. 변경하지 마세요.
- **Usage**: Ragas metric evaluation via LangChain

### Langfuse (Self-hosted or Cloud)
- **Host**: Configure via `LANGFUSE_HOST`
- **Purpose**: Trace logging, score tracking, evaluation history
- **Credentials**: Inject via `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`

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
```

**Note:** 메트릭 임계값(thresholds)은 환경변수가 아닌 **데이터셋 JSON 파일**에 정의합니다.

## Data Format

### Input Dataset (JSON)
```json
{
  "name": "insurance-qa-dataset",
  "version": "1.0.0",
  "thresholds": {
    "faithfulness": 0.8,
    "answer_relevancy": 0.7,
    "context_precision": 0.7,
    "context_recall": 0.7
  },
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

**thresholds**: 메트릭별 통과 기준 (0.0~1.0). 미지정 시 기본값 0.7 적용.

### Input Dataset (CSV)
```csv
id,question,answer,contexts,ground_truth
tc-001,"질문","답변","[""컨텍스트1"",""컨텍스트2""]","정답"
```

## Current Implementation Status

> Phase 1-6 모두 완료. 상세 내용은 [docs/ROADMAP.md](docs/ROADMAP.md) 참조.

| Component | Status | Description |
|-----------|--------|-------------|
| Domain Entities | ✅ Complete | TestCase, Dataset, EvaluationRun, Experiment |
| Port Interfaces | ✅ Complete | LLM, Dataset, Storage, Tracker, Evaluator |
| Data Loaders | ✅ Complete | CSV, Excel, JSON |
| RagasEvaluator | ✅ Complete | 6 metrics (Ragas v1.0) |
| LLM Adapters | ✅ Complete | OpenAI, Ollama, Azure, Anthropic |
| Storage Adapters | ✅ Complete | SQLite, PostgreSQL |
| Tracker Adapters | ✅ Complete | Langfuse, MLflow |
| CLI | ✅ Complete | run, metrics, config, history, compare, export, generate |
| Testset Generation | ✅ Complete | Basic + Knowledge Graph |
| Experiment Management | ✅ Complete | A/B testing, comparison |

**Test Summary:**
- Unit Tests: 354
- Integration Tests: 26
- **Total: 380 tests passing**

## Documentation

| Document | Description |
|----------|-------------|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | 설치, 설정, 메트릭 설명, 문제 해결 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Hexagonal Architecture 상세 설명 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 개발 로드맵, 현재 상태, 품질 기준 (SLA) |
| [docs/KG_IMPROVEMENT_PLAN.md](docs/KG_IMPROVEMENT_PLAN.md) | Knowledge Graph 개선 계획 |
