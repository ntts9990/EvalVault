## 제3부: 데이터 흐름 분석

### 3.1 평가 실행 흐름 (Evaluation Flow)

### 3.1.1 전체 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        평가 실행 전체 흐름                                  │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 사용자 입력
    │
    ├─ CLI: uv run evalvault run dataset.json --metrics faithfulness --profile dev
    └─ Web UI: Evaluation Studio에서 데이터셋 업로드 및 메트릭 선택
    │
    ▼
[2] Inbound Adapter (입력 처리)
    │  - 명령 파싱 및 검증 (CLI)
    │  - 요청 본문 파싱 (Web API)
    │  - 설정 로드 (settings.py, models.yaml)
    │
    ├─> [3] Dataset Loader Factory
    │      │  - 파일 형식 감지
    │      │  - 적절한 로더 선택 (Strategy 패턴)
    │      │
    │      ▼
    │  [4] CSV/Excel/JSON Loader (adapters/outbound/dataset/)
    │      │  - 파일 읽기
    │      │  - Dataset 엔티티로 변환
    │      │
    │      └─> [5] Dataset 엔티티 (domain/entities/dataset.py)
    │              │  - name, version, test_cases, thresholds
    │
    ├─> [6] LLM Adapter Factory
    │      │  - 프로바이더 설정 확인
    │      │  - 적절한 어댑터 생성
    │      │
    │      ▼
    │  [7] OpenAI/Anthropic/Ollama/vLLM Adapter (adapters/outbound/llm/)
    │      │  - LLM 클라이언트 초기화
    │      │  - LLMPort 구현
    │      │
    │      └─> [8] LLMPort 인터페이스 (ports/outbound/llm_port.py)
    │              │  - get_model_name(), as_ragas_llm()
    │
    ├─> [6a] Domain Memory 초기화 (--use-domain-memory 옵션)
    │      │  - SQLiteDomainMemoryAdapter 생성
    │      │  - MemoryAwareEvaluator 생성
    │      │  - 신뢰도 점수 조회 및 threshold 자동 조정
    │      │
    │      └─> [6b] MemoryAwareEvaluator (domain/services/memory_aware_evaluator.py)
    │              │  - RagasEvaluator 래핑
    │              │  - DomainMemoryPort 주입
    │              │
    │              └─> [6c] 컨텍스트 보강 (--augment-context 옵션)
    │                      │  - 각 테스트 케이스 질문으로 관련 사실 검색
    │                      │  - 컨텍스트에 사실 추가
    │
    └─> [9] RagasEvaluator 또는 MemoryAwareEvaluator (domain/services/evaluator.py)
            │  - 평가 실행 오케스트레이션
            │  - 메모리 활용 시: 조정된 threshold로 평가
            │
            ├─> [10] Ragas 메트릭 실행
            │       │  - LLMPort.as_ragas_llm() 호출
            │       │  - 각 테스트 케이스 평가
            │       │
            │       └─> [11] LLM Adapter
            │               - 실제 LLM API 호출
            │               - 토큰 사용량 추적
            │
            ├─> [12] 커스텀 메트릭 실행
            │       │  - InsuranceTermAccuracy 등
            │       │
            │       └─> [13] 도메인 메트릭 (domain/metrics/)
            │
            └─> [14] 결과 집계
                    │  - TestCaseResult 생성
                    │  - EvaluationRun 생성
                    │  - 통과/실패 판정
                    │
                    └─> [15] EvaluationRun 엔티티 (domain/entities/result.py)
                            │  - run_id, dataset_name, model_name, results, metrics_evaluated, thresholds, pass_rate

[16] 결과 출력
    │  - CLI Adapter가 결과 포맷팅
    │  - Web UI Adapter가 결과 반환
    │
    ├─> [17] Storage Adapter (선택적)
    │       │  - EvaluationRun 저장
    │       │
    │       └─> [18] SQLite/PostgreSQL
    │               │  - evaluations, test_case_results, metric_scores 테이블
    │
    └─> [19] Tracker Adapter (선택적)
            │  - Langfuse/MLflow/Phoenix에 기록
            │
            └─> [20] 추적 시스템
                    │  - Trace 생성, Span 로깅, Score 기록
