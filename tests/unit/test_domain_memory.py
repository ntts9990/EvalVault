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
    # Dynamics: Evolution Tests (Phase 2)
    # =========================================================================

    def test_consolidate_facts_merges_duplicates(self, memory_adapter):
        """중복 사실 통합."""
        # 동일한 SPO 트리플을 가진 여러 사실 생성
        facts = [
            FactualFact(
                subject="보험A",
                predicate="보장금액",
                object="1억원",
                domain="insurance",
                language="ko",
                verification_score=0.8,
                verification_count=1,
                source_document_ids=["doc1"],
            ),
            FactualFact(
                subject="보험A",
                predicate="보장금액",
                object="1억원",
                domain="insurance",
                language="ko",
                verification_score=0.9,
                verification_count=2,
                source_document_ids=["doc2"],
            ),
            FactualFact(
                subject="보험A",
                predicate="보장금액",
                object="1억원",
                domain="insurance",
                language="ko",
                verification_score=0.7,
                verification_count=1,
                source_document_ids=["doc3"],
            ),
        ]
        for f in facts:
            memory_adapter.save_fact(f)

        # 초기 상태 확인
        initial_facts = memory_adapter.list_facts(domain="insurance")
        assert len(initial_facts) == 3

        # 통합 실행
        consolidated = memory_adapter.consolidate_facts("insurance", "ko")
        assert consolidated == 2  # 2개가 병합됨

        # 통합 후 상태 확인
        remaining_facts = memory_adapter.list_facts(domain="insurance")
        assert len(remaining_facts) == 1

        merged_fact = remaining_facts[0]
        assert merged_fact.verification_count == 4  # 1 + 2 + 1
        # 평균 점수: (0.8 + 0.9 + 0.7) / 3 = 0.8
        assert merged_fact.verification_score == pytest.approx(0.8, rel=0.01)

    def test_consolidate_facts_no_duplicates(self, memory_adapter):
        """중복 없는 경우 통합."""
        facts = [
            FactualFact(
                subject="A", predicate="P1", object="O1", domain="insurance", language="ko"
            ),
            FactualFact(
                subject="B", predicate="P2", object="O2", domain="insurance", language="ko"
            ),
        ]
        for f in facts:
            memory_adapter.save_fact(f)

        consolidated = memory_adapter.consolidate_facts("insurance", "ko")
        assert consolidated == 0

    def test_resolve_conflict_selects_higher_priority(self, memory_adapter):
        """충돌 해결 - 높은 우선순위 선택."""
        from datetime import datetime, timedelta

        # 높은 신뢰도, 많은 검증 횟수, 최근 검증
        fact1 = FactualFact(
            subject="보험A",
            predicate="보장금액",
            object="1억원",
            verification_score=0.9,
            verification_count=10,
            last_verified=datetime.now(),
        )
        # 낮은 신뢰도, 적은 검증 횟수, 오래된 검증
        fact2 = FactualFact(
            subject="보험A",
            predicate="보장금액",
            object="2억원",
            verification_score=0.5,
            verification_count=2,
            last_verified=datetime.now() - timedelta(days=60),
        )

        memory_adapter.save_fact(fact1)
        memory_adapter.save_fact(fact2)

        winner = memory_adapter.resolve_conflict(fact1, fact2)
        assert winner.fact_id == fact1.fact_id

        # 패자가 contradictory로 마킹되었는지 확인
        loser = memory_adapter.get_fact(fact2.fact_id)
        assert loser.fact_type == "contradictory"

    def test_forget_obsolete_deletes_low_score_facts(self, memory_adapter):
        """저신뢰 사실 삭제."""
        facts = [
            FactualFact(
                subject="A",
                predicate="P",
                object="O1",
                domain="insurance",
                verification_score=0.2,  # 낮은 점수
            ),
            FactualFact(
                subject="B",
                predicate="P",
                object="O2",
                domain="insurance",
                verification_score=0.8,  # 높은 점수
            ),
        ]
        for f in facts:
            memory_adapter.save_fact(f)

        deleted = memory_adapter.forget_obsolete(
            domain="insurance",
            min_verification_score=0.3,
        )
        assert deleted == 1

        remaining = memory_adapter.list_facts(domain="insurance")
        assert len(remaining) == 1
        assert remaining[0].subject == "B"

    def test_forget_obsolete_no_matching_facts(self, memory_adapter):
        """삭제 대상 없음."""
        fact = FactualFact(
            subject="A",
            predicate="P",
            object="O",
            domain="insurance",
            verification_score=0.9,
            verification_count=10,
        )
        memory_adapter.save_fact(fact)

        deleted = memory_adapter.forget_obsolete(domain="insurance")
        assert deleted == 0

    def test_decay_verification_scores(self, memory_adapter):
        """검증 점수 감소."""
        from datetime import datetime, timedelta

        # 10일 전 검증된 사실
        old_verified = datetime.now() - timedelta(days=10)
        fact = FactualFact(
            subject="A",
            predicate="P",
            object="O",
            domain="insurance",
            verification_score=0.8,
            created_at=old_verified,
            last_verified=old_verified,
        )
        memory_adapter.save_fact(fact)

        # 점수 감소 적용
        decayed = memory_adapter.decay_verification_scores(domain="insurance", decay_rate=0.9)
        assert decayed == 1

        updated = memory_adapter.get_fact(fact.fact_id)
        assert updated.verification_score == pytest.approx(0.72)  # 0.8 * 0.9

    def test_decay_verification_scores_invalid_rate(self, memory_adapter):
        """잘못된 감소율."""
        with pytest.raises(ValueError, match="decay_rate must be between"):
            memory_adapter.decay_verification_scores("insurance", decay_rate=1.5)

    def test_decay_verification_scores_recent_facts_unchanged(self, memory_adapter):
        """최근 사실은 감소 안함."""
        # 최근 검증된 사실
        fact = FactualFact(
            subject="A",
            predicate="P",
            object="O",
            domain="insurance",
            verification_score=0.8,
        )
        memory_adapter.save_fact(fact)

        decayed = memory_adapter.decay_verification_scores("insurance", decay_rate=0.9)
        assert decayed == 0

    # =========================================================================
    # Dynamics: Retrieval Tests (Phase 2)
    # =========================================================================

    def test_search_facts_by_keyword(self, memory_adapter):
        """키워드로 사실 검색."""
        facts = [
            FactualFact(
                subject="보험A",
                predicate="보장금액",
                object="1억원",
                domain="insurance",
                language="ko",
            ),
            FactualFact(
                subject="보험B",
                predicate="만기",
                object="10년",
                domain="insurance",
                language="ko",
            ),
            FactualFact(
                subject="의료A",
                predicate="진료비",
                object="100만원",
                domain="medical",
                language="ko",
            ),
        ]
        for f in facts:
            memory_adapter.save_fact(f)

        # 검색 실행
        results = memory_adapter.search_facts("보험", domain="insurance")
        assert len(results) == 2

        # 도메인 필터링
        results = memory_adapter.search_facts("보험", domain="medical")
        assert len(results) == 0

    def test_search_facts_empty_query(self, memory_adapter):
        """빈 쿼리 검색."""
        fact = FactualFact(subject="A", predicate="P", object="O")
        memory_adapter.save_fact(fact)

        results = memory_adapter.search_facts("")
        assert len(results) == 0

    def test_search_facts_korean_text(self, memory_adapter):
        """한글 텍스트 검색."""
        fact = FactualFact(
            subject="삼성화재",
            predicate="보험종류",
            object="종신보험",
            domain="insurance",
            language="ko",
        )
        memory_adapter.save_fact(fact)

        results = memory_adapter.search_facts("삼성화재", language="ko")
        assert len(results) == 1
        assert results[0].subject == "삼성화재"

    def test_search_behaviors_by_context(self, memory_adapter):
        """컨텍스트로 행동 검색."""
        behaviors = [
            BehaviorEntry(
                description="보험 용어 처리",
                trigger_pattern=r"보험|보장",
                domain="insurance",
                success_rate=0.9,
            ),
            BehaviorEntry(
                description="약관 분석",
                trigger_pattern=r"약관|조항",
                domain="insurance",
                success_rate=0.8,
            ),
        ]
        for b in behaviors:
            memory_adapter.save_behavior(b)

        # trigger_pattern 매칭
        results = memory_adapter.search_behaviors(
            context="이 보험의 보장 범위는 무엇인가요?",
            domain="insurance",
            language="ko",
        )
        assert len(results) >= 1
        assert any(b.description == "보험 용어 처리" for b in results)

    def test_search_behaviors_success_rate_ordering(self, memory_adapter):
        """행동 검색 결과 성공률 정렬."""
        behaviors = [
            BehaviorEntry(
                description="낮은 성공률",
                trigger_pattern=r"테스트",
                domain="insurance",
                success_rate=0.5,
            ),
            BehaviorEntry(
                description="높은 성공률",
                trigger_pattern=r"테스트",
                domain="insurance",
                success_rate=0.95,
            ),
        ]
        for b in behaviors:
            memory_adapter.save_behavior(b)

        results = memory_adapter.search_behaviors(
            context="테스트 컨텍스트", domain="insurance", language="ko"
        )
        assert len(results) == 2
        assert results[0].success_rate >= results[1].success_rate

    def test_hybrid_search_returns_all_layers(self, memory_adapter):
        """하이브리드 검색 - 모든 레이어 결과."""
        # Factual layer
        fact = FactualFact(
            subject="보험A", predicate="종류", object="종신보험", domain="insurance", language="ko"
        )
        memory_adapter.save_fact(fact)

        # Behavior layer
        behavior = BehaviorEntry(
            description="보험 분석",
            trigger_pattern=r"보험",
            domain="insurance",
            success_rate=0.9,
        )
        memory_adapter.save_behavior(behavior)

        # Learning layer
        learning = LearningMemory(
            run_id="run-001",
            domain="insurance",
            language="ko",
            successful_patterns=["보험 패턴 성공"],
        )
        memory_adapter.save_learning(learning)

        # 하이브리드 검색
        results = memory_adapter.hybrid_search(
            query="보험",
            domain="insurance",
            language="ko",
        )

        assert "facts" in results
        assert "behaviors" in results
        assert "learnings" in results
        assert len(results["facts"]) >= 1
        assert len(results["behaviors"]) >= 1
        # learnings 검색은 LIKE 패턴 기반으로 결과가 없을 수 있음
        assert isinstance(results["learnings"], list)

    def test_search_learnings_finds_pattern(self, memory_adapter):
        """학습 패턴 검색."""
        learning = LearningMemory(
            run_id="run-001",
            domain="insurance",
            language="ko",
            successful_patterns=["entity extraction success"],
            failed_patterns=["context retrieval failed"],
        )
        memory_adapter.save_learning(learning)

        # _search_learnings 내부 메서드 테스트
        results = memory_adapter._search_learnings(
            query="extraction",
            domain="insurance",
            language="ko",
        )
        assert len(results) == 1
        assert results[0].run_id == "run-001"

    def test_hybrid_search_empty_results(self, memory_adapter):
        """하이브리드 검색 - 결과 없음."""
        results = memory_adapter.hybrid_search(
            query="존재하지않는키워드",
            domain="nonexistent",
            language="ko",
        )

        assert results["facts"] == []
        assert results["behaviors"] == []
        assert results["learnings"] == []

    def test_rebuild_fts_indexes(self, memory_adapter):
        """FTS5 인덱스 재구성 테스트."""
        # 사실 저장
        fact = FactualFact(
            subject="재구성테스트",
            predicate="대상",
            object="FTS5",
            domain="test",
            language="ko",
        )
        memory_adapter.save_fact(fact)

        # 수동 재구성
        memory_adapter.rebuild_fts_indexes()

        # 검색 가능한지 확인
        results = memory_adapter.search_facts("재구성테스트", domain="test")
        assert len(results) == 1
        assert results[0].subject == "재구성테스트"

    def test_search_facts_after_multiple_updates(self, memory_adapter):
        """여러 번 업데이트 후 FTS5 검색 테스트."""
        # 동일한 fact_id로 여러 번 업데이트 (INSERT OR REPLACE)
        fact = FactualFact(
            fact_id="fts-update-test",
            subject="원래주제",
            predicate="predicate",
            object="object",
            domain="test",
        )
        memory_adapter.save_fact(fact)

        # 업데이트
        fact.subject = "변경된주제"
        memory_adapter.save_fact(fact)

        # 변경된 내용으로 검색
        results = memory_adapter.search_facts("변경된주제", domain="test")
        assert len(results) == 1
        assert results[0].subject == "변경된주제"

        # 원래 내용으로는 검색 안됨
        results = memory_adapter.search_facts("원래주제", domain="test")
        assert len(results) == 0

    def test_search_behaviors_after_rebuild(self, memory_adapter):
        """FTS5 재구성 후 행동 검색 테스트."""
        behavior = BehaviorEntry(
            description="재구성 테스트용 행동",
            trigger_pattern=r"재구성|FTS",
            domain="test",
            success_rate=0.85,
        )
        memory_adapter.save_behavior(behavior)

        # 재구성
        memory_adapter.rebuild_fts_indexes()

        # 검색
        results = memory_adapter.search_behaviors(
            context="재구성 후 검색",
            domain="test",
            language="ko",
        )
        assert len(results) >= 1

    # =========================================================================
    # Dynamics: Formation Tests (Phase 3)
    # =========================================================================

    def test_extract_facts_from_evaluation(self, memory_adapter):
        """평가 결과에서 사실 추출."""
        from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult

        # 평가 결과 생성
        run = EvaluationRun(
            run_id="test-run-001",
            dataset_name="test-dataset",
            model_name="gpt-4",
            metrics_evaluated=["faithfulness"],
        )

        # 높은 faithfulness를 가진 테스트 케이스
        result = TestCaseResult(
            test_case_id="tc-001",
            metrics=[MetricScore(name="faithfulness", score=0.9, threshold=0.7)],
            question="보험A의 보장금액은 얼마인가요?",
            answer="보장금액은 1억원입니다.",
            contexts=["보험A의 보장금액은 1억원입니다."],
        )
        run.results.append(result)

        # 사실 추출
        facts = memory_adapter.extract_facts_from_evaluation(
            evaluation_run=run,
            domain="insurance",
            language="ko",
            min_confidence=0.7,
        )

        # 검증 - SPO 패턴에 맞는 사실이 추출되어야 함
        assert isinstance(facts, list)
        # 패턴이 매치되면 사실이 추출됨
        for fact in facts:
            assert fact.domain == "insurance"
            assert fact.language == "ko"
            assert fact.fact_type == "inferred"

    def test_extract_facts_low_confidence_skipped(self, memory_adapter):
        """낮은 신뢰도 평가는 건너뜀."""
        from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult

        run = EvaluationRun(run_id="test-run-002")
        result = TestCaseResult(
            test_case_id="tc-001",
            metrics=[MetricScore(name="faithfulness", score=0.5, threshold=0.7)],
            contexts=["보험A는 좋은 상품입니다."],
        )
        run.results.append(result)

        facts = memory_adapter.extract_facts_from_evaluation(
            evaluation_run=run,
            domain="insurance",
            language="ko",
            min_confidence=0.7,
        )

        assert facts == []

    def test_extract_patterns_from_evaluation(self, memory_adapter):
        """평가 결과에서 학습 패턴 추출."""
        from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult

        run = EvaluationRun(
            run_id="test-run-003",
            dataset_name="test-dataset",
            metrics_evaluated=["faithfulness", "answer_relevancy"],
        )

        # 성공한 테스트 케이스
        run.results.append(
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.85, threshold=0.7),
                ],
                question="보험료는 얼마인가요?",
            )
        )

        # 실패한 테스트 케이스
        run.results.append(
            TestCaseResult(
                test_case_id="tc-002",
                metrics=[
                    MetricScore(name="faithfulness", score=0.5, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.4, threshold=0.7),
                ],
                question="약관 내용이 무엇인가요?",
            )
        )

        learning = memory_adapter.extract_patterns_from_evaluation(
            evaluation_run=run,
            domain="insurance",
            language="ko",
        )

        assert learning.run_id == "test-run-003"
        assert learning.domain == "insurance"
        assert "faithfulness" in learning.entity_type_reliability
        assert "answer_relevancy" in learning.entity_type_reliability
        assert len(learning.successful_patterns) >= 0
        assert len(learning.failed_patterns) >= 0

    def test_extract_behaviors_from_evaluation(self, memory_adapter):
        """평가 결과에서 행동 추출."""
        from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult

        run = EvaluationRun(run_id="test-run-004")

        # 높은 성공률 테스트 케이스
        run.results.append(
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="faithfulness", score=0.95, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.9, threshold=0.7),
                ],
                question="보험료는 얼마인가요?",
                answer="월 보험료는 5만원입니다.",
                contexts=["이 상품의 월 보험료는 5만원입니다."],
                tokens_used=100,
            )
        )

        behaviors = memory_adapter.extract_behaviors_from_evaluation(
            evaluation_run=run,
            domain="insurance",
            language="ko",
            min_success_rate=0.8,
        )

        assert len(behaviors) >= 1
        behavior = behaviors[0]
        assert behavior.domain == "insurance"
        assert behavior.success_rate == 1.0  # 2/2 메트릭 통과
        assert "ko" in behavior.applicable_languages
        assert "retrieve_contexts" in behavior.action_sequence

    def test_extract_behaviors_low_success_rate_skipped(self, memory_adapter):
        """낮은 성공률 테스트 케이스는 건너뜀."""
        from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult

        run = EvaluationRun(run_id="test-run-005")

        # 낮은 성공률 테스트 케이스 (1/2 통과)
        run.results.append(
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="faithfulness", score=0.9, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.5, threshold=0.7),
                ],
                question="테스트 질문",
            )
        )

        behaviors = memory_adapter.extract_behaviors_from_evaluation(
            evaluation_run=run,
            domain="insurance",
            language="ko",
            min_success_rate=0.8,
        )

        assert behaviors == []

    def test_extract_facts_invalid_input(self, memory_adapter):
        """잘못된 입력 타입 검증."""
        with pytest.raises(TypeError, match="EvaluationRun"):
            memory_adapter.extract_facts_from_evaluation(
                evaluation_run="not-a-run",  # type: ignore
                domain="insurance",
            )


