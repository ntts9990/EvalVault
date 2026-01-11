## 제1부: 프로젝트 개요

### 1.1 비전과 미션

### 1.1.1 비전 (Vision)

**"RAG 시스템의 품질을 데이터셋/메트릭/트레이싱 관점에서 일관되게 관리하는 운영 콘솔"**

EvalVault는 단순한 점수 계산기가 아닌, RAG 시스템의 품질을 종합적으로 관리하고 개선하는 플랫폼을 지향합니다. 평가 실행부터 결과 분석, 보고서 생성, 그리고 Phoenix/Langfuse 같은 관측 시스템과의 연동까지 하나의 run_id로 끊김 없이 이어지는 통합 워크플로우를 제공합니다.

### 1.1.2 미션 (Mission)

| 차원 | 미션 문구 | 설명 |
|------|-----------|------|
| **평가(Evaluation)** | 데이터셋 기반 다양한 LLM/리트리버/프롬프트 조합을 실험하고 점수/threshold 관리 | Ragas 메트릭과 커스텀 메트릭을 조합하여 정량적 품질 측정 |
| **관측(Observability)** | Stage 단위 이벤트와 메트릭, Langfuse/Phoenix 트레이스를 한 Run ID로 연결 | 검색→재정렬→생성 단계별 성능 추적 |
| **표준 연동(Open RAG Trace)** | OpenTelemetry + OpenInference 스키마로 외부 RAG 시스템도 동일하게 추적 | 표준 스펙 기반 외부 시스템 계측 |
| **학습(Domain Memory)** | 과거 실행으로부터 도메인 지식/패턴을 축적해 threshold, 컨텍스트, 리포트를 자동 보정 | Factual/Experiential/Behavior 레이어를 통한 지속적 학습 |
| **분석(Analysis Pipelines)** | 통계·NLP·인과 모듈이 포함된 DAG 파이프라인으로 결과를 다각도로 해석 | PipelineOrchestrator 기반 자동 분석 |

### 1.2 문제 정의: RAG 시스템 평가의 도전

### 1.2.1 산업적 문제

**문제 1: "모델/프롬프트/리트리버를 바꿨을 때 정말 좋아진 건지 수치로 설명하기 어렵다."**

- **배경**: LLM 모델 업그레이드, 프롬프트 튜닝, 리트리버 알고리즘 변경 등 다양한 실험 수행
- **현황**: 점수만 봐서는 개선의 원인을 파악하기 어렵고, 실험 간 비교가 일관되지 않음
- **영향**: 의사결정 지연, 잘못된 최적화, 리소스 낭비

**문제 2: "LLM 로그, 검색 로그, 트레이스가 여러 곳에 흩어져 있고 한 눈에 병목·품질 이슈를 잡기 힘들다."**

- **배경**: 각 단계별 데이터가 분산되어 있어 전체 파이프라인을 통합적으로 분석하기 어려움
- **현황**: Langfuse, Phoenix, MLflow 등 다양한 관측 시스템을 사용하지만 통합 뷰 부족
- **영향**: 문제 식별 지연, 디버깅 시간 증가, 운영 비용 증가

**문제 3: "팀/프로젝트마다 ad-hoc 스크립트가 늘어나 재현성과 회귀 테스트가 깨지기 쉽다."**

- **배경**: 표준화된 평가 워크플로우 부재, 각자 편한 방식으로 실험
- **현황**: 코드 중복, 문서 부족, 재현성 문제
- **영향**: 팀 생산성 저하, 지식 공유 어려움, 장기 유지보수 어려움

### 1.2.2 기술적 문제

| 문제 | 설명 | 영향 |
|------|------|------|
| **평가 메트릭 붕괴(Metric Collapse)** | 단일 메트릭만 의존 시 일부 성능만 최적화 | 전반적 품질 저하 |
| **환각(Hallucination) 탐지 어려움** | 생성된 내용의 사실적 정확성 검증 어려움 | 신뢰성 저하 |
| **도메인 특화 평가 부족** | 일반 메트릭만으로는 도메인 특성 반영 어려움 | 정확도 저하 |
| **폐쇄망 환경 제약** | 외부 API 의존성, 데이터 보안 요구사항 | 배포 어려움 |
| **Ground Truth 부족** | 정답 데이터 확보 어려움 | 평가 신뢰성 저하 |

### 1.3 솔루션: EvalVault의 다섯 가지 핵심 축

### 1.3.1 데이터셋 중심 평가 (Dataset-Centric Evaluation)

**아키텍트 관점**:
- JSON/CSV/XLSX 데이터셋에 메트릭/threshold/도메인 정보를 함께 정의
- `Dataset` 엔티티가 비즈니스 규칙을 캡슐화하여 불변성 보장
- 동일 데이터셋으로 모델/리트리버/프롬프트 실험을 반복 가능하게 관리