```

### 3.1.2 코드 예시

```python
# CLI 실행 흐름
@app.command()
def run(
    dataset: Path,
    metrics: str,
    model: str | None = None,
    profile: str = "dev",
    use_domain_memory: bool = False,
    augment_context: bool = False,
):
    """Run RAG evaluation on a dataset."""
    # 1. 입력 파싱
    metric_list = [m.strip() for m in metrics.split(",")]

    # 2. 설정 로드
    settings = Settings()

    # 3. Dataset 로드
    loader = get_loader(dataset)  # DatasetPort 구현
    ds = loader.load(dataset)

    # 4. LLM 어댑터 생성
    llm = get_llm_adapter(settings, profile)  # LLMPort 구현

    # 5. Domain Memory 초기화 (옵션)
    evaluator = RagasEvaluator()
    if use_domain_memory:
        memory_port = get_domain_memory_adapter(settings)
        evaluator = MemoryAwareEvaluator(evaluator, memory_port)
        # Threshold 자동 조정
        if augment_context:
            ds = evaluator.augment_context_with_facts(ds, memory_port)

    # 6. 평가 실행
    result = asyncio.run(evaluator.evaluate(ds, metric_list, llm))

    # 7. 결과 출력
    _display_results(result)

    # 8. 저장 (옵션)
    if settings.db_path:
        storage = get_storage_adapter(settings)
        storage.save_run(result)

    # 9. 추적 (옵션)
    if settings.tracker_type:
        tracker = get_tracker_adapter(settings)
        tracker.log_evaluation_run(result)
```

### 3.2 실험 관리 흐름 (Experiment Flow)

### 3.2.1 전체 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        A/B 테스트 실험 흐름                                   │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 실험 생성
    │
    ▼
[2] ExperimentManager.create_experiment()
    │  - Experiment 엔티티 생성
    │  - 그룹 초기화
    │
    └─> [3] Experiment 엔티티 (domain/entities/experiment.py)
            │  - experiment_id, name, description, metrics_to_compare
            │  - groups: dict[str, ExperimentGroup]

[4] 그룹 추가
    │
    ▼
[5] Experiment.add_group()
    │  - ExperimentGroup 생성
    │  - 그룹 메타데이터 설정
    │
    └─> [6] ExperimentGroup 엔티티
            │  - group_id, name, description, baseline
            │  - run_ids: list[str]

[7] 평가 실행 추가
    │
    ▼
[8] Experiment.add_run_to_group()
    │  - 그룹에 run_id 추가
    │
    └─> [9] Storage Adapter
            │  - EvaluationRun 저장
            │  - experiment_runs 테이블에 run_id와 group_id 매핑
            │
            └─> [10] 데이터베이스

[11] 그룹 비교
     │
     ▼
[12] ExperimentManager.compare_groups()
     │  - 각 그룹의 EvaluationRun 조회
     │  - 메트릭별 평균 점수 계산
     │  - 최고 그룹 및 개선율 계산
     │
     ├─> [13] Storage Adapter
     │       │  - StoragePort.get_run() 호출
     │       │
     │       └─> [14] 데이터베이스
     │
     └─> [15] MetricComparison 결과
             │  - metric_name, group_scores, best_group, improvement
```

### 3.2.2 코드 예시

