"""Playbook loader for improvement rules.

YAML 플레이북 파일을 로드하고 파싱하여 패턴 탐지 규칙을 제공합니다.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from evalvault.ports.outbound.improvement_port import (
    ActionDefinitionProtocol,
    MetricPlaybookProtocol,
    PatternDefinitionProtocol,
    PlaybookPort,
)

logger = logging.getLogger(__name__)


@dataclass
class DetectionRule:
    """패턴 탐지 규칙."""

    rule_type: str  # metric_threshold, feature_threshold, correlation, etc.
    condition: str | None = None
    feature: str | None = None
    threshold: float | None = None
    direction: str | None = None  # greater_than, less_than, etc.
    variables: list[str] = field(default_factory=list)
    min_correlation: float | None = None
    expected_direction: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DetectionRule:
        """딕셔너리에서 생성."""
        return cls(
            rule_type=data.get("type", ""),
            condition=data.get("condition"),
            feature=data.get("feature"),
            threshold=data.get("threshold"),
            direction=data.get("direction"),
            variables=data.get("variables", []),
            min_correlation=data.get("min_correlation"),
            expected_direction=data.get("expected_direction"),
        )


@dataclass
class ActionDefinition(ActionDefinitionProtocol):
    """개선 액션 정의."""

    title: str
    description: str
    implementation_hint: str
    expected_improvement: float
    expected_improvement_range: tuple[float, float]
    effort: str  # low, medium, high

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActionDefinition:
        """딕셔너리에서 생성."""
        improvement_range = data.get("expected_improvement_range", [0.0, 0.0])
        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            implementation_hint=data.get("implementation_hint", ""),
            expected_improvement=data.get("expected_improvement", 0.0),
            expected_improvement_range=(
                improvement_range[0] if len(improvement_range) > 0 else 0.0,
                improvement_range[1] if len(improvement_range) > 1 else 0.0,
            ),
            effort=data.get("effort", "medium"),
        )


@dataclass
class PatternDefinition(PatternDefinitionProtocol):
    """패턴 정의."""

    pattern_id: str
    pattern_type: str
    description: str
    detection_rules: Sequence[Any]
    component: str
    priority: str
    actions: Sequence[ActionDefinitionProtocol]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PatternDefinition:
        """딕셔너리에서 생성."""
        return cls(
            pattern_id=data.get("pattern_id", ""),
            pattern_type=data.get("pattern_type", "unknown"),
            description=data.get("description", ""),
            detection_rules=[DetectionRule.from_dict(r) for r in data.get("detection_rules", [])],
            component=data.get("component", ""),
            priority=data.get("priority", "p2_medium"),
            actions=[ActionDefinition.from_dict(a) for a in data.get("actions", [])],
        )


@dataclass
class MetricPlaybook(MetricPlaybookProtocol):
    """메트릭별 플레이북."""

    metric_name: str
    description: str
    default_threshold: float
    patterns: Sequence[PatternDefinitionProtocol]

    @classmethod
    def from_dict(cls, metric_name: str, data: dict[str, Any]) -> MetricPlaybook:
        """딕셔너리에서 생성."""
        return cls(
            metric_name=metric_name,
            description=data.get("description", ""),
            default_threshold=data.get("default_threshold", 0.7),
            patterns=[PatternDefinition.from_dict(p) for p in data.get("patterns", [])],
        )


@dataclass
class Playbook(PlaybookPort):
    """전체 플레이북."""

    version: str
    global_config: dict[str, Any]
    metrics: dict[str, MetricPlaybookProtocol]
    verification_commands: dict[str, str]

    def get_metric_playbook(self, metric: str) -> MetricPlaybookProtocol | None:
        """특정 메트릭의 플레이북 조회."""
        return self.metrics.get(metric)

    def get_patterns_for_metric(self, metric: str) -> Sequence[PatternDefinitionProtocol]:
        """특정 메트릭의 패턴 목록."""
        playbook = self.get_metric_playbook(metric)
        return playbook.patterns if playbook else []

    def get_all_patterns(self) -> list[tuple[str, PatternDefinitionProtocol]]:
        """모든 메트릭의 패턴 목록 (metric_name, pattern) 튜플."""
        result: list[tuple[str, PatternDefinitionProtocol]] = []
        for metric_name, playbook in self.metrics.items():
            for pattern in playbook.patterns:
                result.append((metric_name, pattern))
        return result


class PlaybookLoader:
    """플레이북 로더."""

    DEFAULT_PLAYBOOK_PATH = (
        Path(__file__).parent.parent.parent.parent
        / "config"
        / "playbooks"
        / "improvement_playbook.yaml"
    )

    def __init__(self, playbook_path: Path | str | None = None):
        """초기화.

        Args:
            playbook_path: 플레이북 파일 경로 (기본: 내장 플레이북)
        """
        if playbook_path is None:
            self._path = self.DEFAULT_PLAYBOOK_PATH
        else:
            self._path = Path(playbook_path)

        self._playbook: Playbook | None = None

    def load(self) -> Playbook:
        """플레이북 로드.

        Returns:
            Playbook 객체

        Raises:
            FileNotFoundError: 플레이북 파일이 없는 경우
            yaml.YAMLError: YAML 파싱 실패
        """
        if self._playbook is not None:
            return self._playbook

        if not self._path.exists():
            raise FileNotFoundError(f"Playbook not found: {self._path}")

        logger.info(f"Loading playbook from: {self._path}")

        with open(self._path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._playbook = self._parse_playbook(data)
        logger.info(
            f"Loaded playbook v{self._playbook.version} with {len(self._playbook.metrics)} metrics"
        )

        return self._playbook

    def _parse_playbook(self, data: dict[str, Any]) -> Playbook:
        """플레이북 파싱."""
        metrics = {}
        for metric_name, metric_data in data.get("metrics", {}).items():
            metrics[metric_name] = MetricPlaybook.from_dict(metric_name, metric_data)

        return Playbook(
            version=data.get("version", "1.0.0"),
            global_config=data.get("global", {}),
            metrics=metrics,
            verification_commands=data.get("verification_commands", {}),
        )

    def reload(self) -> Playbook:
        """플레이북 재로드."""
        self._playbook = None
        return self.load()


# 싱글톤 인스턴스
_default_loader: PlaybookLoader | None = None


def get_default_playbook() -> Playbook:
    """기본 플레이북 조회."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PlaybookLoader()
    return _default_loader.load()
