"""Diagnostic playbook module."""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output
from evalvault.domain.entities import EvaluationRun


class DiagnosticPlaybookModule(BaseAnalysisModule):
    """Generate diagnostics and recommendations from RAGAS summaries."""

    module_id = "diagnostic_playbook"
    name = "Diagnostic Playbook"
    description = "Generate issue hypotheses and remediation hints."
    input_types = ["ragas_summary"]
    output_types = ["diagnostics"]
    requires = ["ragas_evaluator"]
    tags = ["analysis", "diagnostic"]

    METRIC_REMEDIATION_HINTS: dict[str, str] = {
        "faithfulness": ("답변을 검색 컨텍스트에 더 강하게 고정하고 근거 인용을 강화하세요."),
        "summary_faithfulness": ("요약 근거가 원문과 일치하도록 근거 체크리스트를 추가하세요."),
        "factual_correctness": ("원천 데이터 검증 및 사후 팩트체크 단계를 추가하세요."),
        "answer_relevancy": "질문 의도 파악과 프롬프트 정렬을 점검하세요.",
        "context_recall": ("top_k 확대, 쿼리 확장, 청크 전략 조정으로 recall을 높이세요."),
        "context_precision": ("리랭킹/노이즈 필터링으로 불필요한 컨텍스트를 줄이세요."),
        "semantic_similarity": "레퍼런스 표현과 답변 서술 스타일을 정렬하세요.",
        "summary_score": "요약 핵심 정보 보존과 간결성 균형을 점검하세요.",
        "entity_preservation": "보험 핵심 엔티티(금액/기간/조건) 누락 여부를 점검하세요.",
    }

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        params = params or {}
        ragas_output = get_upstream_output(inputs, "ragas_eval", "ragas_evaluator") or {}
        metrics = ragas_output.get("metrics", {}) or {}

        default_threshold = float(params.get("metric_threshold", 0.6))
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run") if isinstance(loader_output, dict) else None

        diagnostics = []
        recommendations = []
        for metric, score in metrics.items():
            threshold = self._resolve_threshold(metric, run, default_threshold)
            if score >= threshold:
                continue
            issue = f"{metric} 점수가 기준치 미달입니다 ({score:.2f} < {threshold:.2f})."
            recommendation = self.METRIC_REMEDIATION_HINTS.get(
                metric, f"{metric} 관련 데이터/프롬프트를 재점검하세요."
            )
            diagnostics.append(
                {
                    "metric": metric,
                    "issue": issue,
                    "score": round(float(score), 4),
                    "threshold": round(float(threshold), 4),
                    "gap": round(float(threshold - score), 4),
                }
            )
            recommendations.append(recommendation)

        recommendations = list(dict.fromkeys(recommendations))

        return {
            "threshold": default_threshold,
            "diagnostics": diagnostics,
            "recommendations": recommendations,
        }

    def _resolve_threshold(
        self,
        metric: str,
        run: EvaluationRun | None,
        default_threshold: float,
    ) -> float:
        if not isinstance(run, EvaluationRun):
            return default_threshold

        if run.thresholds and metric in run.thresholds:
            return float(run.thresholds[metric])

        for result in run.results:
            found = result.get_metric(metric)
            if found and found.threshold is not None:
                return float(found.threshold)

        return default_threshold