```python
# 실험 관리
class ExperimentManager:
    """실험 관리 서비스."""

    def __init__(self, storage: StoragePort):
        self._storage = storage
        self._experiments: dict[str, Experiment] = {}

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str,
        metrics_to_compare: list[str],
    ) -> Experiment:
        """실험 생성"""
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            metrics_to_compare=metrics_to_compare,
            groups={},
        )
        self._experiments[experiment_id] = experiment
        return experiment

    def add_group(
        self,
        experiment_id: str,
        group_id: str,
        name: str,
        baseline: bool = False,
    ) -> ExperimentGroup:
        """그룹 추가"""
        experiment = self.get_experiment(experiment_id)
        group = ExperimentGroup(
            group_id=group_id,
            name=name,
            baseline=baseline,
            run_ids=[],
        )
        experiment.groups[group_id] = group
        return group

    def add_run_to_group(
        self,
        experiment_id: str,
        group_id: str,
        run_id: str,
    ):
        """평가 실행을 그룹에 추가"""
        experiment = self.get_experiment(experiment_id)
        group = experiment.groups[group_id]
        group.run_ids.append(run_id)

    def compare_groups(self, experiment_id: str) -> list[MetricComparison]:
        """그룹 간 메트릭 비교 - 비즈니스 로직"""
        experiment = self.get_experiment(experiment_id)

        # 각 그룹의 run 데이터 수집
        group_runs = self._collect_group_runs(experiment)

        # 메트릭별 비교 (비즈니스 규칙)
        comparisons = []
        for metric in experiment.metrics_to_compare:
            group_scores = self._calculate_group_scores(group_runs, metric)
            best_group = max(group_scores, key=group_scores.get)
            improvement = self._calculate_improvement(group_scores, best_group)

            comparisons.append(MetricComparison(
                metric_name=metric,
                group_scores=group_scores,
                best_group=best_group,
                improvement=improvement,
            ))

        return comparisons
```

### 3.3 테스트셋 생성 흐름 (Testset Generation Flow)

### 3.3.1 전체 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        테스트셋 생성 흐름                                   │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 문서 입력
    │
    ├─ CLI: evalvault generate doc.pdf --method basic
    └─ Web UI: Knowledge Base에서 문서 업로드 및 생성 방법 선택
    │
    ▼
[2] Inbound Adapter
    │  - 문서 파일 읽기
    │  - 생성 방법 선택
    │
    └─> [3] 문서 텍스트

[4] 생성 방법 선택
    │
    ├─> [5] Basic Method
    │       │
    │       ▼
    │   [6] BasicTestsetGenerator
    │       │  - DocumentChunker 사용
    │       │  - 청크에서 질문 생성
    │       │
    │       └─> [7] Dataset 엔티티
    │               │  - name, version, test_cases, thresholds
    │
    └─> [8] Knowledge Graph Method
            │
            ▼
        [9] KnowledgeGraphGenerator
            │  - EntityExtractor 사용
            │  - 지식 그래프 구축
            │  - 그래프에서 질문 생성
            │
            └─> [10] Dataset 엔티티
                    │  - name, version, test_cases, thresholds

[11] 결과 저장
     │  - JSON 파일로 저장
     │  - CSV/Excel 변환 가능
     │
     └─> [12] 파일 시스템
```

### 3.3.2 코드 예시

```python
# 테스트셋 생성
class BasicTestsetGenerator:
    """기본 테스트셋 생성기."""

    def __init__(self, chunker: DocumentChunker):
        self._chunker = chunker

    def generate(
        self,
        documents: list[str],
        llm: LLMPort,
    ) -> Dataset:
        """문서에서 테스트셋 생성"""
        # 1. 문서 청킹
        chunks = self._chunker.chunk_documents(documents)

        # 2. 청크에서 질문 생성
        test_cases = []
        for i, chunk in enumerate(chunks):
            question = self._generate_question(chunk, llm)
            # 3. 답변 생성 (같은 청크 사용)
            answer = self._generate_answer(chunk, llm)

            test_cases.append(TestCase(
                id=f"tc-{i+1:03d}",
                question=question,
                answer=answer,
                contexts=[chunk],
                ground_truth=answer,  # 동일 청크 사용
            ))

        # 4. Dataset 생성
        return Dataset(
            name="generated-dataset",
            version="1.0.0",
            test_cases=test_cases,
        )

    def _generate_question(self, chunk: str, llm: LLMPort) -> str:
        """청크에서 질문 생성"""
        prompt = f"""
다음 텍스트를 바탕으로 질문을 생성하세요:

텍스트:
{chunk}

질문:
"""
        ragas_llm = llm.as_ragas_llm()
        response = ragas_llm.invoke(prompt)
        return response.content

    def _generate_answer(self, chunk: str, llm: LLMPort) -> str:
        """청크에서 답변 생성"""
        # 질문과 동일한 청크 사용
        return chunk[:100]  # 간단하게 청크의 앞부분 사용