**구현 방법**:
```python
# src/evalvault/domain/entities/dataset.py
@dataclass
class Dataset:
    """평가용 데이터셋."""
    name: str
    version: str
    test_cases: list[TestCase]
    thresholds: dict[str, float] = field(default_factory=dict)

    def get_threshold(self, metric_name: str, default: float = 0.7) -> float:
        """비즈니스 규칙: 임계값 조회"""
        return self.thresholds.get(metric_name, default)
```

**효과**:
- 데이터셋별 threshold 자동 관리로 도메인 특성에 맞는 평가 기준 적용
- 재현성 보장: 동일 데이터셋으로 실험 재현 가능

### 1.3.2 LLM/리트리버 프로필 시스템 (Profile System)

**아키텍트 관점**:
- `ModelConfig`가 YAML(`config/models.yaml`) 기반으로 다중 환경 프로필 관리
- `LLMPort` 인터페이스로 OpenAI, Ollama, vLLM, Azure, Anthropic 등 다양한 제공자 추상화
- 로컬/클라우드/폐쇄망 환경 간에도 동일한 CLI·Web 흐름 유지

**구현 방법**:
```yaml
# config/models.yaml
profiles:
  dev:
    provider: ollama
    model: gemma3:1b
    base_url: http://localhost:11434
    embedding_model: qwen3-embedding:0.6b

  prod:
    provider: openai
    model: gpt-4o-mini
    api_key_env: OPENAI_API_KEY
```

**효과**:
- 프로필 기반으로 모델 전환 시 코드 변경 없이 실험 가능
- 폐쇄망 환경 지원 (Ollama, vLLM)

### 1.3.3 Stage 단위 트레이싱 & 디버깅 (Stage-level Tracing)

**아키텍트 관점**:
- `StageEvent`/`StageMetric`/`DebugReport`로 입력 → 검색 → 리랭크 → 최종 답변까지 단계별로 기록
- `RAGTraceData` 엔티티가 Phoenix/OpenTelemetry span 속성으로 직렬화
- Langfuse·Phoenix 트레이서와 연동해 외부 관측 시스템과 바로 연결

**구현 방법**:
```python
# src/evalvault/domain/entities/rag_trace.py
@dataclass
class RAGTraceData:
    trace_id: str = ""
    query: str = ""
    retrieval: RetrievalData | None = None
    generation: GenerationData | None = None
    final_answer: str = ""
    total_time_ms: float = 0.0

    def to_span_attributes(self) -> dict[str, Any]:
        """Phoenix/OpenTelemetry span 속성으로 변환"""
        attrs = {"rag.total_time_ms": self.total_time_ms}
        if self.retrieval:
            attrs.update(self.retrieval.to_span_attributes())
        if self.generation:
            attrs.update(self.generation.to_span_attributes())
        return attrs
```

**효과**:
- 각 단계의 성능과 품질을 세밀하게 추적하여 병목 지점을 빠르게 식별
- Phoenix/Langfuse와 동일한 run_id로 연동하여 통합 관측 가능

### 1.3.4 Domain Memory & 분석 파이프라인 (Domain Memory & Analysis)

**아키텍트 관점**:
- 과거 실행에서 fact/behavior를 추출해 threshold 튜닝, 컨텍스트 보강, 개선 가이드 자동화
- 통계·NLP·인과 분석 모듈이 포함된 DAG 파이프라인으로 성능 저하 원인 추적
- `FactualFact`, `LearningMemory`, `BehaviorEntry` 세 레이어로 도메인 지식 축적

**구현 방법**:
```python
# src/evalvault/domain/services/memory_aware_evaluator.py
class MemoryAwareEvaluator:
    async def evaluate_with_memory(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,
        memory_port: DomainMemoryPort,
        domain: str,
    ) -> EvaluationRun:
        """Domain Memory 기반 평가"""
        # 1. 신뢰도 점수 조회 및 threshold 조정
        reliability = memory_port.get_aggregated_reliability(domain=domain)
        adjusted_thresholds = self._adjust_by_reliability(metrics, dataset.thresholds, reliability)

        # 2. 컨텍스트 보강
        augmented_dataset = self._augment_context_with_facts(dataset, memory_port)

        # 3. 평가 실행
        return await self._evaluator.evaluate(
            dataset=augmented_dataset,
            metrics=metrics,
            llm=llm,
            thresholds=adjusted_thresholds,
        )
```

**효과**:
- 평가 결과를 학습하여 다음 평가에 자동으로 반영하는 지속적 개선 루프
- 통계/NLP/인과 분석으로 성능 저하 원인 추적

### 1.3.5 Web UI + CLI 일관성 (Unified Experience)

