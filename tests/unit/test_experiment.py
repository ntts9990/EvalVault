"""Tests for Experiment entity and ExperimentManager service."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from evalvault.domain.entities import EvaluationRun, MetricScore, TestCaseResult
from evalvault.domain.entities.experiment import Experiment, ExperimentGroup
from evalvault.domain.services.experiment_comparator import ExperimentComparator
from evalvault.domain.services.experiment_manager import (
    ExperimentManager,
    MetricComparison,
)
from evalvault.domain.services.experiment_reporter import ExperimentReportGenerator
from evalvault.domain.services.experiment_repository import ExperimentRepository
from evalvault.domain.services.experiment_statistics import ExperimentStatisticsCalculator


@pytest.fixture
def mock_storage():
    """Mock StoragePort 구현."""
    storage = Mock()
    experiments: dict[str, Experiment] = {}

    def save_experiment(exp):
        experiments[exp.experiment_id] = exp
        return exp.experiment_id

    def get_experiment(exp_id):
        if exp_id not in experiments:
            raise KeyError(f"Experiment not found: {exp_id}")
        return experiments[exp_id]

    def list_experiments(status=None, limit=100):
        exps = list(experiments.values())
        if status:
            exps = [e for e in exps if e.status == status]
        return exps[:limit]

    def update_experiment(exp):
        experiments[exp.experiment_id] = exp

    storage.save_experiment.side_effect = save_experiment
    storage.get_experiment.side_effect = get_experiment
    storage.list_experiments.side_effect = list_experiments
    storage.update_experiment.side_effect = update_experiment
    storage.get_run = Mock()

    return storage


@pytest.fixture
def sample_runs():
    """샘플 EvaluationRun 데이터."""
    run1 = EvaluationRun(
        run_id="run-control-1",
        dataset_name="test-dataset",
        model_name="gpt-4o",
        metrics_evaluated=["faithfulness", "answer_relevancy"],
        results=[
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="faithfulness", score=0.8, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.75, threshold=0.7),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-002",
                metrics=[
                    MetricScore(name="faithfulness", score=0.7, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.7, threshold=0.7),
                ],
            ),
        ],
    )

    run2 = EvaluationRun(
        run_id="run-variant-a-1",
        dataset_name="test-dataset",
        model_name="gpt-5-nano",
        metrics_evaluated=["faithfulness", "answer_relevancy"],
        results=[
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.85, threshold=0.7),
                ],
            ),
            TestCaseResult(
                test_case_id="tc-002",
                metrics=[
                    MetricScore(name="faithfulness", score=0.85, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.8, threshold=0.7),
                ],
            ),
        ],
    )

    return {"control": run1, "variant_a": run2}


class TestExperimentGroup:
    """ExperimentGroup 엔티티 테스트."""

    def test_create_experiment_group(self):
        """ExperimentGroup 생성 테스트."""
        group = ExperimentGroup(name="control", description="Baseline model")
        assert group.name == "control"
        assert group.description == "Baseline model"
        assert group.run_ids == []

    def test_add_run_ids(self):
        """run_id 추가 테스트."""
        group = ExperimentGroup(name="control")
        group.run_ids.append("run-123")
        group.run_ids.append("run-456")
        assert len(group.run_ids) == 2
        assert "run-123" in group.run_ids


class TestExperiment:
    """Experiment 엔티티 테스트."""

    def test_create_experiment(self):
        """Experiment 생성 테스트."""
        exp = Experiment(
            name="A/B Test",
            description="Testing model performance",
            hypothesis="Model A is better than Model B",
        )
        assert exp.name == "A/B Test"
        assert exp.description == "Testing model performance"
        assert exp.hypothesis == "Model A is better than Model B"
        assert exp.status == "draft"
        assert exp.experiment_id is not None
        assert exp.groups == []
        assert exp.metrics_to_compare == []

    def test_experiment_default_values(self):
        """기본값 설정 테스트."""
        exp = Experiment(name="Test")
        assert exp.name == "Test"
        assert exp.description == ""
        assert exp.hypothesis == ""
        assert exp.status == "draft"
        assert exp.conclusion is None
        assert isinstance(exp.created_at, datetime)

    def test_add_group(self):
        """그룹 추가 테스트."""
        exp = Experiment(name="Test")
        group = exp.add_group("control", "Baseline model")

        assert len(exp.groups) == 1
        assert group.name == "control"
        assert group.description == "Baseline model"
        assert group in exp.groups

    def test_add_multiple_groups(self):
        """여러 그룹 추가 테스트."""
        exp = Experiment(name="Test")
        exp.add_group("control", "Baseline")
        exp.add_group("variant_a", "New model A")
        exp.add_group("variant_b", "New model B")

        assert len(exp.groups) == 3
        group_names = [g.name for g in exp.groups]
        assert "control" in group_names
        assert "variant_a" in group_names
        assert "variant_b" in group_names

    def test_add_run_to_group(self):
        """그룹에 run 추가 테스트."""
        exp = Experiment(name="Test")
        exp.add_group("control")
        exp.add_run_to_group("control", "run-123")

        assert "run-123" in exp.groups[0].run_ids

    def test_add_multiple_runs_to_group(self):
        """그룹에 여러 run 추가 테스트."""
        exp = Experiment(name="Test")
        exp.add_group("control")
        exp.add_run_to_group("control", "run-123")
        exp.add_run_to_group("control", "run-456")
        exp.add_run_to_group("control", "run-789")

        assert len(exp.groups[0].run_ids) == 3

    def test_add_run_to_nonexistent_group(self):
        """존재하지 않는 그룹에 run 추가 시 예외 발생."""
        exp = Experiment(name="Test")
        with pytest.raises(ValueError, match="Group not found: nonexistent"):
            exp.add_run_to_group("nonexistent", "run-123")

    def test_experiment_status_transitions(self):
        """실험 상태 전환 테스트."""
        exp = Experiment(name="Test")
        assert exp.status == "draft"

        exp.status = "running"
        assert exp.status == "running"

        exp.status = "completed"
        assert exp.status == "completed"

        exp.status = "archived"
        assert exp.status == "archived"


class TestMetricComparison:
    """MetricComparison 테스트."""

    def test_create_metric_comparison(self):
        """MetricComparison 생성 테스트."""
        comparison = MetricComparison(
            metric_name="faithfulness",
            group_scores={"control": 0.75, "variant_a": 0.85},
            best_group="variant_a",
            improvement=13.33,
        )
        assert comparison.metric_name == "faithfulness"
        assert comparison.group_scores["control"] == 0.75
        assert comparison.group_scores["variant_a"] == 0.85
        assert comparison.best_group == "variant_a"
        assert comparison.improvement == pytest.approx(13.33)


class TestExperimentRepository:
    """ExperimentRepository 동작 테스트."""

    def test_create_and_get_experiment(self, mock_storage):
        repo = ExperimentRepository(mock_storage)
        exp = repo.create(
            name="Repo Test",
            description="desc",
            hypothesis="hypo",
            metrics=["faithfulness"],
        )

        loaded = repo.get(exp.experiment_id)
        assert loaded.name == "Repo Test"
        assert loaded.description == "desc"
        assert loaded.metrics_to_compare == ["faithfulness"]

    def test_add_group_and_run(self, mock_storage):
        repo = ExperimentRepository(mock_storage)
        exp = repo.create(name="Attach")

        repo.add_group(exp.experiment_id, "control", "baseline")
        repo.add_run(exp.experiment_id, "control", "run-1")

        stored = repo.get(exp.experiment_id)
        assert stored.groups[0].name == "control"
        assert stored.groups[0].run_ids == ["run-1"]

    def test_conclude_and_list(self, mock_storage):
        repo = ExperimentRepository(mock_storage)
        draft = repo.create(name="Draft Only")
        running = repo.create(name="Running")
        running.status = "running"
        repo.save(running)

        repo.conclude(draft.experiment_id, "done")
        completed = repo.list(status="completed")

        assert len(completed) == 1
        assert completed[0].name == "Draft Only"
        assert repo.get(draft.experiment_id).conclusion == "done"


class TestExperimentComparator:
    """ExperimentComparator 테스트."""

    def test_compare_returns_metric_scores(self, mock_storage, sample_runs):
        comparator = ExperimentComparator(mock_storage)
        experiment = Experiment(
            name="Comparator",
            metrics_to_compare=["faithfulness", "answer_relevancy"],
        )
        experiment.add_group("control")
        experiment.add_group("variant_a")
        experiment.add_run_to_group("control", "run-control-1")
        experiment.add_run_to_group("variant_a", "run-variant-a-1")

        mock_storage.get_run.side_effect = lambda run_id: sample_runs[
            "control" if "control" in run_id else "variant_a"
        ]

        comparisons = comparator.compare(experiment)

        assert len(comparisons) == 2
        metrics = {c.metric_name for c in comparisons}
        assert "faithfulness" in metrics
        assert "answer_relevancy" in metrics

    def test_compare_handles_empty_groups(self, mock_storage):
        comparator = ExperimentComparator(mock_storage)
        experiment = Experiment(name="Empty")
        experiment.add_group("control")

        assert comparator.compare(experiment) == []


class TestExperimentStatisticsCalculator:
    """ExperimentStatisticsCalculator 테스트."""

    def test_build_summary(self):
        experiment = Experiment(
            name="Summary",
            description="desc",
            hypothesis="hypo",
        )
        experiment.add_group("control", "baseline")
        experiment.add_run_to_group("control", "run-123")

        calculator = ExperimentStatisticsCalculator()
        summary = calculator.build_summary(experiment)

        assert summary["name"] == "Summary"
        assert summary["groups"]["control"]["num_runs"] == 1
        assert summary["groups"]["control"]["description"] == "baseline"


class TestExperimentReportGenerator:
    """ExperimentReportGenerator 테스트."""

    def test_generate_report_combines_sections(self):
        experiment = Experiment(name="Report")
        comparator = Mock(spec=ExperimentComparator)
        comparator.compare.return_value = [
            MetricComparison(
                metric_name="faithfulness",
                group_scores={"control": 0.8},
                best_group="control",
                improvement=0.0,
            )
        ]
        stats = ExperimentStatisticsCalculator()
        reporter = ExperimentReportGenerator(comparator=comparator, statistics_calculator=stats)

        report = reporter.generate(experiment)

        assert report["experiment"]["name"] == "Report"
        assert report["comparisons"][0]["metric_name"] == "faithfulness"
        comparator.compare.assert_called_once_with(experiment)


class TestExperimentManager:
    """ExperimentManager 서비스 테스트."""

    def test_create_experiment(self, mock_storage):
        """실험 생성 테스트."""
        manager = ExperimentManager(mock_storage)
        exp = manager.create_experiment(
            name="Model Comparison",
            description="Compare GPT-4o vs GPT-5-nano",
            hypothesis="GPT-5-nano will have higher faithfulness scores",
            metrics=["faithfulness", "answer_relevancy"],
        )

        assert exp.name == "Model Comparison"
        assert exp.description == "Compare GPT-4o vs GPT-5-nano"
        assert exp.hypothesis == "GPT-5-nano will have higher faithfulness scores"
        assert exp.metrics_to_compare == ["faithfulness", "answer_relevancy"]
        assert exp.status == "draft"
        # 저장소에 저장되었는지 확인
        mock_storage.save_experiment.assert_called_once()
        # 저장소에서 조회 가능한지 확인
        retrieved = manager.get_experiment(exp.experiment_id)
        assert retrieved.experiment_id == exp.experiment_id

    def test_create_experiment_with_defaults(self, mock_storage):
        """기본값으로 실험 생성 테스트."""
        manager = ExperimentManager(mock_storage)
        exp = manager.create_experiment(name="Test Experiment")

        assert exp.name == "Test Experiment"
        assert exp.description == ""
        assert exp.hypothesis == ""
        assert exp.metrics_to_compare == []

    def test_get_experiment(self, mock_storage):
        """실험 조회 테스트."""
        manager = ExperimentManager(mock_storage)
        exp = manager.create_experiment(name="Test")

        retrieved = manager.get_experiment(exp.experiment_id)
        assert retrieved == exp

    def test_get_experiment_not_found(self, mock_storage):
        """존재하지 않는 실험 조회 시 예외."""
        manager = ExperimentManager(mock_storage)
        with pytest.raises(KeyError, match="Experiment not found"):
            manager.get_experiment("nonexistent-id")

    def test_compare_groups(self, mock_storage, sample_runs):
        """그룹 간 메트릭 비교 테스트."""
        # Setup storage mock to return sample runs
        mock_storage.get_run.side_effect = lambda run_id: sample_runs.get(
            "control" if "control" in run_id else "variant_a"
        )

        manager = ExperimentManager(mock_storage)
        exp = manager.create_experiment(
            name="Test",
            metrics=["faithfulness", "answer_relevancy"],
        )
        exp.add_group("control")
        exp.add_group("variant_a")
        exp.add_run_to_group("control", "run-control-1")
        exp.add_run_to_group("variant_a", "run-variant-a-1")

        comparisons = manager.compare_groups(exp.experiment_id)

        assert len(comparisons) == 2

        # Check faithfulness comparison
        faith_comp = next(c for c in comparisons if c.metric_name == "faithfulness")
        assert faith_comp.group_scores["control"] == pytest.approx(0.75)
        assert faith_comp.group_scores["variant_a"] == pytest.approx(0.875)
        assert faith_comp.best_group == "variant_a"
        assert faith_comp.improvement > 0

    def test_compare_groups_empty_groups(self, mock_storage):
        """빈 그룹 비교 시 빈 리스트 반환."""
        manager = ExperimentManager(mock_storage)
        exp = manager.create_experiment(name="Test", metrics=["faithfulness"])
        exp.add_group("control")

        comparisons = manager.compare_groups(exp.experiment_id)
        assert comparisons == []

    def test_get_summary(self, mock_storage, sample_runs):
        """실험 요약 통계 테스트."""
        mock_storage.get_run.side_effect = lambda run_id: sample_runs.get(
            "control" if "control" in run_id else "variant_a"
        )

        manager = ExperimentManager(mock_storage)
        exp = manager.create_experiment(
            name="Test",
            metrics=["faithfulness", "answer_relevancy"],
        )
        exp.add_group("control")
        exp.add_group("variant_a")
        exp.add_run_to_group("control", "run-control-1")
        exp.add_run_to_group("variant_a", "run-variant-a-1")

        summary = manager.get_summary(exp.experiment_id)

        assert summary["experiment_id"] == exp.experiment_id
        assert summary["name"] == "Test"
        assert summary["status"] == "draft"
        assert len(summary["groups"]) == 2
        assert "control" in summary["groups"]
        assert "variant_a" in summary["groups"]

    def test_conclude_experiment(self, mock_storage):
        """실험 완료 및 결론 기록 테스트."""
        manager = ExperimentManager(mock_storage)
        exp = manager.create_experiment(name="Test")

        manager.conclude_experiment(
            exp.experiment_id,
            conclusion="Variant A shows 15% improvement in faithfulness",
        )

        updated_exp = manager.get_experiment(exp.experiment_id)
        assert updated_exp.status == "completed"
        assert updated_exp.conclusion == "Variant A shows 15% improvement in faithfulness"

    def test_list_experiments(self, mock_storage):
        """실험 목록 조회 테스트."""
        manager = ExperimentManager(mock_storage)
        exp1 = manager.create_experiment(name="Experiment 1")
        exp2 = manager.create_experiment(name="Experiment 2")

        experiments = manager.list_experiments()
        assert len(experiments) == 2
        assert exp1 in experiments
        assert exp2 in experiments

    def test_list_experiments_by_status(self, mock_storage):
        """상태별 실험 목록 조회 테스트."""
        manager = ExperimentManager(mock_storage)
        manager.create_experiment(name="Draft Experiment")
        exp2 = manager.create_experiment(name="Running Experiment")
        exp2.status = "running"
        exp3 = manager.create_experiment(name="Completed Experiment")
        manager.conclude_experiment(exp3.experiment_id, "Done")

        draft_exps = manager.list_experiments(status="draft")
        assert len(draft_exps) == 1
        assert draft_exps[0].name == "Draft Experiment"

        completed_exps = manager.list_experiments(status="completed")
        assert len(completed_exps) == 1
        assert completed_exps[0].name == "Completed Experiment"
