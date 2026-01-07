# Query-Based DAG Analysis Pipeline 설계 문서

> 사용자 쿼리를 분석하여 자동으로 DAG 스타일 분석 파이프라인을 실행하고 보고서를 생성하는 시스템
>
> **Last Updated**: 2026-01-07
> **Status**: ✅ 구현 완료

## 📚 관련 문서

| 문서 | 역할 |
|------|------|
| [FEATURE_SPECS.md](./FEATURE_SPECS.md) | 기능 스펙 (DAG Pipeline 섹션) |
| [PROJECT_MAP.md](./PROJECT_MAP.md) | 분석 파이프라인 Mermaid 다이어그램 |
| [CLASS_CATALOG.md](./CLASS_CATALOG.md) | PipelineOrchestrator 등 클래스 상세 |

---

## 1. 개요

### 1.1 문제 정의

사용자가 RAG 시스템을 분석할 때 다음과 같은 니즈가 있음:
- "형태소 분석이 제대로 되고 있는지 확인해보고 싶다"
- "RRF와 다른 하이브리드 방식의 성능을 비교하고 싶다"
- "Context Recall이 낮은 이유를 분석하고 싶다"
- "전체 평가 결과를 요약해서 보고서로 만들어줘"

현재 이러한 니즈를 충족하려면:
1. 어떤 분석 도구를 사용해야 하는지 알아야 함
2. 분석 도구를 순서대로 실행해야 함
3. 결과를 해석하고 보고서로 정리해야 함

### 1.2 솔루션

**사용자 쿼리 → 의도 파악 → DAG 파이프라인 구성 → 자동 실행 → 보고서 생성**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  User Query │───▶│Intent Router│───▶│DAG Executor │───▶│   Report    │
│             │    │             │    │             │    │  Generator  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                   │
                          ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │  Analysis   │    │  Analysis   │
                   │   Catalog   │    │   Results   │
                   └─────────────┘    └─────────────┘
```

## 2. scratch/ragrefine 분석

### 2.1 기존 구현체에서 차용할 개념

| 구성요소 | 파일 | 설명 | 재사용 수준 |
|---------|------|------|------------|
| LangGraph State Machine | `agent/graph.py` | Intent 기반 라우팅, 노드 실행 | 아키텍처 차용 |
| Report DAG | `analysis/report_graph.py` | 6단계 보고서 생성 파이프라인 | 패턴 차용 |
| Analysis Tools | `agent/tools/analysis_tools.py` | 12개 분석 도구 (RAGAS, KeyBERT 등) | 인터페이스 참고 |
| Data Pipeline | `analysis/data_pipeline.py` | CSV/Excel 로드 및 검증 | EvalVault 기존 로더 사용 |
| Diagnostic Playbook | `analysis/diagnostic_playbook.py` | 패턴 기반 문제 진단 | 로직 일부 차용 |

### 2.2 주요 차이점

| 항목 | scratch/ragrefine | EvalVault 신규 구현 |
|-----|-------------------|-------------------|
| LLM | Ollama (gpt-oss:20b) | LLMPort 추상화 (OpenAI, Anthropic 등) |
| 아키텍처 | 단일 모듈 | Hexagonal Architecture (Port/Adapter) |
| UI | CLI + FastAPI | React 웹 UI |
| 상태 관리 | LangGraph MemorySaver | EvalVault Session + LangGraph |
| 확장성 | 하드코딩된 분석 도구 | 플러그인 기반 분석 모듈 |

## 3. 아키텍처 설계

### 3.1 Hexagonal Architecture 통합

```
ports/inbound/
├── analysis_pipeline_port.py      # 분석 파이프라인 포트 인터페이스

ports/outbound/
├── analysis_module_port.py        # 분석 모듈 포트 (플러그인)

adapters/inbound/
├── api/
│   └── routers/
│       └── pipeline.py            # FastAPI 분석 API

frontend/
└── src/pages/AnalysisLab.tsx      # React Analysis Lab

adapters/outbound/
├── analysis/
│   ├── morpheme_analyzer.py       # 형태소 분석 어댑터
│   ├── hybrid_search_comparator.py # 하이브리드 검색 비교 어댑터
│   ├── ragas_analyzer.py          # RAGAS 분석 어댑터
│   └── ...

