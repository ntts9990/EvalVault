## 제4부: 주요 컴포넌트 상세

### 4.1 도메인 엔티티 (Domain Entities)

### 4.1.1 Dataset 엔티티

**Whitepaper Reference**:
- Section 4.1: 도메인 엔티티 - Dataset 엔티티
- Section 3.1: 평가 실행 흐름 - 데이터셋 로드 단계

#### 4.1.1.1 개요

`Dataset` 엔티티는 평가용 데이터셋을 표현하는 Rich Domain Model입니다. 데이터셋의 메타데이터(name, version), 테스트 케이스 목록, 그리고 메트릭별 임계값(thresholds)을 포함합니다.

#### 4.1.1.2 정의

```python
# src/evalvault/domain/entities/dataset.py
@dataclass
class Dataset:
    """평가용 데이터셋.

    Whitepaper Reference:
        - Section 4.1: 도메인 엔티티 - Dataset 엔티티
        - Section 3.1: 평가 실행 흐름 - 데이터셋 로드 단계

    비즈니스 규칙:
        - 불변성 보장 (@frozen=True로 제어)
        - 임계값 조회 메서드 제공
        - 비즈니스 규칙 캡슐화

    Last Updated: 2026-01-10
    """

    name: str
    version: str
    test_cases: list[TestCase]
    thresholds: dict[str, float] = field(default_factory=dict)

    # 비즈니스 규칙: 임계값 조회
    def get_threshold(self, metric_name: str, default: float = 0.7) -> float:
        """비즈니스 규칙: 메트릭별 임계값 조회

        Args:
            metric_name: 메트릭 이름
            default: 기본 임계값

        Returns:
            등록된 임계값, 없으면 기본값 반환
        """
        return self.thresholds.get(metric_name, default)

    # 비즈니스 규칙: 불변성 보장
    def with_threshold(self, metric_name: str, value: float) -> 'Dataset':
        """새로운 임계값을 가진 복사본 반환

        Args:
            metric_name: 메트릭 이름
            value: 임계값

        Returns:
            새로운 임계값을 가진 Dataset 복사본
        """
        new_thresholds = {**self.thresholds, metric_name: value}
        return dataclasses.replace(self, thresholds=new_thresholds)
```

#### 4.1.1.3 비즈니스 규칙

| 규칙 | 설명 | 구현 |
|------|------|------|
| **불변성 보장** | Dataset 생성 후 불변 | `@dataclass(frozen=True)` (섹션 4.1.2 참조) |
| **임계값 관리** | 메트릭별 임계값 조회/업데이트 | `get_threshold()`, `with_threshold()` 메서드 |
| **검증** | test_cases가 최소 1개 이상 | 생성자 검증 로직 (섹션 4.1.2에는 생략됨) |

#### 4.1.1.4 사용법

```python
# 데이터셋 생성
dataset = Dataset(
    name="insurance-qa",
    version="1.0.0",
    test_cases=[
        TestCase(
            id="tc-001",
            question="보장금액은 얼마인가요?",
            answer="보장금액은 1억원입니다.",
            contexts=["보장금액은 1억원입니다."],
            ground_truth="1억원",
        ),
    ],
    thresholds={
        "faithfulness": 0.8,
        "answer_relevancy": 0.7,
    },
)

# 임계값 조회
faithfulness_threshold = dataset.get_threshold("faithfulness")  # 0.8
answer_relevancy_threshold = dataset.get_threshold("answer_relevancy")  # 0.7
unknown_threshold = dataset.get_threshold("unknown", 0.7)  # 0.7 (기본값)

# 불변성 보장: 수정 시 새 객체 반환
updated_dataset = dataset.with_threshold("faithfulness", 0.85)  # 새 Dataset 객체
```

#### 4.1.1.5 전문가 관점 적용

**[인지심리학자 관점]**
- **적용 원칙**: 불변성 보장으로 인지 부하 감소 (데이터 변경 여러 곳 확인 필요 없음)
- **실제 구현**: `@dataclass(frozen=True)`와 복사본 반환 메서드로 불변성 보장

**[소프트웨어 개발 전문가 관점]**
- **적용 원칙**: SOLID 단일 책임 원칙 (SRP) 적용
- **실제 구현**:
  - 단일 책임: 데이터셋 관리만 담당
  - 인터페이스 분리: 외부 어댑터와 독립적으로 테스트 가능

**[아키텍트 관점]**
- **적용 원칙**: Rich Domain Model (불변 객체 + 비즈니스 규칙 캡슐화)
- **실제 구현**: `@dataclass`로 불변성 보장, 비즈니스 로직을 메서드로 캡슐화

### 4.1.2 EvaluationRun 엔티티

**Whitepaper Reference**:
- Section 4.1: 도메인 엔티티 - EvaluationRun 엔티티
- Section 3.1: 평가 실행 흐름 - 결과 집계 단계

#### 4.1.2.1 개요

`EvaluationRun` 엔티티는 전체 평가 실행 결과를 표현합니다. 각 테스트 케이스에 대한 결과(TestCaseResult), 평가된 메트릭 목록, 통과율(pass_rate) 등 통계 정보를 포함합니다.

#### 4.1.2.2 정의