class KnowledgeGraphTestsetGenerator:
    """지식 그래프 기반 테스트셋 생성기."""

    def __init__(self, kg_generator: KnowledgeGraphGenerator):
        self._kg_generator = kg_generator

    def generate(
        self,
        documents: list[str],
        llm: LLMPort,
    ) -> Dataset:
        """문서에서 테스트셋 생성 (지식 그래프 활용)"""
        # 1. 지식 그래프 생성
        kg = self._kg_generator.generate_from_documents(documents, llm)

        # 2. 그래프에서 질문 생성
        test_cases = []
        for i, entity in enumerate(kg.entities[:10]):  # 상위 10개 엔티티
            # 엔티티와 관련된 관계로 질문 생성
            question = self._generate_question_from_entity(kg, entity, llm)
            # 3. 관련 컨텍스트 수집
            contexts = self._get_related_contexts(kg, entity, documents)

            test_cases.append(TestCase(
                id=f"tc-{i+1:03d}",
                question=question,
                answer="",  # 추후 생성
                contexts=contexts,
                ground_truth="",  # 추후 생성
            ))

        # 4. Dataset 생성
        return Dataset(
            name="kg-generated-dataset",
            version="1.0.0",
            test_cases=test_cases,
        )
```

### 3.4 분석 파이프라인 흐름 (Analysis Pipeline Flow)

### 3.4.1 전체 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        분석 파이프라인 실행 흐름                                │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 사용자 쿼리 입력
    │  예: "요약해줘", "비교해줘", "검증해줘"
    │
    ├─ CLI: evalvault pipeline analyze "요약해줘" --run-id abc123
    └─ Web UI: Analysis Lab에서 쿼리 입력 및 파이프라인 템플릿 선택
    │
    ▼
[2] Inbound Adapter (입력 처리)
    │  - 쿼리 파싱
    │
    └─> [3] PipelineOrchestrator
            │  - 모듈 카탈로그, 템플릿 레지스트리, 의도 분류기 주입
            │
            ├─> [4] IntentClassifier
            │       │  - 키워드 기반 의도 분류
            │       │  - AnalysisIntent 추출
            │       │
            │       └─> [5] AnalysisIntent
            │               │  - VERIFY, COMPARE, ANALYZE, GENERATE 등
            │
            ├─> [6] TemplateRegistry
            │       │  - 의도별 템플릿 조회
            │       │
            │       └─> [7] AnalysisPipeline 템플릿
            │               │  - 노드 및 엣지 정의
            │               │  - 노드 ID와 의존성
            │
            └─> [8] Pipeline 빌드
                    │  - 템플릿 복사
                    │  - 컨텍스트 주입
                    │
                    └─> [9] AnalysisPipeline 엔티티
                            │  - intent, nodes, edges, context

[10] 파이프라인 실행
     │
     ▼
[11] PipelineOrchestrator.execute_pipeline()
     │  - DAG 토폴로지 정렬
     │  - 의존성 순서대로 실행
     │
     ├─> [12] AnalysisModule 실행
     │       │  - StatisticalAnalysisModule
     │       │  - NLPAnalysisModule
     │       │  - CausalAnalysisModule
     │       │  - ReportModule
     │       │
     │       └─> [13] NodeResult
     │               │  - node_id, data, metadata
     │
     └─> [14] PipelineResult
             │  - 모든 노드 결과 집계
             │  - 최종 리포트 생성
```

### 3.4.2 코드 예시