**아키텍트 관점**:
- Typer CLI와 FastAPI + React Web UI가 동일한 DB/트레이스 위에서 동작
- 로컬 실험 → 팀 공유 → CI/CD 게이트까지 하나의 도구 체인으로 연결
- CLI로 빠르게 실험하고, Web UI로 결과를 시각화하고 공유하는 통합 워크플로우

**구현 방법**:
```python
# src/evalvault/adapters/inbound/cli.py
@app.command()
def run(dataset: Path, metrics: str, profile: str):
    """CLI로 평가 실행"""
    loader = get_loader(dataset)
    llm = get_llm_adapter(settings, profile)
    evaluator = RagasEvaluator()
    result = asyncio.run(evaluator.evaluate(loader.load(dataset), metrics, llm))
    _display_results(result)

# src/evalvault/adapters/inbound/api/adapter.py
class WebUIAdapter:
    """Web UI용 어댑터"""
    async def run_evaluation(self, request: EvalRequest) -> EvaluationRun:
        """Web UI로 평가 실행 (동일한 도메인 로직 사용)"""
        loader = get_loader(request.dataset_path)
        llm = get_llm_adapter(settings, request.profile)
        evaluator = RagasEvaluator()
        return await evaluator.evaluate(loader.load(request.dataset_path), request.metrics, llm)
```

**효과**:
- CLI/Web UI 일관된 경험으로 학습 비용 감소
- 로컬 실험과 팀 공유를 하나의 도구 체인으로 연결

### 1.4 주요 사용자와 시나리오

### 1.4.1 개발자 (Developer)

**시나리오**: 새로운 LLM 모델로 실험하고 성능 비교

```
1. CLI로 평가 실행
   $ uv run evalvault run tests/fixtures/insurance_qa.json \
       --metrics faithfulness,answer_relevancy \
       --profile dev \
       --db data/db/evalvault.db

2. 결과 확인 및 히스토리 탐색
   $ uv run evalvault history --db data/db/evalvault.db

3. 두 실행 비교
   $ uv run evalvault compare <RUN_A> <RUN_B> --db data/db/evalvault.db

4. 비교 리포트 확인
   $ cat reports/comparison/comparison_<RUN_A>_<RUN_B>.md
```

**담당 컴포넌트**:
- CLI (`adapters/inbound/cli.py`)
- Dataset Loaders (`adapters/outbound/dataset/`)
- LLM Adapters (`adapters/outbound/llm/`)
- Storage Adapters (`adapters/outbound/storage/`)

### 1.4.2 평가 담당자 (Evaluation Specialist)

**시나리오**: Web UI에서 평가 실행, 업로드, 히스토리 탐색, 기본 보고서 생성

```
1. Web UI 접속 (http://localhost:5173)

2. Evaluation Studio에서 평가 실행
   - 데이터셋 업로드 (JSON/CSV/XLSX)
   - 메트릭 선택
   - 모델 프로필 선택

3. Analysis Lab에서 결과 확인
   - 메트릭 점수 시각화
   - 테스트 케이스별 상세 확인

4. Reports에서 보고서 생성
   - Markdown 보고서 다운로드
   - Phoenix 링크로 고급 분석
```

**담당 컴포넌트**:
- Web API (`adapters/inbound/api/`)
- Frontend (`frontend/`)
- Analysis Services (`domain/services/analysis_service.py`)

### 1.4.3 운영팀 (Operations Team)

**시나리오**: Phoenix 기반 드리프트 감시와 Gate 실행

```
1. Phoenix 대시보드 모니터링
   - Run ID로 트레이스 확인
   - 임베딩 드리프트 확인
   - Stage 메트릭 시각화

2. 평가 결과 확인
   $ uv run evalvault history --limit 10 --db data/db/evalvault.db

3. Gate 테스트 실행
   $ uv run evalvault gate --config regressions/default.json \
       --db data/db/evalvault.db

4. 결과 리포트 공유
   - Slack에 Phoenix 링크 공유
   - 보고서 PDF로 내보내기
```

**담당 컴포넌트**:
- Phoenix Adapter (`adapters/outbound/tracker/phoenix_adapter.py`)
- Regression Runner (`scripts/regression_runner.py`)
- Stage Metrics (`domain/entities/stage.py`)

### 1.5 핵심 가치 제안 (Value Proposition)

### 1.5.1 단순 점수 계산기가 아닌 통합 플랫폼

| 항목 | 기존 방식 | EvalVault |
|------|-----------|-----------|
| **평가 실행** | 수동 스크립트 | CLI/Web UI 통합 |
| **결과 저장** | 파일 분산 | 통합 DB (SQLite/PostgreSQL) |
| **트레이싱** | 별도 도구 | Phoenix/Langfuse 연동 |
| **분석** | 수동 분석 | 자동 DAG 파이프라인 |
| **보고서** | 수만 생성 | 자동 생성 + 템플릿 |

