"""Theme and color definitions for web UI."""

# Primary color palette
COLORS = {
    "primary": "#3B82F6",  # Blue
    "success": "#10B981",  # Green
    "warning": "#F59E0B",  # Yellow
    "error": "#EF4444",  # Red
    "info": "#6366F1",  # Indigo
    "background": "#0F172A",  # Dark slate (dark mode)
    "surface": "#1E293B",  # Slate (dark mode)
    "text": "#F8FAFC",  # Light (dark mode)
    "text_secondary": "#94A3B8",  # Gray (dark mode)
    "border": "#334155",  # Border color
}

# Pass rate indicator colors
PASS_RATE_COLORS = {
    "excellent": "#10B981",  # >= 90%
    "good": "#3B82F6",  # >= 70%
    "warning": "#F59E0B",  # >= 50%
    "critical": "#EF4444",  # < 50%
}

# Metric-specific colors
METRIC_COLORS = {
    "faithfulness": "#3B82F6",
    "answer_relevancy": "#10B981",
    "context_precision": "#F59E0B",
    "context_recall": "#8B5CF6",
    "factual_correctness": "#EC4899",
    "semantic_similarity": "#06B6D4",
    "insurance_term_accuracy": "#14B8A6",
}


def get_pass_rate_color(pass_rate: float) -> str:
    """통과율에 따른 색상 반환.

    Args:
        pass_rate: 통과율 (0.0 ~ 1.0)

    Returns:
        색상 코드 (hex)
    """
    if pass_rate >= 0.9:
        return PASS_RATE_COLORS["excellent"]
    elif pass_rate >= 0.7:
        return PASS_RATE_COLORS["good"]
    elif pass_rate >= 0.5:
        return PASS_RATE_COLORS["warning"]
    else:
        return PASS_RATE_COLORS["critical"]


def get_pass_rate_label(pass_rate: float) -> str:
    """통과율에 따른 레이블 반환.

    Args:
        pass_rate: 통과율 (0.0 ~ 1.0)

    Returns:
        레이블 문자열
    """
    if pass_rate >= 0.9:
        return "Excellent"
    elif pass_rate >= 0.7:
        return "Good"
    elif pass_rate >= 0.5:
        return "Warning"
    else:
        return "Critical"


def get_metric_color(metric_name: str) -> str:
    """메트릭에 따른 색상 반환.

    Args:
        metric_name: 메트릭 이름

    Returns:
        색상 코드 (hex)
    """
    return METRIC_COLORS.get(metric_name, COLORS["primary"])
