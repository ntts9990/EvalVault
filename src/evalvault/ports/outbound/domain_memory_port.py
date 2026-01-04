"""Domain Memory port interface for factual, experiential, and working memory layers.

Based on "Memory in the Age of AI Agents: A Survey" framework:
- Forms: Flat (Phase 1), Planar/Hierarchical (Phase 2-3)
- Functions: Factual, Experiential, Working layers
- Dynamics: Formation, Evolution, Retrieval strategies
"""

from typing import TYPE_CHECKING, Protocol

from evalvault.domain.entities.memory import (
    BehaviorEntry,
    BehaviorHandbook,
    DomainMemoryContext,
    FactualFact,
    LearningMemory,
)

if TYPE_CHECKING:
    from evalvault.domain.entities.result import EvaluationRun


class FactualMemoryPort(Protocol):
    """Factual memory CRUD operations."""

    # =========================================================================
    # Factual Layer - 검증된 사실 저장 (Phase 1)
    # =========================================================================

    def save_fact(self, fact: FactualFact) -> str:
        """사실을 저장합니다.

        Args:
            fact: 저장할 FactualFact

        Returns:
            저장된 fact의 ID
        """
        ...

    def get_fact(self, fact_id: str) -> FactualFact:
        """사실을 조회합니다.

        Args:
            fact_id: 조회할 fact ID

        Returns:
            FactualFact 객체

        Raises:
            KeyError: fact_id에 해당하는 사실이 없는 경우
        """
        ...

    def list_facts(
        self,
        domain: str | None = None,
        language: str | None = None,
        subject: str | None = None,
        predicate: str | None = None,
        limit: int = 100,
    ) -> list[FactualFact]:
        """사실 목록을 조회합니다.

        Args:
            domain: 필터링할 도메인 (선택)
            language: 필터링할 언어 (선택)
            subject: 필터링할 주어 (선택)
            predicate: 필터링할 술어 (선택)
            limit: 최대 조회 개수

        Returns:
            FactualFact 리스트 (최신순)
        """
        ...

    def update_fact(self, fact: FactualFact) -> None:
        """사실을 업데이트합니다.

        Args:
            fact: 업데이트할 FactualFact
        """
        ...

    def delete_fact(self, fact_id: str) -> bool:
        """사실을 삭제합니다.

        Args:
            fact_id: 삭제할 fact ID

        Returns:
            삭제 성공 여부
        """
        ...

    def find_fact_by_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        domain: str | None = None,
    ) -> FactualFact | None:
        """SPO 트리플로 사실을 검색합니다.

        Args:
            subject: 주어
            predicate: 술어
            obj: 목적어
            domain: 도메인 필터 (선택)

        Returns:
            일치하는 FactualFact 또는 None
        """
        ...


