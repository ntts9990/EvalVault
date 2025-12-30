"""Improvement adapters for RAG system optimization.

Rule-based 패턴 탐지와 LLM-based 인사이트 생성을 결합한
하이브리드 분석 기능을 제공합니다.
"""

from evalvault.adapters.outbound.improvement.insight_generator import (
    BatchPatternInsight,
    InsightGenerator,
    LLMInsight,
)
from evalvault.adapters.outbound.improvement.pattern_detector import (
    FeatureVector,
    PatternDetector,
)
from evalvault.adapters.outbound.improvement.playbook_loader import (
    ActionDefinition,
    DetectionRule,
    MetricPlaybook,
    PatternDefinition,
    Playbook,
    PlaybookLoader,
    get_default_playbook,
)

__all__ = [
    # Playbook
    "ActionDefinition",
    "DetectionRule",
    "MetricPlaybook",
    "PatternDefinition",
    "Playbook",
    "PlaybookLoader",
    "get_default_playbook",
    # Pattern Detector
    "FeatureVector",
    "PatternDetector",
    # Insight Generator
    "BatchPatternInsight",
    "InsightGenerator",
    "LLMInsight",
]
