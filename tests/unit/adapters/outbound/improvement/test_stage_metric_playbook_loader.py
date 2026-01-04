"""Unit tests for StageMetricPlaybookLoader."""

from pathlib import Path

from evalvault.adapters.outbound.improvement.stage_metric_playbook_loader import (
    StageMetricPlaybookLoader,
)


def test_load_stage_metric_playbook(tmp_path: Path) -> None:
    playbook_path = tmp_path / "stage_metric_playbook.yaml"
    playbook_path.write_text(
        "\n".join(
            [
                'version: "1.0.0"',
                "metrics:",
                "  retrieval.recall_at_k:",
                '    title: "Recall improvement"',
                '    description: "Test description"',
                '    implementation_hint: "Test hint"',
                "    expected_improvement: 0.1",
                "    expected_improvement_range: [0.05, 0.15]",
                '    effort: "high"',
            ]
        ),
        encoding="utf-8",
    )

    loader = StageMetricPlaybookLoader(playbook_path)
    playbook = loader.load()

    assert "retrieval.recall_at_k" in playbook
    assert playbook["retrieval.recall_at_k"]["title"] == "Recall improvement"
    assert playbook["retrieval.recall_at_k"]["expected_improvement"] == 0.1


def test_missing_stage_metric_playbook_returns_empty(tmp_path: Path) -> None:
    loader = StageMetricPlaybookLoader(tmp_path / "missing.yaml")
    playbook = loader.load()

    assert playbook == {}
