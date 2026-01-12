"""Retrieval benchmark module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.nlp.korean import KoreanNLPToolkit
from evalvault.config.settings import Settings
from evalvault.domain.services.benchmark_runner import KoreanRAGBenchmarkRunner


class RetrievalBenchmarkModule(BaseAnalysisModule):
    """Run retrieval benchmark on external document datasets."""

    module_id = "retrieval_benchmark"
    name = "Retrieval Benchmark"
    description = "Run retrieval benchmark using external documents and queries."
    input_types = ["context"]
    output_types = ["benchmark_summary", "report"]
    tags = ["benchmark", "retrieval"]

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        context = inputs.get("__context__", {})
        additional = context.get("additional_params", {}) or {}

        benchmark_path = self._resolve_path(params, additional)
        if not benchmark_path:
            return {
                "available": False,
                "error": "benchmark_path가 필요합니다.",
            }

        path = Path(benchmark_path)
        if not path.exists():
            return {
                "available": False,
                "error": f"벤치마크 파일을 찾을 수 없습니다: {path}",
            }

        top_k = self._resolve_int(params, additional, "top_k", default=5)
        ndcg_k = self._resolve_optional_int(params, additional, "ndcg_k")
        use_hybrid = self._resolve_bool(params, additional, "use_hybrid_search")
        embedding_profile = self._resolve_str(params, additional, "embedding_profile")
        verbose = self._resolve_bool(params, additional, "verbose")

        errors: list[str] = []
        nlp_toolkit = None
        try:
            nlp_toolkit = KoreanNLPToolkit()
        except Exception as exc:
            errors.append(str(exc))
            nlp_toolkit = None

        ollama_adapter = None
        if embedding_profile in {"dev", "prod"}:
            try:
                from evalvault.adapters.outbound.llm.ollama_adapter import OllamaAdapter

                settings = Settings()
                ollama_adapter = OllamaAdapter(settings)
            except Exception as exc:
                errors.append(str(exc))
                ollama_adapter = None

        runner = KoreanRAGBenchmarkRunner(
            use_korean_tokenizer=True,
            verbose=verbose,
            use_hybrid_search=use_hybrid,
            ollama_adapter=ollama_adapter,
            embedding_profile=embedding_profile or None,
            nlp_toolkit=nlp_toolkit,
        )

        try:
            result = runner.run_retrieval_benchmark(
                path,
                top_k=top_k,
                ndcg_k=ndcg_k,
            )
        except Exception as exc:
            return {
                "available": False,
                "error": f"벤치마크 실행 실패: {exc}",
                "errors": errors,
            }

        metrics_summary, metrics_avg = self._extract_metrics(result)
        summary = {
            "task_name": result.task_name,
            "task_type": result.task_type.value,
            "benchmark_path": str(path),
            "total_tests": result.total_tests,
            "passed_tests": result.passed_tests,
            "failed_tests": result.failed_tests,
            "pass_rate": round(result.pass_rate, 4),
            "evaluation_time": round(result.evaluation_time or 0.0, 2),
            "metrics": metrics_avg,
            "top_k": top_k,
            "ndcg_k": ndcg_k or top_k,
            "use_hybrid_search": use_hybrid,
            "embedding_profile": embedding_profile,
        }

        samples = self._build_failure_samples(result.test_results)
        report = self._build_report(summary, metrics_summary, samples)
        insights = self._build_insights(metrics_avg)

        output = {
            "available": True,
            "summary": summary,
            "metrics_summary": metrics_summary,
            "samples": samples,
            "report": report,
            "insights": insights,
        }
        if errors:
            output["errors"] = errors
        return output

    def _resolve_path(
        self,
        params: dict[str, Any],
        additional: dict[str, Any],
    ) -> str | None:
        return (
            params.get("benchmark_path")
            or params.get("retrieval_benchmark_path")
            or params.get("test_file")
            or additional.get("benchmark_path")
            or additional.get("retrieval_benchmark_path")
            or additional.get("test_file")
        )

    def _resolve_bool(
        self,
        params: dict[str, Any],
        additional: dict[str, Any],
        key: str,
    ) -> bool:
        value = params.get(key)
        if value is None:
            value = additional.get(key)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return bool(value)

    def _resolve_int(
        self,
        params: dict[str, Any],
        additional: dict[str, Any],
        key: str,
        *,
        default: int,
    ) -> int:
        value = params.get(key)
        if value is None:
            value = additional.get(key, default)
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return default

    def _resolve_optional_int(
        self,
        params: dict[str, Any],
        additional: dict[str, Any],
        key: str,
    ) -> int | None:
        value = params.get(key)
        if value is None:
            value = additional.get(key)
        if value is None:
            return None
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return None

    def _resolve_str(
        self,
        params: dict[str, Any],
        additional: dict[str, Any],
        key: str,
    ) -> str | None:
        value = params.get(key)
        if value is None:
            value = additional.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    def _extract_metrics(
        self,
        result: Any,
    ) -> tuple[dict[str, Any], dict[str, float]]:
        deepeval = result.to_deepeval_dict()
        metrics_summary = deepeval.get("metrics_summary", {}) or {}
        metrics_avg: dict[str, float] = {}
        for metric, payload in metrics_summary.items():
            average = payload.get("average")
            if isinstance(average, int | float):
                metrics_avg[metric] = round(float(average), 4)
        return metrics_summary, metrics_avg

    def _build_failure_samples(self, results: list[Any]) -> list[dict[str, Any]]:
        samples: list[dict[str, Any]] = []
        for item in results:
            if not getattr(item, "success", False):
                samples.append(
                    {
                        "test_id": item.test_case.test_id,
                        "query": item.test_case.input,
                        "metrics": item.metrics,
                        "threshold": item.threshold,
                        "error": item.error,
                    }
                )
            if len(samples) >= 5:
                break
        return samples

    def _build_report(
        self,
        summary: dict[str, Any],
        metrics_summary: dict[str, Any],
        samples: list[dict[str, Any]],
    ) -> str:
        lines = [
            "# 검색 벤치마크 보고서",
            "",
            f"- 데이터: {summary.get('benchmark_path')}",
            f"- 방식: {'하이브리드' if summary.get('use_hybrid_search') else 'BM25'}",
            f"- top_k: {summary.get('top_k')} / ndcg_k: {summary.get('ndcg_k')}",
            f"- 테스트: {summary.get('total_tests')}개",
            f"- 통과율: {summary.get('pass_rate', 0):.1%}",
            "",
            "## 주요 메트릭",
            "",
        ]

        if metrics_summary:
            for metric, payload in metrics_summary.items():
                avg = payload.get("average", 0.0)
                lines.append(f"- {metric}: {float(avg):.4f}")
        else:
            lines.append("- 메트릭 요약이 없습니다.")

        if samples:
            lines.extend(["", "## 실패 샘플", ""])
            for item in samples:
                lines.append(
                    f"- {item.get('test_id')}: {item.get('query', '')} "
                    f"(metrics: {item.get('metrics')})"
                )

        return "\n".join(lines)

    def _build_insights(self, metrics_avg: dict[str, float]) -> list[str]:
        insights: list[str] = []
        for key, value in metrics_avg.items():
            if "recall" in key and value < 0.5:
                insights.append("Recall 점수가 낮습니다. 검색 범위/쿼리 확장을 점검하세요.")
            if "precision" in key and value < 0.5:
                insights.append("Precision 점수가 낮습니다. 컨텍스트 노이즈를 줄이세요.")
        return insights
