"""Experiment management service for A/B testing and metric comparison."""

from dataclasses import dataclass

from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.experiment import Experiment
from evalvault.ports.outbound.storage_port import StoragePort


@dataclass
class MetricComparison:
    """메트릭 비교 결과.

    여러 그룹 간의 특정 메트릭 성능을 비교한 결과를 담습니다.

    Attributes:
        metric_name: 메트릭 이름 (예: "faithfulness")
        group_scores: 그룹별 평균 점수 (group_name -> avg_score)
        best_group: 가장 높은 점수를 받은 그룹
        improvement: 최고 그룹과 최저 그룹 간 개선율 (percentage)
    """

    metric_name: str
    group_scores: dict[str, float]  # group_name -> avg_score
    best_group: str
    improvement: float  # percentage improvement


class ExperimentManager:
    """실험 관리 서비스.

    A/B 테스트 및 실험을 생성, 관리하고 그룹 간 메트릭을 비교합니다.

    Attributes:
        _storage: 평가 결과를 조회하기 위한 StoragePort
        _experiments: 실험 ID -> Experiment 매핑
    """

    def __init__(self, storage: StoragePort):
        """ExperimentManager 초기화.

        Args:
            storage: 평가 결과를 조회하기 위한 StoragePort
        """
        self._storage = storage

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
        experiment = Experiment(
            name=name,
            description=description,
            hypothesis=hypothesis,
            metrics_to_compare=metrics or [],
        )
        # 저장소에 저장
        self._storage.save_experiment(experiment)
        return experiment

    def get_experiment(self, experiment_id: str) -> Experiment:
        """실험 조회.

        Args:
            experiment_id: 조회할 실험 ID

        Returns:
            Experiment 객체

        Raises:
            KeyError: 실험을 찾을 수 없는 경우
        """
        return self._storage.get_experiment(experiment_id)

    def list_experiments(self, status: str | None = None) -> list[Experiment]:
        """실험 목록 조회.

        Args:
            status: 필터링할 상태 (None이면 모두 조회)

        Returns:
            Experiment 객체 리스트
        """
        return self._storage.list_experiments(status=status)

    def compare_groups(self, experiment_id: str) -> list[MetricComparison]:
        """그룹 간 메트릭 비교.

        실험 내 각 그룹의 평가 결과를 비교하여 메트릭별 성능을 분석합니다.

        Args:
            experiment_id: 실험 ID

        Returns:
            MetricComparison 객체 리스트
        """
        experiment = self.get_experiment(experiment_id)

        # 각 그룹의 run 데이터 수집
        group_runs: dict[str, list[EvaluationRun]] = {}
        for group in experiment.groups:
            runs = []
            for run_id in group.run_ids:
                try:
                    run = self._storage.get_run(run_id)
                    runs.append(run)
                except KeyError:
                    # run이 없으면 스킵
                    continue
            group_runs[group.name] = runs

        # 메트릭이 지정되지 않은 경우 모든 run의 메트릭 수집
        metrics_to_compare = experiment.metrics_to_compare
        if not metrics_to_compare and group_runs:
            # 첫 번째 그룹의 첫 번째 run에서 메트릭 추출
            for runs in group_runs.values():
                if runs:
                    metrics_to_compare = runs[0].metrics_evaluated
                    break

        # 그룹에 run이 없으면 빈 리스트 반환
        if not any(group_runs.values()):
            return []

        # 메트릭별 비교
        comparisons: list[MetricComparison] = []
        for metric in metrics_to_compare:
            group_scores: dict[str, float] = {}

            # 각 그룹의 평균 점수 계산
            for group_name, runs in group_runs.items():
                scores = []
                for run in runs:
                    avg_score = run.get_avg_score(metric)
                    if avg_score is not None:
                        scores.append(avg_score)

                if scores:
                    group_scores[group_name] = sum(scores) / len(scores)

            # 비교 결과가 없으면 스킵
            if not group_scores:
                continue

            # 최고 그룹 및 개선율 계산
            best_group = max(group_scores, key=group_scores.get)  # type: ignore
            best_score = group_scores[best_group]
            worst_score = min(group_scores.values())

            # 개선율 계산 (최저 대비 최고)
            improvement = (
                ((best_score - worst_score) / worst_score) * 100 if worst_score > 0 else 0.0
            )

            comparisons.append(
                MetricComparison(
                    metric_name=metric,
                    group_scores=group_scores,
                    best_group=best_group,
                    improvement=improvement,
                )
            )

        return comparisons

    def get_summary(self, experiment_id: str) -> dict:
        """실험 요약 통계.

        Args:
            experiment_id: 실험 ID

        Returns:
            요약 딕셔너리
        """
        experiment = self.get_experiment(experiment_id)

        # 그룹별 run 수 집계
        groups_summary = {}
        for group in experiment.groups:
            groups_summary[group.name] = {
                "description": group.description,
                "num_runs": len(group.run_ids),
                "run_ids": group.run_ids,
            }

        summary = {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "description": experiment.description,
            "hypothesis": experiment.hypothesis,
            "status": experiment.status,
            "created_at": experiment.created_at.isoformat(),
            "metrics_to_compare": experiment.metrics_to_compare,
            "groups": groups_summary,
            "conclusion": experiment.conclusion,
        }

        return summary

    def conclude_experiment(self, experiment_id: str, conclusion: str) -> None:
        """실험 완료 및 결론 기록.

        Args:
            experiment_id: 실험 ID
            conclusion: 실험 결론
        """
        experiment = self.get_experiment(experiment_id)
        experiment.status = "completed"
        experiment.conclusion = conclusion
        # 저장소에 업데이트
        self._storage.update_experiment(experiment)

    def add_group_to_experiment(
        self, experiment_id: str, group_name: str, description: str = ""
    ) -> None:
        """실험에 그룹 추가.

        Args:
            experiment_id: 실험 ID
            group_name: 그룹 이름
            description: 그룹 설명
        """
        experiment = self.get_experiment(experiment_id)
        experiment.add_group(group_name, description)
        self._storage.update_experiment(experiment)

    def add_run_to_experiment_group(self, experiment_id: str, group_name: str, run_id: str) -> None:
        """실험 그룹에 평가 실행 추가.

        Args:
            experiment_id: 실험 ID
            group_name: 그룹 이름
            run_id: 추가할 평가 실행 ID
        """
        experiment = self.get_experiment(experiment_id)
        experiment.add_run_to_group(group_name, run_id)
        self._storage.update_experiment(experiment)
