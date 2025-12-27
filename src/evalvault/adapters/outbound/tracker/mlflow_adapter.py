"""MLflow tracker adapter implementation."""

import json
import tempfile
from typing import Any

from evalvault.domain.entities import EvaluationRun
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
        import mlflow

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        self._mlflow = mlflow
        self._active_runs: dict[str, Any] = {}  # trace_id -> mlflow run

    def start_trace(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """
        Start a new MLflow run (mapped to trace).

        Args:
            name: Run name
            metadata: Optional metadata to log as parameters

        Returns:
            trace_id: MLflow run ID
        """
        run = self._mlflow.start_run(run_name=name)
        trace_id = run.info.run_id

        # Log metadata as MLflow parameters (only primitive types)
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, str | int | float | bool):
                    self._mlflow.log_param(key, value)

        self._active_runs[trace_id] = run
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
            "input": input_data,
            "output": output_data,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(span_data, f, default=str)
            self._mlflow.log_artifact(f.name, f"spans/{name}")

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
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(data, f, default=str)
                self._mlflow.log_artifact(f.name, f"artifacts/{name}")

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
        # 1. Start MLflow run
        trace_id = self.start_trace(
            name=f"evaluation-{run.run_id[:8]}",
            metadata={
                "dataset_name": run.dataset_name,
                "dataset_version": run.dataset_version,
                "model_name": run.model_name,
                "total_test_cases": run.total_test_cases,
            },
        )

        # 2. Log average metric scores
        for metric_name in run.metrics_evaluated:
            avg_score = run.get_avg_score(metric_name)
            if avg_score is not None:
                self.log_score(trace_id, f"avg_{metric_name}", avg_score)

        # 3. Log overall pass rate
        self.log_score(trace_id, "pass_rate", run.pass_rate)

        # 4. Log resource usage
        self._mlflow.log_metric("total_tokens", run.total_tokens)

        if run.duration_seconds:
            self._mlflow.log_metric("duration_seconds", run.duration_seconds)

        # 5. Save individual test results as artifact
        results_data = []
        for result in run.results:
            result_dict = {
                "test_case_id": result.test_case_id,
                "all_passed": result.all_passed,
                "tokens_used": result.tokens_used,
                "metrics": [
                    {"name": m.name, "score": m.score, "passed": m.passed} for m in result.metrics
                ],
            }
            results_data.append(result_dict)

        self.save_artifact(trace_id, "test_results", results_data)

        # 6. End MLflow run
        self.end_trace(trace_id)

        return trace_id
