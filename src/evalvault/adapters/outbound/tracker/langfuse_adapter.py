"""Langfuse tracker adapter implementation."""

from typing import Any

from langfuse import Langfuse

from evalvault.adapters.outbound.tracker.log_sanitizer import (
    MAX_CONTEXT_CHARS,
    MAX_LOG_CHARS,
    sanitize_payload,
    sanitize_text,
    sanitize_text_list,
)
from evalvault.config.phoenix_support import extract_phoenix_links
from evalvault.domain.entities import EvaluationRun
from evalvault.ports.outbound.tracker_port import TrackerPort


class LangfuseAdapter(TrackerPort):
    """Langfuse implementation of TrackerPort."""

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: str = "https://cloud.langfuse.com",
    ):
        """
        Initialize Langfuse adapter.

        Args:
            public_key: Langfuse public key
            secret_key: Langfuse secret key
            host: Langfuse host URL (default: https://cloud.langfuse.com)
        """
        self._client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        self._host = host
        self._traces: dict[str, Any] = {}  # trace_id -> root span

    def start_trace(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """
        Start a new trace.

        Args:
            name: Name of the trace
            metadata: Optional metadata to attach to the trace

        Returns:
            trace_id: Unique identifier for the trace
        """
        # Support both old (trace) and new (start_span) Langfuse API
        if hasattr(self._client, "start_span"):
            # Langfuse 3.x: start_span creates a root span with trace
            # Set span name to match trace name for visibility
            span = self._client.start_span(name=name)
            trace_id = span.trace_id
            # Update trace-level name and metadata
            if metadata is not None:
                span.update_trace(name=name, metadata=metadata)
            self._traces[trace_id] = span
        else:
            trace_fn: Any = getattr(self._client, "trace", None)
            if trace_fn is None:
                raise RuntimeError("Langfuse client does not expose trace API")
            trace_obj = trace_fn(
                name=name,
                metadata=metadata,
            )
            trace_id = trace_obj.id
            self._traces[trace_id] = trace_obj
        return trace_id

    def add_span(
        self,
        trace_id: str,
        name: str,
        input_data: Any | None = None,
        output_data: Any | None = None,
    ) -> None:
        """
        Add a span to an existing trace.

        Args:
            trace_id: ID of the trace to add the span to
            name: Name of the span
            input_data: Optional input data for the span
            output_data: Optional output data for the span

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._traces:
            raise ValueError(f"Trace not found: {trace_id}")

        trace_or_span = self._traces[trace_id]
        safe_input = (
            sanitize_payload(input_data, max_chars=MAX_LOG_CHARS)
            if input_data is not None
            else None
        )
        safe_output = (
            sanitize_payload(output_data, max_chars=MAX_LOG_CHARS)
            if output_data is not None
            else None
        )
        # Support both old and new Langfuse API
        if hasattr(trace_or_span, "start_span"):
            # Langfuse 3.x: create nested span
            child_span = trace_or_span.start_span(
                name=name,
                input=safe_input,
                output=safe_output,
            )
            child_span.end()
        else:
            # Langfuse 2.x: use span method on trace
            trace_or_span.span(
                name=name,
                input=safe_input,
                output=safe_output,
            )

    def log_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        """
        Log a score to a trace.

        Args:
            trace_id: ID of the trace to log the score to
            name: Name of the score (e.g., metric name)
            value: Score value (typically 0.0 to 1.0)
            comment: Optional comment about the score

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._traces:
            raise ValueError(f"Trace not found: {trace_id}")

        trace_or_span = self._traces[trace_id]
        # Support both old and new Langfuse API
        if hasattr(trace_or_span, "score_trace"):
            # Langfuse 3.x: use score_trace on span
            trace_or_span.score_trace(
                name=name,
                value=value,
                comment=comment,
            )
        else:
            # Langfuse 2.x: use score method on trace
            trace_or_span.score(
                name=name,
                value=value,
                comment=comment,
            )

    def save_artifact(
        self,
        trace_id: str,
        name: str,
        data: Any,
        artifact_type: str = "json",
    ) -> None:
        """
        Save an artifact to a trace.

        Langfuse doesn't have native artifact support, so we store it in metadata.

        Args:
            trace_id: ID of the trace to save the artifact to
            name: Name of the artifact
            data: Artifact data
            artifact_type: Type of artifact (json, text, etc.)

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._traces:
            raise ValueError(f"Trace not found: {trace_id}")

        trace_or_span = self._traces[trace_id]
        artifact_metadata = {
            f"artifact_{name}": data,
            f"artifact_{name}_type": artifact_type,
        }
        # Support both old and new Langfuse API
        if hasattr(trace_or_span, "update_trace"):
            # Langfuse 3.x: update_trace on span
            trace_or_span.update_trace(metadata=artifact_metadata)
        else:
            # Langfuse 2.x: update on trace
            trace_or_span.update(metadata=artifact_metadata)

    def end_trace(self, trace_id: str) -> None:
        """
        End a trace and flush any pending data.

        Args:
            trace_id: ID of the trace to end

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._traces:
            raise ValueError(f"Trace not found: {trace_id}")

        trace_or_span = self._traces[trace_id]
        # Support both old and new Langfuse API
        if hasattr(trace_or_span, "end"):
            # Langfuse 3.x: end the span
            trace_or_span.end()
        # Langfuse 2.x trace objects don't need explicit end

        # Flush all pending data to Langfuse
        self._client.flush()

        # Remove trace from active traces
        del self._traces[trace_id]

    def log_evaluation_run(self, run: EvaluationRun) -> str:
        """
        Log a complete evaluation run as a trace.

        Args:
            run: EvaluationRun entity containing all evaluation results

        Returns:
            trace_id: ID of the created trace
        """
        # Calculate per-metric pass rates and average scores
        metric_summary = {}
        for metric_name in run.metrics_evaluated:
            passed_count = sum(
                1
                for r in run.results
                if (metric := r.get_metric(metric_name)) and metric.passed is True
            )
            avg_score = run.get_avg_score(metric_name)
            threshold = run.thresholds.get(metric_name, 0.7)
            metric_summary[metric_name] = {
                "average_score": round(avg_score, 4) if avg_score else 0.0,
                "threshold": threshold,
                "passed": passed_count,
                "failed": len(run.results) - passed_count,
                "total": len(run.results),
                "pass_rate": round(passed_count / len(run.results), 4) if run.results else 0.0,
            }

        # Trace input: evaluation configuration
        trace_input = {
            "dataset": {
                "name": run.dataset_name,
                "version": run.dataset_version,
                "total_test_cases": run.total_test_cases,
            },
            "evaluation_config": {
                "model": run.model_name,
                "metrics": run.metrics_evaluated,
                "thresholds": run.thresholds,
            },
        }

        # Trace output: evaluation results summary
        trace_output = {
            "summary": {
                "total_test_cases": run.total_test_cases,
                "passed": run.passed_test_cases,
                "failed": run.total_test_cases - run.passed_test_cases,
                "pass_rate": round(run.pass_rate, 4),
                "duration_seconds": round(run.duration_seconds, 2)
                if run.duration_seconds
                else None,
                "total_tokens": run.total_tokens,
            },
            "metrics": metric_summary,
        }

        metadata = {
            "run_id": run.run_id,
            "dataset_name": run.dataset_name,
            "dataset_version": run.dataset_version,
            "model_name": run.model_name,
            "started_at": run.started_at.isoformat(),
            "total_test_cases": run.total_test_cases,
            "passed_test_cases": run.passed_test_cases,
            "pass_rate": run.metric_pass_rate,
            "total_tokens": run.total_tokens,
            "metrics_evaluated": run.metrics_evaluated,
            "thresholds": run.thresholds,
            "metric_pass_rates": metric_summary,
            "event_type": "ragas_evaluation",
        }

        phoenix_links = extract_phoenix_links(getattr(run, "tracker_metadata", None))
        if phoenix_links:
            metadata["phoenix_links"] = phoenix_links
            trace_output["phoenix_links"] = phoenix_links

        if run.finished_at:
            metadata["finished_at"] = run.finished_at.isoformat()
            metadata["duration_seconds"] = run.duration_seconds

        if run.total_cost_usd:
            metadata["total_cost_usd"] = run.total_cost_usd
            trace_output["summary"]["total_cost_usd"] = run.total_cost_usd

        tags = [
            f"dataset:{run.dataset_name}",
            f"model:{run.model_name}",
            "passed" if run.metric_pass_rate >= 1.0 else "failed",
        ]
        # Add metric tags
        for metric_name in run.metrics_evaluated:
            tags.append(f"metric:{metric_name}")

        trace_name = f"evaluation-run-{run.run_id}"
        trace_id = self.start_trace(name=trace_name)
        root_span = self._traces[trace_id]
        self._record_trace_metadata(run, trace_id)

        if hasattr(root_span, "update_trace"):
            root_span.update_trace(
                name=trace_name,
                input=trace_input,
                output=trace_output,
                metadata=metadata,
                tags=tags,
            )
            root_span.update(
                start_time=run.started_at,
                end_time=run.finished_at,
            )
        else:
            root_span.update(
                name=trace_name,
                input=trace_input,
                output=trace_output,
                metadata=metadata,
                tags=tags,
            )
            if hasattr(root_span, "update"):
                root_span.update(
                    start_time=run.started_at,
                    end_time=run.finished_at,
                )

        structured_artifact = {
            "type": "ragas_evaluation",
            "dataset": trace_input["dataset"],
            "evaluation_config": trace_input["evaluation_config"],
            "summary": trace_output["summary"],
            "metrics": metric_summary,
            "phoenix_links": phoenix_links or {},
            "custom_metrics": (run.tracker_metadata or {}).get("custom_metric_snapshot"),
            "test_cases": [
                {
                    "test_case_id": result.test_case_id,
                    "all_passed": result.all_passed,
                    "metrics": {
                        metric.name: {
                            "score": metric.score,
                            "threshold": metric.threshold,
                            "passed": metric.passed,
                        }
                        for metric in result.metrics
                    },
                }
                for result in run.results
            ],
        }
        self.save_artifact(
            trace_id=trace_id,
            name="ragas_evaluation",
            data=structured_artifact,
        )

        # Log average scores for each metric
        for metric_name, summary in metric_summary.items():
            self.log_score(
                trace_id=trace_id,
                name=f"avg_{metric_name}",
                value=summary["average_score"],
                comment=f"Average {metric_name}: {summary['average_score']:.3f} | Pass rate: {summary['pass_rate']:.1%} ({summary['passed']}/{summary['total']}) | Threshold: {summary['threshold']}",
            )

        # Log individual test case results as spans
        for result in run.results:
            # Span input: test case data (question, answer, contexts, ground_truth)
            span_input = {
                "test_case_id": result.test_case_id,
                "question": sanitize_text(result.question, max_chars=MAX_LOG_CHARS),
                "answer": sanitize_text(result.answer, max_chars=MAX_LOG_CHARS),
                "contexts": sanitize_text_list(
                    result.contexts,
                    max_chars=MAX_CONTEXT_CHARS,
                ),
                "ground_truth": sanitize_text(result.ground_truth, max_chars=MAX_LOG_CHARS),
            }

            # Span output: evaluation results
            metric_results = {}
            for m in result.metrics:
                status = "PASS" if m.passed else "FAIL"
                metric_results[m.name] = {
                    "score": round(m.score, 4),
                    "threshold": m.threshold,
                    "passed": m.passed,
                    "status": status,
                }

            span_output = {
                "test_case_id": result.test_case_id,
                "all_passed": result.all_passed,
                "metrics": metric_results,
            }

            # Span metadata: additional info
            span_metadata: dict[str, float | int] = {
                "tokens_used": result.tokens_used,
                "latency_ms": result.latency_ms,
            }
            if result.cost_usd:
                span_metadata = {
                    **span_metadata,
                    "cost_usd": float(result.cost_usd),
                }

            if hasattr(root_span, "start_span"):
                child_span = root_span.start_span(
                    name=f"test-case-{result.test_case_id}",
                    input=span_input,
                    output=span_output,
                    metadata=span_metadata,
                )
                child_span.update(
                    start_time=result.started_at,
                    end_time=result.finished_at,
                )
                child_span.end()
            else:
                root_span.span(
                    name=f"test-case-{result.test_case_id}",
                    input=span_input,
                    output=span_output,
                    metadata=span_metadata,
                )

            # Log individual metric scores
            for metric in result.metrics:
                status = "PASS" if metric.passed else "FAIL"
                self.log_score(
                    trace_id=trace_id,
                    name=f"{result.test_case_id}_{metric.name}",
                    value=metric.score,
                    comment=f"[{status}] {metric.name}: {metric.score:.3f} (threshold: {metric.threshold})",
                )

        # Add a generation span for cost tracking if we have usage data
        if run.total_tokens > 0:
            # Calculate total prompt and completion tokens
            total_prompt_tokens = sum(
                r.tokens_used // 2
                for r in run.results  # Approximate if not tracked
            )
            total_completion_tokens = run.total_tokens - total_prompt_tokens

            # Create generation span for cost tracking (Langfuse v3 API)
            # Note: use start_observation with as_type='generation' (SDK 3.x)
            if hasattr(root_span, "start_observation"):
                generation_span = root_span.start_observation(
                    name="ragas-evaluation",
                    as_type="generation",
                    model=run.model_name,
                    input={
                        "metrics": run.metrics_evaluated,
                        "total_test_cases": run.total_test_cases,
                    },
                    output={"total_tokens": run.total_tokens},
                    usage_details={
                        "input": total_prompt_tokens,
                        "output": total_completion_tokens,
                        "total": run.total_tokens,
                    },
                    metadata={
                        "evaluation_type": "ragas",
                        "metrics": run.metrics_evaluated,
                        "total_test_cases": run.total_test_cases,
                    },
                )
                generation_span.update(
                    start_time=run.started_at,
                    end_time=run.finished_at,
                )
                generation_span.end()

        # End the root span
        if hasattr(root_span, "end"):
            root_span.end()

        # Flush data to Langfuse
        self._client.flush()

        # Remove from active traces
        if trace_id in self._traces:
            del self._traces[trace_id]

        return trace_id

    def _record_trace_metadata(self, run: EvaluationRun, trace_id: str) -> None:
        tracker_metadata = run.tracker_metadata or {}
        langfuse_meta = tracker_metadata.setdefault("langfuse", {})
        langfuse_meta["trace_id"] = trace_id
        langfuse_meta["host"] = self._host

        trace_url = None
        try:
            trace_url = self._client.get_trace_url(trace_id=trace_id)
        except Exception:
            trace_url = None
        if trace_url:
            langfuse_meta["trace_url"] = trace_url

        run.tracker_metadata = tracker_metadata
        run.langfuse_trace_id = trace_id