```python
# src/evalvault/domain/entities/result.py
@dataclass
class EvaluationRun:
    """전체 평가 실행 결과.

    Whitepaper Reference:
        - Section 4.1: 도메인 엔티티 - EvaluationRun 엔티티
        - Section 3.1: 평가 실행 흐름 - 결과 집계 단계

    비즈니스 규칙:
        - 결과 집계 및 통계 계산
        - 통과/실패 판정
        - 메트릭 평균 점수 계산

    Last Updated: 2026-01-10
    """

    run_id: str
    dataset_name: str
    model_name: str
    results: list[TestCaseResult]
    metrics_evaluated: list[str]
    thresholds: dict[str, float]

    # 비즈니스 규칙: 통과율 계산
    @property
    def passed_test_cases(self) -> int:
        """비즈니스 규칙: 통과한 테스트 케이스 수"""
        return sum(1 for r in self.results if r.passed)

    @property
    def total_test_cases(self) -> int:
        """비즈니스 규칙: 전체 테스트 케이스 수"""
        return len(self.results)

    @property
    def pass_rate(self) -> float:
        """비즈니스 규칙: 통과율 계산

        Returns:
            통과율 (0.0 ~ 1.0)
        """
        if not self.results:
            return 0.0
        return self.passed_test_cases / self.total_test_cases

    # 비즈니스 규칙: 메트릭 평균 점수 계산
    def get_avg_score(self, metric_name: str) -> float | None:
        """비즈니스 규칙: 메트릭별 평균 점수 계산

        Args:
            metric_name: 메트릭 이름

        Returns:
            평균 점수 (해당 메트릭이 없으면 None)
        """
        scores = [
            r.get_metric(metric_name).score
            for r in self.results
            if r.get_metric(metric_name) is not None
        ]
        return sum(scores) / len(scores) if scores else None

    # 비즈니스 규칙: 메트릭별 통과/실패 케이스 필터링
    def get_failed_test_cases(self, metric_name: str) -> list[TestCaseResult]:
        """비즈니스 규칙: 메트릭별 실패한 테스트 케이스 필터링

        Args:
            metric_name: 메트릭 이름

        Returns:
            실패한 테스트 케이스 목록
        """
        return [
            r for r in self.results
            if r.get_metric(metric_name) and not r.get_metric(metric_name).passed
        ]
```

#### 4.1.2.3 비즈니스 규칙

| 규칙 | 설명 | 구현 |
|------|------|------|
| **통과율 계산** | 통과한 케이스 / 전체 케이스 | `@property pass_rate` |
| **메트릭 평균** | 메트릭별 평균 점수 계산 | `get_avg_score()` 메서드 |
| **필터링** | 실패 케이스 등 조건부 필터링 | `get_failed_test_cases()` 메서드 |

#### 4.1.2.4 사용법

```python
# 평가 실행 결과 생성
run = EvaluationRun(
    run_id="run-abc123",
    dataset_name="insurance-qa",
    model_name="gpt-4o-mini",
    results=[
        TestCaseResult(
            test_case_id="tc-001",
            question="보장금액은 얼마인가요?",
            answer="보장금액은 1억원입니다.",
            contexts=["보장금액은 1억원입니다."],
            metrics=[
                MetricScore(
                    name="faithfulness",
                    score=0.9,
                    threshold=0.8,
                    passed=True,
                ),
                MetricScore(
                    name="answer_relevancy",
                    score=0.75,
                    threshold=0.7,
                    passed=True,
                ),
            ],
        ),
        # ... 더 많은 테스트 케이스 결과
    ],
    metrics_evaluated=["faithfulness", "answer_relevancy"],
    thresholds={"faithfulness": 0.8, "answer_relevancy": 0.7},
)

# 통과율 계산
print(f"통과율: {run.pass_rate:.2%}")  # 예: 85.0%

# 메트릭 평균 점수 계산
faithfulness_avg = run.get_avg_score("faithfulness")  # 예: 0.85
answer_relevancy_avg = run.get_avg_score("answer_relevancy")  # 예: 0.78

# 실패 케이스 필터링
failed_faithfulness = run.get_failed_test_cases("faithfulness")  # faithfulness 실패 케이스 목록
```

#### 4.1.2.5 전문가 관점 적용

**[정보공학 전문가 관점]**
- **적용 원칙**: 정보 아키텍처 (계층 구조와 집계)
- **실제 구현**:
  - Run → Test Case → Metric 계층 구조
  - 집계 메서드로 통계 정보 제공

**[인지심리학자 관점]**
- **적용 원칙**: 점진적 정보 공개 (Progressive Disclosure)
- **실제 구현**:
  - `pass_rate` 프로퍼티로 요약 정보 제공
  - `get_avg_score()` 등 메서드로 상세 정보 제공

**[UI/UX 전문가 관점]**
- **적용 원칙**: 피드백 제공 (통과/실패 여부 명확)
- **실제 구현**: `passed` 속성으로 각 메트릭 점수별 통과 여부 명확히 표시

### 4.2 도메인 서비스 (Domain Services)

### 4.2.1 RagasEvaluator 서비스

**Whitepaper Reference**:
- Section 4.2: 도메인 서비스 - RagasEvaluator 서비스
- Section 3.1: 평가 실행 흐름 - 평가 실행 단계
- Section 2.3: 의존성 관리

#### 4.2.1.1 개요

`RagasEvaluator`는 Ragas 기반 RAG 평가를 실행하는 핵심 도메인 서비스입니다. Ragas 메트릭과 커스텀 메트릭을 실행하고, 결과를 집계하며, 임계값을 판정합니다.

#### 4.2.1.2 정의