### 1.5.2 재현성과 개선 루프

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                      EvalVault 개선 루프                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. 평가 실행 (CLI/Web UI)                                                     │
│     ├─ 데이터셋 로드                                                            │
│     ├─ 메트릭 선택                                                             │
│     └─ 모델 프로필 선택                                                         │
│         ↓                                                                     │
│  2. 결과 저장 (run_id로 통합 관리)                                              │
│     ├─ EvaluationRun → DB                                                      │
│     ├─ StageEvent → DB                                                         │
│     └─ Phoenix/Langfuse → 트레이스                                              │
│         ↓                                                                     │
│  3. 자동 분석 (DAG 파이프라인)                                                  │
│     ├─ 통계 분석                                                               │
│     ├─ NLP 분석                                                                │
│     └─ 인과 분석                                                               │
│         ↓                                                                     │
│  4. 보고서 생성 (Markdown/JSON)                                                  │
│     ├─ 요약 보고서                                                              │
│     ├─ 상세 보고서                                                              │
│     └─ Phoenix 링크                                                           │
│         ↓                                                                     │
│  5. Domain Memory 학습                                                          │
│     ├─ Fact 추출                                                               │
│     ├─ Pattern 학습                                                             │
│     └─ Behavior 저장                                                            │
│         ↓                                                                     │
│  6. 개선 가이드 (LLM 기반)                                                      │
│     ├─ 패턴 탐지                                                               │
│     ├─ 인사이트 생성                                                             │
│     └─ 액션 제안                                                               │
│         ↓                                                                     │
│  7. 다음 평가에 반영 (자동)                                                    │
│     ├─ Threshold 자동 조정                                                       │
│     ├─ 컨텍스트 보강                                                           │
│     └─ → 1. 평가 실행으로 돌아감                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.5.3 기술적 우위

| 우위 | 설명 | 구현 |
|------|------|------|
| **폐쇄망 지원** | Ollama, vLLM, 로컬 임베딩 | Profile System |
| **표준 스펙 준수** | OpenTelemetry, OpenInference | Open RAG Trace |
| **다양한 메트릭** | Ragas + 커스텀 + Stage | Metrics System |
| **도메인 학습** | Factual/Experiential/Behavior 레이어 | Domain Memory |
| **자동 분석** | DAG 파이프라인 | PipelineOrchestrator |

### 1.6 전문가 관점 적용

### 1.6.1 아키텍트 관점 (Architect Perspective)

**적용 원칙**:
- **의존성 규칙**: 외부 → 내부 방향의 명확한 의존성
- **포트와 어댑터**: 도메인 로직을 외부 의존성으로부터 완전히 격리
- **확장성**: 새로운 LLM 제공자/메트릭/저장소 추가 용이

**실제 구현**:
```
Adapters (외부)
    ↓ depends on
Ports (인터페이스)
    ↓ depends on
Domain (핵심 로직)
```

### 1.6.2 소프트웨어 개발 전문가 관점 (Software Developer Perspective)

**적용 원칙**:
- **SOLID 원칙**: 단일 책임, 개방/폐쇄, 리스코프 치환, 인터페이스 분리, 의존성 역전
- **테스트 가능성**: 포트 인터페이스를 통한 모킹으로 단위 테스트 용이
- **유지보수성**: 각 계층의 책임이 명확하여 코드 이해 및 수정이 용이

**실제 구현**:
```python
# 의존성 주입으로 테스트 용이
class RagasEvaluator:
    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        llm: LLMPort,  # 포트 인터페이스
    ) -> EvaluationRun:
        ...

# 테스트 시 모킹
mock_llm = MockLLMAdapter()
evaluator = RagasEvaluator()
result = await evaluator.evaluate(dataset, metrics, mock_llm)
```

### 1.6.3 UI/UX 전문가 관점 (UI/UX Perspective)

**적용 원칙**:
- **워크플로우 최적화**: 자주 하는 작업을 빠르게
- **점진적 정보 공개**: 기본 → 상세 → 고급 순서
- **피드백 제공**: 모든 액션에 즉각적 피드백

**실제 구현**:
- CLI/Web UI 통합 경험
- Phoenix 링크를 적절한 시점에 표시
- 진행 상황 실시간 표시

---

## 업데이트 이력

| 버전 | 날짜 | 변경 사항 | 담당 |
|------|------|----------|------|
| 1.0.0 | 2026-01-10 | 초기 작성 | EvalVault Team |

## 관련 섹션

- 섹션 2: 아키텍처 설계
- 섹션 3: 데이터 흐름 분석
- 섹션 4: 주요 컴포넌트 상세
- 섹션 5: 전문가 관점 통합 설계
