# EvalVault

RAG(Retrieval-Augmented Generation) 평가 시스템 - Ragas + Langfuse 기반

한국어/영어 보험 문서 RAG 시스템의 품질을 평가하고 추적하는 도구입니다.

## Features

- **Ragas 기반 평가**: faithfulness, answer_relevancy, context_precision, context_recall
- **Langfuse 통합**: 평가 결과 추적 및 시각화 (셀프 호스팅 지원)
- **다양한 입력 형식**: CSV, Excel, JSON 데이터셋 지원
- **CLI 인터페이스**: 간편한 명령줄 도구
- **Hexagonal Architecture**: 확장 가능한 포트/어댑터 아키텍처

## Installation

```bash
# uv 사용
uv pip install -e ".[dev]"

# pip 사용
pip install -e ".[dev]"
```

## Quick Start

### 1. 환경 설정

`.env` 파일 생성:

```bash
# OpenAI (필수)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Langfuse (선택 - 결과 추적용)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# 메트릭 임계값 (기본값: 0.7)
THRESHOLD_FAITHFULNESS=0.7
THRESHOLD_ANSWER_RELEVANCY=0.7
THRESHOLD_CONTEXT_PRECISION=0.7
THRESHOLD_CONTEXT_RECALL=0.7
```

### 2. 평가 실행

```bash
# 기본 평가 (faithfulness + answer_relevancy)
evalvault run data.csv

# 특정 메트릭 지정
evalvault run data.csv --metrics faithfulness,context_precision

# Langfuse 로깅 활성화
evalvault run data.csv --langfuse

# 결과를 파일로 저장
evalvault run data.csv --output results.json --verbose
```

## CLI Commands

```bash
# 평가 실행
evalvault run <dataset> [OPTIONS]
  --metrics, -m    평가할 메트릭 (기본: faithfulness,answer_relevancy)
  --model          사용할 모델
  --output, -o     결과 저장 파일
  --langfuse, -l   Langfuse에 로깅
  --verbose        상세 출력

# 사용 가능한 메트릭 목록
evalvault metrics

# 현재 설정 확인
evalvault config

# 버전 확인
evalvault --version
```

## Input Data Format

### CSV

```csv
id,question,answer,contexts,ground_truth
tc-001,"보험금은 얼마인가요?","1억원입니다.","[""사망보험금은 1억원입니다.""]","1억원"
```

### JSON

```json
{
  "name": "insurance-qa-dataset",
  "version": "1.0.0",
  "test_cases": [
    {
      "id": "tc-001",
      "question": "보험금은 얼마인가요?",
      "answer": "1억원입니다.",
      "contexts": ["사망보험금은 1억원입니다."],
      "ground_truth": "1억원"
    }
  ]
}
```

### Excel

CSV와 동일한 컬럼 구조 (`.xlsx`, `.xls` 지원)

## Metrics

| Metric | Description | Ground Truth Required |
|--------|-------------|----------------------|
| `faithfulness` | 답변이 컨텍스트에 충실한지 | No |
| `answer_relevancy` | 답변이 질문과 관련있는지 | No |
| `context_precision` | 검색된 컨텍스트의 정밀도 | Yes |
| `context_recall` | 필요한 정보가 검색되었는지 | Yes |

## Architecture

**Hexagonal Architecture (Ports & Adapters)**

