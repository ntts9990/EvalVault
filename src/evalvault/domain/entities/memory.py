"""Domain memory entities for factual, experiential, and working memory layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

if TYPE_CHECKING:
    pass


FactType = Literal["verified", "inferred", "contradictory"]


@dataclass
class FactualFact:
    """검증된 도메인 사실.

    Factual Memory Layer의 기본 단위로, 평가 과정에서 검증된 사실을 저장합니다.
    subject-predicate-object 트리플 형태로 지식을 표현합니다.

    Phase 5 확장:
    - Planar Form: kg_entity_id로 Knowledge Graph 엔티티와 연결
    - Hierarchical Form: parent_fact_id와 abstraction_level로 계층 구조 지원
    """

    fact_id: str = field(default_factory=lambda: str(uuid4()))
    subject: str = ""  # 엔티티 이름
    predicate: str = ""  # 관계 타입
    object: str = ""  # 대상 엔티티
    language: str = "ko"  # 언어 코드 (ko, en)
    domain: str = "default"  # 도메인 (insurance, legal, medical)
    fact_type: FactType = "verified"
    verification_score: float = 1.0  # 0.0-1.0
    verification_count: int = 1  # 검증 횟수
    source_document_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_verified: datetime | None = None

    # Phase 5: Planar Form - KG Integration
    kg_entity_id: str | None = None  # 연결된 KG 엔티티 이름
    kg_relation_type: str | None = None  # KG 관계 타입

    # Phase 5: Hierarchical Form - Summary Layers
    parent_fact_id: str | None = None  # 부모 사실 ID (요약의 원본)
    abstraction_level: int = 0  # 0=raw, 1=summary, 2=meta-summary
    child_fact_ids: list[str] = field(default_factory=list)  # 자식 사실 ID 목록

    def __post_init__(self) -> None:
        """검증 및 기본값 설정."""
        if self.verification_score < 0.0 or self.verification_score > 1.0:
            msg = "verification_score must be between 0.0 and 1.0"
            raise ValueError(msg)
        if self.last_verified is None:
            self.last_verified = self.created_at

    def to_triple(self) -> tuple[str, str, str]:
        """SPO 트리플 형태로 반환."""
        return (self.subject, self.predicate, self.object)

    def is_summary(self) -> bool:
        """요약 사실인지 확인."""
        return self.abstraction_level > 0

    def is_linked_to_kg(self) -> bool:
        """KG에 연결되어 있는지 확인."""
        return self.kg_entity_id is not None


@dataclass
class LearningMemory:
    """평가에서 학습된 패턴.

    Experiential Memory Layer의 일부로, 평가 결과에서 학습한 패턴을 저장합니다.
    엔티티/관계 타입별 신뢰도, 성공/실패 패턴 등을 기록합니다.
    """

    learning_id: str = field(default_factory=lambda: str(uuid4()))
    run_id: str = ""  # 원본 평가 run ID
    domain: str = "default"
    language: str = "ko"
    entity_type_reliability: dict[str, float] = field(default_factory=dict)
    relation_type_reliability: dict[str, float] = field(default_factory=dict)
    failed_patterns: list[str] = field(default_factory=list)
    successful_patterns: list[str] = field(default_factory=list)
    faithfulness_by_entity_type: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def get_reliability(self, entity_type: str, default: float = 0.5) -> float:
        """특정 엔티티 타입의 신뢰도 조회."""
        return self.entity_type_reliability.get(entity_type, default)

    def update_reliability(self, entity_type: str, score: float, alpha: float = 0.1) -> None:
        """신뢰도 점수 업데이트 (지수 평활 적용)."""
        current = self.entity_type_reliability.get(entity_type, 0.5)
        self.entity_type_reliability[entity_type] = current * (1 - alpha) + score * alpha


@dataclass
class DomainMemoryContext:
    """현재 실행의 워킹 메모리.

    Working Memory Layer로, 현재 세션에서 활성화된 엔티티와
    실시간 품질 지표를 추적합니다.
    """

    session_id: str = field(default_factory=lambda: str(uuid4()))
    domain: str = "default"
    language: str = "ko"
    active_entities: set[str] = field(default_factory=set)
    entity_type_distribution: dict[str, int] = field(default_factory=dict)
    current_quality_metrics: dict[str, float] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_entity(self, entity: str, entity_type: str) -> None:
        """엔티티 추가 및 분포 업데이트."""
        self.active_entities.add(entity)
        self.entity_type_distribution[entity_type] = (
            self.entity_type_distribution.get(entity_type, 0) + 1
        )
        self.updated_at = datetime.now()

    def update_metric(self, metric_name: str, value: float) -> None:
        """품질 지표 업데이트."""
        self.current_quality_metrics[metric_name] = value
        self.updated_at = datetime.now()

    def clear(self) -> None:
        """세션 종료 시 워킹 메모리 초기화."""
        self.active_entities.clear()
        self.entity_type_distribution.clear()
        self.current_quality_metrics.clear()
        self.updated_at = datetime.now()


@dataclass
class BehaviorEntry:
    """재사용 가능한 행동 정의.

    Metacognitive Reuse 개념을 구현하여, 성공적인 평가에서
    추출한 재사용 가능한 행동 패턴을 저장합니다.
    """

    behavior_id: str = field(default_factory=lambda: str(uuid4()))
    description: str = ""
    trigger_pattern: str = ""  # 이 행동을 트리거하는 조건 (regex 또는 키워드)
    action_sequence: list[str] = field(default_factory=list)
    success_rate: float = 0.0  # 역사적 성공률
    token_savings: int = 0  # 이 행동으로 절감되는 토큰 수
    applicable_languages: list[str] = field(default_factory=lambda: ["ko", "en"])
    domain: str = "default"
    last_used: datetime = field(default_factory=datetime.now)
    use_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def record_usage(self, success: bool) -> None:
        """행동 사용 기록."""
        self.use_count += 1
        self.last_used = datetime.now()
        # 성공률 업데이트 (이동 평균)
        if self.use_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            self.success_rate = (
                self.success_rate * (self.use_count - 1) + (1.0 if success else 0.0)
            ) / self.use_count

    def is_applicable(self, language: str) -> bool:
        """특정 언어에 적용 가능한지 확인."""
        return language in self.applicable_languages


@dataclass
class BehaviorHandbook:
    """도메인별 행동 핸드북.

    Behavior Handbook은 도메인별로 수집된 재사용 가능한 행동들의 컬렉션입니다.
    """

    domain: str = "default"
    behaviors: list[BehaviorEntry] = field(default_factory=list)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_behavior(self, behavior: BehaviorEntry) -> None:
        """행동 추가."""
        behavior.domain = self.domain
        self.behaviors.append(behavior)
        self.updated_at = datetime.now()

    def find_applicable(self, context: str, language: str) -> list[BehaviorEntry]:
        """현재 컨텍스트에 적용 가능한 행동 찾기."""
        import re

        applicable = []
        for behavior in self.behaviors:
            if not behavior.is_applicable(language):
                continue
            # trigger_pattern이 context에 매칭되는지 확인
            try:
                if re.search(behavior.trigger_pattern, context, re.IGNORECASE):
                    applicable.append(behavior)
            except re.error:
                # 잘못된 regex 패턴은 무시
                continue
        return sorted(applicable, key=lambda b: b.success_rate, reverse=True)

    def get_top_behaviors(self, n: int = 5) -> list[BehaviorEntry]:
        """성공률 기준 상위 N개 행동 반환."""
        return sorted(self.behaviors, key=lambda b: b.success_rate, reverse=True)[:n]