class LearningMemoryPort(Protocol):
    """Experiential memory operations."""

    # =========================================================================
    # Experiential Layer - 학습된 패턴 (Phase 1)
    # =========================================================================

    def save_learning(self, learning: LearningMemory) -> str:
        """학습 메모리를 저장합니다.

        Args:
            learning: 저장할 LearningMemory

        Returns:
            저장된 learning의 ID
        """
        ...

    def get_learning(self, learning_id: str) -> LearningMemory:
        """학습 메모리를 조회합니다.

        Args:
            learning_id: 조회할 learning ID

        Returns:
            LearningMemory 객체

        Raises:
            KeyError: learning_id에 해당하는 학습이 없는 경우
        """
        ...

    def list_learnings(
        self,
        domain: str | None = None,
        language: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> list[LearningMemory]:
        """학습 메모리 목록을 조회합니다.

        Args:
            domain: 필터링할 도메인 (선택)
            language: 필터링할 언어 (선택)
            run_id: 필터링할 평가 run ID (선택)
            limit: 최대 조회 개수

        Returns:
            LearningMemory 리스트 (최신순)
        """
        ...

    def get_aggregated_reliability(
        self,
        domain: str,
        language: str,
    ) -> dict[str, float]:
        """도메인/언어별 집계된 엔티티 타입 신뢰도를 조회합니다.

        여러 학습 결과를 집계하여 엔티티 타입별 평균 신뢰도를 반환합니다.

        Args:
            domain: 도메인
            language: 언어

        Returns:
            엔티티 타입 -> 평균 신뢰도 매핑
        """
        ...


class BehaviorMemoryPort(Protocol):
    """Behavior memory operations."""

    # =========================================================================
    # Behavior Layer - Metacognitive Reuse (Phase 1)
    # =========================================================================

    def save_behavior(self, behavior: BehaviorEntry) -> str:
        """행동 엔트리를 저장합니다.

        Args:
            behavior: 저장할 BehaviorEntry

        Returns:
            저장된 behavior의 ID
        """
        ...

    def get_behavior(self, behavior_id: str) -> BehaviorEntry:
        """행동 엔트리를 조회합니다.

        Args:
            behavior_id: 조회할 behavior ID

        Returns:
            BehaviorEntry 객체

        Raises:
            KeyError: behavior_id에 해당하는 행동이 없는 경우
        """
        ...

    def list_behaviors(
        self,
        domain: str | None = None,
        language: str | None = None,
        min_success_rate: float = 0.0,
        limit: int = 100,
    ) -> list[BehaviorEntry]:
        """행동 엔트리 목록을 조회합니다.

        Args:
            domain: 필터링할 도메인 (선택)
            language: 필터링할 언어 (선택)
            min_success_rate: 최소 성공률 (선택)
            limit: 최대 조회 개수

        Returns:
            BehaviorEntry 리스트 (성공률 내림차순)
        """
        ...

    def get_handbook(self, domain: str) -> BehaviorHandbook:
        """도메인별 행동 핸드북을 조회합니다.

        Args:
            domain: 도메인

        Returns:
            BehaviorHandbook 객체 (행동 목록 포함)
        """
        ...

    def update_behavior(self, behavior: BehaviorEntry) -> None:
        """행동 엔트리를 업데이트합니다.

        Args:
            behavior: 업데이트할 BehaviorEntry
        """
        ...


class WorkingMemoryPort(Protocol):
    """Session working memory operations."""

    # =========================================================================
    # Working Layer - 세션 컨텍스트 (Phase 1)
    # =========================================================================

    def save_context(self, context: DomainMemoryContext) -> str:
        """워킹 메모리 컨텍스트를 저장합니다.

        Args:
            context: 저장할 DomainMemoryContext

        Returns:
            저장된 context의 session_id
        """
        ...

    def get_context(self, session_id: str) -> DomainMemoryContext:
        """워킹 메모리 컨텍스트를 조회합니다.

        Args:
            session_id: 조회할 세션 ID

        Returns:
            DomainMemoryContext 객체

        Raises:
            KeyError: session_id에 해당하는 컨텍스트가 없는 경우
        """
        ...

    def update_context(self, context: DomainMemoryContext) -> None:
        """워킹 메모리 컨텍스트를 업데이트합니다.

        Args:
            context: 업데이트할 DomainMemoryContext
        """
        ...

    def delete_context(self, session_id: str) -> bool:
        """워킹 메모리 컨텍스트를 삭제합니다.

        세션 종료 시 호출됩니다.

        Args:
            session_id: 삭제할 세션 ID

        Returns:
            삭제 성공 여부
        """
        ...


class MemoryEvolutionPort(Protocol):
    """Evolution dynamics for domain memory."""

    # =========================================================================
    # Dynamics: Evolution - 메모리 진화 (Phase 2)
    # =========================================================================

    def consolidate_facts(
        self,
        domain: str,
        language: str,
    ) -> int:
        """유사한 사실들을 통합합니다.

        동일한 SPO 트리플을 가진 사실들을 병합하고,
        신뢰도 점수를 집계합니다.

        Args:
            domain: 도메인
            language: 언어

        Returns:
            통합된 사실 수

        Raises:
            NotImplementedError: Phase 2에서 구현 예정
        """
        ...

    def resolve_conflict(
        self,
        fact1: FactualFact,
        fact2: FactualFact,
    ) -> FactualFact:
        """충돌하는 사실을 해결합니다.

        두 사실이 동일한 subject-predicate를 가지지만 다른 object를 가질 때,
        타임스탬프, 검증 횟수, 신뢰도를 기반으로 우선순위를 결정합니다.

        Args:
            fact1: 첫 번째 사실
            fact2: 두 번째 사실

        Returns:
            해결된 FactualFact

        Raises:
            NotImplementedError: Phase 2에서 구현 예정
        """
        ...

    def forget_obsolete(
        self,
        domain: str,
        max_age_days: int = 90,
        min_verification_count: int = 1,
        min_verification_score: float = 0.3,
    ) -> int:
        """오래되거나 신뢰도 낮은 메모리를 삭제합니다.

        다음 조건 중 하나를 만족하면 삭제:
        - last_verified가 max_age_days보다 오래됨
        - verification_count < min_verification_count
        - verification_score < min_verification_score

        Args:
            domain: 도메인
            max_age_days: 최대 경과 일수
            min_verification_count: 최소 검증 횟수
            min_verification_score: 최소 검증 점수

        Returns:
            삭제된 메모리 수

        Raises:
            NotImplementedError: Phase 2에서 구현 예정
        """
        ...

    def decay_verification_scores(
        self,
        domain: str,
        decay_rate: float = 0.95,
    ) -> int:
        """시간에 따라 검증 점수를 감소시킵니다.

        오래 검증되지 않은 사실의 신뢰도를 점진적으로 낮춥니다.

        Args:
            domain: 도메인
            decay_rate: 감소율 (0.0-1.0)

        Returns:
            업데이트된 사실 수

        Raises:
            NotImplementedError: Phase 2에서 구현 예정
        """
        ...


class MemoryRetrievalPort(Protocol):
    """Retrieval strategies for domain memory."""

    # =========================================================================
    # Dynamics: Retrieval - 메모리 검색 (Phase 2)
    # =========================================================================

    def search_facts(
        self,
        query: str,
        domain: str | None = None,
        language: str | None = None,
        limit: int = 10,
    ) -> list[FactualFact]:
        """키워드 기반 사실 검색.

        subject, predicate, object 필드에서 키워드 매칭을 수행합니다.

        Args:
            query: 검색 쿼리
            domain: 도메인 필터 (선택)
            language: 언어 필터 (선택)
            limit: 최대 결과 수

        Returns:
            관련 FactualFact 리스트 (관련도 내림차순)

        Raises:
            NotImplementedError: Phase 2에서 구현 예정
        """
        ...

    def search_behaviors(
        self,
        context: str,
        domain: str,
        language: str,
        limit: int = 5,
    ) -> list[BehaviorEntry]:
        """컨텍스트 기반 행동 검색.

        현재 평가 컨텍스트에 적용 가능한 행동을 검색합니다.
        trigger_pattern 매칭과 성공률을 고려합니다.

        Args:
            context: 현재 컨텍스트 (질문, 문서 등)
            domain: 도메인
            language: 언어
            limit: 최대 결과 수

        Returns:
            적용 가능한 BehaviorEntry 리스트 (성공률 내림차순)

        Raises:
            NotImplementedError: Phase 2에서 구현 예정
        """
        ...

    def hybrid_search(
        self,
        query: str,
        domain: str,
        language: str,
        fact_weight: float = 0.5,
        behavior_weight: float = 0.3,
        learning_weight: float = 0.2,
        limit: int = 10,
    ) -> dict[str, list]:
        """하이브리드 메모리 검색.

        Factual, Experiential, Behavior 레이어에서 통합 검색을 수행합니다.
        각 레이어의 가중치를 조절하여 결과를 반환합니다.

        Args:
            query: 검색 쿼리
            domain: 도메인
            language: 언어
            fact_weight: Factual 레이어 가중치
            behavior_weight: Behavior 레이어 가중치
            learning_weight: Learning 레이어 가중치
            limit: 레이어당 최대 결과 수

        Returns:
            {"facts": [...], "behaviors": [...], "learnings": [...]}

        Raises:
            NotImplementedError: Phase 2에서 구현 예정
        """
        ...


class MemoryFormationPort(Protocol):
    """Formation dynamics for domain memory."""

    # =========================================================================
    # Dynamics: Formation - 메모리 형성 (Phase 3)
    # =========================================================================

    def extract_facts_from_evaluation(
        self,
        evaluation_run: "EvaluationRun",
        domain: str,
        language: str = "ko",
        min_confidence: float = 0.7,
    ) -> list[FactualFact]:
        """평가 결과에서 사실을 추출합니다.

        높은 신뢰도의 평가 결과(faithfulness >= min_confidence)에서
        contexts의 SPO 트리플을 자동 추출합니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인 (예: 'insurance')
            language: 언어 코드 (기본: 'ko')
            min_confidence: 최소 faithfulness 점수

        Returns:
            추출된 FactualFact 리스트
        """
        ...

    def extract_patterns_from_evaluation(
        self,
        evaluation_run: "EvaluationRun",
        domain: str,
        language: str = "ko",
    ) -> LearningMemory:
        """평가 결과에서 학습 패턴을 추출합니다.

        평가 결과에서 성공/실패 패턴, 메트릭별 점수 분포를 학습합니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인
            language: 언어 코드

        Returns:
            추출된 LearningMemory
        """
        ...

    def extract_behaviors_from_evaluation(
        self,
        evaluation_run: "EvaluationRun",
        domain: str,
        language: str = "ko",
        min_success_rate: float = 0.8,
    ) -> list[BehaviorEntry]:
        """평가 결과에서 재사용 가능한 행동을 추출합니다.

        Metacognitive Reuse 개념을 구현하여, 성공적인 평가에서
        재사용 가능한 질문-응답 패턴을 추출합니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인
            language: 언어 코드
            min_success_rate: 최소 성공률 임계값 (전체 메트릭 통과율)

        Returns:
            추출된 BehaviorEntry 리스트
        """
        ...


class KGIntegrationPort(Protocol):
    """Planar form operations for KG integration."""

    # =========================================================================
    # Phase 5: Planar Form - KG Integration
    # =========================================================================

    def link_fact_to_kg(
        self,
        fact_id: str,
        kg_entity_id: str,
        kg_relation_type: str | None = None,
    ) -> None:
        """사실을 Knowledge Graph 엔티티에 연결합니다.

        Args:
            fact_id: 연결할 사실 ID
            kg_entity_id: KG 엔티티 이름/ID
            kg_relation_type: KG 관계 타입 (선택)

        Raises:
            KeyError: fact_id가 존재하지 않는 경우
        """
        ...

    def get_facts_by_kg_entity(
        self,
        kg_entity_id: str,
        domain: str | None = None,
    ) -> list[FactualFact]:
        """특정 KG 엔티티에 연결된 사실들을 조회합니다.

        Args:
            kg_entity_id: KG 엔티티 이름/ID
            domain: 도메인 필터 (선택)

        Returns:
            연결된 FactualFact 리스트
        """
        ...

    def import_kg_as_facts(
        self,
        entities: list[tuple[str, str, dict]],  # (name, entity_type, attributes)
        relations: list[tuple[str, str, str, float]],  # (source, target, relation_type, confidence)
        domain: str,
        language: str = "ko",
    ) -> dict[str, int]:
        """Knowledge Graph의 엔티티와 관계를 사실로 변환하여 저장합니다.

        엔티티는 (subject, "is_a", entity_type) 형태로,
        관계는 (source, relation_type, target) 형태로 저장됩니다.

        Args:
            entities: 엔티티 리스트 [(name, type, attrs), ...]
            relations: 관계 리스트 [(source, target, type, confidence), ...]
            domain: 도메인
            language: 언어

        Returns:
            {"entities_imported": N, "relations_imported": N}
        """
        ...

    def export_facts_as_kg(
        self,
        domain: str,
        language: str | None = None,
        min_confidence: float = 0.5,
    ) -> tuple[list[tuple[str, str, dict]], list[tuple[str, str, str, float]]]:
        """사실들을 Knowledge Graph 형태로 내보냅니다.

        Args:
            domain: 도메인
            language: 언어 필터 (선택)
            min_confidence: 최소 신뢰도

        Returns:
            (entities, relations) 튜플
            - entities: [(name, entity_type, attributes), ...]
            - relations: [(source, target, relation_type, confidence), ...]
        """
        ...


class FactHierarchyPort(Protocol):
    """Hierarchical summary operations for facts."""

    # =========================================================================
    # Phase 5: Hierarchical Form - Summary Layers
    # =========================================================================

    def create_summary_fact(
        self,
        child_fact_ids: list[str],
        summary_subject: str,
        summary_predicate: str,
        summary_object: str,
        domain: str,
        language: str = "ko",
    ) -> FactualFact:
        """여러 사실을 요약하는 상위 사실을 생성합니다.

        자식 사실들의 abstraction_level + 1로 요약 사실을 생성하고,
        자식 사실들의 parent_fact_id를 업데이트합니다.

        Args:
            child_fact_ids: 요약할 자식 사실 ID 목록
            summary_subject: 요약 주어
            summary_predicate: 요약 술어
            summary_object: 요약 목적어
            domain: 도메인
            language: 언어

        Returns:
            생성된 요약 FactualFact

        Raises:
            ValueError: child_fact_ids가 비어있는 경우
            KeyError: 존재하지 않는 fact_id가 포함된 경우
        """
        ...

    def get_facts_by_level(
        self,
        abstraction_level: int,
        domain: str | None = None,
        language: str | None = None,
        limit: int = 100,
    ) -> list[FactualFact]:
        """특정 추상화 레벨의 사실들을 조회합니다.

        Args:
            abstraction_level: 추상화 레벨 (0=raw, 1=summary, 2=meta)
            domain: 도메인 필터 (선택)
            language: 언어 필터 (선택)
            limit: 최대 조회 개수

        Returns:
            해당 레벨의 FactualFact 리스트
        """
        ...

    def get_fact_hierarchy(
        self,
        fact_id: str,
    ) -> dict[str, list[FactualFact] | FactualFact | None]:
        """사실의 전체 계층 구조를 조회합니다.

        Args:
            fact_id: 조회할 사실 ID

        Returns:
            {
                "fact": FactualFact,
                "parent": FactualFact | None,
                "children": list[FactualFact],
                "ancestors": list[FactualFact],  # 최상위까지
                "descendants": list[FactualFact]  # 최하위까지
            }

        Raises:
            KeyError: fact_id가 존재하지 않는 경우
        """
        ...

    def get_child_facts(
        self,
        parent_fact_id: str,
    ) -> list[FactualFact]:
        """특정 사실의 자식 사실들을 조회합니다.

        Args:
            parent_fact_id: 부모 사실 ID

        Returns:
            자식 FactualFact 리스트
        """
        ...


class MemoryStatisticsPort(Protocol):
    """Memory statistics utilities."""

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_statistics(
        self,
        domain: str | None = None,
    ) -> dict[str, int]:
        """메모리 통계를 조회합니다.

        Args:
            domain: 도메인 필터 (선택)

        Returns:
            {"facts": N, "learnings": N, "behaviors": N, "contexts": N}
        """
        ...


class MemoryInsightPort(LearningMemoryPort, MemoryRetrievalPort, Protocol):
    """Insight helpers for analysis and memory-aware evaluation."""

    ...


class MemoryLifecyclePort(
    FactualMemoryPort,
    LearningMemoryPort,
    BehaviorMemoryPort,
    MemoryFormationPort,
    MemoryEvolutionPort,
    Protocol,
):
    """Formation/Evolution workflows for domain learning hooks."""

    ...


class DomainMemoryPort(
    FactualMemoryPort,
    LearningMemoryPort,
    BehaviorMemoryPort,
    WorkingMemoryPort,
    MemoryEvolutionPort,
    MemoryRetrievalPort,
    MemoryFormationPort,
    KGIntegrationPort,
    FactHierarchyPort,
    MemoryStatisticsPort,
    Protocol,
):
    """도메인 메모리 저장소 인터페이스.

    세 가지 메모리 레이어를 관리합니다:
    - Factual Layer: 검증된 도메인 사실 (SPO 트리플)
    - Experiential Layer: 평가에서 학습된 패턴
    - Working Layer: 현재 세션의 활성 컨텍스트

    Dynamics 확장 포인트:
    - Formation: 평가 결과에서 메모리 형성
    - Evolution: 메모리 통합, 업데이트, 망각
    - Retrieval: 하이브리드 검색 (키워드 + 의미론적)
    """

    ...