domain/
├── services/
│   ├── query_intent_classifier.py # 쿼리 의도 분류기
│   ├── dag_pipeline_builder.py    # DAG 파이프라인 빌더
│   └── report_generator.py        # 보고서 생성기
├── entities/
│   ├── analysis_intent.py         # 분석 의도 엔티티
│   ├── analysis_pipeline.py       # 분석 파이프라인 엔티티
│   └── analysis_result.py         # 분석 결과 엔티티
```

### 3.2 분석 의도 분류 (Intent Classification)

```python
class AnalysisIntent(Enum):
    """사용자 쿼리에서 파악되는 분석 의도"""

    # 검증 (Verification)
    VERIFY_MORPHEME = "verify_morpheme"           # 형태소 분석 검증
    VERIFY_EMBEDDING = "verify_embedding"         # 임베딩 품질 검증
    VERIFY_RETRIEVAL = "verify_retrieval"         # 검색 품질 검증

    # 비교 (Comparison)
    COMPARE_SEARCH_METHODS = "compare_search"     # 검색 방식 비교 (RRF vs 다른 방식)
    COMPARE_MODELS = "compare_models"             # 모델 비교
    COMPARE_RUNS = "compare_runs"                 # 실행 결과 비교

    # 분석 (Analysis)
    ANALYZE_LOW_METRICS = "analyze_low_metrics"   # 낮은 메트릭 원인 분석
    ANALYZE_PATTERNS = "analyze_patterns"         # 패턴 분석
    ANALYZE_TRENDS = "analyze_trends"             # 시계열 추세 분석

    # 벤치마크 (Benchmark)
    BENCHMARK_RETRIEVAL = "benchmark_retrieval"   # 검색 벤치마크

    # 보고서 (Report)
    GENERATE_SUMMARY = "generate_summary"         # 요약 보고서
    GENERATE_DETAILED = "generate_detailed"       # 상세 보고서
    GENERATE_COMPARISON = "generate_comparison"   # 비교 보고서
```

### 3.3 DAG 파이프라인 구조

```python
@dataclass
class AnalysisPipeline:
    """분석 파이프라인 DAG 정의"""

    intent: AnalysisIntent
    nodes: list[AnalysisNode]
    edges: list[tuple[str, str]]  # (source_node_id, target_node_id)

    def to_langgraph(self) -> StateGraph:
        """LangGraph StateGraph로 변환"""
        ...

@dataclass
class AnalysisNode:
    """분석 노드"""

    id: str
    name: str
    module: str  # 분석 모듈 어댑터 이름
    params: dict[str, Any]
    depends_on: list[str]  # 의존 노드 ID