```python
# src/evalvault/domain/services/evaluator.py
class RagasEvaluator:
    """Ragas 기반 RAG 평가 서비스.

    Whitepaper Reference:
        - Section 4.2: 도메인 서비스 - RagasEvaluator 서비스
        - Section 3.1: 평가 실행 흐름 - 평가 실행 단계

    책임:
        - Ragas 메트릭 실행
        - 커스텀 메트릭 실행
        - 결과 집계 및 임계값 판정
        - 토큰 사용량 및 비용 추적

    의존성:
        - LLMPort: LLM 추상화 (구체적인 LLM 구현에 의존하지 않음)
        - Dataset: 도메인 엔티티

    Last Updated: 2026-01-10
    """

    # 커스텀 메트릭 매핑
    CUSTOM_METRIC_MAP: dict[str, type] = {
        "insurance_term_accuracy": InsuranceTermAccuracy,
        "entity_preservation": EntityPreservation,
    }

    def __init__(self, llm: LLMPort):
        """초기화

        Args:
            llm: LLM 포트 인터페이스
        """
        self._llm = llm

    async def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        thresholds: dict[str, float] | None = None,
        parallel: bool = True,
        batch_size: int = 10,
    ) -> EvaluationRun:
        """평가 실행 - 핵심 비즈니스 로직

        Args:
            dataset: 평가용 데이터셋
            metrics: 실행할 메트릭 목록
            thresholds: 메트릭별 임계값 (None이면 데이터셋 기본값 사용)
            parallel: 병렬 실행 여부
            batch_size: 배치 크기

        Returns:
            EvaluationRun: 평가 실행 결과

        비즈니스 규칙:
            1. 임계값 해석
            2. Ragas 메트릭 실행
            3. 커스텀 메트릭 실행
            4. 결과 집계
        """
        # 1. 임계값 해석 (비즈니스 규칙)
        resolved_thresholds = self._resolve_thresholds(dataset, metrics, thresholds)

        # 2. 평가 실행 (Ragas + 커스텀)
        eval_results = await self._evaluate_with_ragas(dataset, metrics, parallel, batch_size)

        # 3. 결과 집계 (비즈니스 로직)
        run = self._aggregate_results(dataset, metrics, eval_results, resolved_thresholds)

        return run

    def _resolve_thresholds(
        self,
        dataset: Dataset,
        metrics: list[str],
        thresholds: dict[str, float] | None,
    ) -> dict[str, float]:
        """비즈니스 규칙: 임계값 해석

        우선순위:
        1. 명시된 thresholds (함수 인자)
        2. 데이터셋 thresholds
        3. 기본값 (0.7)
        """
        resolved = {}

        for metric in metrics:
            # 명시된 thresholds 우선
            if thresholds and metric in thresholds:
                resolved[metric] = thresholds[metric]
            # 데이터셋 thresholds 다음
            elif metric in dataset.thresholds:
                resolved[metric] = dataset.thresholds[metric]
            # 기본값
            else:
                resolved[metric] = 0.7

        return resolved

    async def _evaluate_with_ragas(
        self,
        dataset: Dataset,
        metrics: list[str],
        parallel: bool = True,
        batch_size: int = 10,
    ) -> dict[str, list[MetricScore]]:
        """Ragas 메트릭 실행"""
        # Ragas 평가 로직...
        pass  # 실제 구현은 코드에서 확인 가능

    def _aggregate_results(
        self,
        dataset: Dataset,
        metrics: list[str],
        eval_results: dict[str, list[MetricScore]],
        thresholds: dict[str, float],
    ) -> EvaluationRun:
        """결과 집계 (비즈니스 로직)"""
        results = []

        # 각 테스트 케이스별 결과 생성
        for i, test_case in enumerate(dataset.test_cases):
            metric_scores = []

            # 각 메트릭별 점수 추출
            for metric in metrics:
                if metric in eval_results:
                    metric_score = MetricScore(
                        name=metric,
                        score=eval_results[metric][i].score,
                        threshold=thresholds[metric],
                        passed=eval_results[metric][i].score >= thresholds[metric],
                    )
                    metric_scores.append(metric_score)

            # TestCaseResult 생성
            result = TestCaseResult(
                test_case_id=test_case.id,
                question=test_case.question,
                answer=test_case.answer,
                contexts=test_case.contexts,
                ground_truth=test_case.ground_truth,
                metrics=metric_scores,
            )
            results.append(result)

        # EvaluationRun 생성
        return EvaluationRun(
            run_id=f"run-{uuid.uuid4()[:8]}",
            dataset_name=dataset.name,
            model_name=self._llm.get_model_name(),
            results=results,
            metrics_evaluated=metrics,
            thresholds=thresholds,
        )
```

#### 4.2.1.3 의존성

```python
# 의존성 주입 (생성자 주입)
class RagasEvaluator:
    def __init__(self, llm: LLMPort):
        """
        의존성 방향: 포트 → 도메인

        LLMPort: 추상화된 인터페이스
        - 구체적인 LLM 구현(OpenAI, Anthropic 등)에 의존하지 않음
        - 테스트 시 MockLLMAdapter로 쉽게 교체 가능
        """
        self._llm = llm
```

#### 4.2.1.4 비즈니스 규칙

| 규칙 | 설명 | 구현 |
|------|------|------|
| **임계값 우선순위** | 명시 → 데이터셋 → 기본값 | `_resolve_thresholds()` 메서드 |
| **메트릭 조합** | Ragas + 커스텀 메트릭 실행 | `evaluate()` 메서드 |
| **결과 집계** | 통과/실패 판정, 평균 점수 계산 | `_aggregate_results()` 메서드 |

#### 4.2.1.5 사용법

```python
# LLM 어댑터 생성
settings = Settings()
llm = get_llm_adapter(settings, "dev")  # OpenAIAdapter 등 LLMPort 구현체

# 평가자 생성
evaluator = RagasEvaluator(llm=llm)

# 데이터셋 로드
loader = get_loader("tests/fixtures/insurance_qa.json")
dataset = loader.load("tests/fixtures/insurance_qa.json")

# 평가 실행
run = await evaluator.evaluate(
    dataset=dataset,
    metrics=["faithfulness", "answer_relevancy"],
    thresholds={"faithfulness": 0.9},  # 명시된 임계값
    parallel=True,
    batch_size=10,
)

# 결과 확인
print(f"실행 ID: {run.run_id}")
print(f"통과율: {run.pass_rate:.2%}")
print(f"Faithfulness 평균: {run.get_avg_score('faithfulness'):.3f}")
print(f"Answer Relevancy 평균: {run.get_avg_score('answer_relevancy'):.3f}")
```

#### 4.2.1.6 전문가 관점 적용

**[SOLID 단일 책임 원칙 (SRP) 관점]**
- **적용 원칙**: 평가 실행만 담당
- **실제 구현**:
  - Ragas 메트릭 실행, 커스텀 메트릭 실행, 결과 집계만 담당
  - 데이터셋 로드, 저장소 저장은 다른 서비스 책임