```python
# 파이프라인 오케스트레이터
@dataclass
class PipelineOrchestrator:
    """파이프라인 오케스트레이터."""

    module_catalog: ModuleCatalog
    template_registry: PipelineTemplateRegistry
    intent_classifier: KeywordIntentClassifier
    _modules: dict[str, AnalysisModulePort]

    def __post_init__(self):
        self._modules = self._load_modules()

    def build_pipeline(
        self,
        intent: AnalysisIntent,
        context: AnalysisContext,
    ) -> AnalysisPipeline:
        """의도와 컨텍스트에 따라 파이프라인 빌드"""
        # 1. 템플릿 조회
        template = self.template_registry.get_template(intent)

        # 2. 파이프라인 복사
        pipeline = deepcopy(template)

        # 3. 컨텍스트 주입
        pipeline.context = context

        # 4. 노드 모듈 연결
        for node in pipeline.nodes:
            module = self._modules[node.module_id]
            node.module = module

        return pipeline

    async def execute_pipeline(
        self,
        pipeline: AnalysisPipeline,
        context: AnalysisContext,
    ) -> PipelineResult:
        """파이프라인 실행"""
        # 1. DAG 토폴로지 정렬
        execution_order = self._topological_sort(pipeline)

        # 2. 노드 순차 실행
        results = {}
        for node_id in execution_order:
            node = pipeline.nodes[node_id]

            # 3. 의존성 체크
            dependencies = self._get_dependencies(node, pipeline)
            if not all(dep.id in results for dep in dependencies):
                raise ValueError(f"의존성이 충족되지 않음: {node_id}")

            # 4. 노드 실행
            input_data = self._prepare_input(node, results, dependencies)
            node_result = await node.module.execute(context, input_data)
            results[node_id] = node_result

        # 5. 결과 집계
        return PipelineResult(
            pipeline_id=pipeline.id,
            results=results,
            context=context,
        )

    def _topological_sort(self, pipeline: AnalysisPipeline) -> list[str]:
        """DAG 토폴로지 정렬 (Kahn's algorithm)"""
        in_degree = {node.id: len(node.dependencies) for node in pipeline.nodes}
        queue = [node.id for node in pipeline.nodes if len(node.dependencies) == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            # 진입 간선 감소
            for node in pipeline.nodes:
                if node_id in node.dependencies:
                    in_degree[node.id] -= 1
                    if in_degree[node.id] == 0:
                        queue.append(node.id)

        if len(result) != len(pipeline.nodes):
            raise ValueError("순환 의존성이 존재합니다!")

        return result
```

### 3.5 도메인 메모리 형성 흐름 (Domain Memory Formation Flow)

### 3.5.1 전체 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        도메인 메모리 형성 흐름                                 │
└─────────────────────────────────────────────────────────────────────────────┘

[1] 평가 완료
    │  - EvaluationRun 생성 완료
    │
    ▼
[2] DomainLearningHook.on_evaluation_complete()
    │  - 평가 결과 처리 훅 호출
    │
    ├─> [3] Factual Layer 형성
    │       │  - 평가 결과에서 SPO 트리플 추출
    │       │  - 높은 신뢰도 사실만 저장
    │       │
    │       └─> [4] DomainMemoryPort.save_fact()
    │               └─> [5] SQLiteDomainMemoryAdapter
    │                       └─> [6] 도메인 메모리 DB
    │                               │  - facts 테이블 (subject, predicate, object, confidence, ...)
    │
    ├─> [7] Experiential Layer 형성
    │       │  - 성공/실패 패턴 추출
    │       │  - 메트릭별 점수 분포 학습
    │       │
    │       └─> [8] DomainMemoryPort.save_learning()
    │
    └─> [9] Behavior Layer 형성
            │  - 재사용 가능한 행동 패턴 추출
            │  - 성공률 기반 필터링
            │
            └─> [10] DomainMemoryPort.save_behavior()

