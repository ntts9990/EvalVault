"""Korean RAG Benchmark Runner.

한국어 RAG 최적화 효과를 측정하는 벤치마크 러너입니다.
MTEB/DeepEval 호환 결과 형식을 지원하며, pytest와 통합됩니다.

Usage:
    # 직접 실행
    runner = KoreanRAGBenchmarkRunner()
    results = runner.run_faithfulness_benchmark("path/to/data.json")

    # pytest fixture로 사용
    @pytest.fixture
    def benchmark_runner():
        return KoreanRAGBenchmarkRunner()

References:
    - MTEB: https://github.com/embeddings-benchmark/mteb
    - DeepEval: https://github.com/confident-ai/deepeval
    - lm-evaluation-harness: https://github.com/EleutherAI/lm-evaluation-harness
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from evalvault.domain.entities.benchmark import (
    BenchmarkResult,
    BenchmarkSuite,
    RAGTestCase,
    RAGTestCaseResult,
    TaskType,
)


@dataclass
class BenchmarkComparison:
    """벤치마크 비교 결과 (형태소 분석 vs 기준선)."""

    metric_name: str
    baseline_score: float
    optimized_score: float
    improvement: float
    improvement_percent: float
    is_significant: bool  # 통계적 유의성
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            "metric": self.metric_name,
            "baseline": self.baseline_score,
            "optimized": self.optimized_score,
            "improvement": self.improvement,
            "improvement_percent": self.improvement_percent,
            "is_significant": self.is_significant,
            "details": self.details,
        }


class KoreanRAGBenchmarkRunner:
    """한국어 RAG 벤치마크 러너.

    형태소 분석 기반 최적화 효과를 측정합니다:
    - Faithfulness: 조사/어미 변형 무시 효과
    - Keyword Extraction: 형태소 분석 vs 공백 기반
    - Retrieval: BM25 + Dense 하이브리드 검색 효과
    """

    def __init__(
        self,
        use_korean_tokenizer: bool = True,
        threshold: float = 0.7,
        verbose: bool = False,
    ) -> None:
        """벤치마크 러너 초기화.

        Args:
            use_korean_tokenizer: Kiwi 형태소 분석기 사용 여부
            threshold: 통과 기준 점수
            verbose: 상세 출력 여부
        """
        self.use_korean_tokenizer = use_korean_tokenizer
        self.threshold = threshold
        self.verbose = verbose
        self._tokenizer = None
        self._faithfulness_checker = None
        self._semantic_similarity = None

    @property
    def tokenizer(self) -> Any:
        """KiwiTokenizer 인스턴스 (lazy loading)."""
        if self._tokenizer is None and self.use_korean_tokenizer:
            try:
                from evalvault.adapters.outbound.nlp.korean import KiwiTokenizer

                self._tokenizer = KiwiTokenizer()
            except ImportError:
                self._tokenizer = None
        return self._tokenizer

    @property
    def faithfulness_checker(self) -> Any:
        """KoreanFaithfulnessChecker 인스턴스 (lazy loading)."""
        if self._faithfulness_checker is None:
            try:
                from evalvault.adapters.outbound.nlp.korean import (
                    KoreanFaithfulnessChecker,
                )

                self._faithfulness_checker = KoreanFaithfulnessChecker(tokenizer=self.tokenizer)
            except ImportError:
                self._faithfulness_checker = None
        return self._faithfulness_checker

    @property
    def semantic_similarity(self) -> Any:
        """KoreanSemanticSimilarity 인스턴스 (lazy loading)."""
        if self._semantic_similarity is None:
            try:
                from evalvault.adapters.outbound.nlp.korean import (
                    KoreanSemanticSimilarity,
                )

                self._semantic_similarity = KoreanSemanticSimilarity(tokenizer=self.tokenizer)
            except ImportError:
                self._semantic_similarity = None
        return self._semantic_similarity

    def load_test_data(self, file_path: str | Path) -> dict[str, Any]:
        """테스트 데이터 로드."""
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    def run_faithfulness_benchmark(
        self,
        test_file: str | Path,
        compare_baseline: bool = True,
    ) -> BenchmarkResult:
        """Faithfulness 벤치마크 실행.

        조사/어미 변형이 포함된 답변의 충실성을 정확히 판단할 수 있는지 측정합니다.

        Args:
            test_file: 테스트 데이터 파일 경로
            compare_baseline: 기준선(공백 기반)과 비교 여부

        Returns:
            BenchmarkResult: 벤치마크 결과
        """
        data = self.load_test_data(test_file)
        test_cases = data.get("test_cases", [])

        result = BenchmarkResult(
            task_name=data.get("name", "korean-faithfulness-benchmark"),
            task_type=TaskType.RAG_FAITHFULNESS,
            dataset_version=data.get("version", "1.0.0"),
            domain="insurance",
        )

        for tc in test_cases:
            start_time = time.time()

            # RAG 테스트 케이스 생성
            rag_case = RAGTestCase(
                test_id=tc.get("test_id", ""),
                category=tc.get("category", ""),
                input=tc.get("answer", ""),  # answer를 input으로 사용
                actual_output=tc.get("answer", ""),
                retrieval_context=tc.get("contexts", []),
                expected_output=str(tc.get("expected_faithful", True)),
            )

            # 형태소 분석 기반 Faithfulness 검사
            metrics: dict[str, float] = {}
            reason = None
            error = None

            try:
                if self.faithfulness_checker:
                    faith_result = self.faithfulness_checker.check_faithfulness(
                        answer=tc.get("answer", ""),
                        contexts=tc.get("contexts", []),
                    )
                    metrics["faithfulness"] = faith_result.score
                    metrics["coverage"] = faith_result.coverage
                    reason = (
                        f"Verified {faith_result.verified_count}/{faith_result.total_claims} claims"
                    )
                else:
                    # Fallback: 단순 문자열 비교
                    metrics["faithfulness"] = self._simple_faithfulness(
                        tc.get("answer", ""),
                        tc.get("contexts", []),
                    )

                # 기대 점수 범위 체크
                expected_range = tc.get("expected_score_range", [0.0, 1.0])
                in_range = expected_range[0] <= metrics["faithfulness"] <= expected_range[1]
                metrics["in_expected_range"] = 1.0 if in_range else 0.0

            except Exception as e:
                error = str(e)
                metrics["faithfulness"] = 0.0

            duration_ms = (time.time() - start_time) * 1000

            # 통과 여부 결정
            expected_faithful = tc.get("expected_faithful")
            if expected_faithful is True:
                success = metrics.get("faithfulness", 0) >= self.threshold
            elif expected_faithful is False:
                success = metrics.get("faithfulness", 0) < self.threshold
            else:  # partial
                success = 0.3 <= metrics.get("faithfulness", 0) <= 0.7

            test_result = RAGTestCaseResult(
                test_case=rag_case,
                metrics=metrics,
                threshold=self.threshold,
                success=success,
                reason=reason,
                duration_ms=duration_ms,
                error=error,
            )
            result.add_test_result(test_result)

            if self.verbose:
                status = "✓" if success else "✗"
                print(
                    f"  {status} {tc.get('test_id')}: "
                    f"faithfulness={metrics.get('faithfulness', 0):.3f}"
                )

        result.finalize()
        return result

    def run_keyword_extraction_benchmark(
        self,
        test_file: str | Path,
    ) -> BenchmarkResult:
        """키워드 추출 벤치마크 실행.

        형태소 분석이 의미있는 키워드를 더 정확하게 추출하는지 측정합니다.

        Args:
            test_file: 테스트 데이터 파일 경로

        Returns:
            BenchmarkResult: 벤치마크 결과
        """
        data = self.load_test_data(test_file)
        test_cases = data.get("test_cases", [])

        result = BenchmarkResult(
            task_name=data.get("name", "korean-keyword-extraction-benchmark"),
            task_type=TaskType.KEYWORD_EXTRACTION,
            dataset_version=data.get("version", "1.0.0"),
            domain="insurance",
        )

        for tc in test_cases:
            start_time = time.time()

            text = tc.get("text", "")
            ground_truth = set(tc.get("ground_truth_keywords", []))

            rag_case = RAGTestCase(
                test_id=tc.get("test_id", ""),
                category="keyword_extraction",
                input=text,
                actual_output="",  # 추출된 키워드로 채워짐
                expected_output=",".join(ground_truth),
            )

            metrics: dict[str, float] = {}
            error = None

            try:
                # 형태소 분석 기반 키워드 추출
                if self.tokenizer:
                    extracted = set(self.tokenizer.extract_keywords(text))
                else:
                    # Fallback: 공백 기반
                    extracted = set(text.split())

                rag_case.actual_output = ",".join(extracted)

                # Precision, Recall, F1 계산
                if extracted:
                    tp = len(extracted & ground_truth)
                    precision = tp / len(extracted)
                    recall = tp / len(ground_truth) if ground_truth else 0.0
                    f1 = (
                        2 * precision * recall / (precision + recall)
                        if (precision + recall) > 0
                        else 0.0
                    )
                else:
                    precision = recall = f1 = 0.0

                metrics["precision"] = precision
                metrics["recall"] = recall
                metrics["f1"] = f1

                # 기준선 비교 (공백 기반)
                whitespace_extracted = {w for w in text.split() if len(w) >= 2}
                if whitespace_extracted:
                    ws_tp = len(whitespace_extracted & ground_truth)
                    ws_precision = ws_tp / len(whitespace_extracted)
                    metrics["baseline_precision"] = ws_precision
                    metrics["improvement"] = precision - ws_precision

            except Exception as e:
                error = str(e)
                metrics["f1"] = 0.0

            duration_ms = (time.time() - start_time) * 1000
            success = metrics.get("f1", 0) >= 0.5  # F1 >= 0.5 통과

            test_result = RAGTestCaseResult(
                test_case=rag_case,
                metrics=metrics,
                threshold=0.5,
                success=success,
                duration_ms=duration_ms,
                error=error,
            )
            result.add_test_result(test_result)

            if self.verbose:
                status = "✓" if success else "✗"
                print(
                    f"  {status} {tc.get('test_id')}: "
                    f"precision={metrics.get('precision', 0):.3f}, "
                    f"recall={metrics.get('recall', 0):.3f}, "
                    f"f1={metrics.get('f1', 0):.3f}"
                )

        result.finalize()
        return result

    def run_retrieval_benchmark(
        self,
        test_file: str | Path,
    ) -> BenchmarkResult:
        """검색 벤치마크 실행.

        조사/어미 변형이 검색 결과에 미치는 영향을 측정합니다.

        Args:
            test_file: 테스트 데이터 파일 경로

        Returns:
            BenchmarkResult: 벤치마크 결과
        """
        data = self.load_test_data(test_file)
        documents = data.get("documents", [])
        test_cases = data.get("test_cases", [])

        result = BenchmarkResult(
            task_name=data.get("name", "korean-retrieval-benchmark"),
            task_type=TaskType.RETRIEVAL,
            dataset_version=data.get("version", "1.0.0"),
            domain="insurance",
        )

        # 검색기 초기화
        retriever = None

        try:
            from evalvault.adapters.outbound.nlp.korean import KoreanBM25Retriever

            if self.tokenizer:
                retriever = KoreanBM25Retriever(tokenizer=self.tokenizer)
                doc_contents = [d.get("content", "") for d in documents]
                retriever.index(doc_contents)
            else:
                # tokenizer 없으면 기본 BM25로 fallback
                # KoreanBM25Retriever는 tokenizer 필수이므로 None인 경우 스킵
                pass

        except ImportError:
            pass

        doc_id_map = {d.get("doc_id"): i for i, d in enumerate(documents)}

        for tc in test_cases:
            start_time = time.time()

            query = tc.get("query", "")
            relevant_doc_ids = tc.get("relevant_docs", [])
            relevant_indices = {
                doc_id_map[doc_id] for doc_id in relevant_doc_ids if doc_id in doc_id_map
            }

            rag_case = RAGTestCase(
                test_id=tc.get("test_id", ""),
                category=tc.get("category", ""),
                input=query,
                actual_output="",
                expected_output=",".join(relevant_doc_ids),
            )

            metrics: dict[str, float] = {}
            error = None

            try:
                # 형태소 분석 기반 검색
                if retriever:
                    results = retriever.search(query, top_k=5)
                    # 검색 결과에서 doc_id 추출
                    retrieved_doc_ids = set()
                    for i, res in enumerate(results):
                        if hasattr(res, "doc_id"):
                            retrieved_doc_ids.add(res.doc_id)
                        else:
                            retrieved_doc_ids.add(i)

                    # Recall@5 계산
                    hits = len(relevant_indices & retrieved_doc_ids)
                    recall_at_5 = hits / len(relevant_indices) if relevant_indices else 0.0
                    metrics["recall_at_5"] = recall_at_5

                    # MRR 계산
                    for rank, res in enumerate(results, 1):
                        doc_id = res.doc_id if hasattr(res, "doc_id") else rank - 1
                        if doc_id in relevant_indices:
                            metrics["mrr"] = 1.0 / rank
                            break
                    else:
                        metrics["mrr"] = 0.0
                else:
                    # retriever 없으면 단순 키워드 매칭
                    doc_contents = [d.get("content", "") for d in documents]
                    query_words = set(query.lower().split())
                    scores = []
                    for i, doc in enumerate(doc_contents):
                        doc_words = set(doc.lower().split())
                        overlap = len(query_words & doc_words)
                        scores.append((i, overlap))
                    scores.sort(key=lambda x: x[1], reverse=True)
                    retrieved_ids = {s[0] for s in scores[:5]}

                    hits = len(relevant_indices & retrieved_ids)
                    recall_at_5 = hits / len(relevant_indices) if relevant_indices else 0.0
                    metrics["recall_at_5"] = recall_at_5
                    metrics["mrr"] = 0.0
                    for rank, (doc_id, _) in enumerate(scores[:5], 1):
                        if doc_id in relevant_indices:
                            metrics["mrr"] = 1.0 / rank
                            break

            except Exception as e:
                error = str(e)
                metrics["recall_at_5"] = 0.0

            duration_ms = (time.time() - start_time) * 1000
            success = metrics.get("recall_at_5", 0) >= 0.5

            test_result = RAGTestCaseResult(
                test_case=rag_case,
                metrics=metrics,
                threshold=0.5,
                success=success,
                duration_ms=duration_ms,
                error=error,
            )
            result.add_test_result(test_result)

            if self.verbose:
                status = "✓" if success else "✗"
                print(
                    f"  {status} {tc.get('test_id')}: "
                    f"recall@5={metrics.get('recall_at_5', 0):.3f}, "
                    f"mrr={metrics.get('mrr', 0):.3f}"
                )

        result.finalize()
        return result

    def run_full_suite(
        self,
        benchmark_dir: str | Path,
        output_dir: str | Path | None = None,
    ) -> BenchmarkSuite:
        """전체 벤치마크 스위트 실행.

        Args:
            benchmark_dir: 벤치마크 데이터 디렉토리
            output_dir: 결과 출력 디렉토리

        Returns:
            BenchmarkSuite: 전체 벤치마크 결과
        """
        benchmark_dir = Path(benchmark_dir)

        suite = BenchmarkSuite(
            name="korean-rag-benchmark-suite",
            version="1.0.0",
            description="한국어 RAG 최적화 효과 측정 벤치마크",
            languages=["kor-Hang"],
            domain="insurance",
        )

        print("=" * 60)
        print("Korean RAG Benchmark Suite")
        print("=" * 60)

        # 1. Faithfulness 벤치마크
        faithfulness_file = benchmark_dir / "faithfulness_test.json"
        if faithfulness_file.exists():
            print("\n[1/3] Running Faithfulness Benchmark...")
            result = self.run_faithfulness_benchmark(faithfulness_file)
            suite.add_result(result)
            print(f"  → Score: {result.main_score:.3f}, Pass Rate: {result.pass_rate:.1%}")

        # 2. Keyword Extraction 벤치마크
        keyword_file = benchmark_dir / "keyword_extraction_test.json"
        if keyword_file.exists():
            print("\n[2/3] Running Keyword Extraction Benchmark...")
            result = self.run_keyword_extraction_benchmark(keyword_file)
            suite.add_result(result)
            print(f"  → F1 Score: {result.main_score:.3f}, Pass Rate: {result.pass_rate:.1%}")

        # 3. Retrieval 벤치마크
        retrieval_file = benchmark_dir / "retrieval_test.json"
        if retrieval_file.exists():
            print("\n[3/3] Running Retrieval Benchmark...")
            result = self.run_retrieval_benchmark(retrieval_file)
            suite.add_result(result)
            print(f"  → Recall@5: {result.main_score:.3f}, Pass Rate: {result.pass_rate:.1%}")

        suite.finalize()

        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"  Tasks: {suite.task_count}")
        print(f"  Average Score: {suite.average_score:.3f}")
        print(f"  Total Pass Rate: {suite.total_pass_rate:.1%}")
        print(f"  Evaluation Time: {suite.total_evaluation_time:.2f}s")

        # 결과 저장
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # MTEB 형식
            mteb_file = output_dir / "results_mteb.json"
            with open(mteb_file, "w", encoding="utf-8") as f:
                json.dump(suite.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"\n  Results saved to: {mteb_file}")

            # Leaderboard 형식
            leaderboard_file = output_dir / "leaderboard.json"
            with open(leaderboard_file, "w", encoding="utf-8") as f:
                json.dump(suite.to_leaderboard_format(), f, indent=2, ensure_ascii=False)
            print(f"  Leaderboard saved to: {leaderboard_file}")

        return suite

    def _simple_faithfulness(
        self,
        answer: str,
        contexts: list[str],
    ) -> float:
        """단순 문자열 기반 Faithfulness 계산 (기준선)."""
        if not answer or not contexts:
            return 0.0

        context_text = " ".join(contexts).lower()
        answer_words = set(answer.lower().split())

        if not answer_words:
            return 0.0

        matched = sum(1 for w in answer_words if w in context_text)
        return matched / len(answer_words)

    def compare_with_baseline(
        self,
        test_file: str | Path,
        task_type: str = "faithfulness",
    ) -> list[BenchmarkComparison]:
        """형태소 분석 vs 기준선 비교.

        Args:
            test_file: 테스트 데이터 파일 경로
            task_type: 벤치마크 타입 (faithfulness, keyword, retrieval)

        Returns:
            list[BenchmarkComparison]: 비교 결과 목록
        """
        comparisons = []

        # 형태소 분석 모드로 실행
        self.use_korean_tokenizer = True
        self._tokenizer = None  # Reset
        self._faithfulness_checker = None

        if task_type == "faithfulness":
            optimized_result = self.run_faithfulness_benchmark(test_file)
        elif task_type == "keyword":
            optimized_result = self.run_keyword_extraction_benchmark(test_file)
        else:
            optimized_result = self.run_retrieval_benchmark(test_file)

        # 기준선 모드로 실행
        self.use_korean_tokenizer = False
        self._tokenizer = None
        self._faithfulness_checker = None

        if task_type == "faithfulness":
            baseline_result = self.run_faithfulness_benchmark(test_file)
        elif task_type == "keyword":
            baseline_result = self.run_keyword_extraction_benchmark(test_file)
        else:
            baseline_result = self.run_retrieval_benchmark(test_file)

        # 메트릭별 비교
        if optimized_result.scores.get("test") and baseline_result.scores.get("test"):
            opt_metrics = optimized_result.scores["test"][0].metrics
            base_metrics = baseline_result.scores["test"][0].metrics

            for metric_name in opt_metrics:
                if metric_name in base_metrics:
                    opt_score = opt_metrics[metric_name]
                    base_score = base_metrics[metric_name]
                    improvement = opt_score - base_score
                    improvement_pct = (improvement / base_score * 100) if base_score > 0 else 0.0

                    comparisons.append(
                        BenchmarkComparison(
                            metric_name=metric_name,
                            baseline_score=base_score,
                            optimized_score=opt_score,
                            improvement=improvement,
                            improvement_percent=improvement_pct,
                            is_significant=abs(improvement) >= 0.05,
                        )
                    )

        return comparisons


# =============================================================================
# pytest Integration
# =============================================================================


def pytest_benchmark_fixture(
    benchmark_dir: str | Path,
    verbose: bool = False,
) -> Callable:
    """pytest fixture 생성 헬퍼.

    Usage:
        @pytest.fixture
        def korean_benchmark():
            return pytest_benchmark_fixture("examples/benchmarks/korean_rag")
    """

    def _run_benchmarks() -> BenchmarkSuite:
        runner = KoreanRAGBenchmarkRunner(verbose=verbose)
        return runner.run_full_suite(benchmark_dir)

    return _run_benchmarks