**[의존성 역전 원칙 (DIP) 관점]**
- **적용 원칙**: 추상화(LLMPort)에 의존
- **실제 구현**:
  - 생성자 주입으로 LLMPort 추상화에 의존
  - 구체적인 OpenAIAdapter, AnthropicAdapter 등에 의존하지 않음

**[테스트 가능성 관점]**
- **적용 원칙**: 포트 인터페이스를 통한 모킹
- **실제 구현**:
  - 테스트 시 MockLLMAdapter로 교체 가능
  - 단위 테스트에서 외부 API 호출 불필요

### 4.2.2 ExperimentManager 서비스

**Whitepaper Reference**:
- Section 4.2: 도메인 서비스 - ExperimentManager 서비스
- Section 3.2: 실험 관리 흐름

#### 4.2.2.1 개요

`ExperimentManager`는 A/B 테스트 실험을 관리하는 서비스입니다. 여러 평가 실행을 그룹으로 묶어 비교하고, 최적의 설정을 식별하는 데 사용됩니다.

#### 4.2.2.2 정의

```python
# src/evalvault/domain/services/experiment_manager.py
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class ExperimentGroup:
    """실험 그룹"""
    group_id: str
    name: str
    description: str = ""
    baseline: bool = False
    run_ids: List[str] = field(default_factory=list)

@dataclass
class MetricComparison:
    """메트릭 비교 결과"""
    metric_name: str
    group_scores: Dict[str, float]
    best_group: str
    improvement: float

@dataclass
class Experiment:
    """실험"""
    experiment_id: str
    name: str
    description: str = ""
    metrics_to_compare: List[str] = field(default_factory=list)
    groups: Dict[str, ExperimentGroup] = field(default_factory=dict)
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

class ExperimentManager:
    """실험 관리 서비스.

    Whitepaper Reference:
        - Section 4.2: 도메인 서비스 - ExperimentManager 서비스
        - Section 3.2: 실험 관리 흐름

    책임:
        - 실험 생성 및 관리
        - 그룹 추가 및 관리
        - 그룹 간 메트릭 비교

    의존성:
        - StoragePort: 저장소 추상화

    Last Updated: 2026-01-10
    """

    def __init__(self, storage: StoragePort):
        """초기화

        Args:
            storage: 저장소 포트 인터페이스
        """
        self._storage = storage
        self._experiments: Dict[str, Experiment] = {}

    def create_experiment(
        self,
        experiment_id: str,
        name: str,
        description: str,
        metrics_to_compare: List[str],
    ) -> Experiment:
        """실험 생성 (비즈니스 로직)

        Args:
            experiment_id: 실험 ID
            name: 실험 이름
            description: 실험 설명
            metrics_to_compare: 비교할 메트릭 목록

        Returns:
            Experiment: 생성된 실험

        비즈니스 규칙:
            - Experiment 엔티티 생성
            - 중복 ID 검사
        """
        if experiment_id in self._experiments:
            raise ValueError(f"이미 존재하는 실험 ID: {experiment_id}")

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
        """그룹 추가 (비즈니스 로직)

        Args:
            experiment_id: 실험 ID
            group_id: 그룹 ID
            name: 그룹 이름
            baseline: 기준 그룹 여부

        Returns:
            ExperimentGroup: 생성된 그룹

        비즈니스 규칙:
            - 실험이 존재하는지 확인
            - 그룹 엔티티 생성
        """
        experiment = self.get_experiment(experiment_id)

        if group_id in experiment.groups:
            raise ValueError(f"이미 존재하는 그룹 ID: {group_id}")

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
        """그룹에 실행 추가 (비즈니스 로직)

        Args:
            experiment_id: 실험 ID
            group_id: 그룹 ID
            run_id: 실행 ID

        비즈니스 규칙:
            - 실험과 그룹이 존재하는지 확인
            - 중복 실행 ID 검사
        """
        experiment = self.get_experiment(experiment_id)
        group = experiment.groups[group_id]

        if run_id in group.run_ids:
            raise ValueError(f"이미 존재하는 실행 ID: {run_id}")

        group.run_ids.append(run_id)

    def compare_groups(self, experiment_id: str) -> List[MetricComparison]:
        """그룹 간 메트릭 비교 (비즈니스 로직)

        Args:
            experiment_id: 실험 ID

        Returns:
            List[MetricComparison]: 메트릭별 비교 결과

        비즈니스 규칙:
            - 각 그룹의 run 데이터 수집
            - 메트릭별 평균 점수 계산
            - 최고 그룹 및 개선율 계산
        """
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

    def _collect_group_runs(
        self,
        experiment: Experiment,
    ) -> Dict[str, Dict[str, EvaluationRun]]:
        """각 그룹의 run 데이터 수집 (비즈니스 로직)"""
        group_runs = {}

        for group_id, group in experiment.groups.items():
            runs = {}
            for run_id in group.run_ids:
                # StoragePort에서 run 데이터 조회
                run = self._storage.get_run(run_id)
                if run:
                    runs[run_id] = run

            group_runs[group_id] = runs

        return group_runs

    def _calculate_group_scores(
        self,
        group_runs: Dict[str, Dict[str, EvaluationRun]],
        metric: str,
    ) -> Dict[str, float]:
        """메트릭별 그룹 평균 점수 계산 (비즈니스 로직)"""
        group_scores = {}

        for group_id, runs in group_runs.items():
            if not runs:
                continue

            scores = [
                run.get_avg_score(metric)
                for run in runs.values()
                if run.get_avg_score(metric) is not None
            ]

            if scores:
                avg_score = sum(scores) / len(scores)
                group_scores[group_id] = avg_score

        return group_scores

    def _calculate_improvement(
        self,
        group_scores: Dict[str, float],
        best_group: str,
    ) -> float:
        """개선율 계산 (비즈니스 로직)"""
        best_score = group_scores[best_group]

        # 기준 그룹 찾기
        baseline_group = None
        for group_id, scores in group_scores.items():
            if group_id in self._experiments.values():
                if self._experiments.values().groups[group_id].baseline:
                    baseline_group = group_id
                    break

        if baseline_group and baseline_group in group_scores:
            baseline_score = group_scores[baseline_group]
            improvement = (best_score - baseline_score) / baseline_score * 100
            return improvement
        else:
            return 0.0
```

