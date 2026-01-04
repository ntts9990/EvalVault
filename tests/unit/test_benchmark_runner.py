"""Korean RAG Benchmark Runner 테스트.

벤치마크 러너의 기능을 검증합니다:
- Faithfulness 벤치마크
- Keyword Extraction 벤치마크
- Retrieval 벤치마크
- 기준선 비교
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from evalvault.domain.entities.benchmark import (
    BenchmarkResult,
    BenchmarkSuite,
    RAGTestCase,
    RAGTestCaseResult,
    TaskType,
)
from evalvault.domain.services.benchmark_runner import (
    BenchmarkComparison,
    KoreanRAGBenchmarkRunner,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_faithfulness_data() -> dict:
    """샘플 Faithfulness 테스트 데이터."""
    return {
        "name": "test-faithfulness-benchmark",
        "version": "1.0.0",
        "test_cases": [
            {
                "test_id": "faith-001",
                "category": "faithful_exact",
                "answer": "보험료는 월 15만원입니다.",
                "contexts": ["보험료는 월 15만원입니다."],
                "expected_faithful": True,
                "expected_score_range": [0.9, 1.0],
            },
            {
                "test_id": "faith-002",
                "category": "faithful_with_variation",
                "answer": "보험료가 월 15만원이에요.",
                "contexts": ["보험료는 월 15만원입니다."],
                "expected_faithful": True,
                "expected_score_range": [0.7, 1.0],
            },
            {
                "test_id": "faith-003",
                "category": "unfaithful",
                "answer": "보험료는 월 20만원입니다.",
                "contexts": ["보험료는 월 15만원입니다."],
                "expected_faithful": False,
                "expected_score_range": [0.0, 0.3],
            },
        ],
    }


@pytest.fixture
def sample_keyword_data() -> dict:
    """샘플 키워드 추출 테스트 데이터."""
    return {
        "name": "test-keyword-benchmark",
        "version": "1.0.0",
        "test_cases": [
            {
                "test_id": "kw-001",
                "text": "보험료가 월 15만원이며, 납입 기간은 20년입니다.",
                "ground_truth_keywords": ["보험료", "15만원", "납입", "기간", "20년"],
            },
            {
                "test_id": "kw-002",
                "text": "사망보험금은 피보험자 사망 시 수익자에게 지급됩니다.",
                "ground_truth_keywords": ["사망보험금", "피보험자", "사망", "수익자", "지급"],
            },
        ],
    }


@pytest.fixture
def sample_retrieval_data() -> dict:
    """샘플 검색 테스트 데이터."""
    return {
        "name": "test-retrieval-benchmark",
        "version": "1.0.0",
        "evaluation_metrics": ["recall@5", "mrr", "ndcg@5"],
        "documents": [
            {"doc_id": "doc-001", "content": "보험료는 월 15만원입니다."},
            {"doc_id": "doc-002", "content": "사망보험금은 1억원입니다."},
            {"doc_id": "doc-003", "content": "암 진단비는 3천만원입니다."},
        ],
        "test_cases": [
            {
                "test_id": "ret-001",
                "category": "baseline",
                "query": "보험료",
                "relevant_doc_ids": ["doc-001"],
            },
            {
                "test_id": "ret-002",
                "category": "particle_variation",
                "query": "사망보험금이 얼마인가요",
                "relevant_doc_ids": ["doc-002"],
            },
        ],
    }


@pytest.fixture
def sample_retrieval_data_legacy() -> dict:
    """레거시 relevant_docs 테스트 데이터."""
    return {
        "name": "test-retrieval-benchmark-legacy",
        "version": "1.0.0",
        "documents": [
            {"doc_id": "doc-001", "content": "보험료는 월 15만원입니다."},
            {"doc_id": "doc-002", "content": "사망보험금은 1억원입니다."},
        ],
        "test_cases": [
            {
                "test_id": "ret-legacy-001",
                "category": "baseline",
                "query": "보험료",
                "relevant_docs": ["doc-001"],
            },
        ],
    }


@pytest.fixture
def benchmark_runner() -> KoreanRAGBenchmarkRunner:
    """벤치마크 러너 fixture."""
    return KoreanRAGBenchmarkRunner(
        use_korean_tokenizer=False,  # 테스트에서는 기본 모드
        threshold=0.7,
        verbose=False,
    )


# =============================================================================
# Entity Tests
# =============================================================================


class TestRAGTestCase:
    """RAGTestCase 테스트."""

    def test_create_test_case(self) -> None:
        """테스트 케이스 생성."""
        tc = RAGTestCase(
            input="질문입니다",
            actual_output="답변입니다",
            retrieval_context=["컨텍스트1", "컨텍스트2"],
            expected_output="기대 답변",
        )

        assert tc.input == "질문입니다"
        assert tc.actual_output == "답변입니다"
        assert len(tc.retrieval_context) == 2
        assert tc.expected_output == "기대 답변"
        assert tc.test_id  # 자동 생성됨

    def test_to_deepeval_dict(self) -> None:
        """DeepEval 호환 딕셔너리 변환."""
        tc = RAGTestCase(
            input="질문",
            actual_output="답변",
            retrieval_context=["컨텍스트"],
            expected_output="기대",
        )

        d = tc.to_deepeval_dict()

        assert d["input"] == "질문"
        assert d["actual_output"] == "답변"
        assert d["retrieval_context"] == ["컨텍스트"]
        assert d["expected_output"] == "기대"

    def test_to_ragas_dict(self) -> None:
        """Ragas 호환 딕셔너리 변환."""
        tc = RAGTestCase(
            input="질문",
            actual_output="답변",
            retrieval_context=["컨텍스트"],
            expected_output="기대",
        )

        d = tc.to_ragas_dict()

        assert d["question"] == "질문"
        assert d["answer"] == "답변"
        assert d["contexts"] == ["컨텍스트"]
        assert d["ground_truth"] == "기대"


class TestRAGTestCaseResult:
    """RAGTestCaseResult 테스트."""

    def test_create_result(self) -> None:
        """결과 생성."""
        tc = RAGTestCase(input="질문", actual_output="답변")
        result = RAGTestCaseResult(
            test_case=tc,
            metrics={"faithfulness": 0.85, "relevancy": 0.9},
            threshold=0.7,
            success=True,
        )

        assert result.main_score == 0.85  # 첫 번째 메트릭
        assert result.success is True
        assert result.threshold == 0.7

    def test_to_dict(self) -> None:
        """딕셔너리 변환."""
        tc = RAGTestCase(
            test_id="test-001",
            category="test",
            input="질문",
            actual_output="답변",
        )
        result = RAGTestCaseResult(
            test_case=tc,
            metrics={"faithfulness": 0.85},
            success=True,
        )

        d = result.to_dict()

        assert d["test_id"] == "test-001"
        assert d["metrics"]["faithfulness"] == 0.85
        assert d["success"] is True


class TestBenchmarkResult:
    """BenchmarkResult 테스트."""

    def test_create_result(self) -> None:
        """결과 생성."""
        result = BenchmarkResult(
            task_name="test-benchmark",
            task_type=TaskType.RAG_FAITHFULNESS,
        )

        assert result.task_name == "test-benchmark"
        assert result.task_type == TaskType.RAG_FAITHFULNESS
        assert result.total_tests == 0

    def test_add_test_result(self) -> None:
        """테스트 결과 추가."""
        result = BenchmarkResult(
            task_name="test",
            task_type=TaskType.RAG_FAITHFULNESS,
        )

        tc = RAGTestCase(input="q", actual_output="a")
        test_result = RAGTestCaseResult(
            test_case=tc,
            metrics={"faithfulness": 0.8},
            success=True,
        )

        result.add_test_result(test_result)

        assert result.total_tests == 1
        assert result.passed_tests == 1

    def test_finalize_calculates_scores(self) -> None:
        """finalize 호출 시 점수 계산."""
        result = BenchmarkResult(
            task_name="test",
            task_type=TaskType.RAG_FAITHFULNESS,
        )

        for score in [0.8, 0.9, 0.7]:
            tc = RAGTestCase(input="q", actual_output="a")
            result.add_test_result(
                RAGTestCaseResult(
                    test_case=tc,
                    metrics={"faithfulness": score},
                    success=score >= 0.7,
                )
            )

        result.finalize()

        assert result.main_score is not None
        assert abs(result.main_score - 0.8) < 0.01  # 평균 0.8

    def test_to_mteb_dict(self) -> None:
        """MTEB 형식 변환."""
        result = BenchmarkResult(
            task_name="test",
            task_type=TaskType.RAG_FAITHFULNESS,
        )
        result.finalize()

        d = result.to_mteb_dict()

        assert "task_name" in d
        assert "scores" in d
        assert "mteb_version" in d

    def test_to_lm_harness_dict(self) -> None:
        """lm-harness 형식 변환."""
        result = BenchmarkResult(
            task_name="test",
            task_type=TaskType.RAG_FAITHFULNESS,
        )
        result.finalize()

        d = result.to_lm_harness_dict()

        assert "results" in d
        assert "n-shot" in d
        assert "config" in d

    def test_to_deepeval_dict(self) -> None:
        """DeepEval 형식 변환."""
        result = BenchmarkResult(
            task_name="test",
            task_type=TaskType.RAG_FAITHFULNESS,
        )

        tc = RAGTestCase(input="q", actual_output="a")
        result.add_test_result(
            RAGTestCaseResult(
                test_case=tc,
                metrics={"faithfulness": 0.8},
                success=True,
            )
        )
        result.finalize()

        d = result.to_deepeval_dict()

        assert "test_results" in d
        assert "metrics_summary" in d
        assert "overall_success" in d
        assert d["pass_rate"] == 1.0


class TestBenchmarkSuite:
    """BenchmarkSuite 테스트."""

    def test_create_suite(self) -> None:
        """스위트 생성."""
        suite = BenchmarkSuite(
            name="test-suite",
            description="테스트 스위트",
        )

        assert suite.name == "test-suite"
        assert suite.task_count == 0

    def test_add_result(self) -> None:
        """결과 추가."""
        suite = BenchmarkSuite(name="test")

        result = BenchmarkResult(
            task_name="task1",
            task_type=TaskType.RAG_FAITHFULNESS,
        )
        result.finalize()

        suite.add_result(result)

        assert suite.task_count == 1

    def test_to_leaderboard_format(self) -> None:
        """리더보드 형식 변환."""
        suite = BenchmarkSuite(
            name="test",
            model_name="test-model",
        )

        for i, score in enumerate([0.8, 0.9]):
            result = BenchmarkResult(
                task_name=f"task{i}",
                task_type=TaskType.RAG_FAITHFULNESS,
            )
            tc = RAGTestCase(input="q", actual_output="a")
            result.add_test_result(
                RAGTestCaseResult(
                    test_case=tc,
                    metrics={"faithfulness": score},
                    success=True,
                )
            )
            result.finalize()
            suite.add_result(result)

        suite.finalize()

        d = suite.to_leaderboard_format()

        assert d["model"] == "test-model"
        assert "average" in d
        assert "task0" in d
        assert "task1" in d


# =============================================================================
# Runner Tests
# =============================================================================


class TestKoreanRAGBenchmarkRunner:
    """벤치마크 러너 테스트."""

    def test_init(self) -> None:
        """러너 초기화."""
        runner = KoreanRAGBenchmarkRunner(
            use_korean_tokenizer=False,
            threshold=0.8,
            verbose=True,
        )

        assert runner.threshold == 0.8
        assert runner.verbose is True

    def test_load_test_data(
        self,
        benchmark_runner: KoreanRAGBenchmarkRunner,
        sample_faithfulness_data: dict,
    ) -> None:
        """테스트 데이터 로드."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_faithfulness_data, f)
            f.flush()

            data = benchmark_runner.load_test_data(f.name)

            assert data["name"] == "test-faithfulness-benchmark"
            assert len(data["test_cases"]) == 3

    def test_run_faithfulness_benchmark(
        self,
        benchmark_runner: KoreanRAGBenchmarkRunner,
        sample_faithfulness_data: dict,
    ) -> None:
        """Faithfulness 벤치마크 실행."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_faithfulness_data, f)
            f.flush()

            result = benchmark_runner.run_faithfulness_benchmark(f.name)

            assert result.task_type == TaskType.RAG_FAITHFULNESS
            assert result.total_tests == 3
            assert result.main_score is not None

    def test_run_keyword_extraction_benchmark(
        self,
        benchmark_runner: KoreanRAGBenchmarkRunner,
        sample_keyword_data: dict,
    ) -> None:
        """키워드 추출 벤치마크 실행."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_keyword_data, f)
            f.flush()

            result = benchmark_runner.run_keyword_extraction_benchmark(f.name)

            assert result.task_type == TaskType.KEYWORD_EXTRACTION
            assert result.total_tests == 2
            # F1 점수가 계산되었는지 확인
            if result.test_results:
                assert "f1" in result.test_results[0].metrics

    def test_run_retrieval_benchmark(
        self,
        benchmark_runner: KoreanRAGBenchmarkRunner,
        sample_retrieval_data: dict,
    ) -> None:
        """검색 벤치마크 실행."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_retrieval_data, f)
            f.flush()

            result = benchmark_runner.run_retrieval_benchmark(f.name)

            assert result.task_type == TaskType.RETRIEVAL
            assert result.total_tests == 2
            if result.test_results:
                metrics = result.test_results[0].metrics
                assert "precision_at_5" in metrics
                assert "recall_at_5" in metrics
                assert "mrr" in metrics
                assert "ndcg_at_5" in metrics

    def test_run_retrieval_benchmark_legacy_field(
        self,
        benchmark_runner: KoreanRAGBenchmarkRunner,
        sample_retrieval_data_legacy: dict,
    ) -> None:
        """relevant_docs 필드 호환 테스트."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_retrieval_data_legacy, f)
            f.flush()

            result = benchmark_runner.run_retrieval_benchmark(f.name)

            assert result.task_type == TaskType.RETRIEVAL
            assert result.total_tests == 1

    def test_simple_faithfulness_fallback(
        self,
        benchmark_runner: KoreanRAGBenchmarkRunner,
    ) -> None:
        """단순 Faithfulness 폴백 테스트."""
        score = benchmark_runner._simple_faithfulness(
            answer="보험료는 월 15만원입니다",
            contexts=["보험료는 월 15만원입니다"],
        )

        assert score > 0.5  # 대부분의 단어가 매칭

    def test_simple_faithfulness_no_match(
        self,
        benchmark_runner: KoreanRAGBenchmarkRunner,
    ) -> None:
        """매칭 없는 경우 테스트."""
        score = benchmark_runner._simple_faithfulness(
            answer="완전히 다른 내용입니다",
            contexts=["보험료는 월 15만원입니다"],
        )

        assert score < 0.5