[11] 메모리 활용
     │  - 향후 평가에서 메모리 검색
     │  - Knowledge Graph 연동
```

### 3.5.2 코드 예시

```python
# 도메인 학습 훅
class DomainLearningHook:
    """평가 결과에서 메모리 형성 훅."""

    def __init__(self, memory_port: DomainMemoryPort):
        self._memory_port = memory_port

    def on_evaluation_complete(
        self,
        run: EvaluationRun,
    ):
        """평가 종료 후 메모리 형성"""
        # 1. Factual Layer 형성
        self._form_factual_layer(run)

        # 2. Experiential Layer 형성
        self._form_experiential_layer(run)

        # 3. Behavior Layer 형성
        self._form_behavior_layer(run)

    def _form_factual_layer(self, run: EvaluationRun):
        """Factual Layer 형성"""
        for result in run.results:
            # 높은 faithfulness 점수를 가진 케이스에서 사실 추출
            faithfulness_score = result.get_metric("faithfulness").score
            if faithfulness_score > 0.85:  # 높은 점수만
                # 답변에서 주장(Claim) 추출
                claims = self._extract_claims(result.answer)

                for claim in claims:
                    # 컨텍스트에서 사실(SPO 트리플) 추출
                    fact = self._extract_fact(claim, result.contexts)

                    if fact:
                        # 신뢰도 계산 (faithfulness 기반)
                        confidence = min(faithfulness_score, 0.95)

                        # 메모리에 저장
                        fact_id = self._memory_port.save_fact(FactualFact(
                            subject=fact["subject"],
                            predicate=fact["predicate"],
                            object=fact["object"],
                            confidence=confidence,
                            source_run_id=run.run_id,
                            source_test_case_id=result.test_case_id,
                        ))

    def _form_experiential_layer(self, run: EvaluationRun):
        """Experiential Layer 형성"""
        # 메트릭별 점수 분포 학습
        metric_distributions = self._calculate_metric_distributions(run)

        for metric_name, distribution in metric_distributions.items():
            # 평균, 표준편차, 최솟값, 최댓값 계산
            learning = LearningMemory(
                metric_name=metric_name,
                domain=run.dataset_name,
                avg_score=distribution["avg"],
                std_score=distribution["std"],
                min_score=distribution["min"],
                max_score=distribution["max"],
                timestamp=datetime.now(),
                source_run_id=run.run_id,
            )

            # 메모리에 저장
            self._memory_port.save_learning(learning)
```

### 3.6 관측성 · 추적 흐름 (Observability & Tracing Flow)

### 3.6.1 전체 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  Open RAG Trace 표준 연동 흐름                                   │
└─────────────────────────────────────────────────────────────────────────────┘

[1] CLI --phoenix-enabled / --tracker 옵션
    │
    ├─ CLI: evalvault run dataset.json --tracker phoenix --phoenix-enabled
    └─ Web UI: Observability Settings에서 Phoenix 설정
    │
    ▼
[2] Phoenix/Instrumentation 설정
    │  - OpenTelemetry TracerProvider 구성
    │  - LangChain/OpenAI 자동 계측
    │
    └─> instrumentation_span() 컨텍스트 매니저
            │
            ├─> MemoryAwareEvaluator / DatasetLoader / PhoenixSyncService
            │       - Domain Memory 검색, 스트리밍 로딩, Phoenix 업로드에 span 부여
            │
            └─> domain/entities/rag_trace.py
                    - RetrievalData, GenerationData, RAGTraceData 작성

[3] TrackerPort 구현체 (Langfuse / MLflow / Phoenix)
    │  - run 결과를 trace/span/score로 기록
    │  - Prompt manifest diff 정보를 metadata에 포함
    │
    └─> [4] 추적 시스템
            │  - Langfuse Dashboard
            │  - Phoenix Dashboard
            │  - MLflow Experiment

[5] PhoenixSyncService (옵션)
    │  - Dataset/Experiment 업로드
    │  - Prompt manifest + Phoenix metadata 연동
    │
    └─> [6] Phoenix UI
            │  - 트레이스/실험/데이터셋을 한 번에 탐색

[7] CLI/Web UI 출력
    │  - Phoenix 링크 표시
    │  - Tracker metadata 표시
    │
    └─> config/phoenix_support.extract_phoenix_links()
            - CLI/Web UI 출력에 Phoenix Trace/Experiment URL 삽입
```

