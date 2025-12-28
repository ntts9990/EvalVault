# EvalVault Development Roadmap

> Last Updated: 2025-12-28
> Current Version: 1.0.0
> Status: Phase 7 Complete (Production Ready)

---

## Overview

EvalVault의 개발 로드맵입니다. Phase 1-7까지 모두 완료되었습니다.

### Progress Summary

| Phase | Description | Status | Tests |
|-------|-------------|--------|-------|
| Phase 1-3 | Core System | ✅ Complete | 118 |
| Phase 4 | Foundation Enhancement | ✅ Complete | +60 |
| Phase 5 | Storage & Domain | ✅ Complete | +42 |
| Phase 6 | Advanced Features | ✅ Complete | +160 |
| Phase 7 | Production Ready | ✅ Complete | +10 |
| **Total** | | | **390** |

---

## Completed Phases

### Phase 1-3: Core System ✅

**Status**: Complete (2024-12-24)

| Component | Status | Description |
|-----------|--------|-------------|
| Domain Entities | ✅ | TestCase, Dataset, EvaluationRun, MetricScore |
| Port Interfaces | ✅ | LLMPort, DatasetPort, StoragePort, TrackerPort, EvaluatorPort |
| Data Loaders | ✅ | CSV, Excel, JSON loaders |
| RagasEvaluator | ✅ | Async evaluation with 4 core metrics |
| OpenAI Adapter | ✅ | LangChain integration with token tracking |
| Langfuse Adapter | ✅ | Trace/score logging, SDK v3 support |
| CLI Interface | ✅ | run, metrics, config commands |

---

### Phase 4: Foundation Enhancement ✅

**Status**: Complete (2024-12-24)

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| TASK-4.3 | FactualCorrectness Metric | ✅ DONE | `evaluator.py`, `settings.py` |
| TASK-4.4 | SemanticSimilarity Metric | ✅ DONE | `evaluator.py`, `settings.py` |
| TASK-4.5a | Azure OpenAI Adapter | ✅ DONE | `src/evalvault/adapters/outbound/llm/azure_adapter.py` |
| TASK-4.5b | Anthropic Claude Adapter | ✅ DONE | `src/evalvault/adapters/outbound/llm/anthropic_adapter.py` |

#### Implemented Features

**New Metrics**:
- `factual_correctness` - ground_truth 대비 사실적 정확성
- `semantic_similarity` - 답변과 ground_truth 간 의미적 유사도

---

### Phase 5: Storage & Domain ✅

**Status**: Complete (2024-12-24)

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| TASK-5.1 | SQLite Storage Adapter | ✅ DONE | `sqlite_adapter.py`, `schema.sql` |
| TASK-5.2 | History CLI Commands | ✅ DONE | `cli.py` (history, compare, export) |
| TASK-5.3 | InsuranceTermAccuracy Metric | ✅ DONE | `src/evalvault/domain/metrics/insurance.py` |
| TASK-5.4 | Basic Testset Generation | ✅ DONE | `testset_generator.py`, `document_chunker.py` |

#### Implemented Features

**SQLite Storage** (`src/evalvault/adapters/outbound/storage/sqlite_adapter.py`):
- `save_run(run)` - 평가 결과 저장
- `get_run(run_id)` - 단일 결과 조회
- `list_runs(limit, dataset_name, model_name)` - 필터링된 목록 조회
- `delete_run(run_id)` - 결과 삭제

**CLI Commands**:
- `evalvault history` - 평가 히스토리 조회
- `evalvault compare <run_id1> <run_id2>` - 두 평가 결과 비교
- `evalvault export <run_id> -o <file>` - 결과 JSON 내보내기
- `evalvault generate <documents> -n <num>` - 테스트셋 생성

**InsuranceTermAccuracy** (`src/evalvault/domain/metrics/insurance.py`):
- 보험 도메인 특화 용어 정확도 평가
- 용어 사전 기반 매칭 (`terms_dictionary.json`)
- Ragas Metric 인터페이스 호환

**Testset Generation** (`src/evalvault/domain/services/testset_generator.py`):
- `BasicTestsetGenerator` - LLM 없이 기본 테스트셋 생성
- `DocumentChunker` - 문서 청킹 유틸리티
- factual/reasoning 질문 유형 지원

---

### Phase 6: Advanced Features ✅

**Status**: Complete (2025-12-24)

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| TASK-6.1 | Knowledge Graph Testset Generation | ✅ DONE | `kg_generator.py`, `entity_extractor.py` |
| TASK-6.2 | Experiment Management System | ✅ DONE | `experiment.py`, `experiment_manager.py` |
| TASK-6.4 | PostgreSQL Storage Adapter | ✅ DONE | `postgres_adapter.py` |
| TASK-6.5 | MLflow Tracker Adapter | ✅ DONE | `mlflow_adapter.py` |
| TASK-6.6 | Azure OpenAI Adapter | ✅ DONE | `azure_adapter.py` |
| TASK-6.7 | Anthropic Claude Adapter | ✅ DONE | `anthropic_adapter.py` |