class TestBenchmarkComparison:
    """BenchmarkComparison 테스트."""

    def test_create_comparison(self) -> None:
        """비교 결과 생성."""
        comp = BenchmarkComparison(
            metric_name="faithfulness",
            baseline_score=0.6,
            optimized_score=0.85,
            improvement=0.25,
            improvement_percent=41.7,
            is_significant=True,
        )

        assert comp.metric_name == "faithfulness"
        assert comp.improvement == 0.25
        assert comp.is_significant is True

    def test_to_dict(self) -> None:
        """딕셔너리 변환."""
        comp = BenchmarkComparison(
            metric_name="f1",
            baseline_score=0.5,
            optimized_score=0.8,
            improvement=0.3,
            improvement_percent=60.0,
            is_significant=True,
        )

        d = comp.to_dict()

        assert d["metric"] == "f1"
        assert d["baseline"] == 0.5
        assert d["optimized"] == 0.8
        assert d["improvement"] == 0.3


# =============================================================================
# Integration Tests
# =============================================================================


class TestBenchmarkIntegration:
    """벤치마크 통합 테스트."""

    def test_full_benchmark_workflow(
        self,
        sample_faithfulness_data: dict,
        sample_keyword_data: dict,
    ) -> None:
        """전체 벤치마크 워크플로우."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # 테스트 데이터 저장
            faith_file = tmpdir / "faithfulness_test.json"
            with open(faith_file, "w") as f:
                json.dump(sample_faithfulness_data, f)

            keyword_file = tmpdir / "keyword_extraction_test.json"
            with open(keyword_file, "w") as f:
                json.dump(sample_keyword_data, f)

            # 벤치마크 실행
            runner = KoreanRAGBenchmarkRunner(
                use_korean_tokenizer=False,
                verbose=False,
            )

            faith_result = runner.run_faithfulness_benchmark(faith_file)
            keyword_result = runner.run_keyword_extraction_benchmark(keyword_file)

            # 스위트 생성
            suite = BenchmarkSuite(name="test-suite")
            suite.add_result(faith_result)
            suite.add_result(keyword_result)
            suite.finalize()

            # 검증
            assert suite.task_count == 2
            assert suite.average_score is not None

            # 출력 형식 검증
            mteb_dict = faith_result.to_mteb_dict()
            assert "scores" in mteb_dict

            deepeval_dict = faith_result.to_deepeval_dict()
            assert "test_results" in deepeval_dict

            leaderboard = suite.to_leaderboard_format()
            assert "average" in leaderboard