```
                            ┌─────────────────────────────────────────────────────────────┐
                            │                    EXTERNAL SYSTEMS                         │
                            │  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐  │
                            │  │  OpenAI  │    │ Langfuse │    │ CSV / Excel / JSON   │  │
                            │  └────┬─────┘    └────┬─────┘    └──────────┬───────────┘  │
                            └───────┼───────────────┼─────────────────────┼──────────────┘
                                    │               │                     │
┌───────────────────────────────────┼───────────────┼─────────────────────┼───────────────────────┐
│                                   │               │                     │                       │
│   O U T B O U N D   A D A P T E R S               │                     │                       │
│   ┌───────────────┐       ┌───────────────┐       │         ┌───────────────────────────────┐   │
│   │ OpenAIAdapter │       │LangfuseAdapter│       │         │      DatasetLoaders           │   │
│   │  (LangChain)  │       │ (trace/score) │       │         │  CSV | Excel | JSON           │   │
│   └───────┬───────┘       └───────┬───────┘       │         └─────────────┬─────────────────┘   │
│           │                       │               │                       │                     │
└───────────┼───────────────────────┼───────────────┼───────────────────────┼─────────────────────┘
            │                       │               │                       │
            ▼                       ▼               │                       ▼
┌───────────────────────────────────────────────────┼───────────────────────────────────────────┐
│                                                   │                                           │
│   O U T B O U N D   P O R T S                     │                                           │
│   ┌─────────┐  ┌─────────────┐  ┌─────────────┐   │   ┌─────────────┐                         │
│   │ LLMPort │  │ TrackerPort │  │ StoragePort │   │   │ DatasetPort │                         │
│   └────┬────┘  └──────┬──────┘  └──────┬──────┘   │   └──────┬──────┘                         │
│        │              │                │          │          │                                │
│        └──────────────┼────────────────┼──────────┼──────────┘                                │
│                       │                │          │                                           │
│                       ▼                ▼          │                                           │
│          ╔════════════════════════════════════════╧═══════════════════════════════╗           │
│          ║                                                                        ║           │
│          ║                        D O M A I N                                     ║           │
│          ║                                                                        ║           │
│          ║   ┌─────────────────────────────────────────────────────────────┐      ║           │
│          ║   │                      SERVICES                               │      ║           │
│          ║   │                   RagasEvaluator                            │      ║           │
│          ║   │        (faithfulness, relevancy, precision, recall)         │      ║           │
│          ║   └─────────────────────────────────────────────────────────────┘      ║           │
│          ║                                                                        ║           │
│          ║   ┌─────────────────────────────────────────────────────────────┐      ║           │
│          ║   │                      ENTITIES                               │      ║           │
│          ║   │   TestCase │ Dataset │ EvaluationRun │ MetricScore          │      ║           │
│          ║   └─────────────────────────────────────────────────────────────┘      ║           │
│          ║                                                                        ║           │
│          ╚════════════════════════════════════════════════════════════════════════╝           │
│                                       ▲                                                       │
│                                       │                                                       │
│   I N B O U N D   P O R T             │                                                       │
│   ┌───────────────────────────────────┴───────────────────────────────────┐                   │
│   │                         EvaluatorPort                                 │                   │
│   │                    evaluate(dataset, metrics, llm)                    │                   │
│   └───────────────────────────────────┬───────────────────────────────────┘                   │
│                                       │                                                       │
└───────────────────────────────────────┼───────────────────────────────────────────────────────┘
                                        │
┌───────────────────────────────────────┼───────────────────────────────────────────────────────┐
│                                       │                                                       │
│   I N B O U N D   A D A P T E R       │                                                       │
│   ┌───────────────────────────────────┴───────────────────────────────────┐                   │
│   │                              CLI (Typer)                              │                   │
│   │                     evalvault run | metrics | config                  │                   │
│   └───────────────────────────────────────────────────────────────────────┘                   │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │
                                   ┌────┴────┐
                                   │  User   │
                                   └─────────┘
```

**Directory Structure:**

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
│       ├── storage/      # (TODO: SQLite adapter)
│       └── tracker/      # LangfuseAdapter
└── config/               # Settings (pydantic-settings)
```

**Implementation Status:**

| Port | Adapter | Status |
|------|---------|--------|
| LLMPort | OpenAIAdapter | ✅ |
| DatasetPort | CSV/Excel/JSON | ✅ |
| TrackerPort | LangfuseAdapter | ✅ |
| StoragePort | - | ⏳ Planned |
| EvaluatorPort | RagasEvaluator | ✅ |

**Data Flow:**

```
User Input (CSV/Excel/JSON)
         │
         ▼
    ┌─────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────┐
    │  Load   │ ───▶ │   Evaluate   │ ───▶ │   Track     │ ───▶ │  Output  │
    │ Dataset │      │  with Ragas  │      │ to Langfuse │      │ Results  │
    └─────────┘      └──────────────┘      └─────────────┘      └──────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   OpenAI    │
                     │   (LLM)     │
                     └─────────────┘
```

## Development

```bash
# 테스트 실행
pytest tests/ -v

# 단위 테스트만
pytest tests/unit/

# 통합 테스트만
pytest tests/integration/

# API 키 없이 테스트
pytest tests/ -m "not requires_openai and not requires_langfuse"

# 린트
ruff check src/
ruff format src/
```

## License

Apache 2.0 - See [LICENSE.md](LICENSE.md)
