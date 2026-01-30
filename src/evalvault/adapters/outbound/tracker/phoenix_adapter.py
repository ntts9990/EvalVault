"""Phoenix tracker adapter implementation using OpenTelemetry."""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Any

from evalvault.adapters.outbound.tracer.open_rag_trace_helpers import serialize_json
from evalvault.adapters.outbound.tracker.log_sanitizer import (
    MAX_CONTEXT_CHARS,
    MAX_LOG_CHARS,
    sanitize_payload,
    sanitize_text,
    sanitize_text_list,
)
from evalvault.domain.entities import (
    EvaluationRun,
    GenerationData,
    RAGTraceData,
    RetrievalData,
    RetrievedDocument,
)
from evalvault.ports.outbound.tracker_port import TrackerPort

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import TracerProvider


class PhoenixAdapter(TrackerPort):
    """Phoenix implementation of TrackerPort using OpenTelemetry.

    Phoenix는 OpenTelemetry 기반 LLM 옵저버빌리티 플랫폼입니다.
    RAG 시스템의 검색 품질 분석, 임베딩 시각화, 레이턴시 분해를 지원합니다.

    Langfuse 대비 장점:
    - 검색 품질 자동 분석 (Precision@K, NDCG)
    - 임베딩 공간 시각화 (UMAP)
    - OpenTelemetry 표준 준수
    - Ragas 네이티브 통합

    Example:
        >>> adapter = PhoenixAdapter(endpoint="http://localhost:6006/v1/traces")
        >>> trace_id = adapter.start_trace("evaluation-run")
        >>> adapter.log_score(trace_id, "faithfulness", 0.85)
        >>> adapter.end_trace(trace_id)
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:6006/v1/traces",
        service_name: str = "evalvault",
        project_name: str | None = None,
        annotations_enabled: bool = True,
    ):
        """Initialize Phoenix adapter with OpenTelemetry.

        Args:
            endpoint: Phoenix OTLP endpoint (default: http://localhost:6006/v1/traces)
            service_name: Service name for traces (default: evalvault)
        """
        self._endpoint = endpoint
        self._service_name = service_name
        self._project_name = project_name
        self._annotations_enabled = annotations_enabled
        self._tracer: Any | None = None
        self._tracer_provider: TracerProvider | None = None
        self._active_spans: dict[str, Any] = {}
        self._tracer_any: Any | None = None
        self._initialized = False
        self._annotations_client: Any | None = None

    def _ensure_initialized(self) -> None:
        """Lazy initialization of OpenTelemetry tracer."""
        if self._initialized:
            return

        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            from evalvault.config.instrumentation import (
                get_tracer_provider,
                is_instrumentation_enabled,
            )

            if is_instrumentation_enabled():
                provider = get_tracer_provider()
                if provider:
                    self._tracer_provider = provider
                    self._tracer_any = trace.get_tracer(__name__)
                    self._tracer = self._tracer_any
                    self._initialized = True
                    return

            # Create resource with service name
            resource_attributes = {"service.name": self._service_name}
            if self._project_name:
                resource_attributes["project.name"] = self._project_name
            resource = Resource.create(resource_attributes)

            # Create tracer provider
            self._tracer_provider = TracerProvider(resource=resource)

            # Add OTLP exporter for Phoenix
            otlp_exporter = OTLPSpanExporter(endpoint=self._endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            self._tracer_provider.add_span_processor(span_processor)

            # Set as global tracer provider
            trace.set_tracer_provider(self._tracer_provider)

            # Get tracer
            self._tracer_any = trace.get_tracer(__name__)
            self._tracer = self._tracer_any
            self._initialized = True

        except ImportError as e:
            raise ImportError(
                "Phoenix dependencies not installed. Install with: uv sync --extra phoenix"
            ) from e
        except Exception as e:  # pragma: no cover - network/setup issues
            raise RuntimeError(
                "Failed to initialize Phoenix tracer. Check endpoint configuration and dependencies."
            ) from e

    def _phoenix_base_url(self) -> str:
        if "/v1/traces" in self._endpoint:
            return self._endpoint.split("/v1/traces")[0]
        return self._endpoint.rstrip("/")

    def _get_annotations_client(self) -> Any | None:
        if not self._annotations_enabled:
            return None
        if self._annotations_client is not None:
            return self._annotations_client
        try:
            from phoenix.client import Client
        except Exception:
            return None
        self._annotations_client = Client(base_url=self._phoenix_base_url())
        return self._annotations_client

    def _annotate_span(
        self,
        *,
        span: Any,
        name: str,
        label: str,
        score: float | None = None,
        explanation: str | None = None,
    ) -> None:
        client = self._get_annotations_client()
        if client is None or span is None:
            return
        try:
            from opentelemetry.trace import format_span_id

            span_id = format_span_id(span.get_span_context().span_id)
            client.annotations.add_span_annotation(
                annotation_name=name,
                annotator_kind="CODE",
                span_id=span_id,
                label=label,
                score=score,
                explanation=explanation,
            )
        except Exception:
            return

    def start_trace(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """Start a new trace.

        Args:
            name: Name of the trace
            metadata: Optional metadata to attach to the trace

        Returns:
            trace_id: Unique identifier for the trace
        """
        self._ensure_initialized()

        # Start a new span as root
        tracer = self._tracer_any
        if tracer is None:
            tracer = self._tracer
        if tracer is None:
            raise RuntimeError("Phoenix tracer is not initialized")
        span = tracer.start_span(name)
        trace_id = str(uuid.uuid4())

        # Set metadata as span attributes
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, str | int | float | bool):
                    span.set_attribute(f"metadata.{key}", value)
                elif isinstance(value, list | dict):
                    span.set_attribute(f"metadata.{key}", json.dumps(value))

        self._active_spans[trace_id] = span
        return trace_id

    def add_span(
        self,
        trace_id: str,
        name: str,
        input_data: Any | None = None,
        output_data: Any | None = None,
    ) -> None:
        """Add a span to an existing trace.

        Args:
            trace_id: ID of the trace to add the span to
            name: Name of the span
            input_data: Optional input data for the span
            output_data: Optional output data for the span

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._active_spans:
            raise ValueError(f"Trace not found: {trace_id}")

        self._ensure_initialized()

        from opentelemetry import trace

        tracer = self._tracer_any
        if tracer is None:
            tracer = self._tracer
        if tracer is None:
            raise RuntimeError("Phoenix tracer is not initialized")
        parent_span = self._active_spans[trace_id]
        context = trace.set_span_in_context(parent_span)

        with tracer.start_span(name, context=context) as span:
            if input_data is not None:
                safe_input = sanitize_payload(input_data, max_chars=MAX_LOG_CHARS)
                span.set_attribute("input", json.dumps(safe_input, default=str))
            if output_data is not None:
                safe_output = sanitize_payload(output_data, max_chars=MAX_LOG_CHARS)
                span.set_attribute("output", json.dumps(safe_output, default=str))

    def log_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        """Log a score to a trace.

        Args:
            trace_id: ID of the trace to log the score to
            name: Name of the score (e.g., metric name)
            value: Score value (typically 0.0 to 1.0)
            comment: Optional comment about the score

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._active_spans:
            raise ValueError(f"Trace not found: {trace_id}")

        span = self._active_spans[trace_id]
        span.set_attribute(f"score.{name}", value)
        if comment:
            span.set_attribute(f"score.{name}.comment", comment)

    def save_artifact(
        self,
        trace_id: str,
        name: str,
        data: Any,
        artifact_type: str = "json",
    ) -> None:
        """Save an artifact to a trace.

        OpenTelemetry doesn't have native artifact support,
        so we store it as a span attribute.

        Args:
            trace_id: ID of the trace to save the artifact to
            name: Name of the artifact
            data: Artifact data
            artifact_type: Type of artifact (json, text, etc.)

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._active_spans:
            raise ValueError(f"Trace not found: {trace_id}")

        span = self._active_spans[trace_id]

        if artifact_type == "json":
            span.set_attribute(f"artifact.{name}", json.dumps(data, default=str))
        else:
            span.set_attribute(f"artifact.{name}", str(data))

    def end_trace(self, trace_id: str) -> None:
        """End a trace and flush data to Phoenix.

        Args:
            trace_id: ID of the trace to end

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._active_spans:
            raise ValueError(f"Trace not found: {trace_id}")

        span = self._active_spans[trace_id]
        span.end()

        # Force flush to ensure data is sent
        if self._tracer_provider:
            self._tracer_provider.force_flush()

        del self._active_spans[trace_id]

    def log_evaluation_run(self, run: EvaluationRun) -> str:
        """Log a complete evaluation run as a trace.

        Args:
            run: EvaluationRun entity containing all evaluation results

        Returns:
            trace_id: ID of the created trace
        """
        self._ensure_initialized()

        # Calculate per-metric summary
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

        # Start root trace
        metadata = {
            "run_id": run.run_id,
            "dataset_name": run.dataset_name,
            "dataset_version": run.dataset_version,
            "model_name": run.model_name,
            "total_test_cases": run.total_test_cases,
            "passed_test_cases": run.passed_test_cases,
            "pass_rate": run.pass_rate,
            "total_tokens": run.total_tokens,
            "event_type": "ragas_evaluation",
        }

        if run.finished_at:
            metadata["duration_seconds"] = run.duration_seconds

        if run.total_cost_usd:
            metadata["total_cost_usd"] = run.total_cost_usd

        trace_name = f"evaluation-run-{run.run_id[:8]}"
        trace_id = self.start_trace(name=trace_name, metadata=metadata)

        # Set evaluation-specific attributes
        span = self._active_spans[trace_id]
        span.set_attribute("openinference.span.kind", "EVALUATOR")
        span.set_attribute("evaluation.metrics", json.dumps(run.metrics_evaluated))
        span.set_attribute("evaluation.thresholds", json.dumps(run.thresholds))
        span.set_attribute("evaluation.status", "pass" if run.pass_rate >= 1.0 else "fail")
        if run.tracker_metadata:
            project_name = run.tracker_metadata.get("project_name")
            if project_name:
                span.set_attribute("project.name", project_name)
            project_kind = run.tracker_metadata.get("evaluation_task") or "evaluation"
            span.set_attribute("project.kind", project_kind)
            span.set_attribute("project.status", "pass" if run.pass_rate >= 1.0 else "fail")

        # Log average scores for each metric
        for metric_name, summary in metric_summary.items():
            self.log_score(
                trace_id=trace_id,
                name=f"avg_{metric_name}",
                value=summary["average_score"],
                comment=f"Pass rate: {summary['pass_rate']:.1%} ({summary['passed']}/{summary['total']})",
            )

        # Log individual test case results as child spans
        for result in run.results:
            self._log_test_case_span(trace_id, result, run)

        # Save structured artifact
        structured_artifact = {
            "type": "ragas_evaluation",
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
            "custom_metrics": (run.tracker_metadata or {}).get("custom_metric_snapshot"),
            "prompt_metadata": (run.tracker_metadata or {}).get("phoenix", {}).get("prompts"),
            "tracker_metadata": run.tracker_metadata,
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

        self.save_artifact(trace_id, "ragas_evaluation", structured_artifact)

        # End the trace
        self.end_trace(trace_id)

        return trace_id

    def _log_test_case_span(
        self,
        trace_id: str,
        result: Any,
        run: EvaluationRun,
    ) -> None:
        """Log a test case result as a child span.

        Args:
            trace_id: Parent trace ID
            result: TestCaseResult entity
            run: Parent EvaluationRun
        """
        from opentelemetry import trace

        tracer = self._tracer_any
        if tracer is None:
            tracer = self._tracer
        if tracer is None:
            raise RuntimeError("Phoenix tracer is not initialized")
        parent_span = self._active_spans[trace_id]
        context = trace.set_span_in_context(parent_span)

        with tracer.start_span(
            f"test-case-{result.test_case_id}",
            context=context,
        ) as span:
            try:
                from opentelemetry.trace import Status, StatusCode

                span.set_status(Status(StatusCode.OK if result.all_passed else StatusCode.ERROR))
            except Exception:
                pass
            span.set_attribute("openinference.span.kind", "EVALUATOR")
            span.set_attribute("evaluation.status", "pass" if result.all_passed else "fail")
            self._annotate_span(
                span=span,
                name="evaluation_result",
                label="pass" if result.all_passed else "fail",
                score=1.0 if result.all_passed else 0.0,
                explanation="All metrics passed"
                if result.all_passed
                else "One or more metrics failed",
            )
            # Input data
            safe_question = sanitize_text(result.question, max_chars=MAX_LOG_CHARS) or ""
            safe_answer = sanitize_text(result.answer, max_chars=MAX_LOG_CHARS) or ""
            span.set_attribute("input.question", safe_question)
            span.set_attribute("input.answer", safe_answer)
            if result.contexts:
                safe_contexts = sanitize_text_list(
                    result.contexts,
                    max_chars=MAX_CONTEXT_CHARS,
                )
                span.set_attribute("input.contexts", json.dumps(safe_contexts))
            if result.ground_truth:
                safe_ground_truth = sanitize_text(result.ground_truth, max_chars=MAX_LOG_CHARS)
                if safe_ground_truth:
                    span.set_attribute("input.ground_truth", safe_ground_truth)

            # Metrics
            span.set_attribute("output.all_passed", result.all_passed)
            span.set_attribute("output.tokens_used", result.tokens_used)
            if result.tokens_used:
                span.set_attribute("llm.token_count.total", result.tokens_used)
            if result.cost_usd is not None:
                span.set_attribute("llm.cost.total", result.cost_usd)

            for metric in result.metrics:
                span.set_attribute(f"metric.{metric.name}.score", metric.score)
                span.set_attribute(f"metric.{metric.name}.threshold", metric.threshold)
                span.set_attribute(f"metric.{metric.name}.passed", metric.passed)

                # Claim-level details for faithfulness metrics
                if metric.claim_details:
                    cd = metric.claim_details
                    span.set_attribute(
                        f"metric.{metric.name}.claim_details",
                        json.dumps(cd.to_dict()),
                    )
                    span.set_attribute(
                        f"metric.{metric.name}.total_claims",
                        cd.total_claims,
                    )
                    span.set_attribute(
                        f"metric.{metric.name}.supported_claims",
                        cd.supported_claims,
                    )
                    span.set_attribute(
                        f"metric.{metric.name}.not_supported_claims",
                        cd.not_supported_claims,
                    )
                    span.set_attribute(
                        f"metric.{metric.name}.support_rate",
                        cd.support_rate,
                    )

            # Timing
            if result.started_at:
                span.set_attribute(
                    "timing.started_at",
                    result.started_at.isoformat()
                    if isinstance(result.started_at, datetime)
                    else str(result.started_at),
                )
            if result.finished_at:
                span.set_attribute(
                    "timing.finished_at",
                    result.finished_at.isoformat()
                    if isinstance(result.finished_at, datetime)
                    else str(result.finished_at),
                )
            if result.latency_ms:
                span.set_attribute("timing.latency_ms", result.latency_ms)
                span.set_attribute("evaluation.latency_ms", result.latency_ms)

    def log_retrieval(
        self,
        trace_id: str,
        data: RetrievalData,
    ) -> None:
        """Log retrieval data as a child span.

        검색 단계의 상세 데이터를 OpenTelemetry span으로 기록합니다.
        Phoenix UI에서 검색 품질 분석이 가능합니다.

        Args:
            trace_id: Parent trace ID
            data: RetrievalData entity with retrieval details

        Raises:
            ValueError: If trace_id is not found

        Example:
            >>> adapter.log_retrieval(trace_id, RetrievalData(
            ...     query="보험 보장금액은?",
            ...     retrieval_method="hybrid",
            ...     top_k=5,
            ...     candidates=[...],
            ... ))
        """
        if trace_id not in self._active_spans:
            raise ValueError(f"Trace not found: {trace_id}")

        self._ensure_initialized()

        from opentelemetry import trace

        parent_span = self._active_spans[trace_id]
        context = trace.set_span_in_context(parent_span)

        tracer = self._tracer_any
        if tracer is None:
            tracer = self._tracer
        if tracer is None:
            raise RuntimeError("Phoenix tracer is not initialized")
        with tracer.start_span("retrieval", context=context) as span:
            try:
                from opentelemetry.trace import Status, StatusCode

                span.set_status(Status(StatusCode.OK))
            except Exception:
                pass
            span.set_attribute("openinference.span.kind", "RETRIEVER")
            # Set retrieval attributes
            for key, value in data.to_span_attributes().items():
                span.set_attribute(key, value)

            # Set query
            if data.query:
                safe_query = sanitize_text(data.query, max_chars=MAX_LOG_CHARS)
                if safe_query:
                    span.set_attribute("retrieval.query", safe_query)
                    span.set_attribute("input.value", safe_query)

            span.set_attribute("spec.version", "0.1")
            span.set_attribute("rag.module", "retrieve")
            if data.retrieval_time_ms:
                span.set_attribute("retrieval.latency_ms", data.retrieval_time_ms)

            documents_payload = _build_retrieval_payload(data.candidates)
            span.set_attribute("custom.retrieval.doc_count", len(documents_payload))
            if documents_payload:
                span.set_attribute("retrieval.documents_json", serialize_json(documents_payload))
                previews = [
                    item.get("content_preview")
                    for item in documents_payload
                    if item.get("content_preview")
                ]
                if previews:
                    span.set_attribute("output.value", previews)
                else:
                    doc_ids = _extract_doc_ids(documents_payload)
                    if doc_ids:
                        span.set_attribute("output.value", doc_ids)

            # Log each retrieved document as an event
            for i, doc in enumerate(data.candidates):
                event_attrs = {
                    "doc.rank": doc.rank,
                    "doc.score": doc.score,
                    "doc.source": doc.source,
                }
                if doc.rerank_score is not None:
                    event_attrs["doc.rerank_score"] = doc.rerank_score
                if doc.rerank_rank is not None:
                    event_attrs["doc.rerank_rank"] = doc.rerank_rank
                if doc.chunk_id:
                    event_attrs["doc.chunk_id"] = doc.chunk_id
                safe_preview = (
                    sanitize_text(doc.content, max_chars=MAX_CONTEXT_CHARS) if doc.content else ""
                )
                if safe_preview:
                    event_attrs["doc.preview"] = safe_preview
                if doc.metadata:
                    safe_metadata = sanitize_payload(doc.metadata, max_chars=MAX_LOG_CHARS)
                    event_attrs["doc.metadata"] = json.dumps(safe_metadata, default=str)
                span.add_event(f"retrieved_doc_{i}", attributes=event_attrs)

    def log_generation(
        self,
        trace_id: str,
        data: GenerationData,
    ) -> None:
        """Log generation data as a child span.

        생성 단계의 상세 데이터를 OpenTelemetry span으로 기록합니다.
        Phoenix UI에서 토큰 사용량, 레이턴시 분석이 가능합니다.

        Args:
            trace_id: Parent trace ID
            data: GenerationData entity with generation details

        Raises:
            ValueError: If trace_id is not found

        Example:
            >>> adapter.log_generation(trace_id, GenerationData(
            ...     model="gpt-5-nano",
            ...     prompt="...",
            ...     response="...",
            ...     input_tokens=150,
            ...     output_tokens=50,
            ... ))
        """
        if trace_id not in self._active_spans:
            raise ValueError(f"Trace not found: {trace_id}")

        self._ensure_initialized()

        from opentelemetry import trace

        parent_span = self._active_spans[trace_id]
        context = trace.set_span_in_context(parent_span)

        tracer = self._tracer_any
        if tracer is None:
            tracer = self._tracer
        if tracer is None:
            raise RuntimeError("Phoenix tracer is not initialized")
        with tracer.start_span("generation", context=context) as span:
            try:
                from opentelemetry.trace import Status, StatusCode

                span.set_status(Status(StatusCode.OK))
            except Exception:
                pass
            span.set_attribute("openinference.span.kind", "LLM")
            # Set generation attributes
            for key, value in data.to_span_attributes().items():
                span.set_attribute(key, value)

            if data.model:
                span.set_attribute("llm.model_name", data.model)
                provider = data.model.split("/")[0] if "/" in data.model else ""
                if provider:
                    span.set_attribute("llm.provider", provider)
            if data.input_tokens:
                span.set_attribute("llm.token_count.prompt", data.input_tokens)
            if data.output_tokens:
                span.set_attribute("llm.token_count.completion", data.output_tokens)
            if data.total_tokens:
                span.set_attribute("llm.token_count.total", data.total_tokens)
            if data.cost_usd is not None:
                span.set_attribute("llm.cost.total", data.cost_usd)

            # Set prompt/response (truncate if too long)
            prompt = sanitize_text(data.prompt, max_chars=MAX_LOG_CHARS) or ""
            response = sanitize_text(data.response, max_chars=MAX_LOG_CHARS) or ""
            if prompt:
                span.set_attribute("generation.prompt", prompt)
                span.set_attribute("input.value", prompt)
            if response:
                span.set_attribute("generation.response", response)
                span.set_attribute("output.value", response)

            span.set_attribute("spec.version", "0.1")
            span.set_attribute("rag.module", "llm")

            # Set prompt template if available
            if data.prompt_template:
                safe_template = sanitize_text(data.prompt_template, max_chars=MAX_LOG_CHARS)
                if safe_template:
                    span.set_attribute("generation.prompt_template", safe_template)
                    span.set_attribute("llm.prompt_template.template", safe_template)
                    span.set_attribute("llm.prompt_template.version", "v1")
            prompt_vars = data.metadata.get("prompt_variables") if data.metadata else None
            if prompt_vars:
                span.set_attribute(
                    "llm.prompt_template.variables", json.dumps(prompt_vars, default=str)
                )

    def log_rag_trace(self, data: RAGTraceData) -> str:
        """Log a full RAG trace (retrieval + generation) to Phoenix."""

        self._ensure_initialized()
        metadata = {"event_type": "rag_trace", "total_time_ms": data.total_time_ms}
        safe_query = sanitize_text(data.query, max_chars=MAX_LOG_CHARS)
        if safe_query:
            metadata["query"] = safe_query
        if data.metadata:
            safe_metadata = sanitize_payload(data.metadata, max_chars=MAX_LOG_CHARS)
            metadata.update(safe_metadata)

        should_end = False
        trace_id = data.trace_id
        if trace_id and trace_id in self._active_spans:
            span = self._active_spans[trace_id]
        else:
            trace_name = f"rag-trace-{(safe_query or 'run')[:12]}"
            trace_id = self.start_trace(trace_name, metadata=metadata)
            span = self._active_spans[trace_id]
            should_end = True

        span.set_attribute("openinference.span.kind", "CHAIN")

        for key, value in data.to_span_attributes().items():
            span.set_attribute(key, value)

        if data.retrieval:
            self.log_retrieval(trace_id, data.retrieval)
        if data.generation:
            self.log_generation(trace_id, data.generation)
        output_preview = ""
        if data.final_answer:
            output_preview = sanitize_text(data.final_answer, max_chars=MAX_LOG_CHARS)
        if not output_preview and data.generation and data.generation.response:
            output_preview = sanitize_text(data.generation.response, max_chars=MAX_LOG_CHARS)
        if not output_preview and data.retrieval:
            previews = [
                sanitize_text(doc.content, max_chars=MAX_CONTEXT_CHARS)
                for doc in data.retrieval.candidates
                if doc.content
            ]
            output_preview = "\n".join(previews[:3])
        if output_preview:
            span.set_attribute("rag.final_answer", output_preview)
            span.set_attribute("output.value", output_preview)

        if safe_query:
            span.set_attribute("input.value", safe_query)

        span.set_attribute("spec.version", "0.1")
        span.set_attribute("rag.module", "custom.pipeline")

        if should_end:
            self.end_trace(trace_id)

        return trace_id

    def shutdown(self) -> None:
        """Shutdown the tracer provider and flush remaining data."""
        if self._tracer_provider:
            self._tracer_provider.shutdown()
            self._initialized = False


def _build_retrieval_payload(
    documents: Sequence[RetrievedDocument],
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for index, doc in enumerate(documents, start=1):
        doc_id = doc.chunk_id or doc.source or doc.metadata.get("doc_id") or f"doc_{index}"
        preview = ""
        if doc.content:
            preview = sanitize_text(doc.content, max_chars=MAX_CONTEXT_CHARS)
        item: dict[str, Any] = {
            "doc_id": doc_id,
            "score": doc.score,
            "content_preview": preview,
        }
        if doc.source:
            item["source"] = doc.source
        if doc.rerank_score is not None:
            item["rerank_score"] = doc.rerank_score
        if doc.rerank_rank is not None:
            item["rerank_rank"] = doc.rerank_rank
        payload.append(item)
    return payload


def _extract_doc_ids(documents: Sequence[dict[str, Any]]) -> list[str]:
    doc_ids: list[str] = []
    for document in documents:
        doc_id = document.get("doc_id")
        if doc_id is not None:
            doc_ids.append(str(doc_id))
    return doc_ids