#### 4.2.2.3 의존성

```python
# 의존성 주입 (생성자 주입)
class ExperimentManager:
    def __init__(self, storage: StoragePort):
        """
        의존성 방향: 포트 → 도메인

        StoragePort: 추상화된 저장소 인터페이스
        - 구체적인 SQLite, PostgreSQL 등에 의존하지 않음
        - 테스트 시 MockStorageAdapter로 쉽게 교체 가능
        """
        self._storage = storage
```

#### 4.2.2.4 비즈니스 규칙

| 규칙 | 설명 | 구현 |
|------|------|------|
| **실험 관리** | 실험 생성, 그룹 추가, 실행 추가 | `create_experiment()`, `add_group()`, `add_run_to_group()` |
| **그룹 비교** | 메트릭별 그룹 간 비교 및 개선율 계산 | `compare_groups()` 메서드 |
| **데이터 검증** | 중복 ID 검사, 존재성 확인 | 생성자/메서드에서 검증 로직 |

#### 4.2.2.5 사용법

```python
# 저장소 어댑터 생성
settings = Settings()
storage = get_storage_adapter(settings)  # SQLiteStorageAdapter 등 StoragePort 구현체

# 실험 관리자 생성
manager = ExperimentManager(storage=storage)

# 실험 생성
experiment = manager.create_experiment(
    experiment_id="exp-001",
    name="프롬프트 A/B 테스트",
    description="프롬프트 v1 vs v2 비교",
    metrics_to_compare=["faithfulness", "answer_relevancy"],
)

# 그룹 추가
group_a = manager.add_group(experiment_id="exp-001", group_id="group-a", name="Prompt v1", baseline=True)
group_b = manager.add_group(experiment_id="exp-001", group_id="group-b", name="Prompt v2", baseline=False)

# 실행 추가 (가정: run-a-001, run-b-001이 저장소에 있다고 가정)
manager.add_run_to_group(experiment_id="exp-001", group_id="group-a", run_id="run-a-001")
manager.add_run_to_group(experiment_id="exp-001", group_id="group-b", run_id="run-b-001")

# 그룹 비교
comparisons = manager.compare_groups(experiment_id="exp-001")

# 비교 결과 확인
for comp in comparisons:
    print(f"\n메트릭: {comp.metric_name}")
    print(f"  그룹 점수: {comp.group_scores}")
    print(f"  최고 그룹: {comp.best_group}")
    print(f"  개선율: {comp.improvement:.2f}%")
```

#### 4.2.2.6 전문가 관점 적용

**[SOLID 단일 책임 원칙 (SRP) 관점]**
- **적용 원칙**: 실험 관리만 담당
- **실제 구현**:
  - 실험 생성, 그룹 관리, 비교 로직만 담당
  - 데이터셋 로드, 평가 실행은 다른 서비스 책임

**[정보공학 전문가 관점]**
- **적용 원칙**: 정보 구조화 (실험 → 그룹 → 메트릭)
- **실제 구현**:
  - Experiment → ExperimentGroup → EvaluationRun 계층 구조
  - MetricComparison으로 정량적 비교 결과 제공

**[교육공학 전문가 관점]**
- **적용 원칙**: A/B 테스트 교육적 효과
- **실제 구현**:
  - Baseline 그룹 명시
  - 개선율 계산으로 학습 효과 제공
  - 명확한 비교 결과로 결론 도출

### 4.3 포트 인터페이스 (Port Interfaces)

### 4.3.1 LLMPort

**Whitepaper Reference**:
- Section 2.3: 포트 계층 - Outbound Ports
- Section 4.2.1: 도메인 서비스 - RagasEvaluator 서비스

#### 4.3.1.1 개요

`LLMPort`는 LLM 서비스에 대한 추상화된 인터페이스입니다. OpenAI, Anthropic, Azure, Ollama, vLLM 등 다양한 LLM 제공자를 통일된 방식으로 사용할 수 있게 합니다.

#### 4.3.1.2 정의

```python
# src/evalvault/ports/outbound/llm_port.py
from abc import ABC, abstractmethod

class LLMPort(ABC):
    """LLM adapter interface for Ragas metrics evaluation.

    Whitepaper Reference:
        - Section 2.3: 포트 계층 - Outbound Ports
        - Section 4.2.1: 도메인 서비스 - RagasEvaluator 서비스

    계약(Contract):
        - LLM 제공자를 위한 통합 인터페이스
        - Ragas 호환 LLM 인스턴스 제공

    확장점(Extensibility):
        - 새로운 LLM 제공자 추가 시 이 인터페이스만 구현

    Last Updated: 2026-01-10
    """

    @abstractmethod
    def get_model_name(self) -> str:
        """모델 이름 반환

        Returns:
            모델 이름 (예: "gpt-4o-mini")
        """
        pass

    @abstractmethod
    def as_ragas_llm(self):
        """Ragas 호환 LLM 인스턴스 반환

        Returns:
            Ragas에서 사용할 수 있는 LLM 인스턴스
        """
        pass

    @abstractmethod
    def get_token_count(self) -> int:
        """토큰 사용량 반환

        Returns:
            사용된 토큰 수 (0이면 사용하지 않음)
        """
        pass

    @abstractmethod
    def get_cost_estimate(self) -> float:
        """비용 추정 반환

        Returns:
            추정 비용 (USD)
        """
        pass
```

#### 4.3.1.3 구현 예시