```

### 3.4 분석 모듈 카탈로그

| 모듈 ID | 이름 | 의존성 | 설명 |
|--------|------|-------|------|
| `data_loader` | 데이터 로더 | storage | StoragePort를 통해 EvaluationRun/metrics 로드 |
| `statistical_analyzer` | 통계 분석기 | data_loader | `StatisticalAnalysisAdapter.analyze()` 호출 |
| `morpheme` | 형태소 분석기 | korean extra | kiwipiepy 기반 형태소 분석 |
| `bm25` | BM25 검색 | korean extra | rank-bm25 기반 키워드 검색 |
| `hybrid_rrf` | RRF 하이브리드 | morpheme, bm25 | Reciprocal Rank Fusion |
| `hybrid_weighted` | 가중치 하이브리드 | morpheme, bm25 | 가중 합산 방식 |
| `embedding_quality` | 임베딩 품질 | - | 임베딩 분포 및 유사도 분석 |
| `ragas_eval` | RAGAS 평가 | - | 6개 메트릭 평가 |
| `diagnostic` | 진단 플레이북 | ragas_eval | 패턴 기반 문제 진단 |
| `causal` | 인과 분석 | ragas_eval | 메트릭 간 인과 관계 분석 |
| `retrieval_benchmark` | 검색 벤치마크 | - | 문서/쿼리 기반 검색 성능 평가 |
| `report` | 보고서 생성 | * | LLM 기반 종합 보고서 |

`data_loader` → `statistical_analyzer` 구간은 베이스 분석 어댑터와 직접 연동됩니다.
- DataLoaderModule은 StoragePort(예: SQLite/SQLiteStorageAdapter)를 사용해 `run_id` 기반 EvaluationRun을 불러오고, 로드된 객체와 메트릭 시리즈를 다음 노드에 전달합니다.
- StatisticalAnalyzerModule은 `StatisticalAnalysisAdapter`를 주입받아 `analyze(run)`을 실행하고, 생성된 `StatisticalAnalysis`를 요약/통계 딕셔너리로 직렬화하여 후속 보고서 모듈이 그대로 소비하도록 합니다.

### 3.5 파이프라인 정책

#### 빈 파이프라인 정책

`PipelineOrchestrator.build_pipeline()`은 템플릿이 없는 의도에 대해 빈 파이프라인(`AnalysisPipeline(intent=intent)`)을 반환합니다. 이는 다음과 같은 설계 결정에 기반합니다:

- **허용**: 빈 파이프라인은 유효한 상태로 간주됩니다. 실행 시 노드가 없으므로 즉시 완료되며, `PipelineResult.all_succeeded`는 `True`를 반환합니다.
- **용도**: 새로운 의도 추가 시 점진적 구현을 지원하고, 테스트 환경에서 파이프라인 인프라만 검증할 때 유용합니다.
- **현황**: 현재 모든 12개 `AnalysisIntent`에 대해 템플릿이 등록되어 있어 실제 운영에서 빈 파이프라인이 생성되지 않습니다.

#### 모듈 미등록 처리

등록되지 않은 모듈을 참조하는 노드 실행 시:

```python
NodeResult(
    node_id=node.id,
    status=NodeExecutionStatus.FAILED,
    error=f"Module not found: {node.module}",
)
```

- **실패 전파**: 실패한 노드에 의존하는 후속 노드는 `SKIPPED` 상태로 처리됩니다.
- **에러 메시지**: 누락된 모듈 ID가 에러 메시지에 포함되어 디버깅을 용이하게 합니다.
- **권장 사항**: 새 템플릿 추가 시 `scripts/pipeline_template_inspect.py`로 모듈 등록 상태를 먼저 확인하세요.

## 4. 쿼리-파이프라인 매핑

### 4.1 예시 쿼리와 생성되는 파이프라인

#### 예시 1: "형태소 분석이 제대로 되고 있는지 확인"

```yaml
intent: VERIFY_MORPHEME
pipeline:
  nodes:
    - id: load_data
      module: data_loader
    - id: morpheme_analysis
      module: morpheme
      depends_on: [load_data]
    - id: quality_check
      module: morpheme_quality_checker
      depends_on: [morpheme_analysis]
    - id: report
      module: verification_report
      depends_on: [quality_check]

  execution_order:
    load_data → morpheme_analysis → quality_check → report
```

#### 예시 2: "RRF와 다른 하이브리드 방식 성능 비교"

```yaml
intent: COMPARE_SEARCH_METHODS
pipeline:
  nodes:
    - id: load_data
      module: data_loader
    - id: morpheme_analysis
      module: morpheme
      depends_on: [load_data]
    - id: bm25_search
      module: bm25
      depends_on: [morpheme_analysis]
    - id: embedding_search
      module: embedding_retrieval
      depends_on: [load_data]
    - id: rrf_hybrid
      module: hybrid_rrf
      depends_on: [bm25_search, embedding_search]
    - id: weighted_hybrid
      module: hybrid_weighted
      depends_on: [bm25_search, embedding_search]
    - id: comparison
      module: search_comparator
      depends_on: [rrf_hybrid, weighted_hybrid]
    - id: report
      module: comparison_report
      depends_on: [comparison]

  execution_order:
    load_data → morpheme_analysis → bm25_search ─┬─▶ rrf_hybrid ────┬─▶ comparison → report
               └─▶ embedding_search ─┴─▶ weighted_hybrid ─┘