---

#### Implemented Features

**Knowledge Graph Generator** (`src/evalvault/domain/services/kg_generator.py`):
- `KnowledgeGraph` - 지식 그래프 데이터 구조
- `KnowledgeGraphGenerator` - 문서 기반 그래프 생성
- Multi-hop 질문 생성 지원
- Entity 타입별 질문 생성

**Entity Extractor** (`src/evalvault/domain/services/entity_extractor.py`):
- 보험 도메인 엔티티 추출 (회사, 상품, 금액, 기간, 보장)
- 관계 추출 (PROVIDES, COVERS, HAS_AMOUNT 등)

**Experiment Management** (`src/evalvault/domain/services/experiment_manager.py`):
- `Experiment`, `ExperimentGroup` 엔티티
- A/B 테스트 그룹 비교
- 메트릭 통계 분석 및 결과 요약

**PostgreSQL Adapter** (`src/evalvault/adapters/outbound/storage/postgres_adapter.py`):
- asyncpg 기반 비동기 PostgreSQL 지원
- StoragePort 인터페이스 호환

**MLflow Adapter** (`src/evalvault/adapters/outbound/tracker/mlflow_adapter.py`):
- MLflow 실험 추적 연동
- TrackerPort 인터페이스 호환

**Azure OpenAI Adapter** (`src/evalvault/adapters/outbound/llm/azure_adapter.py`):
- Azure OpenAI Service 연동
- LLMPort 인터페이스 호환

**Anthropic Adapter** (`src/evalvault/adapters/outbound/llm/anthropic_adapter.py`):
- Anthropic Claude API 연동
- OpenAI embeddings fallback 지원
- LLMPort 인터페이스 호환

---

### Phase 7: Production Ready ✅

**Status**: Complete (2025-12-28)

| Task | Description | Status | Files |
|------|-------------|--------|-------|
| TASK-7.1 | Performance Optimization | ✅ DONE | `evaluator.py` (parallel, batch_size) |
| TASK-7.2 | Docker Containerization | ✅ DONE | `Dockerfile`, `docker-compose.yml` |

#### Implemented Features

**Performance Optimization**:
- `--parallel` CLI 옵션으로 병렬 평가 활성화
- `--batch-size` 옵션으로 배치 크기 조절
- 대규모 데이터셋 평가 성능 향상

**Docker Support**:
- Multi-stage build로 최적화된 이미지
- `docker-compose.yml`로 PostgreSQL + EvalVault 스택 구성
- 비root 사용자로 보안 강화

---

## Future Enhancements

> YAGNI 원칙에 따라, 아래 기능은 실제 사용자 요구가 있을 때 구현합니다.
> 현재는 CLI + Langfuse/MLflow UI 조합으로 대부분의 사용 사례를 충족합니다.

| Feature | Description | Status |
|---------|-------------|--------|
| API Server (FastAPI) | HTTP API 노출 | ⏸️ Deferred (Langfuse/MLflow UI 활용) |
| Dashboard Web UI | 평가 결과 시각화 | ⏸️ Deferred (Langfuse/MLflow UI 활용) |
| Kubernetes Deployment | K8s 배포 지원 | ⏸️ Deferred (Docker로 충분) |

---

## Supported Metrics (Current)

| Metric | Type | Ground Truth | Embeddings | Status |
|--------|------|--------------|------------|--------|
| `faithfulness` | Ragas | No | No | ✅ |
| `answer_relevancy` | Ragas | No | Yes | ✅ |
| `context_precision` | Ragas | Yes | No | ✅ |
| `context_recall` | Ragas | Yes | No | ✅ |
| `factual_correctness` | Ragas | Yes | No | ✅ |
| `semantic_similarity` | Ragas | Yes | Yes | ✅ |
| `insurance_term_accuracy` | Custom | Yes | No | ✅ |

---

## CLI Commands (Current)

```bash
# Core Commands
evalvault run <dataset> --metrics <metrics> [--langfuse]
evalvault metrics
evalvault config

# History Commands
evalvault history [--limit N] [--dataset NAME] [--model NAME]
evalvault compare <run_id1> <run_id2>
evalvault export <run_id> -o <file>

# Generation Commands
evalvault generate <documents> -n <num> -o <output>
```

---

## Test Summary

| Category | Count | Description |
|----------|-------|-------------|
| Unit Tests | 339 | Domain, ports, adapters, services |
| Integration Tests | 26 | End-to-end flows |
| **Total** | **365** | All passing |

