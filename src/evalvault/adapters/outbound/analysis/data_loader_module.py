"""Phase 14.4: Data Loader Module.

데이터 로드 모듈입니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule


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
        additional_params = context.get("additional_params", {})

        result = {
            "loaded": True,
            "query": query,
        }

        if run_id:
            result["run_id"] = run_id
            # 실제 구현에서는 run_id로 평가 결과를 로드

        if additional_params:
            result["additional_params"] = additional_params

        # 샘플 메트릭 데이터 (실제 구현에서는 DB에서 로드)
        result["metrics"] = {
            "faithfulness": [0.8, 0.85, 0.75, 0.9],
            "answer_relevancy": [0.78, 0.82, 0.85, 0.88],
            "context_precision": [0.7, 0.75, 0.8, 0.72],
            "context_recall": [0.65, 0.7, 0.68, 0.75],
        }

        return result
