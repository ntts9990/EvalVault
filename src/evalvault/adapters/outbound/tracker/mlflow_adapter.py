"""MLflow tracker adapter implementation."""

import json
import tempfile
from typing import Any

from evalvault.adapters.outbound.tracker.log_sanitizer import MAX_LOG_CHARS, sanitize_payload
from evalvault.domain.entities import EvaluationRun, TestCaseResult
from evalvault.ports.outbound.tracker_port import TrackerPort


class MLflowAdapter(TrackerPort):
    """MLflow implementation of TrackerPort.

    MLflow는 ML 실험 추적 플랫폼으로, run/experiment 개념을 사용합니다.
    TrackerPort의 trace는 MLflow run으로 매핑됩니다.
    Span은 MLflow에 네이티브 개념이 아니므로 artifact로 저장합니다.
    """

    def __init__(
        self,
        tracking_uri: str = "http://localhost:5000",
        experiment_name: str = "evalvault",
    ):
        """
        Initialize MLflow adapter.

        Args:
            tracking_uri: MLflow tracking server URI
            experiment_name: MLflow experiment name
        """
        try:
            import torch  # type: ignore
        except Exception:
            torch = None  # type: ignore
        if torch is not None and not hasattr(torch, "Tensor"):

            class _TorchTensor:  # pragma: no cover - guard for namespace package
                pass

            torch.Tensor = _TorchTensor  # type: ignore[attr-defined]

        import mlflow

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        self._mlflow = mlflow
        self._active_runs: dict[str, Any] = {}  # trace_id -> mlflow run

    def _enable_system_metrics(self) -> None:
        try:
            enable_fn = getattr(self._mlflow, "enable_system_metrics_logging", None)
            if callable(enable_fn):
                enable_fn()
        except Exception:  # pragma: no cover - optional dependency
            return

    def _start_mlflow_run(self, name: str) -> Any:
        try:
            return self._mlflow.start_run(run_name=name, log_system_metrics=True)
        except TypeError:
            self._enable_system_metrics()
            return self._mlflow.start_run(run_name=name)

    def start_trace(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """
        Start a new MLflow run (mapped to trace).

        Args:
            name: Run name
            metadata: Optional metadata to log as parameters

        Returns:
            trace_id: MLflow run ID
        """
        run = self._start_mlflow_run(name)
        trace_id = run.info.run_id

        # Log metadata as MLflow parameters (only primitive types)
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, str | int | float | bool):
                    self._mlflow.log_param(key, value)

        self._active_runs[trace_id] = run
        return trace_id

    def _write_temp_file(self, suffix: str, content: str) -> str:
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            f.write(content)
            f.flush()
        return f.name

    def add_span(
        self,
        trace_id: str,
        name: str,
        input_data: Any | None = None,
        output_data: Any | None = None,
    ) -> None:
        """
        Add a span to an existing trace.

        MLflow doesn't have native span support, so we store spans as JSON artifacts.

        Args:
            trace_id: ID of the trace (MLflow run ID)
            name: Name of the span
            input_data: Optional input data for the span
            output_data: Optional output data for the span

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._active_runs:
            raise ValueError(f"Run not found: {trace_id}")

        # Store span data as JSON artifact
        span_data = {
            "name": name,
            "input": sanitize_payload(input_data, max_chars=MAX_LOG_CHARS),
            "output": sanitize_payload(output_data, max_chars=MAX_LOG_CHARS),
        }
        payload = json.dumps(span_data, default=str)
        path = self._write_temp_file(".json", payload)
        self._mlflow.log_artifact(path, f"spans/{name}")

    def log_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        """
        Log a score as MLflow metric.

        Args:
            trace_id: ID of the trace (MLflow run ID)
            name: Metric name
            value: Metric value
            comment: Optional comment (stored as parameter due to MLflow limitations)

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._active_runs:
            raise ValueError(f"Run not found: {trace_id}")

        self._mlflow.log_metric(name, value)

        # Store comment as parameter (MLflow has 250 char limit for params)
        if comment:
            self._mlflow.log_param(f"{name}_comment", comment[:250])

    def save_artifact(
        self,
        trace_id: str,
        name: str,
        data: Any,
        artifact_type: str = "json",
    ) -> None:
        """
        Save an artifact to MLflow.

        Args:
            trace_id: ID of the trace (MLflow run ID)
            name: Artifact name
            data: Artifact data
            artifact_type: Type of artifact (default: "json")

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._active_runs:
            raise ValueError(f"Run not found: {trace_id}")

        if artifact_type == "json":
            payload = json.dumps(data, default=str)
            path = self._write_temp_file(".json", payload)
            self._mlflow.log_artifact(path, f"artifacts/{name}")
        elif artifact_type == "text":
            path = self._write_temp_file(".txt", str(data))
            self._mlflow.log_artifact(path, f"artifacts/{name}")
        else:
            path = self._write_temp_file(".txt", str(data))
            self._mlflow.log_artifact(path, f"artifacts/{name}")

    def end_trace(self, trace_id: str) -> None:
        """
        End a trace and close the MLflow run.

        Args:
            trace_id: ID of the trace to end

        Raises:
            ValueError: If trace_id is not found
        """
        if trace_id not in self._active_runs:
            raise ValueError(f"Run not found: {trace_id}")

        self._mlflow.end_run()
        del self._active_runs[trace_id]

    def log_evaluation_run(self, run: EvaluationRun) -> str:
        """
        Log a complete evaluation run as an MLflow run.

        Maps EvaluationRun to MLflow run with:
        - Run metadata as parameters
        - Metric scores as MLflow metrics
        - Test results as artifacts

        Args:
            run: EvaluationRun entity containing all evaluation results

        Returns:
            trace_id: ID of the created MLflow run
        """

        def _log_run() -> str:
            trace_id = self.start_trace(
                name=f"evaluation-{run.run_id[:8]}",
                metadata={
                    "dataset_name": run.dataset_name,
                    "dataset_version": run.dataset_version,
                    "model_name": run.model_name,
                    "total_test_cases": run.total_test_cases,
                },
            )

            self._mlflow.set_tag("run_id", run.run_id)
            self._mlflow.set_tag("model_name", run.model_name)
            self._mlflow.set_tag("dataset", f"{run.dataset_name}:{run.dataset_version}")
            if run.tracker_metadata:
                project_name = run.tracker_metadata.get("project_name")
                if project_name:
                    self._mlflow.set_tag("project_name", project_name)

            for metric_name in run.metrics_evaluated:
                avg_score = run.get_avg_score(metric_name)
                if avg_score is not None:
                    self.log_score(trace_id, f"avg_{metric_name}", avg_score)

            self.log_score(trace_id, "pass_rate", run.pass_rate)
            self._mlflow.log_metric("total_tokens", run.total_tokens)
            if run.duration_seconds:
                self._mlflow.log_metric("duration_seconds", run.duration_seconds)
            if run.total_cost_usd is not None:
                self._mlflow.log_metric("total_cost_usd", run.total_cost_usd)

            results_data = []
            for result in run.results:
                result_dict = {
                    "test_case_id": result.test_case_id,
                    "all_passed": result.all_passed,
                    "tokens_used": result.tokens_used,
                    "metrics": [
                        {"name": m.name, "score": m.score, "passed": m.passed}
                        for m in result.metrics
                    ],
                }
                results_data.append(result_dict)
                self._trace_test_case(result)

            self.save_artifact(trace_id, "test_results", results_data)
            self.save_artifact(
                trace_id,
                "custom_metric_snapshot",
                (run.tracker_metadata or {}).get("custom_metric_snapshot"),
            )
            if run.tracker_metadata:
                self.save_artifact(trace_id, "tracker_metadata", run.tracker_metadata)
                self._register_prompts(run)

            self.end_trace(trace_id)
            return trace_id

        trace_name = f"evaluation-{run.run_id[:8]}"
        trace_attrs = {
            "dataset_name": run.dataset_name,
            "dataset_version": run.dataset_version,
            "model_name": run.model_name,
        }
        try:
            traced = self._mlflow.trace(
                name=trace_name, span_type="EVALUATION", attributes=trace_attrs
            )
            return traced(_log_run)()
        except Exception:
            return _log_run()

    def _register_prompts(self, run: EvaluationRun) -> None:
        genai = getattr(self._mlflow, "genai", None)
        if genai is None:
            return
        register_fn = getattr(genai, "register_prompt", None)
        if not callable(register_fn):
            return

        prompt_entries = self._extract_prompt_entries(run)
        if not prompt_entries:
            return

        for entry in prompt_entries:
            name = entry.get("name") or entry.get("role") or "prompt"
            content = entry.get("content") or entry.get("content_preview") or ""
            if not content:
                continue
            tags = {
                "kind": str(entry.get("kind") or "custom"),
                "role": str(entry.get("role") or ""),
                "checksum": str(entry.get("checksum") or ""),
                "run_id": run.run_id,
            }
            prompt_set_name = entry.get("prompt_set_name")
            if prompt_set_name:
                tags["prompt_set"] = str(prompt_set_name)
            register_fn(
                name=name,
                template=content,
                commit_message=entry.get("checksum"),
                tags=tags,
                model_config={
                    "model_name": run.model_name,
                },
            )

    def _extract_prompt_entries(self, run: EvaluationRun) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        metadata = run.tracker_metadata or {}
        prompt_set_detail = metadata.get("prompt_set_detail")
        if isinstance(prompt_set_detail, dict):
            prompt_set_name = prompt_set_detail.get("name")
            for item in prompt_set_detail.get("items", []):
                prompt = item.get("prompt") or {}
                if not isinstance(prompt, dict):
                    continue
                entries.append(
                    {
                        "name": prompt.get("name"),
                        "role": item.get("role"),
                        "kind": prompt.get("kind"),
                        "checksum": prompt.get("checksum"),
                        "content": prompt.get("content"),
                        "prompt_set_name": prompt_set_name,
                    }
                )

        phoenix_meta = metadata.get("phoenix") or {}
        if isinstance(phoenix_meta, dict):
            for entry in phoenix_meta.get("prompts", []) or []:
                if not isinstance(entry, dict):
                    continue
                entries.append(entry)
        return entries

    def _trace_test_case(self, result: TestCaseResult) -> None:
        trace_fn = getattr(self._mlflow, "trace", None)
        if not callable(trace_fn):
            return

        attrs = {
            "test_case_id": result.test_case_id,
            "all_passed": result.all_passed,
            "tokens_used": result.tokens_used,
            "latency_ms": result.latency_ms,
        }

        def _emit() -> dict[str, Any]:
            return {
                "metrics": [
                    {"name": m.name, "score": m.score, "passed": m.passed} for m in result.metrics
                ],
                "tokens_used": result.tokens_used,
                "latency_ms": result.latency_ms,
            }

        try:
            wrapped = trace_fn(
                name=f"test_case_{result.test_case_id}",
                span_type="EVALUATION",
                attributes=attrs,
            )
            wrapped(_emit)()
        except Exception:
            return