### Test Files
```
tests/
├── unit/
│   ├── test_entities.py          # 19 tests
│   ├── test_data_loaders.py      # 21 tests
│   ├── test_evaluator.py         # 13 tests (including parallel)
│   ├── test_langfuse_tracker.py  # 18 tests
│   ├── test_openai_adapter.py    # 4 tests
│   ├── test_ports.py             # 24 tests
│   ├── test_cli.py               # 7 tests
│   ├── test_insurance_metric.py  # 18 tests
│   ├── test_sqlite_storage.py    # 18 tests
│   ├── test_testset_generator.py # 16 tests
│   ├── test_kg_generator.py      # 27 tests (Phase 6)
│   ├── test_entity_extractor.py  # 20 tests (Phase 6)
│   ├── test_experiment.py        # 21 tests (Phase 6)
│   ├── test_postgres_storage.py  # 19 tests (Phase 6)
│   ├── test_mlflow_tracker.py    # 17 tests (Phase 6)
│   ├── test_azure_adapter.py     # 18 tests (Phase 6)
│   └── test_anthropic_adapter.py # 19 tests (Phase 6)
└── integration/
    ├── test_evaluation_flow.py   # 6 tests
    ├── test_data_flow.py         # 8 tests
    ├── test_langfuse_flow.py     # 5 tests
    └── test_storage_flow.py      # 7 tests
```

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2024-12-24 | Phase 3 Complete - Core System |
| 0.2.0 | 2024-12-24 | Phase 5 Complete - Storage & Domain |
| 0.3.0 | 2025-12-24 | Phase 6 Complete - Advanced Features |
| 1.0.0 | 2025-12-28 | OSS Release - PyPI 배포, CI/CD 자동화 |

---

## CI/CD & Release

### Cross-Platform CI

| Platform | Python | Status |
|----------|--------|--------|
| Ubuntu | 3.12, 3.13 | ✅ |
| macOS | 3.12 | ✅ |
| Windows | 3.12 | ✅ |

### Automatic Versioning (python-semantic-release)

main 브랜치에 머지되면 Conventional Commits 규칙에 따라 자동으로 버전이 결정되고 PyPI에 배포됩니다:

| Commit Type | Version Bump | Example |
|-------------|--------------|---------|
| `feat:` | Minor (0.x.0) | `feat: Add new metric` |
| `fix:`, `perf:` | Patch (0.0.x) | `fix: Correct calculation` |
| Other | No release | `docs:`, `chore:`, `ci:`, etc. |

### Release Workflow

1. PR 생성 → CI 테스트 (Ubuntu, macOS, Windows)
2. PR 머지 → main 브랜치 푸시
3. Release 워크플로우 실행:
   - Conventional Commits 분석
   - 버전 태그 생성 (예: v1.0.1)
   - PyPI 배포
   - GitHub Release 생성

---

## Architecture

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
│       ├── llm/          # OpenAI, Azure OpenAI, Anthropic adapters
│       ├── storage/      # SQLite, PostgreSQL adapters
│       └── tracker/      # Langfuse, MLflow adapters
└── config/               # Settings (pydantic-settings)
```

### Port/Adapter Implementation Status

| Port | Adapter | Status |
|------|---------|--------|
| LLMPort | OpenAIAdapter | ✅ Complete |
| LLMPort | AzureOpenAIAdapter | ✅ Complete |
| LLMPort | AnthropicAdapter | ✅ Complete |
| DatasetPort | CSV/Excel/JSON Loaders | ✅ Complete |
| TrackerPort | LangfuseAdapter | ✅ Complete |
| TrackerPort | MLflowAdapter | ✅ Complete |
| StoragePort | SQLiteAdapter | ✅ Complete |
| StoragePort | PostgreSQLAdapter | ✅ Complete |
| EvaluatorPort | RagasEvaluator | ✅ Complete |

---

## Quality Standards (SLA)

### Metric Thresholds

| Metric | Minimum | Target | Excellent |
|--------|---------|--------|-----------|
| Faithfulness | 0.60 | 0.80 | 0.90 |
| Answer Relevancy | 0.65 | 0.80 | 0.90 |
| Context Precision | 0.60 | 0.75 | 0.85 |
| Context Recall | 0.60 | 0.80 | 0.90 |
| Factual Correctness | 0.70 | 0.85 | 0.95 |
| Semantic Similarity | 0.70 | 0.85 | 0.95 |

### System Requirements

- **Throughput**: 100 test cases / 5 minutes
- **Result Storage**: Dual storage (SQLite + Langfuse)
- **Reproducibility**: Deterministic results (temperature=0)

---

## References

- [Ragas Documentation](https://docs.ragas.io/)
- [Langfuse Documentation](https://langfuse.com/docs)
