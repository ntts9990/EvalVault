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
import logging
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
from evalvault.domain.services.retrieval_metrics import (
    compute_retrieval_metrics,
    resolve_doc_id,
)
from evalvault.ports.outbound.korean_nlp_port import KoreanNLPToolkitPort

logger = logging.getLogger(__name__)


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
        use_hybrid_search: bool = False,
        ollama_adapter: Any = None,
        embedding_profile: str | None = None,
        nlp_toolkit: KoreanNLPToolkitPort | None = None,
    ) -> None:
        """벤치마크 러너 초기화.

        Args:
            use_korean_tokenizer: Kiwi 형태소 분석기 사용 여부
            threshold: 통과 기준 점수
            verbose: 상세 출력 여부
            use_hybrid_search: 하이브리드 검색 (BM25 + Dense) 사용 여부
            ollama_adapter: Ollama LLM 어댑터 (Qwen3-Embedding 사용 시)
            embedding_profile: 임베딩 프로파일 ('dev' 또는 'prod')
        """
        self.use_korean_tokenizer = use_korean_tokenizer
        self.threshold = threshold
        self.verbose = verbose
        self.use_hybrid_search = use_hybrid_search
        self.ollama_adapter = ollama_adapter
        self.embedding_profile = embedding_profile
        self._nlp_toolkit = nlp_toolkit

    def _extract_keywords(self, text: str) -> set[str]:
        if self.use_korean_tokenizer and self._nlp_toolkit:
            try:
                return set(self._nlp_toolkit.extract_keywords(text))
            except Exception:  # pragma: no cover - best effort
                logger.warning("Korean keyword extraction failed, falling back to whitespace split")
        return {w for w in text.split() if w}

    def _check_faithfulness(self, answer: str, contexts: list[str]):
        if self.use_korean_tokenizer and self._nlp_toolkit:
            try:
                return self._nlp_toolkit.check_faithfulness(answer=answer, contexts=contexts)
            except Exception:  # pragma: no cover
                logger.warning("Faithfulness checker failure, falling back to simple comparison")
        return None

    def _build_retriever(self, documents: list[str]):
        if not self._nlp_toolkit:
            return None
        try:
            return self._nlp_toolkit.build_retriever(
                documents,
                use_hybrid=self.use_hybrid_search,
                ollama_adapter=self.ollama_adapter,
                embedding_profile=self.embedding_profile,
                verbose=self.verbose,
            )
        except Exception:  # pragma: no cover
            logger.warning("Korean retriever initialization failed, using fallback keyword search")
            return None

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
                faith_result = self._check_faithfulness(
                    tc.get("answer", ""),
                    tc.get("contexts", []),
                )
                if faith_result:
                    metrics["faithfulness"] = faith_result.score
                    # Calculate average coverage from claim results
                    if faith_result.claim_results:
                        avg_coverage = sum(cr.coverage for cr in faith_result.claim_results) / len(
                            faith_result.claim_results
                        )
                        metrics["coverage"] = avg_coverage
                    else:
                        metrics["coverage"] = 1.0
                    reason = f"Verified {faith_result.faithful_claims}/{faith_result.total_claims} claims"
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
                extracted = self._extract_keywords(text)
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
        *,
        top_k: int = 5,
        ndcg_k: int | None = None,
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
        doc_ids = _normalize_document_ids(documents)
        doc_contents = [str(doc.get("content", "")) for doc in documents]
        recall_k, resolved_ndcg_k = _resolve_retrieval_ks(
            data,
            default_recall_k=top_k,
            default_ndcg_k=ndcg_k,
        )

        result = BenchmarkResult(
            task_name=data.get("name", "korean-retrieval-benchmark"),
            task_type=TaskType.RETRIEVAL,
            dataset_version=data.get("version", "1.0.0"),
            domain="insurance",
        )

        # 검색기 초기화
        retriever = self._build_retriever(doc_contents)
        recall_key = f"recall_at_{recall_k}"
        ndcg_key = f"ndcg_at_{resolved_ndcg_k}"

        for tc in test_cases:
            start_time = time.time()

            query = tc.get("query", "")
            if "relevant_doc_ids" in tc:
                relevant_doc_ids = tc.get("relevant_doc_ids", [])
            else:
                relevant_doc_ids = tc.get("relevant_docs", [])
            relevant_doc_ids = [str(doc_id) for doc_id in relevant_doc_ids]

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
                    results = retriever.search(query, top_k=recall_k)
                    retrieved_doc_ids = [
                        resolve_doc_id(getattr(res, "doc_id", None), doc_ids, idx)
                        for idx, res in enumerate(results, start=1)
                    ]
                    metrics.update(
                        compute_retrieval_metrics(
                            retrieved_doc_ids,
                            relevant_doc_ids,
                            recall_k=recall_k,
                            ndcg_k=resolved_ndcg_k,
                        )
                    )
                else:
                    # retriever 없으면 단순 키워드 매칭
                    retrieved_doc_ids = _keyword_search(doc_contents, doc_ids, query, recall_k)
                    metrics.update(
                        compute_retrieval_metrics(
                            retrieved_doc_ids,
                            relevant_doc_ids,
                            recall_k=recall_k,
                            ndcg_k=resolved_ndcg_k,
                        )
                    )

            except Exception as e:
                error = str(e)
                metrics[recall_key] = 0.0
                metrics["mrr"] = 0.0
                metrics[ndcg_key] = 0.0

            duration_ms = (time.time() - start_time) * 1000
            success = metrics.get(recall_key, 0) >= 0.5

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
                    f"recall@{recall_k}={metrics.get(recall_key, 0):.3f}, "
                    f"mrr={metrics.get('mrr', 0):.3f}, "
                    f"ndcg@{resolved_ndcg_k}={metrics.get(ndcg_key, 0):.3f}"
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

        if task_type == "faithfulness":
            optimized_result = self.run_faithfulness_benchmark(test_file)
        elif task_type == "keyword":
            optimized_result = self.run_keyword_extraction_benchmark(test_file)
        else:
            optimized_result = self.run_retrieval_benchmark(test_file)

        # 기준선 모드로 실행
        self.use_korean_tokenizer = False

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
# Retrieval helpers
# =============================================================================