```python
# OpenAI 구현
# src/evalvault/adapters/outbound/llm/openai_adapter.py
class OpenAIAdapter(LLMPort):
    """OpenAI LLM adapter."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._token_count = 0

        # Ragas 호환 LLM 생성
        from langchain_openai import ChatOpenAI
        self._ragas_llm = llm_factory(
            model=settings.openai_model,
            provider="openai",
            api_key=settings.openai_api_key,
        )

        # 비용 추적을 위한 wrapper
        self._llm_wrapper = TokenAwareChat(
            llm=ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
            ),
            token_callback=self._update_token_count,
        )

    def get_model_name(self) -> str:
        """모델 이름 반환"""
        return self._settings.openai_model

    def as_ragas_llm(self):
        """Ragas 호환 LLM 반환"""
        return self._ragas_llm

    def get_token_count(self) -> int:
        """토큰 사용량 반환"""
        return self._token_count

    def get_cost_estimate(self) -> float:
        """비용 추정 반환"""
        # OpenAI 가격표 기반 비용 계산
        # 입력 토큰 + 출력 토큰 * 가격/1M 토큰
        return self._token_count * 0.00015  # 예시 가격

# Ollama 구현
# src/evalvault/adapters/outbound/llm/ollama_adapter.py
class OllamaAdapter(LLMPort):
    """Ollama LLM adapter."""

    def __init__(self, settings: Settings):
        self._settings = settings
        self._token_count = 0

        # Ragas 호환 LLM 생성
        from langchain_community.llms import OllamaLLM
        self._ragas_llm = llm_factory(
            model=settings.ollama_model,
            provider="ollama",
            base_url=settings.ollama_base_url,
        )

    def get_model_name(self) -> str:
        return self._settings.ollama_model

    def as_ragas_llm(self):
        return self._ragas_llm

    def get_token_count(self) -> int:
        return self._token_count

    def get_cost_estimate(self) -> float:
        # Ollama는 로컬이므로 비용 0
        return 0.0
```

#### 4.3.1.4 전문가 관점 적용

**[아키텍트 관점]**
- **적용 원칙**: 포트 기반 설계 (Ports & Adapters)
- **실제 구현**:
  - LLMPort 인터페이스로 추상화
  - 각 제공자(Adapter)가 인터페이스 구현
  - 의존성 방향: Adapter → Port → Domain

**[확장성 관점]**
- **적용 원칙**: 새로운 LLM 추가 용이
- **실제 구현**:
  - 새로운 LLM 제공자 추가 시 LLMPort만 구현
  - 도메인 코드 수정 없음 (RagasEvaluator는 LLMPort 인터페이스만 사용)

**[테스트 가능성 관점]**
- **적용 원칙**: 포트 인터페이스를 통한 모킹
- **실제 구현**:
  - 테스트 시 MockLLMAdapter로 교체 가능
  - 단위 테스트에서 실제 LLM API 호출 불필요

### 4.3.2 StoragePort

**Whitepaper Reference**:
- Section 2.3: 포트 계층 - Outbound Ports
- Section 4.2.1: 도메인 서비스 - RagasEvaluator 서비스

#### 4.3.2.1 개요

`StoragePort`는 평가 결과를 저장하는 추상화된 인터페이스입니다. SQLite, PostgreSQL 등 다양한 데이터베이스를 통일된 방식으로 사용할 수 있게 합니다.

#### 4.3.2.2 정의

```python
# src/evalvault/ports/outbound/storage_port.py
from typing import Protocol

class StoragePort(Protocol):
    """평가 결과 저장을 위한 포트 인터페이스.

    Whitepaper Reference:
        - Section 2.3: 포트 계층 - Outbound Ports
        - Section 4.2.1: 도메인 서비스 - RagasEvaluator 서비스

    계약(Contract):
        - EvaluationRun 저장 및 조회를 위한 통합 인터페이스

    확장점(Extensibility):
        - 새로운 저장소(MySQL, MongoDB 등) 추가 시 이 인터페이스만 구현

    Last Updated: 2026-01-10
    """

    def save_run(self, run: EvaluationRun) -> str:
        """평가 실행 결과 저장

        Args:
            run: EvaluationRun 엔티티

        Returns:
            저장된 run_id

        비즈니스 규칙:
            - EvaluationRun을 데이터베이스 스키마에 맞게 저장
            - run_id 반환
        """
        pass

    def get_run(self, run_id: str) -> EvaluationRun:
        """저장된 평가 실행 결과 조회

        Args:
            run_id: 실행 ID

        Returns:
            EvaluationRun: 조회된 엔티티

        비즈니스 규칙:
            - 데이터베이스 스키마에서 EvaluationRun 재구성
            - 존재하지 않는 run_id일 경우 None 반환
        """
        pass

    def list_runs(
        self,
        limit: int = 100,
        dataset_name: str | None = None,
        model_name: str | None = None,
    ) -> list[EvaluationRun]:
        """저장된 평가 실행 결과 목록 조회

        Args:
            limit: 최대 결과 수
            dataset_name: 데이터셋 이름 필터 (선택)
            model_name: 모델 이름 필터 (선택)

        Returns:
            List[EvaluationRun]: 조회된 엔티티 목록

        비즈니스 규칙:
            - 지정된 조건에 맞는 엔티티 필터링
            - 최신순 정렬
        """
        pass

    def delete_run(self, run_id: str) -> bool:
        """평가 실행 결과 삭제

        Args:
            run_id: 실행 ID

        Returns:
            삭제 성공 여부
        """
        pass
```

#### 4.3.2.3 구현 예시

