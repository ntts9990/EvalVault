"""Unit tests for StageMetricGuideService."""

from evalvault.domain.entities.improvement import EffortLevel
from evalvault.domain.entities.stage import StageMetric
from evalvault.domain.services.stage_metric_guide_service import StageMetricGuideService


def test_stage_metric_action_override_applied() -> None:
    metric = StageMetric(
        run_id="run-001",
        stage_id="stg-retrieval",
        metric_name="retrieval.recall_at_k",
        score=0.4,
        threshold=0.6,
    )
    overrides = {
        "retrieval.recall_at_k": {
            "title": "Custom recall improvement",
            "description": "Test description",
            "implementation_hint": "Test hint",
            "expected_improvement": 0.2,
            "expected_improvement_range": [0.1, 0.3],
            "effort": "high",
        }
    }

    service = StageMetricGuideService(action_overrides=overrides)
    guides = service.build_guides([metric])

    assert guides
    action = guides[0].actions[0]
    assert action.title == "Custom recall improvement"
    assert action.expected_improvement == 0.2
    assert action.expected_improvement_range == (0.1, 0.3)
    assert action.effort == EffortLevel.HIGH
