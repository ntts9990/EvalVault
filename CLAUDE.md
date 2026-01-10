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
│   └── metrics/          # InsuranceTermAccuracy (custom metrics)
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
- **Model**: `gpt-5-mini` (default, configurable via OPENAI_MODEL)
- **Note**: OpenAI 모델은 비용이 발생하므로 필요할 때만 선택합니다.
- **Usage**: Ragas metric evaluation via LangChain

### Langfuse (Self-hosted or Cloud)
- **Host**: Configure via `LANGFUSE_HOST`
- **Purpose**: Trace logging, score tracking, evaluation history
- **Credentials**: Inject via `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`

## Development Commands

```bash
# Install dependencies (uv sync 사용 필수)
uv sync --extra dev                              # 전체 기능 개발 환경 (dev 도구 + 모든 extras)

# Optional extras:
#   --extra korean  : 한국어 NLP (kiwipiepy, rank-bm25)
#   --extra postgres: PostgreSQL 지원
#   --extra mlflow  : MLflow 트래커
#   --extra anthropic: Anthropic LLM

# Run all tests (항상 uv run 사용)
uv run pytest tests/

# Run unit tests only
uv run pytest tests/unit/

# Run integration tests only
uv run pytest tests/integration/

# Run with verbose output
uv run pytest tests/ -v --tb=short

# Skip tests requiring API keys
uv run pytest tests/ -v -m "not requires_openai and not requires_langfuse"

# Lint
uv run ruff check src/
uv run ruff format src/

# Add dependencies
uv add <package>           # 런타임 의존성
uv add --dev <package>     # 개발 의존성

# CLI usage (uv run 사용)
uv run evalvault run data.csv --metrics faithfulness,answer_relevancy
uv run evalvault run data.csv --metrics faithfulness --parallel --batch-size 10
uv run evalvault metrics
uv run evalvault config
```

> **Note**: 모든 Python 명령어는 `uv run`을 통해 실행해야 가상환경이 올바르게 적용됩니다.

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

## CI/CD & Release

### GitHub Actions Workflows

| Workflow | Trigger | Description |
|----------|---------|-------------|
| CI | Push/PR to main, develop | Lint, format check, tests on all platforms |
| Release | Push to main | Automatic versioning and PyPI publish |

### Cross-Platform Testing

CI는 다음 플랫폼에서 테스트를 실행합니다:
- Ubuntu (Python 3.12, 3.13)
- macOS (Python 3.12)
- Windows (Python 3.12)

### Automatic Versioning (python-semantic-release)

Conventional Commits 규칙에 따라 자동으로 버전이 결정됩니다:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat:` | Minor (0.x.0) | `feat: Add new metric` → 0.2.0 |
| `fix:` | Patch (0.0.x) | `fix: Correct calculation` → 0.1.1 |
| `perf:` | Patch (0.0.x) | `perf: Improve query speed` → 0.1.1 |
| `chore:`, `docs:`, `ci:`, `test:`, `style:`, `refactor:` | No release | 버전 변경 없음 |

**중요**: `pyproject.toml`의 버전은 자동 업데이트되지 않습니다 (브랜치 보호 규칙). 실제 배포 버전은 git 태그 기반입니다.

### Commit Message Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

**Examples**:
```bash
feat(metrics): Add custom insurance accuracy metric
fix(cli): Handle empty dataset gracefully
docs: Update installation guide
chore(deps): Bump ragas to 1.0.5
```

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

> Phase 1-14 모두 완료. 상세 내용은 [docs/ROADMAP.md](docs/ROADMAP.md) 참조.

| Component | Status | Description |
|-----------|--------|-------------|
| Domain Entities | ✅ Complete | TestCase, Dataset, EvaluationRun, Experiment |
| Port Interfaces | ✅ Complete | LLM, Dataset, Storage, Tracker, Evaluator |
| Data Loaders | ✅ Complete | CSV, Excel, JSON |
| RagasEvaluator | ✅ Complete | 6 metrics (Ragas v1.0) |
| LLM Adapters | ✅ Complete | OpenAI, Ollama, Azure, Anthropic |
| Storage Adapters | ✅ Complete | SQLite, PostgreSQL |
| Tracker Adapters | ✅ Complete | Langfuse, MLflow |
| CLI | ✅ Complete | run, metrics, config, history, compare, export, generate, pipeline, benchmark |
| Testset Generation | ✅ Complete | Basic + Knowledge Graph |
| Experiment Management | ✅ Complete | A/B testing, comparison |
| Korean NLP | ✅ Complete | KiwiTokenizer, BM25, Dense/Hybrid Retrieval |
| Web UI | ✅ Complete | React + FastAPI Evaluation Studio/Analysis Lab |
| Analysis Pipeline | ✅ Complete | DAG-based query analysis, Intent classification |

**Test Summary:**
- Unit Tests: 1,261
- Integration Tests: 91
- **Total: 1,352 tests passing**
- **Test Coverage: 89%**

## Documentation

| Document | Description |
|----------|-------------|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | 설치, 설정, 메트릭 설명, 문제 해결 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Hexagonal Architecture 상세 설명 |
| [docs/COMPLETED.md](docs/COMPLETED.md) | Phase 1-14 완료 내역, 기술 스펙, 아키텍처 현황 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 2026-2027 개발 로드맵 (Phase 15-19+) |
| [docs/IMPROVEMENT_PLAN.md](docs/IMPROVEMENT_PLAN.md) | 코드 품질 개선 계획 (P1-P7 우선순위, 병렬 에이전트 워크플로우) |
| [docs/KG_IMPROVEMENT_PLAN.md](docs/KG_IMPROVEMENT_PLAN.md) | Knowledge Graph 개선 계획 |
| [agent/README.md](agent/README.md) | 자율 에이전트 시스템 사용 가이드 |

## Autonomous Agent System

EvalVault includes an autonomous agent system for development automation, based on [nonstop-agent](https://github.com/seolcoding/nonstop-agent) (MIT License).

### Agent Types

| Agent | Focus | P-Levels |
|-------|-------|----------|
| `architecture` | Code structure, Hexagonal Architecture | P0, P1, P2 |
| `observability` | Phoenix integration, OpenTelemetry | P7 |
| `rag-data` | Retrieval data collection, metrics | P7 |
| `performance` | Caching, batch processing | P3 |
| `testing` | Test optimization, coverage | P5 |
| `documentation` | Tutorials, API docs | P6 |
| `coordinator` | Parallel workflow management | All |

### Usage

```bash
# Prerequisites
cd agent/
export ANTHROPIC_API_KEY='your-key'
uv add claude-agent-sdk

# List available agents
uv run python main.py --list-agents

# Run specific agent
uv run python main.py --project-dir .. --agent-type architecture

# Run coordinator to check all agents
uv run python main.py --project-dir .. --agent-type coordinator
```

### Memory System

Agents maintain persistent memory in `agent/memory/`:
- `agents/<agent-type>/` - Per-agent session logs
- `shared/decisions.md` - Cross-agent architecture decisions (ADR format)
- `shared/dependencies.md` - Task dependencies and blocking issues

See [agent/README.md](agent/README.md) for full documentation.