```python
# SQLite 구현
# src/evalvault/adapters/outbound/storage/sqlite_adapter.py
import sqlite3
from typing import Optional
from evalvault.domain.entities.result import EvaluationRun

class SQLiteStorageAdapter(StoragePort):
    """SQLite 저장소 어댑터."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._init_schema()

    def _init_schema(self):
        """스키마 초기화"""
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    run_id TEXT PRIMARY KEY,
                    dataset_name TEXT,
                    model_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metrics_evaluated TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_case_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    test_case_id TEXT,
                    question TEXT,
                    answer TEXT,
                    contexts TEXT,
                    ground_truth TEXT,
                    passed INTEGER,
                    FOREIGN KEY (run_id) REFERENCES evaluations(run_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metric_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    result_id INTEGER,
                    metric_name TEXT,
                    score REAL,
                    threshold REAL,
                    passed INTEGER,
                    FOREIGN KEY (result_id) REFERENCES test_case_results(id)
                )
            """)
            conn.commit()

    def save_run(self, run: EvaluationRun) -> str:
        """평가 실행 결과 저장"""
        with sqlite3.connect(self._db_path) as conn:
            # evaluations 테이블에 저장
            conn.execute("""
                INSERT INTO evaluations (run_id, dataset_name, model_name, metrics_evaluated)
                VALUES (?, ?, ?, ?)
            """, (run.run_id, run.dataset_name, run.model_name, ",".join(run.metrics_evaluated)))

            # test_case_results 테이블에 저장
            for result in run.results:
                cursor = conn.execute("""
                    INSERT INTO test_case_results (run_id, test_case_id, question, answer, contexts, ground_truth, passed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    run.run_id,
                    result.test_case_id,
                    result.question,
                    result.answer,
                    json.dumps(result.contexts),
                    result.ground_truth,
                    1 if result.passed else 0,
                ))
                result_id = cursor.lastrowid

                # metric_scores 테이블에 저장
                for metric in result.metrics:
                    conn.execute("""
                        INSERT INTO metric_scores (result_id, metric_name, score, threshold, passed)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        result_id,
                        metric.name,
                        metric.score,
                        metric.threshold,
                        1 if metric.passed else 0,
                    ))

            conn.commit()

        return run.run_id

    def get_run(self, run_id: str) -> Optional[EvaluationRun]:
        """저장된 평가 실행 결과 조회"""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row

            # evaluations 테이블 조회
            eval_row = conn.execute("""
                SELECT * FROM evaluations WHERE run_id = ?
            """, (run_id,)).fetchone()

            if not eval_row:
                return None

            # test_case_results 테이블 조회
            cursor = conn.execute("""
                SELECT * FROM test_case_results WHERE run_id = ?
            """, (run_id,))
            rows = cursor.fetchall()

            results = []
            for row in rows:
                # metric_scores 테이블 조회
                metric_cursor = conn.execute("""
                    SELECT metric_name, score, threshold, passed
                    FROM metric_scores
                    WHERE result_id = ?
                """, (row["id"],))
                metrics = [
                    MetricScore(
                        name=metric_row["metric_name"],
                        score=metric_row["score"],
                        threshold=metric_row["threshold"],
                        passed=bool(metric_row["passed"]),
                    )
                    for metric_row in metric_cursor.fetchall()
                ]

                result = TestCaseResult(
                    test_case_id=row["test_case_id"],
                    question=row["question"],
                    answer=row["answer"],
                    contexts=json.loads(row["contexts"]) if row["contexts"] else [],
                    ground_truth=row["ground_truth"],
                    passed=bool(row["passed"]),
                    metrics=metrics,
                )
                results.append(result)

            return EvaluationRun(
                run_id=eval_row["run_id"],
                dataset_name=eval_row["dataset_name"],
                model_name=eval_row["model_name"],
                results=results,
                metrics_evaluated=eval_row["metrics_evaluated"].split(",") if eval_row["metrics_evaluated"] else [],
                thresholds={},
            )

# PostgreSQL 구현 (선택)
# src/evalvault/adapters/outbound/storage/postgres_adapter.py
class PostgreSQLStorageAdapter(StoragePort):
    """PostgreSQL 저장소 어댑터."""

    def __init__(self, connection_string: str):
        self._conn = psycopg2.connect(connection_string)
        self._init_schema()

    # 저장소 초기화, 메서드 구현...
    pass
```

#### 4.3.2.4 전문가 관점 적용

**[아키텍트 관점]**
- **적용 원칙**: 포트 기반 설계 (Ports & Adapters)
- **실제 구현**:
  - StoragePort 인터페이스로 추상화
  - 각 저장소(Adapter)가 인터페이스 구현
  - 의존성 방향: Adapter → Port → Domain

**[확장성 관점]**
- **적용 원칙**: 새로운 저장소 추가 용이
- **실제 구현**:
  - 새로운 저장소(MySQL, MongoDB, Redis 등) 추가 시 StoragePort만 구현
  - 도메인 코드 수정 없음 (ExperimentManager는 StoragePort 인터페이스만 사용)

**[데이터 무결성성(ACID) 관점]**
- **적용 원칙**: 데이터베이스 교체 시 도메인 로직 무결성
- **실제 구현**:
  - SQLite → PostgreSQL 교환 시 도메인 코드(RagasEvaluator, ExperimentManager) 수정 불필요
  - StoragePort 구현체만 교환

### 4.4 어댑터 (Adapters)

### 4.4.1 CLI Adapter

**Whitepaper Reference**:
- Section 2.3: 어댑터 계층 - Inbound Adapters
- Section 4.5: 사용 가이드 - CLI 사용법

#### 4.4.1.1 개요

CLI Adapter는 Typer 기반 커맨드라인 인터페이스입니다. 사용자가 터미널에서 평가를 실행하고 결과를 확인할 수 있게 합니다.

#### 4.4.1.2 주요 명령

| 명령 | 설명 | 구현 |
|------|------|------|
| `run` | 평가 실행 | `adapters/inbound/cli/commands/run.py` |
| `run-simple` | 심플 모드 평가 실행 | `adapters/inbound/cli/commands/run.py` |
| `run-full` | 전체 모드 평가 실행 | `adapters/inbound/cli/commands/run.py` |
| `generate` | 테스트셋/지식 그래프 생성 | `adapters/inbound/cli/commands/generate.py` |
| `history` | 실행 히스토리 조회 | `adapters/inbound/cli/commands/history.py` |
| `compare` | 두 실행 결과 비교 | `adapters/inbound/cli/commands/compare.py` |
| `pipeline` | 분석 파이프라인 실행 | `adapters/inbound/cli/commands/pipeline.py` |
| `benchmark` | 벤치마크 실행 | `adapters/inbound/cli/commands/benchmark.py` |
| `gate` | 회귀 테스트 실행 | `adapters/inbound/cli/commands/gate.py` |
| `domain` | 도메인 메모리 관리 | `adapters/inbound/cli/commands/domain.py` |
| `stage` | Stage 메트릭 조회 | `adapters/inbound/cli/commands/stage.py` |

