"""Experiment management service for A/B testing and metric comparison."""

from __future__ import annotations

from evalvault.domain.entities.experiment import Experiment
from evalvault.domain.services.experiment_comparator import (
    ExperimentComparator,
    MetricComparison,
)
from evalvault.domain.services.experiment_reporter import ExperimentReportGenerator
from evalvault.domain.services.experiment_repository import ExperimentRepository
from evalvault.domain.services.experiment_statistics import ExperimentStatisticsCalculator
from evalvault.ports.outbound.storage_port import StoragePort


class ExperimentManager:
    """실험 관리 서비스.

    A/B 테스트 및 실험을 생성, 관리하고 그룹 간 메트릭을 비교합니다.

    Attributes:
        _repository: 실험 CRUD 전담 레이어
        _comparator: 메트릭 비교 유틸리티
        _statistics: 통계 요약 계산기
        _reporter: 보고서 생성기
    """

    def __init__(self, storage: StoragePort):
        """ExperimentManager 초기화.

        Args:
            storage: 평가 결과를 조회하기 위한 StoragePort
        """
        self._repository = ExperimentRepository(storage)
        self._comparator = ExperimentComparator(storage)
        self._statistics = ExperimentStatisticsCalculator()
        self._reporter = ExperimentReportGenerator(
            comparator=self._comparator,
            statistics_calculator=self._statistics,
        )

    def create_experiment(
        self,
        name: str,
        description: str = "",
        hypothesis: str = "",
        metrics: list[str] | None = None,
    ) -> Experiment:
        """새 실험 생성.

        Args:
            name: 실험 이름
            description: 실험 설명
            hypothesis: 가설
            metrics: 비교할 메트릭 목록

        Returns:
            생성된 Experiment 객체
        """
        return self._repository.create(
            name=name,
            description=description,
            hypothesis=hypothesis,
            metrics=metrics,
        )

    def get_experiment(self, experiment_id: str) -> Experiment:
        """실험 조회.

        Args:
            experiment_id: 조회할 실험 ID

        Returns:
            Experiment 객체

        Raises:
            KeyError: 실험을 찾을 수 없는 경우
        """
        return self._repository.get(experiment_id)

    def list_experiments(self, status: str | None = None) -> list[Experiment]:
        """실험 목록 조회.

        Args:
            status: 필터링할 상태 (None이면 모두 조회)

        Returns:
            Experiment 객체 리스트
        """
        return self._repository.list(status=status)

    def compare_groups(self, experiment_id: str) -> list[MetricComparison]:
        """그룹 간 메트릭 비교.

        실험 내 각 그룹의 평가 결과를 비교하여 메트릭별 성능을 분석합니다.

        Args:
            experiment_id: 실험 ID

        Returns:
            MetricComparison 객체 리스트
        """
        experiment = self.get_experiment(experiment_id)
        return self._comparator.compare(experiment)

    def get_summary(self, experiment_id: str) -> dict:
        """실험 요약 통계.

        Args:
            experiment_id: 실험 ID

        Returns:
            요약 딕셔너리
        """
        experiment = self.get_experiment(experiment_id)
        return self._statistics.build_summary(experiment)

    def conclude_experiment(self, experiment_id: str, conclusion: str) -> None:
        """실험 완료 및 결론 기록.

        Args:
            experiment_id: 실험 ID
            conclusion: 실험 결론
        """
        self._repository.conclude(experiment_id, conclusion)

    def add_group_to_experiment(
        self, experiment_id: str, group_name: str, description: str = ""
    ) -> None:
        """실험에 그룹 추가.

        Args:
            experiment_id: 실험 ID
            group_name: 그룹 이름
            description: 그룹 설명
        """
        self._repository.add_group(experiment_id, group_name, description)

    def add_run_to_experiment_group(self, experiment_id: str, group_name: str, run_id: str) -> None:
        """실험 그룹에 평가 실행 추가.

        Args:
            experiment_id: 실험 ID
            group_name: 그룹 이름
            run_id: 추가할 평가 실행 ID
        """
        self._repository.add_run(experiment_id, group_name, run_id)

    def generate_report(self, experiment_id: str) -> dict:
        """실험 요약과 메트릭 비교가 포함된 보고서 생성."""
        experiment = self.get_experiment(experiment_id)
        return self._reporter.generate(experiment)


__all__ = ["ExperimentManager", "MetricComparison"]
