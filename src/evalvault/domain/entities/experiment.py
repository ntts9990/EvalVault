"""Experiment entity for A/B testing and experiment management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4


@dataclass
class ExperimentGroup:
    """실험 그룹 (A/B 테스트의 각 그룹).

    실험 내 각 그룹은 서로 다른 모델, 프롬프트, 파라미터 등을 테스트합니다.
    """

    name: str  # "control", "variant_a", "variant_b"
    run_ids: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Experiment:
    """실험 엔티티.

    A/B 테스트 및 실험 관리를 위한 엔티티입니다.
    여러 평가 실행을 그룹으로 묶어 비교 분석할 수 있습니다.

    Attributes:
        experiment_id: 고유 실험 ID
        name: 실험 이름
        description: 실험 설명
        hypothesis: 가설 (예: "모델 A가 모델 B보다 성능이 좋을 것이다")
        created_at: 실험 생성 시각
        status: 실험 상태 (draft, running, completed, archived)
        groups: 실험 그룹 목록
        metrics_to_compare: 비교할 메트릭 목록
        conclusion: 실험 결론 (완료 시)
    """

    experiment_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    hypothesis: str = ""  # 가설
    created_at: datetime = field(default_factory=datetime.now)
    status: Literal["draft", "running", "completed", "archived"] = "draft"
    groups: list[ExperimentGroup] = field(default_factory=list)
    metrics_to_compare: list[str] = field(default_factory=list)
    conclusion: str | None = None

    def add_group(self, name: str, description: str = "") -> ExperimentGroup:
        """실험 그룹 추가.

        Args:
            name: 그룹 이름 (예: "control", "variant_a")
            description: 그룹 설명

        Returns:
            생성된 ExperimentGroup 객체
        """
        group = ExperimentGroup(name=name, description=description)
        self.groups.append(group)
        return group

    def add_run_to_group(self, group_name: str, run_id: str) -> None:
        """그룹에 평가 실행 추가.

        Args:
            group_name: 그룹 이름
            run_id: 추가할 평가 실행 ID

        Raises:
            ValueError: 그룹을 찾을 수 없는 경우
        """
        for group in self.groups:
            if group.name == group_name:
                group.run_ids.append(run_id)
                return
        raise ValueError(f"Group not found: {group_name}")