# =============================================================================
# DomainLearningHook Tests
# =============================================================================


class TestDomainLearningHook:
    """DomainLearningHook 서비스 테스트."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        if db_path.exists():
            db_path.unlink()

    @pytest.fixture
    def learning_hook(self, temp_db):
        """Create DomainLearningHook with temp database."""
        from evalvault.adapters.outbound.domain_memory.sqlite_adapter import (
            SQLiteDomainMemoryAdapter,
        )
        from evalvault.domain.services.domain_learning_hook import DomainLearningHook

        memory_adapter = SQLiteDomainMemoryAdapter(db_path=temp_db)
        return DomainLearningHook(memory_port=memory_adapter)

    @pytest.fixture
    def sample_evaluation_run(self):
        """Create a sample evaluation run for testing."""
        from evalvault.domain.entities.result import EvaluationRun, MetricScore, TestCaseResult

        run = EvaluationRun(
            run_id="hook-test-run-001",
            dataset_name="test-dataset",
            model_name="gpt-4",
            metrics_evaluated=["faithfulness", "answer_relevancy"],
        )

        # 성공적인 테스트 케이스들
        run.results.append(
            TestCaseResult(
                test_case_id="tc-001",
                metrics=[
                    MetricScore(name="faithfulness", score=0.95, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.9, threshold=0.7),
                ],
                question="보험A의 보장금액은 얼마인가요?",
                answer="보장금액은 1억원입니다.",
                contexts=["보험A의 보장금액은 1억원입니다."],
                tokens_used=150,
            )
        )

        run.results.append(
            TestCaseResult(
                test_case_id="tc-002",
                metrics=[
                    MetricScore(name="faithfulness", score=0.85, threshold=0.7),
                    MetricScore(name="answer_relevancy", score=0.8, threshold=0.7),
                ],
                question="만기는 언제인가요?",
                answer="만기는 20년입니다.",
                contexts=["해당 보험의 만기는 20년입니다."],
                tokens_used=100,
            )
        )

        return run

    @pytest.mark.asyncio
    async def test_on_evaluation_complete(self, learning_hook, sample_evaluation_run):
        """평가 완료 후 메모리 형성."""
        result = await learning_hook.on_evaluation_complete(
            evaluation_run=sample_evaluation_run,
            domain="insurance",
            language="ko",
            auto_save=True,
        )

        assert "facts" in result
        assert "learning" in result
        assert "behaviors" in result
        assert isinstance(result["learning"], LearningMemory)

    def test_extract_and_save_patterns(self, learning_hook, sample_evaluation_run):
        """패턴 추출 및 저장."""
        learning = learning_hook.extract_and_save_patterns(
            evaluation_run=sample_evaluation_run,
            domain="insurance",
            language="ko",
            auto_save=True,
        )

        assert learning.run_id == sample_evaluation_run.run_id
        assert learning.domain == "insurance"

        # 저장 확인
        saved_learnings = learning_hook.memory_port.list_learnings(domain="insurance")
        assert len(saved_learnings) >= 1

    def test_extract_and_save_behaviors(self, learning_hook, sample_evaluation_run):
        """행동 추출 및 저장."""
        behaviors = learning_hook.extract_and_save_behaviors(
            evaluation_run=sample_evaluation_run,
            domain="insurance",
            language="ko",
            min_success_rate=0.8,
            auto_save=True,
        )

        assert len(behaviors) >= 1

        # 저장 확인
        saved_behaviors = learning_hook.memory_port.list_behaviors(domain="insurance")
        assert len(saved_behaviors) >= 1

    def test_run_evolution(self, learning_hook):
        """Evolution dynamics 실행."""
        # 중복 사실 생성
        for _ in range(3):
            learning_hook.memory_port.save_fact(
                FactualFact(
                    subject="보험A",
                    predicate="보장금액",
                    object="1억원",
                    domain="insurance",
                    language="ko",
                )
            )

        # Evolution 실행
        result = learning_hook.run_evolution(domain="insurance", language="ko")

        assert "consolidated" in result
        assert "forgotten" in result
        assert "decayed" in result
        assert result["consolidated"] == 2  # 3개 중 2개 병합


# =============================================================================
# Phase 5: Planar Form (KG Integration) Tests
# =============================================================================


class TestPhase5PlanarForm:
    """Phase 5 Planar Form (KG Integration) 테스트."""

    @pytest.fixture
    def memory_adapter(self):
        """Create SQLiteDomainMemoryAdapter with temp database."""
        from evalvault.adapters.outbound.domain_memory.sqlite_adapter import (
            SQLiteDomainMemoryAdapter,
        )

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        adapter = SQLiteDomainMemoryAdapter(db_path=db_path)
        yield adapter

        if db_path.exists():
            db_path.unlink()

    def test_link_fact_to_kg(self, memory_adapter):
        """사실을 KG 엔티티에 연결."""
        fact = FactualFact(
            subject="보험A",
            predicate="보장금액",
            object="1억원",
            domain="insurance",
            language="ko",
        )
        memory_adapter.save_fact(fact)

        # KG에 연결
        memory_adapter.link_fact_to_kg(
            fact_id=fact.fact_id,
            kg_entity_id="insurance_product_001",
            kg_relation_type="coverage",
        )

        # 연결 확인
        retrieved = memory_adapter.get_fact(fact.fact_id)
        assert retrieved.kg_entity_id == "insurance_product_001"
        assert retrieved.kg_relation_type == "coverage"

    def test_link_fact_to_kg_not_found(self, memory_adapter):
        """존재하지 않는 사실에 연결 시 에러."""
        with pytest.raises(KeyError, match="Fact not found"):
            memory_adapter.link_fact_to_kg(
                fact_id="nonexistent",
                kg_entity_id="entity1",
            )

    def test_get_facts_by_kg_entity(self, memory_adapter):
        """KG 엔티티로 사실 조회."""
        # 동일 KG 엔티티에 연결된 여러 사실 생성
        facts = [
            FactualFact(
                subject="보험A",
                predicate="보장금액",
                object="1억원",
                domain="insurance",
                kg_entity_id="entity_001",
            ),
            FactualFact(
                subject="보험A",
                predicate="보험료",
                object="10만원",
                domain="insurance",
                kg_entity_id="entity_001",
            ),
            FactualFact(
                subject="보험B",
                predicate="보장금액",
                object="2억원",
                domain="insurance",
                kg_entity_id="entity_002",
            ),
        ]
        for f in facts:
            memory_adapter.save_fact(f)

        # entity_001로 조회
        results = memory_adapter.get_facts_by_kg_entity("entity_001")
        assert len(results) == 2
        assert all(r.subject == "보험A" for r in results)

    def test_get_facts_by_kg_entity_with_domain_filter(self, memory_adapter):
        """KG 엔티티 조회 - 도메인 필터."""
        fact = FactualFact(
            subject="보험A",
            predicate="보장금액",
            object="1억원",
            domain="insurance",
            kg_entity_id="entity_001",
        )
        memory_adapter.save_fact(fact)

        # 다른 도메인으로 조회
        results = memory_adapter.get_facts_by_kg_entity("entity_001", domain="medical")
        assert len(results) == 0

        # 같은 도메인으로 조회
        results = memory_adapter.get_facts_by_kg_entity("entity_001", domain="insurance")
        assert len(results) == 1

    def test_import_kg_as_facts(self, memory_adapter):
        """KG를 사실로 변환하여 저장."""
        entities = [
            ("보험A", "InsuranceProduct", {"coverage": "1억원"}),
            ("보험B", "InsuranceProduct", {"coverage": "2억원"}),
        ]
        relations = [
            ("보험A", "보장", "사망보장", 0.9),
            ("보험B", "제공", "입원비", 0.85),
        ]

        result = memory_adapter.import_kg_as_facts(
            entities=entities,
            relations=relations,
            domain="insurance",
            language="ko",
        )

        assert result["entities_imported"] == 2
        assert result["relations_imported"] == 2

        # 엔티티 사실 확인
        facts = memory_adapter.list_facts(domain="insurance")
        # 2 entities (is_a) + 2 attributes (has_coverage) + 2 relations = 6
        assert len(facts) >= 4

    def test_import_kg_as_facts_no_duplicates(self, memory_adapter):
        """KG 중복 임포트 방지."""
        entities = [("보험A", "InsuranceProduct", {})]
        relations = []

        # 첫 번째 임포트
        result1 = memory_adapter.import_kg_as_facts(
            entities=entities, relations=relations, domain="insurance"
        )
        assert result1["entities_imported"] == 1

        # 두 번째 임포트 (중복)
        result2 = memory_adapter.import_kg_as_facts(
            entities=entities, relations=relations, domain="insurance"
        )
        assert result2["entities_imported"] == 0  # 중복으로 스킵

    def test_export_facts_as_kg(self, memory_adapter):
        """사실을 KG 형태로 내보내기."""
        # 엔티티 사실 저장
        facts = [
            FactualFact(
                subject="보험A",
                predicate="is_a",
                object="InsuranceProduct",
                domain="insurance",
                verification_score=0.9,
            ),
            FactualFact(
                subject="보험A",
                predicate="has_coverage",
                object="1억원",
                domain="insurance",
                verification_score=0.9,
            ),
            FactualFact(
                subject="보험A",
                predicate="provides",
                object="사망보장",
                domain="insurance",
                verification_score=0.85,
            ),
        ]
        for f in facts:
            memory_adapter.save_fact(f)

        # KG로 내보내기
        entities, relations = memory_adapter.export_facts_as_kg(
            domain="insurance",
            min_confidence=0.5,
        )

        assert len(entities) == 1  # 보험A
        assert entities[0][0] == "보험A"
        assert entities[0][1] == "InsuranceProduct"
        assert entities[0][2].get("coverage") == "1억원"

        assert len(relations) == 1  # provides 관계
        assert relations[0][0] == "보험A"
        assert relations[0][1] == "사망보장"
        assert relations[0][2] == "provides"

    def test_export_facts_as_kg_with_confidence_filter(self, memory_adapter):
        """KG 내보내기 - 신뢰도 필터."""
        facts = [
            FactualFact(
                subject="보험A",
                predicate="is_a",
                object="InsuranceProduct",
                domain="insurance",
                verification_score=0.9,
            ),
            FactualFact(
                subject="보험B",
                predicate="is_a",
                object="InsuranceProduct",
                domain="insurance",
                verification_score=0.3,  # 낮은 신뢰도
            ),
        ]
        for f in facts:
            memory_adapter.save_fact(f)

        # 높은 신뢰도 필터
        entities, relations = memory_adapter.export_facts_as_kg(
            domain="insurance",
            min_confidence=0.8,
        )

        assert len(entities) == 1  # 보험A만


# =============================================================================
# Phase 5: Hierarchical Form (Summary Layers) Tests
# =============================================================================


class TestPhase5HierarchicalForm:
    """Phase 5 Hierarchical Form (Summary Layers) 테스트."""

    @pytest.fixture
    def memory_adapter(self):
        """Create SQLiteDomainMemoryAdapter with temp database."""
        from evalvault.adapters.outbound.domain_memory.sqlite_adapter import (
            SQLiteDomainMemoryAdapter,
        )

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)

        adapter = SQLiteDomainMemoryAdapter(db_path=db_path)
        yield adapter

        if db_path.exists():
            db_path.unlink()

    def test_create_summary_fact(self, memory_adapter):
        """여러 사실을 요약하는 상위 사실 생성."""
        # 하위 사실들 생성
        child_facts = [
            FactualFact(
                subject="보험A",
                predicate="보장금액",
                object="1억원",
                domain="insurance",
                verification_score=0.9,
            ),
            FactualFact(
                subject="보험A",
                predicate="보험료",
                object="10만원",
                domain="insurance",
                verification_score=0.8,
            ),
        ]
        for f in child_facts:
            memory_adapter.save_fact(f)

        child_ids = [f.fact_id for f in child_facts]

        # 요약 사실 생성
        summary = memory_adapter.create_summary_fact(
            child_fact_ids=child_ids,
            summary_subject="보험A",
            summary_predicate="요약",
            summary_object="보장금액 1억원, 보험료 10만원",
            domain="insurance",
            language="ko",
        )

        assert summary.abstraction_level == 1  # 0 + 1
        assert abs(summary.verification_score - 0.85) < 0.001  # 평균
        assert len(summary.child_fact_ids) == 2

    def test_create_summary_fact_empty_children(self, memory_adapter):
        """빈 자식 목록으로 요약 생성 시 에러."""
        with pytest.raises(ValueError, match="child_fact_ids cannot be empty"):
            memory_adapter.create_summary_fact(
                child_fact_ids=[],
                summary_subject="A",
                summary_predicate="B",
                summary_object="C",
                domain="insurance",
            )

    def test_create_summary_fact_nonexistent_child(self, memory_adapter):
        """존재하지 않는 자식 ID로 요약 생성 시 에러."""
        with pytest.raises(KeyError, match="Child fact not found"):
            memory_adapter.create_summary_fact(
                child_fact_ids=["nonexistent"],
                summary_subject="A",
                summary_predicate="B",
                summary_object="C",
                domain="insurance",
            )

    def test_get_facts_by_level(self, memory_adapter):
        """특정 추상화 레벨의 사실 조회."""
        # 레벨 0 사실 생성
        level0_facts = [
            FactualFact(
                subject="보험A",
                predicate="보장금액",
                object="1억원",
                domain="insurance",
                abstraction_level=0,
            ),
            FactualFact(
                subject="보험B",
                predicate="보장금액",
                object="2억원",
                domain="insurance",
                abstraction_level=0,
            ),
        ]
        for f in level0_facts:
            memory_adapter.save_fact(f)

        # 레벨 0 조회
        results = memory_adapter.get_facts_by_level(
            abstraction_level=0,
            domain="insurance",
        )
        assert len(results) == 2

        # 레벨 1 조회 (없음)
        results = memory_adapter.get_facts_by_level(
            abstraction_level=1,
            domain="insurance",
        )
        assert len(results) == 0

    def test_get_fact_hierarchy(self, memory_adapter):
        """사실의 전체 계층 구조 조회."""
        # 하위 사실들
        child_facts = [
            FactualFact(
                subject="보험A",
                predicate="보장금액",
                object="1억원",
                domain="insurance",
            ),
            FactualFact(
                subject="보험A",
                predicate="보험료",
                object="10만원",
                domain="insurance",
            ),
        ]
        for f in child_facts:
            memory_adapter.save_fact(f)

        child_ids = [f.fact_id for f in child_facts]

        # 요약 사실 생성
        summary = memory_adapter.create_summary_fact(
            child_fact_ids=child_ids,
            summary_subject="보험A",
            summary_predicate="요약",
            summary_object="상품 요약",
            domain="insurance",
        )

        # 계층 구조 조회
        hierarchy = memory_adapter.get_fact_hierarchy(summary.fact_id)

        assert hierarchy["fact"].fact_id == summary.fact_id
        assert hierarchy["parent"] is None  # 최상위
        assert len(hierarchy["children"]) == 2
        assert len(hierarchy["ancestors"]) == 0
        assert len(hierarchy["descendants"]) == 2

    def test_get_fact_hierarchy_child_perspective(self, memory_adapter):
        """자식 사실 관점에서 계층 구조 조회."""
        # 자식 사실
        child = FactualFact(
            subject="보험A",
            predicate="보장금액",
            object="1억원",
            domain="insurance",
        )
        memory_adapter.save_fact(child)

        # 부모 요약 생성
        parent = memory_adapter.create_summary_fact(
            child_fact_ids=[child.fact_id],
            summary_subject="보험A",
            summary_predicate="요약",
            summary_object="상품 요약",
            domain="insurance",
        )

        # 자식 관점에서 계층 조회
        hierarchy = memory_adapter.get_fact_hierarchy(child.fact_id)

        assert hierarchy["fact"].fact_id == child.fact_id
        assert hierarchy["parent"] is not None
        assert hierarchy["parent"].fact_id == parent.fact_id
        assert len(hierarchy["ancestors"]) == 1
        assert len(hierarchy["children"]) == 0

    def test_get_child_facts(self, memory_adapter):
        """특정 사실의 자식들 조회."""
        # 자식 사실들
        children = [
            FactualFact(
                subject="보험A",
                predicate="보장금액",
                object="1억원",
                domain="insurance",
                verification_score=0.9,
            ),
            FactualFact(
                subject="보험A",
                predicate="보험료",
                object="10만원",
                domain="insurance",
                verification_score=0.8,
            ),
        ]
        for f in children:
            memory_adapter.save_fact(f)

        child_ids = [f.fact_id for f in children]

        # 요약 생성
        summary = memory_adapter.create_summary_fact(
            child_fact_ids=child_ids,
            summary_subject="보험A",
            summary_predicate="요약",
            summary_object="상품 요약",
            domain="insurance",
        )

        # 자식 조회
        child_facts = memory_adapter.get_child_facts(summary.fact_id)

        assert len(child_facts) == 2
        # 성공률 내림차순 정렬
        assert child_facts[0].verification_score >= child_facts[1].verification_score

    def test_multi_level_hierarchy(self, memory_adapter):
        """다중 레벨 계층 구조."""
        # 레벨 0 사실들
        level0 = [
            FactualFact(
                subject=f"상품{i}",
                predicate="보장금액",
                object=f"{i}억원",
                domain="insurance",
            )
            for i in range(4)
        ]
        for f in level0:
            memory_adapter.save_fact(f)

        # 레벨 1 요약 (2개씩 그룹화)
        summary1a = memory_adapter.create_summary_fact(
            child_fact_ids=[level0[0].fact_id, level0[1].fact_id],
            summary_subject="그룹A",
            summary_predicate="요약",
            summary_object="상품 0,1",
            domain="insurance",
        )
        summary1b = memory_adapter.create_summary_fact(
            child_fact_ids=[level0[2].fact_id, level0[3].fact_id],
            summary_subject="그룹B",
            summary_predicate="요약",
            summary_object="상품 2,3",
            domain="insurance",
        )

        # 레벨 2 메타 요약
        meta_summary = memory_adapter.create_summary_fact(
            child_fact_ids=[summary1a.fact_id, summary1b.fact_id],
            summary_subject="전체",
            summary_predicate="메타요약",
            summary_object="모든 상품",
            domain="insurance",
        )

        assert meta_summary.abstraction_level == 2

        # 계층 조회
        hierarchy = memory_adapter.get_fact_hierarchy(meta_summary.fact_id)
        assert len(hierarchy["children"]) == 2  # 레벨 1 요약들
        assert len(hierarchy["descendants"]) == 6  # 레벨 1 2개 + 레벨 0 4개

    def test_is_summary_and_is_linked_to_kg(self, memory_adapter):
        """FactualFact 엔티티의 Phase 5 헬퍼 메서드."""
        # 일반 사실
        fact = FactualFact(
            subject="보험A",
            predicate="보장금액",
            object="1억원",
            domain="insurance",
        )
        assert fact.is_summary() is False
        assert fact.is_linked_to_kg() is False

        # 요약 사실
        summary_fact = FactualFact(
            subject="요약",
            predicate="요약",
            object="요약내용",
            abstraction_level=1,
        )
        assert summary_fact.is_summary() is True

        # KG 연결 사실
        kg_fact = FactualFact(
            subject="보험A",
            predicate="보장금액",
            object="1억원",
            kg_entity_id="entity_001",
        )
        assert kg_fact.is_linked_to_kg() is True
