"""결과 저장 인터페이스."""

from typing import Any, Protocol

from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.experiment import Experiment


class StoragePort(Protocol):
    """평가 결과 저장을 위한 포트 인터페이스.

    SQLite, PostgreSQL 등 다양한 저장소에 평가 결과를 저장합니다.
    """

    def save_run(self, run: EvaluationRun) -> str:
        """평가 실행 결과를 저장합니다.

        Args:
            run: 저장할 평가 실행 결과

        Returns:
            저장된 run의 ID
        """
        ...

    def get_run(self, run_id: str) -> EvaluationRun:
        """저장된 평가 실행 결과를 조회합니다.

        Args:
            run_id: 조회할 run의 ID

        Returns:
            EvaluationRun 객체

        Raises:
            KeyError: run_id에 해당하는 결과가 없는 경우
        """
        ...

    def list_runs(
        self,
        limit: int = 100,
        dataset_name: str | None = None,
        model_name: str | None = None,
    ) -> list[EvaluationRun]:
        """저장된 평가 실행 결과 목록을 조회합니다.

        Args:
            limit: 최대 조회 개수
            dataset_name: 필터링할 데이터셋 이름 (선택)
            model_name: 필터링할 모델 이름 (선택)

        Returns:
            EvaluationRun 객체 리스트 (최신순)
        """
        ...

    # Experiment 관련 메서드

    def save_experiment(self, experiment: Experiment) -> str:
        """실험을 저장합니다.

        Args:
            experiment: 저장할 실험

        Returns:
            저장된 experiment의 ID
        """
        ...

    def get_experiment(self, experiment_id: str) -> Experiment:
        """실험을 조회합니다.

        Args:
            experiment_id: 조회할 실험 ID

        Returns:
            Experiment 객체

        Raises:
            KeyError: 실험을 찾을 수 없는 경우
        """
        ...

    def list_experiments(
        self,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Experiment]:
        """실험 목록을 조회합니다.

        Args:
            status: 필터링할 상태 (선택)
            limit: 최대 조회 개수

        Returns:
            Experiment 객체 리스트
        """
        ...

    def update_experiment(self, experiment: Experiment) -> None:
        """실험을 업데이트합니다.

        Args:
            experiment: 업데이트할 실험
        """
        ...

    # Pipeline result history 메서드

    def save_pipeline_result(self, record: dict[str, Any]) -> None:
        """파이프라인 분석 결과 히스토리를 저장합니다."""
        ...

    def list_pipeline_results(self, limit: int = 50) -> list[dict[str, Any]]:
        """파이프라인 분석 결과 목록을 조회합니다."""
        ...

    def get_pipeline_result(self, result_id: str) -> dict[str, Any]:
        """저장된 파이프라인 분석 결과를 조회합니다."""
        ...
