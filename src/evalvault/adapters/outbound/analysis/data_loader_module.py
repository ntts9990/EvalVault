"""Phase 14.4: Data Loader Module.

데이터 로드 모듈입니다.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.domain.entities import EvaluationRun
from evalvault.ports.outbound.storage_port import StoragePort


class DataLoaderModule(BaseAnalysisModule):
    """데이터 로더 모듈.

    분석 컨텍스트에서 데이터를 로드합니다.
    """

    module_id = "data_loader"
    name = "데이터 로더"
    description = "분석 컨텍스트에서 데이터를 로드합니다."
    input_types = ["context"]
    output_types = ["data", "metadata"]
    tags = ["loader", "data"]

    def __init__(self, storage: StoragePort | None = None):
        """옵션으로 StoragePort를 주입합니다."""
        self._storage = storage

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """데이터 로드 실행.

        Args:
            inputs: 입력 데이터 (__context__ 포함)
            params: 실행 파라미터

        Returns:
            로드된 데이터
        """
        context = inputs.get("__context__", {})
        query = context.get("query", "")
        run_id = context.get("run_id")
        additional_params = context.get("additional_params", {}) or {}
        params = params or {}
        allow_sample = params.get("allow_sample")
        if allow_sample is None:
            allow_sample = additional_params.get("allow_sample", True)
        if isinstance(allow_sample, str):
            allow_sample = allow_sample.strip().lower() in {"1", "true", "yes", "y", "on"}

        run = self._load_run(run_id, additional_params)

        result: dict[str, Any] = {
            "loaded": bool(run) or bool(allow_sample),
            "query": query,
        }

        if run_id:
            result["run_id"] = run_id

        if additional_params:
            result["additional_params"] = additional_params

        if run:
            result["run"] = run
            result["metrics"] = self._extract_metrics(run)
            result["summary"] = run.to_summary_dict()
        elif allow_sample:
            result["metrics"] = self._sample_metrics()
            result["sample"] = True
        else:
            result["metrics"] = {}

        return result

    def _load_run(
        self,
        run_id: str | None,
        additional_params: dict[str, Any],
    ) -> EvaluationRun | None:
        """StoragePort에서 EvaluationRun 로드."""
        if additional_params.get("evaluation_run") is not None:
            run = additional_params["evaluation_run"]
            if isinstance(run, EvaluationRun):
                return run

        if not run_id or self._storage is None:
            return None

        try:
            return self._storage.get_run(run_id)
        except KeyError:
            return None

    def _extract_metrics(self, run: EvaluationRun) -> dict[str, list[float]]:
        """EvaluationRun에서 메트릭별 점수 추출."""
        metric_map: dict[str, list[float]] = defaultdict(list)
        for result in run.results:
            for metric in result.metrics:
                metric_map[metric.name].append(metric.score)
        return dict(metric_map)

    def _sample_metrics(self) -> dict[str, list[float]]:
        """샘플 데이터를 반환합니다."""
        return {
            "faithfulness": [0.8, 0.85, 0.75, 0.9],
            "answer_relevancy": [0.78, 0.82, 0.85, 0.88],
            "context_precision": [0.7, 0.75, 0.8, 0.72],
            "context_recall": [0.65, 0.7, 0.68, 0.75],
        }
