"""Metric selection components."""

from __future__ import annotations

# 사용 가능한 메트릭 정의
AVAILABLE_METRICS = {
    "faithfulness": {
        "name": "Faithfulness",
        "description": "답변이 컨텍스트에 충실한지 평가",
        "icon": "🎯",
        "category": "generation",
    },
    "answer_relevancy": {
        "name": "Answer Relevancy",
        "description": "답변이 질문과 관련있는지 평가",
        "icon": "🔗",
        "category": "generation",
    },
    "context_precision": {
        "name": "Context Precision",
        "description": "검색된 컨텍스트의 정밀도 평가",
        "icon": "🎯",
        "category": "retrieval",
    },
    "context_recall": {
        "name": "Context Recall",
        "description": "필요한 정보가 검색되었는지 평가",
        "icon": "📥",
        "category": "retrieval",
    },
    "factual_correctness": {
        "name": "Factual Correctness",
        "description": "ground_truth 대비 사실적 정확성 평가",
        "icon": "✅",
        "category": "generation",
    },
    "semantic_similarity": {
        "name": "Semantic Similarity",
        "description": "답변과 ground_truth 간 의미적 유사도 평가",
        "icon": "🔄",
        "category": "generation",
    },
    "summary_score": {
        "name": "Summary Score",
        "description": "요약 내 핵심 정보 보존과 간결성 평가",
        "icon": "📝",
        "category": "summary",
    },
    "summary_faithfulness": {
        "name": "Summary Faithfulness",
        "description": "요약 내용이 원문 근거에 충실한지 평가",
        "icon": "🧭",
        "category": "summary",
    },
    "insurance_term_accuracy": {
        "name": "Insurance Term Accuracy",
        "description": "보험 용어 정확성 평가",
        "icon": "📋",
        "category": "domain",
    },
    "entity_preservation": {
        "name": "Entity Preservation",
        "description": "보험 핵심 엔티티 보존율 평가",
        "icon": "🏷️",
        "category": "summary",
    },
}

# 기본 선택 메트릭
DEFAULT_METRICS = ["faithfulness", "answer_relevancy"]


class MetricSelector:
    """메트릭 선택 컴포넌트.

    사용 가능한 메트릭 목록을 제공하고 선택을 검증합니다.
    """

    def __init__(self, available_metrics: dict | None = None):
        """선택기 초기화.

        Args:
            available_metrics: 사용 가능한 메트릭 딕셔너리 (기본값 사용)
        """
        self.metrics = available_metrics or AVAILABLE_METRICS

    def get_available_metrics(self) -> list[str]:
        """사용 가능한 메트릭 이름 목록 반환."""
        return list(self.metrics.keys())

    def get_description(self, metric_name: str) -> str | None:
        """메트릭 설명 반환.

        Args:
            metric_name: 메트릭 이름

        Returns:
            설명 문자열 또는 None
        """
        metric = self.metrics.get(metric_name)
        return metric["description"] if metric else None

    def get_icon(self, metric_name: str) -> str | None:
        """메트릭 아이콘 반환.

        Args:
            metric_name: 메트릭 이름

        Returns:
            아이콘 문자열 또는 None
        """
        metric = self.metrics.get(metric_name)
        return metric["icon"] if metric else None

    def get_default_metrics(self) -> list[str]:
        """기본 선택 메트릭 목록 반환."""
        return DEFAULT_METRICS.copy()

    def validate_selection(self, selected: list[str]) -> bool:
        """선택된 메트릭 검증.

        Args:
            selected: 선택된 메트릭 이름 목록

        Returns:
            유효하면 True, 아니면 False
        """
        if not selected:
            return False

        available = set(self.metrics.keys())
        return all(metric in available for metric in selected)

    def get_metrics_by_category(self) -> dict[str, list[str]]:
        """카테고리별 메트릭 그룹화.

        Returns:
            카테고리별 메트릭 이름 딕셔너리
        """
        categories: dict[str, list[str]] = {}
        for name, info in self.metrics.items():
            category = info.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(name)
        return categories

    def get_display_name(self, metric_name: str) -> str:
        """메트릭 표시 이름 반환.

        Args:
            metric_name: 메트릭 이름

        Returns:
            표시 이름 또는 원래 이름
        """
        metric = self.metrics.get(metric_name)
        return metric["name"] if metric else metric_name
