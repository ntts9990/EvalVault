#!/usr/bin/env python3
"""한국어 RAG 벤치마크 실행 스크립트.

EvalVault의 한국어 RAG 최적화 효과를 측정합니다:
- Faithfulness: 조사/어미 변형 무시 효과 (+25%p 예상)
- Keyword Extraction: 형태소 분석 vs 공백 기반 (+20-50%p 예상)
- Retrieval: 하이브리드 검색 효과 (+15-20% 예상)

Usage:
    # 전체 벤치마크 실행
    python run_korean_benchmark.py

    # 개별 벤치마크 실행
    python run_korean_benchmark.py --task faithfulness
    python run_korean_benchmark.py --task keyword
    python run_korean_benchmark.py --task retrieval

    # 기준선 비교
    python run_korean_benchmark.py --compare

    # 상세 출력
    python run_korean_benchmark.py --verbose

Output:
    - results_mteb.json: MTEB 호환 결과
    - leaderboard.json: 리더보드 형식 결과
    - comparison.json: 형태소 분석 vs 기준선 비교

References:
    - MTEB: https://github.com/embeddings-benchmark/mteb
    - DeepEval: https://github.com/confident-ai/deepeval
    - lm-evaluation-harness: https://github.com/EleutherAI/lm-evaluation-harness
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def main() -> int:
    """메인 함수."""
    parser = argparse.ArgumentParser(
        description="한국어 RAG 벤치마크 실행",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--task",
        choices=["all", "faithfulness", "keyword", "retrieval"],
        default="all",
        help="실행할 벤치마크 태스크 (default: all)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="형태소 분석 vs 기준선 비교 실행",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="상세 출력",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path(__file__).parent / "output",
        help="결과 출력 디렉토리",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="통과 기준 점수 (default: 0.7)",
    )
    parser.add_argument(
        "--hybrid",
        action="store_true",
        help="하이브리드 검색 사용 (BM25 + Dense Embedding)",
    )
    parser.add_argument(
        "--embedding-profile",
        choices=["dev", "prod"],
        default=None,
        help="Qwen3-Embedding 프로파일 (dev: 0.6b/256d, prod: 8b/1024d)",
    )

    args = parser.parse_args()

    # 벤치마크 데이터 디렉토리
    benchmark_dir = Path(__file__).parent / "korean_rag"

    if not benchmark_dir.exists():
        print(f"Error: Benchmark directory not found: {benchmark_dir}")
        return 1

    try:
        from evalvault.domain.services.benchmark_runner import (
            KoreanRAGBenchmarkRunner,
        )
    except ImportError as e:
        print(f"Error: Failed to import benchmark runner: {e}")
        print("Please ensure you're running from the project root with:")
        print("  uv run python examples/benchmarks/run_korean_benchmark.py")
        return 1

    # Ollama 어댑터 초기화 (Qwen3-Embedding 사용 시)
    ollama_adapter = None
    if args.hybrid and args.embedding_profile:
        try:
            from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter
            from evalvault.config.settings import Settings

            settings = Settings()
            ollama_adapter = OllamaAdapter(settings)
            print(f"  Ollama adapter initialized: {settings.ollama_base_url}")
        except Exception as e:
            print(f"  Warning: Failed to initialize Ollama adapter: {e}")
            print("  Falling back to HuggingFace embedding model")

    toolkit = None
    try:
        from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit

        toolkit = KoreanNLPToolkit()
    except ImportError:
        print("Warning: Korean NLP extras not installed. Benchmarks will run in baseline mode.")

    # 벤치마크 러너 초기화
    runner = KoreanRAGBenchmarkRunner(
        use_korean_tokenizer=True,
        threshold=args.threshold,
        verbose=args.verbose,
        use_hybrid_search=args.hybrid,
        ollama_adapter=ollama_adapter,
        embedding_profile=args.embedding_profile,
        nlp_toolkit=toolkit,
    )

    # 출력 디렉토리 생성
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 70)
    print("  EvalVault Korean RAG Benchmark")
    print("=" * 70)
    print(f"  Benchmark Dir: {benchmark_dir}")
    print(f"  Output Dir: {args.output_dir}")
    print(f"  Threshold: {args.threshold}")
    print(f"  Task: {args.task}")
    if args.hybrid:
        profile_info = f" ({args.embedding_profile})" if args.embedding_profile else ""
        print(f"  Hybrid Search: Enabled{profile_info}")
    print("=" * 70)

    # 벤치마크 실행
    if args.task == "all":
        suite = runner.run_full_suite(
            benchmark_dir=benchmark_dir,
            output_dir=args.output_dir,
        )

        # 전체 결과 저장
        full_result_file = args.output_dir / "full_results.json"
        with open(full_result_file, "w", encoding="utf-8") as f:
            json.dump(suite.to_dict(), f, indent=2, ensure_ascii=False, default=str)

    else:
        # 개별 태스크 실행
        if args.task == "faithfulness":
            result = runner.run_faithfulness_benchmark(benchmark_dir / "faithfulness_test.json")
        elif args.task == "keyword":
            result = runner.run_keyword_extraction_benchmark(
                benchmark_dir / "keyword_extraction_test.json"
            )
        else:  # retrieval
            result = runner.run_retrieval_benchmark(benchmark_dir / "retrieval_test.json")

        # 결과 출력
        print()
        print(f"Task: {result.task_name}")
        print(f"  Main Score: {result.main_score:.4f}")
        print(f"  Pass Rate: {result.pass_rate:.1%}")
        print(f"  Total Tests: {result.total_tests}")
        print(f"  Passed: {result.passed_tests}")
        print(f"  Failed: {result.failed_tests}")
        print(f"  Evaluation Time: {result.evaluation_time:.2f}s")

        # 결과 저장
        result_file = args.output_dir / f"{args.task}_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        print(f"\n  Saved to: {result_file}")

    # 기준선 비교
    if args.compare:
        print()
        print("=" * 70)
        print("  Baseline Comparison (Morpheme Analysis vs Whitespace)")
        print("=" * 70)

        comparisons = []

        for task_type, task_file in [
            ("faithfulness", "faithfulness_test.json"),
            ("keyword", "keyword_extraction_test.json"),
            ("retrieval", "retrieval_test.json"),
        ]:
            test_file = benchmark_dir / task_file
            if test_file.exists():
                print(f"\n  [{task_type.upper()}]")
                task_comparisons = runner.compare_with_baseline(test_file, task_type)

                for comp in task_comparisons:
                    sign = "+" if comp.improvement >= 0 else ""
                    sig = "✓" if comp.is_significant else " "
                    print(
                        f"    {sig} {comp.metric_name}: "
                        f"{comp.baseline_score:.3f} → {comp.optimized_score:.3f} "
                        f"({sign}{comp.improvement:.3f}, {sign}{comp.improvement_percent:.1f}%)"
                    )

                comparisons.extend({"task": task_type, **c.to_dict()} for c in task_comparisons)

        # 비교 결과 저장
        comparison_file = args.output_dir / "comparison.json"
        with open(comparison_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "generated_at": datetime.now().isoformat(),
                    "comparisons": comparisons,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\n  Comparison saved to: {comparison_file}")

    print()
    print("=" * 70)
    print("  Benchmark Complete!")
    print("=" * 70)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
