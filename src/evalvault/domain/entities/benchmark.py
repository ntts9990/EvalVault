"""Benchmark entities with multi-framework compatibility.

MTEB, lm-evaluation-harness, DeepEval 스타일의 벤치마크 결과 형식을 지원합니다.

Compatibility:
    - MTEB: results/{model}/{task}.json (임베딩 벤치마크)
    - lm-harness: Task/version/filter/n-shot/metric (LLM 벤치마크)
    - DeepEval: LLMTestCase(input, actual_output, retrieval_context) (RAG 평가)

References:
    - MTEB: https://github.com/embeddings-benchmark/mteb
    - lm-evaluation-harness: https://github.com/EleutherAI/lm-evaluation-harness
    - DeepEval: https://github.com/confident-ai/deepeval
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    """벤치마크 태스크 타입 (MTEB + DeepEval 호환)."""

    # MTEB standard tasks
    RETRIEVAL = "Retrieval"
    CLASSIFICATION = "Classification"
    CLUSTERING = "Clustering"
    PAIR_CLASSIFICATION = "PairClassification"
    RERANKING = "Reranking"
    STS = "STS"
    SUMMARIZATION = "Summarization"

    # DeepEval/RAG specific tasks
    RAG_FAITHFULNESS = "RAGFaithfulness"
    RAG_ANSWER_RELEVANCY = "RAGAnswerRelevancy"
    RAG_CONTEXTUAL_PRECISION = "RAGContextualPrecision"
    RAG_CONTEXTUAL_RECALL = "RAGContextualRecall"
    KEYWORD_EXTRACTION = "KeywordExtraction"


class MetricType(str, Enum):
    """벤치마크 메트릭 타입."""

    # MTEB/lm-harness metrics
    ACCURACY = "accuracy"
    F1 = "f1"
    PRECISION = "precision"
    RECALL = "recall"
    MAP = "map"
    MRR = "mrr"
    NDCG_AT_5 = "ndcg_at_5"
    NDCG_AT_10 = "ndcg_at_10"
    RECALL_AT_5 = "recall_at_5"
    RECALL_AT_10 = "recall_at_10"

    # DeepEval/RAG metrics
    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCY = "answer_relevancy"
    CONTEXTUAL_PRECISION = "contextual_precision"
    CONTEXTUAL_RECALL = "contextual_recall"
    CONTEXTUAL_RELEVANCY = "contextual_relevancy"


# =============================================================================
# DeepEval Compatible Test Case
# =============================================================================


@dataclass
class RAGTestCase:
    """DeepEval LLMTestCase 호환 RAG 테스트 케이스.

    DeepEval LLMTestCase 구조:
        - input: 사용자 질문
        - actual_output: RAG 파이프라인 생성 답변
        - expected_output: 기대 답변 (ground truth)
        - retrieval_context: 검색된 컨텍스트
        - context: 전체 컨텍스트 (optional)

    References:
        https://deepeval.com/docs/getting-started-rag
    """

    # Required fields (DeepEval compatible)
    input: str  # 사용자 질문
    actual_output: str  # RAG 생성 답변

    # RAG specific fields
    retrieval_context: list[str] = field(default_factory=list)  # 검색된 컨텍스트
    expected_output: str | None = None  # ground truth
    context: list[str] | None = None  # 전체 컨텍스트

    # EvalVault extensions
    test_id: str = ""
    category: str = ""
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.test_id:
            self.test_id = generate_result_id()

    def to_deepeval_dict(self) -> dict[str, Any]:
        """DeepEval LLMTestCase 호환 딕셔너리."""
        return {
            "input": self.input,
            "actual_output": self.actual_output,
            "expected_output": self.expected_output,
            "retrieval_context": self.retrieval_context,
            "context": self.context,
        }

    def to_ragas_dict(self) -> dict[str, Any]:
        """Ragas 호환 딕셔너리."""
        return {
            "question": self.input,
            "answer": self.actual_output,
            "contexts": self.retrieval_context,
            "ground_truth": self.expected_output,
        }

    def to_dict(self) -> dict[str, Any]:
        """전체 딕셔너리."""
        return {
            "test_id": self.test_id,
            "category": self.category,
            "input": self.input,
            "actual_output": self.actual_output,
            "expected_output": self.expected_output,
            "retrieval_context": self.retrieval_context,
            "context": self.context,
            "keywords": self.keywords,
            "metadata": self.metadata,
        }


@dataclass
class RAGTestCaseResult:
    """RAG 테스트 케이스 평가 결과.

    DeepEval 스타일의 메트릭 결과:
        - score: 0.0 ~ 1.0
        - threshold: 통과 기준
        - success: 통과 여부
        - reason: 점수 이유 (DeepEval include_reason)
    """

    test_case: RAGTestCase
    metrics: dict[str, float]  # {metric_name: score}
    threshold: float = 0.7
    success: bool = True
    reason: str | None = None  # DeepEval include_reason
    duration_ms: float = 0.0
    error: str | None = None

    @property
    def main_score(self) -> float:
        """메인 점수 (첫 번째 메트릭 또는 평균)."""
        if not self.metrics:
            return 0.0
        return list(self.metrics.values())[0]

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "test_id": self.test_case.test_id,
            "category": self.test_case.category,
            "input": self.test_case.input,
            "actual_output": self.test_case.actual_output,
            "expected_output": self.test_case.expected_output,
            "retrieval_context": self.test_case.retrieval_context,
            "metrics": self.metrics,
            "threshold": self.threshold,
            "success": self.success,
            "reason": self.reason,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


# =============================================================================
# MTEB Compatible Results
# =============================================================================


@dataclass
class SplitScores:
    """데이터 분할별 점수 (MTEB 호환).

    MTEB scores 구조:
        {"test": [{"main_score": 0.85, ...}], "validation": [...]}
    """

    main_score: float
    metrics: dict[str, float] = field(default_factory=dict)
    hf_subset: str = "default"
    languages: list[str] = field(default_factory=lambda: ["kor-Hang"])

    def to_dict(self) -> dict[str, Any]:
        """MTEB 호환 딕셔너리로 변환."""
        result = {
            "main_score": self.main_score,
            "hf_subset": self.hf_subset,
            "languages": self.languages,
        }
        result.update(self.metrics)
        return result


@dataclass
class BenchmarkResult:
    """벤치마크 결과 (MTEB/lm-harness/DeepEval 호환).

    Multi-framework compatibility:
        - MTEB: to_mteb_dict()
        - lm-harness: to_lm_harness_dict()
        - DeepEval: to_deepeval_dict()
    """

    # Task identification
    task_name: str
    task_type: TaskType

    # Version info
    dataset_version: str = "1.0.0"
    mteb_version: str = "1.14.20"
    evalvault_version: str = "1.0.0"

    # Language and domain
    languages: list[str] = field(default_factory=lambda: ["kor-Hang"])
    domain: str = "insurance"

    # Scores by split (MTEB style)
    scores: dict[str, list[SplitScores]] = field(default_factory=dict)

    # Individual test results (DeepEval style)
    test_results: list[RAGTestCaseResult] = field(default_factory=list)

    # Timing
    evaluation_time: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    # Model info
    model_name: str | None = None
    model_revision: str | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def main_score(self) -> float | None:
        """메인 점수 반환."""
        if "test" in self.scores and self.scores["test"]:
            return self.scores["test"][0].main_score
        return None

    @property
    def total_tests(self) -> int:
        """전체 테스트 수."""
        return len(self.test_results)

    @property
    def passed_tests(self) -> int:
        """통과한 테스트 수."""
        return sum(1 for r in self.test_results if r.success)

    @property
    def failed_tests(self) -> int:
        """실패한 테스트 수."""
        return sum(1 for r in self.test_results if not r.success)

    @property
    def pass_rate(self) -> float:
        """통과율."""
        if self.total_tests == 0:
            return 0.0
        return self.passed_tests / self.total_tests

    def add_test_result(self, result: RAGTestCaseResult) -> None:
        """테스트 결과 추가."""
        self.test_results.append(result)

    def calculate_scores(self, split: str = "test") -> None:
        """테스트 결과에서 점수 계산."""
        if not self.test_results:
            return

        # Aggregate metrics
        all_metrics: dict[str, list[float]] = {}
        for result in self.test_results:
            for metric_name, value in result.metrics.items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(value)

        # Calculate averages
        avg_metrics = {
            name: sum(values) / len(values) for name, values in all_metrics.items() if values
        }

        # Determine main score
        main_score = 0.0
        if "accuracy" in avg_metrics:
            main_score = avg_metrics["accuracy"]
        elif "f1" in avg_metrics:
            main_score = avg_metrics["f1"]
        elif "faithfulness" in avg_metrics:
            main_score = avg_metrics["faithfulness"]
        elif avg_metrics:
            main_score = list(avg_metrics.values())[0]

        split_score = SplitScores(
            main_score=main_score,
            metrics=avg_metrics,
            languages=self.languages,
        )

        if split not in self.scores:
            self.scores[split] = []
        self.scores[split].append(split_score)

    def finalize(self) -> None:
        """결과 완료 처리."""
        self.completed_at = datetime.now(UTC)
        if self.started_at:
            self.evaluation_time = (self.completed_at - self.started_at).total_seconds()
        self.calculate_scores()

    def to_mteb_dict(self) -> dict[str, Any]:
        """MTEB 호환 딕셔너리."""
        return {
            "task_name": self.task_name,
            "task_type": self.task_type.value,
            "mteb_version": self.mteb_version,
            "evalvault_version": self.evalvault_version,
            "dataset_revision": self.dataset_version,
            "languages": self.languages,
            "scores": {
                split: [score.to_dict() for score in scores]
                for split, scores in self.scores.items()
            },
            "evaluation_time": self.evaluation_time,
            "metadata": {
                "domain": self.domain,
                "model_name": self.model_name,
                "model_revision": self.model_revision,
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "pass_rate": self.pass_rate,
                **self.metadata,
            },
        }

    def to_lm_harness_dict(self) -> dict[str, Any]:
        """lm-evaluation-harness 호환 딕셔너리."""
        metrics = {}
        if "test" in self.scores and self.scores["test"]:
            for score in self.scores["test"]:
                for metric_name, value in score.metrics.items():
                    metrics[f"{metric_name},none"] = value
                metrics["main_score,none"] = score.main_score

        return {
            "results": {
                self.task_name: metrics,
            },
            "n-shot": 0,
            "config": {
                "task": self.task_name,
                "task_type": self.task_type.value,
                "languages": self.languages,
                "domain": self.domain,
            },
            "versions": {
                self.task_name: self.dataset_version,
            },
            "evaluation_time": self.evaluation_time,
        }

    def to_deepeval_dict(self) -> dict[str, Any]:
        """DeepEval 호환 딕셔너리.

        DeepEval evaluate() 결과 형식:
            {
                "test_results": [...],
                "metrics_summary": {...},
                "overall_success": true/false
            }
        """
        metrics_summary: dict[str, dict[str, float]] = {}
        for result in self.test_results:
            for metric_name, value in result.metrics.items():
                if metric_name not in metrics_summary:
                    metrics_summary[metric_name] = {
                        "scores": [],
                        "threshold": result.threshold,
                    }
                metrics_summary[metric_name]["scores"].append(value)

        # Calculate averages
        for metric_name in metrics_summary:
            scores = metrics_summary[metric_name]["scores"]
            metrics_summary[metric_name]["average"] = sum(scores) / len(scores) if scores else 0.0
            metrics_summary[metric_name]["min"] = min(scores) if scores else 0.0
            metrics_summary[metric_name]["max"] = max(scores) if scores else 0.0

        return {
            "test_results": [r.to_dict() for r in self.test_results],
            "metrics_summary": metrics_summary,
            "overall_success": all(r.success for r in self.test_results),
            "pass_rate": self.pass_rate,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "evaluation_time": self.evaluation_time,
        }

    def to_dict(self) -> dict[str, Any]:
        """전체 결과 딕셔너리."""
        result = self.to_mteb_dict()
        result["deepeval_format"] = self.to_deepeval_dict()
        result["test_results"] = [r.to_dict() for r in self.test_results]
        result["started_at"] = self.started_at.isoformat() if self.started_at else None
        result["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        return result


# =============================================================================
# Benchmark Suite
# =============================================================================


@dataclass
class BenchmarkSuite:
    """벤치마크 스위트 (여러 태스크 포함).

    MTEB/DeepEval 호환 스위트:
        - 여러 태스크를 포함
        - 전체 평균 점수 계산
        - 리더보드 형식 출력
    """

    name: str
    version: str = "1.0.0"
    description: str = ""
    languages: list[str] = field(default_factory=lambda: ["kor-Hang"])
    domain: str = "insurance"

    task_results: list[BenchmarkResult] = field(default_factory=list)

    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    total_evaluation_time: float = 0.0

    model_name: str | None = None
    model_revision: str | None = None

    @property
    def average_score(self) -> float | None:
        """전체 평균 점수."""
        scores = [r.main_score for r in self.task_results if r.main_score is not None]
        if not scores:
            return None
        return sum(scores) / len(scores)

    @property
    def task_count(self) -> int:
        """태스크 수."""
        return len(self.task_results)

    @property
    def total_pass_rate(self) -> float:
        """전체 통과율."""
        total = sum(r.total_tests for r in self.task_results)
        passed = sum(r.passed_tests for r in self.task_results)
        return passed / total if total > 0 else 0.0

    def add_result(self, result: BenchmarkResult) -> None:
        """태스크 결과 추가."""
        self.task_results.append(result)

    def finalize(self) -> None:
        """스위트 완료 처리."""
        self.completed_at = datetime.now(UTC)
        self.total_evaluation_time = sum(r.evaluation_time for r in self.task_results)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "languages": self.languages,
            "domain": self.domain,
            "model_name": self.model_name,
            "model_revision": self.model_revision,
            "summary": {
                "average_score": self.average_score,
                "task_count": self.task_count,
                "total_pass_rate": self.total_pass_rate,
                "total_evaluation_time": self.total_evaluation_time,
            },
            "tasks": [r.to_mteb_dict() for r in self.task_results],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
        }

    def to_leaderboard_format(self) -> dict[str, Any]:
        """HuggingFace Open LLM Leaderboard 스타일."""
        result = {
            "model": self.model_name or "unknown",
            "revision": self.model_revision or "unknown",
            "average": self.average_score,
            "pass_rate": self.total_pass_rate,
        }
        for task_result in self.task_results:
            result[task_result.task_name] = task_result.main_score
        return result


# =============================================================================
# Benchmark Config
# =============================================================================


@dataclass
class BenchmarkConfig:
    """벤치마크 설정."""

    name: str
    version: str = "1.0.0"
    task_type: TaskType = TaskType.RAG_FAITHFULNESS
    languages: list[str] = field(default_factory=lambda: ["kor-Hang"])
    domain: str = "insurance"
    test_file: str | None = None
    output_dir: str = "./benchmark_results"
    output_format: str = "full"  # mteb, lm_harness, deepeval, full
    threshold: float = 0.7
    verbose: bool = False
    model_name: str | None = None
    model_revision: str | None = None


def generate_result_id() -> str:
    """결과 ID 생성."""
    return uuid.uuid4().hex[:16]