def _normalize_document_ids(documents: list[dict[str, Any]]) -> list[str]:
    doc_ids: list[str] = []
    for idx, doc in enumerate(documents, start=1):
        doc_id = doc.get("doc_id") or doc.get("id") or f"doc_{idx}"
        doc_ids.append(str(doc_id))
    return doc_ids


def _keyword_search(
    documents: list[str],
    doc_ids: list[str],
    query: str,
    top_k: int,
) -> list[str]:
    query_words = set(query.lower().split())
    scores: list[tuple[int, int, str]] = []
    for i, doc in enumerate(documents):
        doc_words = set(doc.lower().split())
        overlap = len(query_words & doc_words)
        scores.append((overlap, i, doc_ids[i]))
    scores.sort(key=lambda item: (-item[0], item[1]))
    return [doc_id for _, _, doc_id in scores[:top_k]]


def _resolve_retrieval_ks(
    data: dict[str, Any],
    *,
    default_recall_k: int,
    default_ndcg_k: int | None,
) -> tuple[int, int]:
    metrics = data.get("evaluation_metrics")
    recall_k = _extract_metric_k(metrics, "recall") or _coerce_int(data.get("top_k"))
    resolved_recall_k = recall_k or default_recall_k
    ndcg_k = _extract_metric_k(metrics, "ndcg") or default_ndcg_k
    resolved_ndcg_k = ndcg_k or resolved_recall_k
    return resolved_recall_k, resolved_ndcg_k


def _extract_metric_k(metrics: Any, prefix: str) -> int | None:
    if not isinstance(metrics, list):
        return None
    for metric in metrics:
        if not isinstance(metric, str):
            continue
        candidate = metric.lower()
        if not candidate.startswith(prefix):
            continue
        if "@" in candidate:
            suffix = candidate.split("@", 1)[1]
        elif "_at_" in candidate:
            suffix = candidate.split("_at_", 1)[1]
        else:
            continue
        try:
            return int(suffix)
        except ValueError:
            continue
    return None


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