```

#### 예시 3: "Context Recall이 낮은 이유 분석"

```yaml
intent: ANALYZE_LOW_METRICS
target_metric: context_recall
pipeline:
  nodes:
    - id: load_data
      module: data_loader
    - id: ragas_eval
      module: ragas_evaluator
      depends_on: [load_data]
    - id: low_samples
      module: low_performer_extractor
      params: {metric: context_recall, threshold: 0.5}
      depends_on: [ragas_eval]
    - id: diagnostic
      module: diagnostic_playbook
      depends_on: [ragas_eval]
    - id: causal
      module: causal_analyzer
      depends_on: [ragas_eval]
    - id: root_cause
      module: root_cause_analyzer
      depends_on: [low_samples, diagnostic, causal]
    - id: report
      module: analysis_report
      depends_on: [root_cause]
```

### 4.5 AI Agent 작업 가이드

1. **템플릿 파악**
   `python scripts/pipeline_template_inspect.py --intent analyze_low_metrics` 명령으로
   의도별 DAG 노드와 의존성을 확인합니다. `--intent all` 옵션을 주면 모든 템플릿을
   스캔할 수 있어 새로운 자동화 시나리오를 설계할 때 빠르게 참조할 수 있습니다.

2. **모듈 계약 확인**
   모든 분석 모듈은 `BaseAnalysisModule`을 상속하고 `module_id`, `metadata`를 채워야 합니다.
   `PipelineOrchestrator.register_module()`는 이 metadata를 `ModuleCatalog`에 적재하므로,
   새 모듈을 추가할 때는 register 호출을 잊지 말아야 하며, metadata가 누락되면
   템플릿 검증 및 스크립트 생성이 실패합니다.

3. **파이프라인 빌드 & 실행**
   `AnalysisPipelineService`(또는 `PipelineOrchestrator`)를 사용하여
   `register_module → build_pipeline(intent, context) → execute(pipeline, context)` 순으로
   실행합니다. Web/CLI 어댑터도 동일한 방식으로 동작하므로, AI 코딩 에이전트가 동일한
   순서를 자동화에 재사용할 수 있습니다.

4. **의존성 주입 규칙**
   분석 모듈은 외부 API 접근 시 반드시 outbound port를 통해 의존성을 주입받아야 하며,
   모듈 metadata의 `requires`/`optional_requires` 필드를 채워 템플릿 레벨에서
   의존성 그래프를 추적할 수 있도록 해야 합니다.

## 5. 구현 상태 (2026-01-07 현행화)

> **Phase 14 전체 완료** - DAG 분석 파이프라인이 구현되어 운영 중입니다.

### Phase 14.1: 기반 인프라 ✅ 완료

**목표**: 분석 파이프라인 포트/어댑터 기본 구조

- [x] `AnalysisPipelinePort` 인터페이스 정의
- [x] `AnalysisModulePort` 플러그인 인터페이스 정의
- [x] `AnalysisIntent` 엔티티 및 분류기 구현
- [x] `AnalysisPipeline` 엔티티 구현
- [x] 테스트 작성 (TDD)

**구현 파일**:
- `src/evalvault/ports/inbound/analysis_pipeline_port.py`
- `src/evalvault/ports/outbound/analysis_module_port.py`
- `src/evalvault/domain/entities/analysis_pipeline.py` (AnalysisIntent 포함)
- `tests/unit/test_analysis_pipeline.py`

### Phase 14.2: 의도 분류기 ✅ 완료

**목표**: 사용자 쿼리에서 분석 의도 추출

- [x] 키워드 기반 규칙 분류기 (MVP)
- [ ] LLM 기반 분류기 (향후 확장)
- [x] 의도별 파이프라인 템플릿 매핑
- [x] 테스트 작성

**구현 파일**:
- `src/evalvault/domain/services/intent_classifier.py`
- `src/evalvault/domain/services/pipeline_template_registry.py`
- `src/evalvault/ports/outbound/intent_classifier_port.py`
- `tests/unit/test_intent_classifier.py`

### Phase 14.3: DAG 파이프라인 빌더 ✅ 완료

**목표**: DAG 기반 파이프라인 구성 및 실행

- [x] `PipelineOrchestrator` 서비스 구현
- [x] DAG 토폴로지 정렬 및 실행
- [x] 노드 실행 및 결과 수집
- [x] 에러 핸들링 (실패/스킵 전파)
- [x] 테스트 작성

**구현 파일**:
- `src/evalvault/domain/services/pipeline_orchestrator.py`
- `tests/unit/test_pipeline_orchestrator.py`

### Phase 14.4: 분석 모듈 어댑터 ✅ 완료 (40+ 모듈)

**목표**: 핵심 분석 모듈 구현

MVP 완료:
- [x] `morpheme_analyzer_module.py` - 형태소 분석
- [x] `bm25_searcher_module.py` - BM25 검색
- [x] `hybrid_rrf_module.py`, `hybrid_weighted_module.py` - 하이브리드 검색
- [x] `diagnostic_playbook_module.py` - 진단 플레이북

확장 구현:
- `data_loader_module.py`, `run_loader_module.py` - 데이터 로딩
- `statistical_analyzer_module.py`, `nlp_analyzer_module.py`, `causal_analyzer_module.py` - 분석
- `summary_report_module.py`, `verification_report_module.py`, `comparison_report_module.py` - 보고서
- `embedding_*_module.py` - 임베딩 분석
- `retrieval_*_module.py` - 검색 분석
- 기타 40+ 모듈

**구현 위치**: `src/evalvault/adapters/outbound/analysis/`

### Phase 14.5: 보고서 생성기 ✅ 완료

**목표**: 분석 결과를 보고서로 변환

- [x] Markdown 보고서 템플릿 (`summary_report_module.py`)
- [x] LLM 요약 통합 (`llm_report_module.py`)
- [x] 다양한 리포트 타입 (verification, comparison, analysis, detailed)

**구현 파일**:
- `src/evalvault/adapters/outbound/analysis/*_report_module.py`
- `src/evalvault/adapters/outbound/report/markdown_adapter.py`

### Phase 14.6: CLI 통합 ✅ 완료

**목표**: CLI pipeline 명령어

- [x] 쿼리 기반 파이프라인 실행 (`evalvault pipeline analyze`)
- [x] 템플릿 조회 (`scripts/pipeline_template_inspect.py`)

**참고**: Web UI 통합은 React 기반 별도 개발 진행 중

## 6. 확장 계획

### 6.1 추가 분석 모듈 (향후)

| 모듈 | 설명 | 우선순위 |
|-----|------|---------|
| Topic Clustering | 토픽 클러스터링 | Medium |
| KeyBERT Analysis | 키워드 추출 | Medium |
| Temporal Analysis | 시계열 분석 | Low |
| Causal Analysis | 인과 분석 | Low |
| Network Graph | 네트워크 그래프 | Low |

### 6.2 LLM 통합 (향후)

- 의도 분류에 LLM 사용 (현재 키워드 기반)
- 보고서 생성에 LLM 요약 통합
- 대화형 분석 (follow-up 질문)

### 6.3 플러그인 시스템 (향후)

- 외부 분석 모듈 등록/해제
- 커스텀 파이프라인 템플릿 저장
- 분석 결과 캐싱

## 7. 기술 스택

| 구성요소 | 기술 | 이유 |
|---------|------|-----|
| DAG 실행 | LangGraph | 상태 관리, 조건부 라우팅, 체크포인팅 |
| 형태소 분석 | kiwipiepy | 한국어 최적화, 순수 Python |
| BM25 검색 | rank-bm25 | 가벼운 키워드 검색 |
| 웹 UI | React + FastAPI | 빠른 프로토타이핑, 분리된 프론트/백엔드 |
| 시각화 | Plotly | 인터랙티브 차트 |
| 보고서 | Jinja2 + WeasyPrint | HTML/PDF 생성 |

## 8. 성공 지표

### 8.1 MVP 완료 기준

- [ ] 최소 3가지 분석 의도 지원 (검증, 비교, 분석)
- [ ] DAG 파이프라인 자동 구성 및 실행
- [ ] Markdown 보고서 생성
- [ ] 웹 UI 통합
- [ ] 단위 테스트 80% 이상 커버리지

### 8.2 사용자 경험 목표

- 쿼리 입력 → 보고서 생성: 5분 이내
- 파이프라인 시각화로 진행 상황 파악 가능
- 보고서 다운로드 (PDF/HTML/Markdown)

## 9. 참고 자료

- `scratch/ragrefine/agent/graph.py` - LangGraph 상태 머신 구현
- `scratch/ragrefine/analysis/report_graph.py` - 보고서 DAG 구현
- `scratch/ragrefine/agent/tools/analysis_tools.py` - 12개 분석 도구
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) - 공식 문서
