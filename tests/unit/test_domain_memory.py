"""Unit tests for Domain Memory entities and SQLite adapter.

Based on "Memory in the Age of AI Agents: A Survey" framework:
- Forms: Flat structure (SQLite tables)
- Functions: Factual, Experiential, Working layers
- Dynamics: Formation, Evolution, Retrieval (Phase 2-3)
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from evalvault.domain.entities.memory import (
    BehaviorEntry,
    BehaviorHandbook,
    DomainMemoryContext,
    FactualFact,
    LearningMemory,
)

# =============================================================================
# FactualFact Entity Tests
# =============================================================================


class TestFactualFact:
    """FactualFact 엔티티 테스트."""

    def test_create_fact(self):
        """기본 사실 생성."""
        fact = FactualFact(
            subject="보험A",
            predicate="보장금액",
            object="1억원",
            domain="insurance",
            language="ko",
        )
        assert fact.subject == "보험A"
        assert fact.predicate == "보장금액"
        assert fact.object == "1억원"
        assert fact.domain == "insurance"
        assert fact.language == "ko"
        assert fact.fact_type == "verified"
        assert fact.verification_score == 1.0

    def test_fact_id_auto_generated(self):
        """fact_id 자동 생성."""
        fact1 = FactualFact(subject="A", predicate="B", object="C")
        fact2 = FactualFact(subject="A", predicate="B", object="C")
        assert fact1.fact_id != fact2.fact_id

    def test_verification_score_validation(self):
        """검증 점수 유효성 검사."""
        with pytest.raises(ValueError, match="verification_score must be between"):
            FactualFact(subject="A", predicate="B", object="C", verification_score=1.5)

        with pytest.raises(ValueError, match="verification_score must be between"):
            FactualFact(subject="A", predicate="B", object="C", verification_score=-0.1)

    def test_to_triple(self):
        """SPO 트리플 반환."""
        fact = FactualFact(subject="보험A", predicate="보장금액", object="1억원")
        triple = fact.to_triple()
        assert triple == ("보험A", "보장금액", "1억원")

    def test_last_verified_defaults_to_created_at(self):
        """last_verified 기본값."""
        fact = FactualFact(subject="A", predicate="B", object="C")
        assert fact.last_verified == fact.created_at

    def test_fact_types(self):
        """사실 타입."""
        for fact_type in ["verified", "inferred", "contradictory"]:
            fact = FactualFact(subject="A", predicate="B", object="C", fact_type=fact_type)
            assert fact.fact_type == fact_type


# =============================================================================
# LearningMemory Entity Tests
# =============================================================================


class TestLearningMemory:
    """LearningMemory 엔티티 테스트."""

    def test_create_learning(self):
        """기본 학습 메모리 생성."""
        learning = LearningMemory(
            run_id="run-001",
            domain="insurance",
            language="ko",
            entity_type_reliability={"보험": 0.9, "보장": 0.85},
        )
        assert learning.run_id == "run-001"
        assert learning.domain == "insurance"
        assert learning.entity_type_reliability["보험"] == 0.9

    def test_get_reliability(self):
        """신뢰도 조회."""
        learning = LearningMemory(
            run_id="run-001",
            entity_type_reliability={"보험": 0.9},
        )
        assert learning.get_reliability("보험") == 0.9
        assert learning.get_reliability("unknown", default=0.3) == 0.3

    def test_update_reliability(self):
        """신뢰도 업데이트 (지수 평활)."""
        learning = LearningMemory(
            run_id="run-001",
            entity_type_reliability={"보험": 0.5},
        )
        # alpha=0.1: new = 0.5 * 0.9 + 0.9 * 0.1 = 0.45 + 0.09 = 0.54
        learning.update_reliability("보험", 0.9, alpha=0.1)
        assert learning.entity_type_reliability["보험"] == pytest.approx(0.54)

    def test_update_reliability_new_entity(self):
        """새 엔티티 타입 신뢰도 업데이트."""
        learning = LearningMemory(run_id="run-001")
        learning.update_reliability("새타입", 0.8, alpha=0.1)
        # 기본값 0.5 * 0.9 + 0.8 * 0.1 = 0.45 + 0.08 = 0.53
        assert learning.entity_type_reliability["새타입"] == pytest.approx(0.53)

    def test_patterns_storage(self):
        """패턴 저장."""
        learning = LearningMemory(
            run_id="run-001",
            failed_patterns=["pattern1", "pattern2"],
            successful_patterns=["pattern3"],
        )
        assert len(learning.failed_patterns) == 2
        assert len(learning.successful_patterns) == 1


# =============================================================================
# DomainMemoryContext Entity Tests
# =============================================================================


class TestDomainMemoryContext:
    """DomainMemoryContext 엔티티 테스트."""

    def test_create_context(self):
        """기본 컨텍스트 생성."""
        context = DomainMemoryContext(
            domain="insurance",
            language="ko",
        )
        assert context.domain == "insurance"
        assert len(context.active_entities) == 0

    def test_add_entity(self):
        """엔티티 추가."""
        context = DomainMemoryContext()
        context.add_entity("보험A", "보험상품")
        context.add_entity("보험B", "보험상품")
        context.add_entity("홍길동", "인물")

        assert len(context.active_entities) == 3
        assert "보험A" in context.active_entities
        assert context.entity_type_distribution["보험상품"] == 2
        assert context.entity_type_distribution["인물"] == 1

    def test_update_metric(self):
        """품질 지표 업데이트."""
        context = DomainMemoryContext()
        context.update_metric("faithfulness", 0.85)
        context.update_metric("context_precision", 0.9)

        assert context.current_quality_metrics["faithfulness"] == 0.85
        assert context.current_quality_metrics["context_precision"] == 0.9

    def test_clear(self):
        """세션 종료 시 초기화."""
        context = DomainMemoryContext()
        context.add_entity("entity1", "type1")
        context.update_metric("metric1", 0.8)

        context.clear()

        assert len(context.active_entities) == 0
        assert len(context.entity_type_distribution) == 0
        assert len(context.current_quality_metrics) == 0


# =============================================================================
# BehaviorEntry Entity Tests
# =============================================================================


class TestBehaviorEntry:
    """BehaviorEntry 엔티티 테스트."""

    def test_create_behavior(self):
        """기본 행동 생성."""
        behavior = BehaviorEntry(
            description="보험 용어 처리",
            trigger_pattern=r"보험|보장|약관",
            action_sequence=["extract_terms", "verify_context"],
            domain="insurance",
        )
        assert behavior.description == "보험 용어 처리"
        assert behavior.success_rate == 0.0
        assert behavior.use_count == 0

    def test_record_usage(self):
        """사용 기록."""
        behavior = BehaviorEntry(description="Test")
        behavior.record_usage(success=True)
        assert behavior.use_count == 1
        assert behavior.success_rate == 1.0

        behavior.record_usage(success=False)
        assert behavior.use_count == 2
        assert behavior.success_rate == 0.5

    def test_is_applicable(self):
        """언어 적용 가능성."""
        behavior = BehaviorEntry(
            description="Test",
            applicable_languages=["ko", "en"],
        )
        assert behavior.is_applicable("ko") is True
        assert behavior.is_applicable("ja") is False


# =============================================================================
# BehaviorHandbook Entity Tests
# =============================================================================


class TestBehaviorHandbook:
    """BehaviorHandbook 엔티티 테스트."""

    def test_add_behavior(self):
        """행동 추가."""
        handbook = BehaviorHandbook(domain="insurance")
        behavior = BehaviorEntry(description="Test", domain="default")
        handbook.add_behavior(behavior)

        assert len(handbook.behaviors) == 1
        assert handbook.behaviors[0].domain == "insurance"

    def test_find_applicable(self):
        """적용 가능한 행동 찾기."""
        handbook = BehaviorHandbook(domain="insurance")
        behavior1 = BehaviorEntry(
            description="보험 처리",
            trigger_pattern=r"보험",
            success_rate=0.9,
        )
        behavior2 = BehaviorEntry(
            description="약관 처리",
            trigger_pattern=r"약관",
            success_rate=0.8,
        )
        handbook.add_behavior(behavior1)
        handbook.add_behavior(behavior2)

        applicable = handbook.find_applicable("보험 약관 검토", language="ko")
        assert len(applicable) == 2
        assert applicable[0].success_rate >= applicable[1].success_rate

    def test_get_top_behaviors(self):
        """상위 행동 조회."""
        handbook = BehaviorHandbook(domain="insurance")
        for i in range(10):
            handbook.add_behavior(BehaviorEntry(description=f"Behavior {i}", success_rate=i * 0.1))

        top = handbook.get_top_behaviors(n=3)
        assert len(top) == 3
        assert top[0].success_rate == 0.9


# =============================================================================
# SQLiteDomainMemoryAdapter Tests
# =============================================================================


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def memory_adapter(temp_db):
    """Create SQLiteDomainMemoryAdapter with temp database."""
    from evalvault.adapters.outbound.domain_memory.sqlite_adapter import (
        SQLiteDomainMemoryAdapter,
    )

    return SQLiteDomainMemoryAdapter(db_path=temp_db)


class TestSQLiteDomainMemoryAdapter:
    """SQLiteDomainMemoryAdapter 테스트."""

    def test_initialization_creates_tables(self, temp_db):
        """테이블 생성 확인."""
        from evalvault.adapters.outbound.domain_memory.sqlite_adapter import (
            SQLiteDomainMemoryAdapter,
        )

        SQLiteDomainMemoryAdapter(db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "factual_facts" in tables
        assert "learning_memories" in tables
        assert "behavior_entries" in tables
        assert "memory_contexts" in tables

    # =========================================================================
    # Factual Layer Tests
    # =========================================================================

    def test_save_and_get_fact(self, memory_adapter):
        """사실 저장 및 조회."""
        fact = FactualFact(
            subject="보험A",
            predicate="보장금액",
            object="1억원",
            domain="insurance",
            language="ko",
        )
        fact_id = memory_adapter.save_fact(fact)
        retrieved = memory_adapter.get_fact(fact_id)

        assert retrieved.subject == "보험A"
        assert retrieved.predicate == "보장금액"
        assert retrieved.object == "1억원"

    def test_get_fact_not_found(self, memory_adapter):
        """존재하지 않는 사실 조회."""
        with pytest.raises(KeyError, match="Fact not found"):
            memory_adapter.get_fact("nonexistent")

    def test_list_facts_with_filters(self, memory_adapter):
        """사실 목록 조회 (필터)."""
        facts = [
            FactualFact(
                subject="A", predicate="P1", object="O1", domain="insurance", language="ko"
            ),
            FactualFact(
                subject="B", predicate="P2", object="O2", domain="insurance", language="en"
            ),
            FactualFact(subject="C", predicate="P1", object="O3", domain="medical", language="ko"),
        ]
        for f in facts:
            memory_adapter.save_fact(f)

        # 도메인 필터
        insurance_facts = memory_adapter.list_facts(domain="insurance")
        assert len(insurance_facts) == 2

        # 언어 필터
        ko_facts = memory_adapter.list_facts(language="ko")
        assert len(ko_facts) == 2

        # 복합 필터
        filtered = memory_adapter.list_facts(domain="insurance", language="ko")
        assert len(filtered) == 1

    def test_find_fact_by_triple(self, memory_adapter):
        """SPO 트리플로 사실 검색."""
        fact = FactualFact(subject="보험A", predicate="보장금액", object="1억원")
        memory_adapter.save_fact(fact)

        found = memory_adapter.find_fact_by_triple("보험A", "보장금액", "1억원")
        assert found is not None
        assert found.fact_id == fact.fact_id

        not_found = memory_adapter.find_fact_by_triple("보험B", "보장금액", "1억원")
        assert not_found is None

    def test_delete_fact(self, memory_adapter):
        """사실 삭제."""
        fact = FactualFact(subject="A", predicate="B", object="C")
        memory_adapter.save_fact(fact)

        result = memory_adapter.delete_fact(fact.fact_id)
        assert result is True

        result = memory_adapter.delete_fact(fact.fact_id)
        assert result is False

    # =========================================================================
    # Experiential Layer Tests
    # =========================================================================

    def test_save_and_get_learning(self, memory_adapter):
        """학습 메모리 저장 및 조회."""
        learning = LearningMemory(
            run_id="run-001",
            domain="insurance",
            language="ko",
            entity_type_reliability={"보험": 0.9, "보장": 0.85},
            failed_patterns=["pattern1"],
            successful_patterns=["pattern2", "pattern3"],
        )
        learning_id = memory_adapter.save_learning(learning)
        retrieved = memory_adapter.get_learning(learning_id)

        assert retrieved.run_id == "run-001"
        assert retrieved.entity_type_reliability["보험"] == 0.9
        assert len(retrieved.failed_patterns) == 1
        assert len(retrieved.successful_patterns) == 2

    def test_list_learnings_with_filters(self, memory_adapter):
        """학습 메모리 목록 조회."""
        learnings = [
            LearningMemory(run_id="run-001", domain="insurance", language="ko"),
            LearningMemory(run_id="run-002", domain="insurance", language="en"),
            LearningMemory(run_id="run-003", domain="medical", language="ko"),
        ]
        for learning in learnings:
            memory_adapter.save_learning(learning)

        result = memory_adapter.list_learnings(domain="insurance")
        assert len(result) == 2

    def test_get_aggregated_reliability(self, memory_adapter):
        """집계된 신뢰도 조회."""
        learnings = [
            LearningMemory(
                run_id="run-001",
                domain="insurance",
                language="ko",
                entity_type_reliability={"보험": 0.8, "보장": 0.7},
            ),
            LearningMemory(
                run_id="run-002",
                domain="insurance",
                language="ko",
                entity_type_reliability={"보험": 0.9, "약관": 0.6},
            ),
        ]
        for learning in learnings:
            memory_adapter.save_learning(learning)

        aggregated = memory_adapter.get_aggregated_reliability("insurance", "ko")
        assert aggregated["보험"] == pytest.approx(0.85)  # (0.8 + 0.9) / 2
        assert aggregated["보장"] == 0.7
        assert aggregated["약관"] == 0.6

    # =========================================================================
    # Behavior Layer Tests
    # =========================================================================

    def test_save_and_get_behavior(self, memory_adapter):
        """행동 저장 및 조회."""
        behavior = BehaviorEntry(
            description="보험 용어 처리",
            trigger_pattern=r"보험|보장",
            action_sequence=["step1", "step2"],
            success_rate=0.85,
            domain="insurance",
        )
        behavior_id = memory_adapter.save_behavior(behavior)
        retrieved = memory_adapter.get_behavior(behavior_id)

        assert retrieved.description == "보험 용어 처리"
        assert retrieved.success_rate == 0.85
        assert len(retrieved.action_sequence) == 2

    def test_list_behaviors_with_filters(self, memory_adapter):
        """행동 목록 조회."""
        behaviors = [
            BehaviorEntry(description="B1", domain="insurance", success_rate=0.9),
            BehaviorEntry(description="B2", domain="insurance", success_rate=0.5),
            BehaviorEntry(description="B3", domain="medical", success_rate=0.8),
        ]
        for b in behaviors:
            memory_adapter.save_behavior(b)

        # 도메인 필터
        result = memory_adapter.list_behaviors(domain="insurance")
        assert len(result) == 2

        # 최소 성공률 필터
        result = memory_adapter.list_behaviors(min_success_rate=0.7)
        assert len(result) == 2

    def test_get_handbook(self, memory_adapter):
        """핸드북 조회."""
        behaviors = [
            BehaviorEntry(description="B1", domain="insurance", success_rate=0.9),
            BehaviorEntry(description="B2", domain="insurance", success_rate=0.7),
        ]
        for b in behaviors:
            memory_adapter.save_behavior(b)

        handbook = memory_adapter.get_handbook("insurance")
        assert handbook.domain == "insurance"
        assert len(handbook.behaviors) == 2

    # =========================================================================
    # Working Layer Tests
    # =========================================================================

    def test_save_and_get_context(self, memory_adapter):
        """컨텍스트 저장 및 조회."""
        context = DomainMemoryContext(
            domain="insurance",
            language="ko",
            active_entities={"entity1", "entity2"},
            entity_type_distribution={"type1": 2},
            current_quality_metrics={"faithfulness": 0.85},
        )
        session_id = memory_adapter.save_context(context)
        retrieved = memory_adapter.get_context(session_id)

        assert retrieved.domain == "insurance"
        assert "entity1" in retrieved.active_entities
        assert retrieved.entity_type_distribution["type1"] == 2
        assert retrieved.current_quality_metrics["faithfulness"] == 0.85

    def test_delete_context(self, memory_adapter):
        """컨텍스트 삭제."""
        context = DomainMemoryContext(domain="insurance")
        memory_adapter.save_context(context)

        result = memory_adapter.delete_context(context.session_id)
        assert result is True

        result = memory_adapter.delete_context(context.session_id)
        assert result is False

    # =========================================================================
    # Statistics Tests
    # =========================================================================

    def test_get_statistics(self, memory_adapter):
        """통계 조회."""
        # 데이터 추가
        memory_adapter.save_fact(
            FactualFact(subject="A", predicate="B", object="C", domain="insurance")
        )
        memory_adapter.save_fact(
            FactualFact(subject="D", predicate="E", object="F", domain="insurance")
        )
        memory_adapter.save_learning(LearningMemory(run_id="run-001", domain="insurance"))
        memory_adapter.save_behavior(BehaviorEntry(description="B1", domain="insurance"))

        stats = memory_adapter.get_statistics(domain="insurance")
        assert stats["facts"] == 2
        assert stats["learnings"] == 1
        assert stats["behaviors"] == 1
        assert stats["contexts"] == 0

    def test_get_statistics_all_domains(self, memory_adapter):
        """전체 도메인 통계."""
        memory_adapter.save_fact(
            FactualFact(subject="A", predicate="B", object="C", domain="insurance")
        )
        memory_adapter.save_fact(
            FactualFact(subject="D", predicate="E", object="F", domain="medical")
        )

        stats = memory_adapter.get_statistics()
        assert stats["facts"] == 2

    # =========================================================================
    # Dynamics Tests (Phase 2-3 - NotImplementedError)
    # =========================================================================

    def test_evolution_methods_not_implemented(self, memory_adapter):
        """Evolution 메서드 미구현 확인."""
        with pytest.raises(NotImplementedError, match="Phase 2"):
            memory_adapter.consolidate_facts("insurance", "ko")

        with pytest.raises(NotImplementedError, match="Phase 2"):
            fact1 = FactualFact(subject="A", predicate="B", object="C")
            fact2 = FactualFact(subject="A", predicate="B", object="D")
            memory_adapter.resolve_conflict(fact1, fact2)

        with pytest.raises(NotImplementedError, match="Phase 2"):
            memory_adapter.forget_obsolete("insurance")

        with pytest.raises(NotImplementedError, match="Phase 2"):
            memory_adapter.decay_verification_scores("insurance")

    def test_retrieval_methods_not_implemented(self, memory_adapter):
        """Retrieval 메서드 미구현 확인."""
        with pytest.raises(NotImplementedError, match="Phase 2"):
            memory_adapter.search_facts("query")

        with pytest.raises(NotImplementedError, match="Phase 2"):
            memory_adapter.search_behaviors("context", "insurance", "ko")

        with pytest.raises(NotImplementedError, match="Phase 2"):
            memory_adapter.hybrid_search("query", "insurance", "ko")

    def test_formation_methods_not_implemented(self, memory_adapter):
        """Formation 메서드 미구현 확인."""
        with pytest.raises(NotImplementedError, match="Phase 3"):
            memory_adapter.extract_facts_from_evaluation("run-001")

        with pytest.raises(NotImplementedError, match="Phase 3"):
            memory_adapter.extract_patterns_from_evaluation("run-001")

        with pytest.raises(NotImplementedError, match="Phase 3"):
            memory_adapter.extract_behaviors_from_evaluation("run-001")