### 3.6.2 코드 예시

```python
# Phoenix 추적
class PhoenixAdapter(TrackerPort):
    """Phoenix 추적 어댑터."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = px.Client(
            host=settings.phoenix_host,
            port=settings.phoenix_port,
        )

    def log_evaluation_run(self, run: EvaluationRun) -> str:
        """EvaluationRun을 Phoenix trace로 기록"""
        # 1. Trace 생성
        trace = self._client.create_trace(
            name=f"evaluation-{run.run_id}",
            metadata={
                "dataset": run.dataset_name,
                "model": run.model_name,
                "run_id": run.run_id,
            },
        )

        # 2. 각 테스트 케이스를 span으로 기록
        for result in run.results:
            span = self._client.create_span(
                trace_id=trace.id,
                name=result.test_case_id,
                start_time=result.start_time,
                end_time=result.end_time,
                input={"question": result.question},
                output={"answer": result.answer},
                metadata={
                    "contexts": result.contexts,
                    "ground_truth": result.ground_truth,
                },
            )

            # 3. 메트릭 점수 기록
            for metric in result.metrics:
                self._client.create_score(
                    span_id=span.id,
                    name=metric.name,
                    value=metric.score,
                    metadata={
                        "threshold": metric.threshold,
                        "passed": metric.passed,
                    },
                )

        return trace.id

# RAG Trace 데이터
@dataclass
class RAGTraceData:
    """RAG 추적 데이터."""

    trace_id: str = ""
    query: str = ""
    retrieval: RetrievalData | None = None
    generation: GenerationData | None = None
    final_answer: str = ""
    total_time_ms: float = 0.0

    def to_span_attributes(self) -> dict[str, Any]:
        """Phoenix/OpenTelemetry span 속성으로 변환"""
        attrs = {
            "rag.total_time_ms": self.total_time_ms,
            "rag.query": self.query,
            "rag.final_answer": self.final_answer,
        }
        if self.retrieval:
            attrs.update(self.retrieval.to_span_attributes())
        if self.generation:
            attrs.update(self.generation.to_span_attributes())
        return attrs

@dataclass
class RetrievalData:
    """검색 단계 데이터."""

    query: str = ""
    retrieved_docs: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    latency_ms: float = 0.0
    precision_at_k: float = 0.0
    recall_at_k: float = 0.0

    def to_span_attributes(self) -> dict[str, Any]:
        """span 속성 변환"""
        return {
            "rag.retrieval.query": self.query,
            "rag.retrieval.latency_ms": self.latency_ms,
            "rag.retrieval.precision_at_k": self.precision_at_k,
            "rag.retrieval.recall_at_k": self.recall_at_k,
            "rag.retrieval.doc_count": len(self.retrieved_docs),
        }

@dataclass
class GenerationData:
    """생성 단계 데이터."""

    prompt: str = ""
    response: str = ""
    latency_ms: float = 0.0
    token_count: int = 0
    cost: float = 0.0

    def to_span_attributes(self) -> dict[str, Any]:
        """span 속성 변환"""
        return {
            "rag.generation.latency_ms": self.latency_ms,
            "rag.generation.token_count": self.token_count,
            "rag.generation.cost": self.cost,
        }
```

---

## 업데이트 이력

| 버전 | 날짜 | 변경 사항 | 담당 |
|------|------|----------|------|
| 1.0.0 | 2026-01-10 | 초기 작성 | EvalVault Team |

## 관련 섹션

- 섹션 1: 프로젝트 개요
- 섹션 2: 아키텍처 설계
- 섹션 4: 주요 컴포넌트 상세
