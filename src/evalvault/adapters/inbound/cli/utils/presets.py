"""Preset system for common evaluation configurations.

This module provides pre-configured metric and option combinations
for different use cases, reducing onboarding time for new users.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationPreset:
    """Defines a preset configuration for evaluation runs."""

    name: str
    description: str
    metrics: tuple[str, ...]
    parallel: bool = False
    batch_size: int = 5


# Preset definitions
PRESETS: dict[str, EvaluationPreset] = {
    "quick": EvaluationPreset(
        name="quick",
        description="Fast evaluation with a single metric for quick iteration",
        metrics=("faithfulness",),
        parallel=True,
        batch_size=10,
    ),
    "production": EvaluationPreset(
        name="production",
        description="Balanced production-ready evaluation with core metrics",
        metrics=(
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
        ),
        parallel=True,
        batch_size=5,
    ),
    "summary": EvaluationPreset(
        name="summary",
        description="Summarization evaluation with summary-focused metrics",
        metrics=(
            "summary_score",
            "summary_faithfulness",
            "entity_preservation",
        ),
        parallel=True,
        batch_size=5,
    ),
    "comprehensive": EvaluationPreset(
        name="comprehensive",
        description="Complete evaluation with all available metrics",
        metrics=(
            "faithfulness",
            "answer_relevancy",
            "context_precision",
            "context_recall",
            "factual_correctness",
            "semantic_similarity",
        ),
        parallel=True,
        batch_size=3,
    ),
}


def get_preset(name: str | None) -> EvaluationPreset | None:
    """Get preset by name (case-insensitive).

    Args:
        name: Preset name (quick, production, summary, comprehensive)

    Returns:
        EvaluationPreset if found, None otherwise

    Examples:
        >>> preset = get_preset("quick")
        >>> preset.metrics
        ('faithfulness',)
    """
    if not name or not isinstance(name, str):
        return None
    return PRESETS.get(name.lower())


def list_presets() -> list[str]:
    """Get list of available preset names.

    Returns:
        Sorted list of preset names

    Examples:
        >>> list_presets()
        ['comprehensive', 'production', 'quick']
    """
    return sorted(PRESETS.keys())


def format_preset_help() -> str:
    """Format preset descriptions for help text.

    Returns:
        Formatted string describing all presets

    Examples:
        >>> help_text = format_preset_help()
        >>> "quick" in help_text
        True
    """
    lines = ["Available presets:"]
    for name in sorted(PRESETS.keys()):
        preset = PRESETS[name]
        metrics_str = ", ".join(preset.metrics)
        lines.append(f"  {name}: {preset.description}")
        lines.append(f"    Metrics: {metrics_str}")
    return "\n".join(lines)


__all__ = [
    "EvaluationPreset",
    "PRESETS",
    "get_preset",
    "list_presets",
    "format_preset_help",
]