#### 4.4.1.3 구현 예시

```python
# src/evalvault/adapters/inbound/cli.py
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="evalvault",
    help="RAG evaluation system using Ragas with Phoenix/Langfuse tracing",
    add_completion=False,
)

console = Console()

@app.command()
def run(
    dataset: Path,
    metrics: str,
    model: str | None = None,
    profile: str = "dev",
    use_domain_memory: bool = False,
    augment_context: bool = False,
    parallel: bool = True,
    batch_size: int = 10,
):
    """Run RAG evaluation on a dataset."""
    # 1. 입력 파싱
    metric_list = [m.strip() for m in metrics.split(",")]

    # 2. 설정 로드
    from evalvault.config.settings import Settings
    settings = Settings()

    # 3. 어댑터 생성 (Factory 패턴)
    from evalvault.adapters.outbound.dataset.loader_factory import get_loader
    from evalvault.adapters.outbound.llm.llm_factory import get_llm_adapter
    from evalvault.domain.services.evaluator import RagasEvaluator

    loader = get_loader(dataset)
    llm = get_llm_adapter(settings, profile)

    # 4. 도메인 서비스 호출
    evaluator = RagasEvaluator(llm=llm)

    # Domain Memory 초기화 (선택적)
    if use_domain_memory:
        from evalvault.adapters.outbound.domain_memory.sqlite_adapter import get_domain_memory_adapter
        from evalvault.domain.services.memory_aware_evaluator import MemoryAwareEvaluator

        memory_port = get_domain_memory_adapter(settings)
        evaluator = MemoryAwareEvaluator(evaluator, memory_port)

    # 5. 평가 실행
    import asyncio
    result = asyncio.run(evaluator.evaluate(
        loader.load(dataset),
        metric_list,
        parallel=parallel,
        batch_size=batch_size,
    ))

    # 6. 결과 포맷팅 및 출력
    _display_results(result)

    # 7. 저장 (선택적)
    if settings.db_path:
        from evalvault.adapters.outbound.storage.storage_factory import get_storage_adapter
        storage = get_storage_adapter(settings)
        storage.save_run(result)

@app.command()
def history(
    db: str = "data/db/evalvault.db",
    limit: int = 10,
    dataset_name: str | None = None,
    model_name: str | None = None,
):
    """Show evaluation history."""
    from evalvault.adapters.outbound.storage.storage_factory import get_storage_adapter
    from evalvault.config.settings import Settings

    settings = Settings()
    storage = get_storage_adapter(settings, db_path=db)

    # 저장소에서 히스토리 조회
    runs = storage.list_runs(limit=limit, dataset_name=dataset_name, model_name=model_name)

    # 테이블 형식으로 표시
    table = Table(title="Evaluation History")
    table.add_column("Run ID", style="cyan")
    table.add_column("Dataset", style="green")
    table.add_column("Model", style="blue")
    table.add_column("Metrics", style="yellow")
    table.add_column("Pass Rate", style="magenta")
    table.add_column("Created", style="dim")

    for run in runs:
        table.add_row(
            run.run_id[:8],
            run.dataset_name,
            run.model_name,
            ",".join(run.metrics_evaluated[:3]) + "..." if len(run.metrics_evaluated) > 3 else ",".join(run.metrics_evaluated),
            f"{run.pass_rate:.2%}",
            run.created_at,
        )

    console.print(table)

@app.command()
def compare(
    run_a: str,
    run_b: str,
    db: str = "data/db/evalvault.db",
):
    """Compare two evaluation runs."""
    from evalvault.adapters.outbound.storage.storage_factory import get_storage_adapter
    from evalvault.config.settings import Settings
    from evalvault.domain.services.experiment_comparator import ExperimentComparator

    settings = Settings()
    storage = get_storage_adapter(settings, db_path=db)

    # 두 실행 조회
    run_a_data = storage.get_run(run_a)
    run_b_data = storage.get_run(run_b)

    # 비교 수행
    comparator = ExperimentComparator()
    comparison_result = comparator.compare(run_a_data, run_b_data)

    # 결과 표시
    _display_comparison(comparison_result)

def _display_results(result: EvaluationRun):
    """결과를 테이블 형식으로 표시"""
    # 메트릭 요약 테이블
    table = Table(title="Evaluation Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Avg Score", style="green")
    table.add_column("Threshold", style="yellow")
    table.add_column("Pass Rate", style="magenta")

    for metric in result.metrics_evaluated:
        avg_score = result.get_avg_score(metric)
        threshold = result.thresholds.get(metric, 0.7)
        pass_count = sum(1 for r in result.results if r.get_metric(metric) and r.get_metric(metric).passed)
        pass_rate = pass_count / len(result.results)

        table.add_row(
            metric,
            f"{avg_score:.3f}",
            f"{threshold:.2f}",
            f"{pass_rate:.2%}",
        )

    console.print(table)

    # 통과율 표시
    console.print(f"\n✅ Overall Pass Rate: {result.pass_rate:.2%}")
    console.print(f"📊 Total Test Cases: {len(result.results)}")
```

---

## 업데이트 이력

| 버전 | 날짜 | 변경 사항 | 담당 |
|------|------|----------|------|
| 1.0.0 | 2026-01-10 | 초기 작성 | EvalVault Team |

## 관련 섹션

- 섹션 1: 프로젝트 개요
- 섹션 2: 아키텍처 설계
- 섹션 3: 데이터 흐름 분석
- 섹션 5: 전문가 관점 통합 설계
