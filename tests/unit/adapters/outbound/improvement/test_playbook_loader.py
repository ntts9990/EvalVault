"""Unit tests for PlaybookLoader."""

from pathlib import Path

import pytest

from evalvault.adapters.outbound.improvement.playbook_loader import (
    ActionDefinition,
    DetectionRule,
    MetricPlaybook,
    PatternDefinition,
    Playbook,
    PlaybookLoader,
    get_default_playbook,
)


class TestDetectionRule:
    """DetectionRule 테스트."""

    def test_from_dict_metric_threshold(self):
        """메트릭 임계값 규칙 파싱."""
        data = {
            "type": "metric_threshold",
            "condition": "faithfulness < 0.6",
        }
        rule = DetectionRule.from_dict(data)

        assert rule.rule_type == "metric_threshold"
        assert rule.condition == "faithfulness < 0.6"

    def test_from_dict_feature_threshold(self):
        """피처 임계값 규칙 파싱."""
        data = {
            "type": "feature_threshold",
            "feature": "question_length",
            "threshold": 50,
            "direction": "greater_than",
        }
        rule = DetectionRule.from_dict(data)

        assert rule.rule_type == "feature_threshold"
        assert rule.feature == "question_length"
        assert rule.threshold == 50
        assert rule.direction == "greater_than"

    def test_from_dict_correlation(self):
        """상관관계 규칙 파싱."""
        data = {
            "type": "correlation",
            "variables": ["question_length", "context_precision"],
            "min_correlation": -0.3,
            "expected_direction": "negative",
        }
        rule = DetectionRule.from_dict(data)

        assert rule.rule_type == "correlation"
        assert rule.variables == ["question_length", "context_precision"]
        assert rule.min_correlation == -0.3
        assert rule.expected_direction == "negative"


class TestActionDefinition:
    """ActionDefinition 테스트."""

    def test_from_dict(self):
        """액션 정의 파싱."""
        data = {
            "title": "Temperature 감소",
            "description": "LLM의 창의성을 낮춤",
            "implementation_hint": "temperature=0.0",
            "expected_improvement": 0.08,
            "expected_improvement_range": [0.05, 0.12],
            "effort": "low",
        }
        action = ActionDefinition.from_dict(data)

        assert action.title == "Temperature 감소"
        assert action.description == "LLM의 창의성을 낮춤"
        assert action.expected_improvement == 0.08
        assert action.expected_improvement_range == (0.05, 0.12)
        assert action.effort == "low"

    def test_from_dict_defaults(self):
        """기본값 처리."""
        data = {}
        action = ActionDefinition.from_dict(data)

        assert action.title == ""
        assert action.expected_improvement == 0.0
        assert action.expected_improvement_range == (0.0, 0.0)
        assert action.effort == "medium"


class TestPatternDefinition:
    """PatternDefinition 테스트."""

    def test_from_dict(self):
        """패턴 정의 파싱."""
        data = {
            "pattern_id": "hallucination",
            "pattern_type": "hallucination",
            "description": "LLM이 컨텍스트에 없는 정보를 생성",
            "detection_rules": [{"type": "metric_threshold", "condition": "faithfulness < 0.6"}],
            "component": "generator",
            "priority": "p1_high",
            "actions": [
                {
                    "title": "Temperature 감소",
                    "expected_improvement": 0.08,
                    "effort": "low",
                }
            ],
        }
        pattern = PatternDefinition.from_dict(data)

        assert pattern.pattern_id == "hallucination"
        assert pattern.pattern_type == "hallucination"
        assert pattern.component == "generator"
        assert pattern.priority == "p1_high"
        assert len(pattern.detection_rules) == 1
        assert len(pattern.actions) == 1


class TestMetricPlaybook:
    """MetricPlaybook 테스트."""

    def test_from_dict(self):
        """메트릭 플레이북 파싱."""
        data = {
            "description": "답변이 컨텍스트에 충실한지 평가",
            "default_threshold": 0.8,
            "patterns": [
                {
                    "pattern_id": "hallucination",
                    "pattern_type": "hallucination",
                    "description": "할루시네이션",
                    "detection_rules": [],
                    "component": "generator",
                    "priority": "p1_high",
                    "actions": [],
                }
            ],
        }
        playbook = MetricPlaybook.from_dict("faithfulness", data)

        assert playbook.metric_name == "faithfulness"
        assert playbook.description == "답변이 컨텍스트에 충실한지 평가"
        assert playbook.default_threshold == 0.8
        assert len(playbook.patterns) == 1


class TestPlaybook:
    """Playbook 테스트."""

    def test_get_metric_playbook(self):
        """메트릭 플레이북 조회."""
        metrics = {
            "faithfulness": MetricPlaybook(
                metric_name="faithfulness",
                description="충실도",
                default_threshold=0.8,
                patterns=[],
            )
        }
        playbook = Playbook(
            version="1.0.0",
            global_config={},
            metrics=metrics,
            verification_commands={},
        )

        result = playbook.get_metric_playbook("faithfulness")
        assert result is not None
        assert result.metric_name == "faithfulness"

        result = playbook.get_metric_playbook("unknown")
        assert result is None

    def test_get_all_patterns(self):
        """모든 패턴 조회."""
        pattern = PatternDefinition(
            pattern_id="test",
            pattern_type="test",
            description="테스트",
            detection_rules=[],
            component="generator",
            priority="p2_medium",
            actions=[],
        )
        metrics = {
            "faithfulness": MetricPlaybook(
                metric_name="faithfulness",
                description="충실도",
                default_threshold=0.8,
                patterns=[pattern],
            )
        }
        playbook = Playbook(
            version="1.0.0",
            global_config={},
            metrics=metrics,
            verification_commands={},
        )

        all_patterns = playbook.get_all_patterns()
        assert len(all_patterns) == 1
        assert all_patterns[0] == ("faithfulness", pattern)


class TestPlaybookLoader:
    """PlaybookLoader 테스트."""

    def test_load_default_playbook(self):
        """기본 플레이북 로드."""
        loader = PlaybookLoader()
        playbook = loader.load()

        assert playbook is not None
        assert playbook.version == "1.0.0"
        assert "faithfulness" in playbook.metrics
        assert "summary_faithfulness" in playbook.metrics
        assert "summary_score" in playbook.metrics
        assert "entity_preservation" in playbook.metrics
        assert "context_precision" in playbook.metrics

    def test_load_cached(self):
        """캐시된 플레이북 반환."""
        loader = PlaybookLoader()
        playbook1 = loader.load()
        playbook2 = loader.load()

        assert playbook1 is playbook2  # 동일 객체

    def test_reload(self):
        """플레이북 재로드."""
        loader = PlaybookLoader()
        playbook1 = loader.load()
        playbook2 = loader.reload()

        assert playbook1 is not playbook2  # 다른 객체

    def test_file_not_found(self):
        """존재하지 않는 파일."""
        loader = PlaybookLoader(Path("/nonexistent/path.yaml"))

        with pytest.raises(FileNotFoundError):
            loader.load()


class TestGetDefaultPlaybook:
    """get_default_playbook 테스트."""

    def test_get_default_playbook(self):
        """기본 플레이북 조회."""
        playbook = get_default_playbook()

        assert playbook is not None
        assert isinstance(playbook, Playbook)
        assert "faithfulness" in playbook.metrics
        assert "summary_faithfulness" in playbook.metrics
        assert "summary_score" in playbook.metrics
        assert "entity_preservation" in playbook.metrics
