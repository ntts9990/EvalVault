"""SQLite adapter for Domain Memory storage.

Based on "Memory in the Age of AI Agents: A Survey" framework:
- Phase 1: Basic CRUD for Factual, Experiential, Working layers
- Phase 2: Evolution dynamics (consolidate, forget, decay)
- Phase 3: Formation dynamics (extraction from evaluations)
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from evalvault.domain.entities.memory import (
    BehaviorEntry,
    BehaviorHandbook,
    DomainMemoryContext,
    FactualFact,
    LearningMemory,
)


class SQLiteDomainMemoryAdapter:
    """SQLite 기반 도메인 메모리 저장 어댑터.

    Implements DomainMemoryPort using SQLite for local persistence.
    """

    def __init__(self, db_path: str | Path = "evalvault_memory.db"):
        """Initialize SQLite domain memory adapter.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "domain_memory_schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # =========================================================================
    # Factual Layer - 검증된 사실 저장 (Phase 1)
    # =========================================================================

    def save_fact(self, fact: FactualFact) -> str:
        """사실을 저장합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO factual_facts (
                    fact_id, subject, predicate, object, language, domain,
                    fact_type, verification_score, verification_count,
                    source_document_ids, created_at, last_verified
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fact.fact_id,
                    fact.subject,
                    fact.predicate,
                    fact.object,
                    fact.language,
                    fact.domain,
                    fact.fact_type,
                    fact.verification_score,
                    fact.verification_count,
                    json.dumps(fact.source_document_ids),
                    fact.created_at.isoformat(),
                    fact.last_verified.isoformat() if fact.last_verified else None,
                ),
            )
            conn.commit()
            return fact.fact_id
        finally:
            conn.close()

    def get_fact(self, fact_id: str) -> FactualFact:
        """사실을 조회합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT fact_id, subject, predicate, object, language, domain,
                       fact_type, verification_score, verification_count,
                       source_document_ids, created_at, last_verified
                FROM factual_facts WHERE fact_id = ?
                """,
                (fact_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Fact not found: {fact_id}")

            return self._row_to_fact(row)
        finally:
            conn.close()

    def _row_to_fact(self, row: tuple) -> FactualFact:
        """Convert database row to FactualFact."""
        return FactualFact(
            fact_id=row[0],
            subject=row[1],
            predicate=row[2],
            object=row[3],
            language=row[4],
            domain=row[5],
            fact_type=row[6],
            verification_score=row[7],
            verification_count=row[8],
            source_document_ids=json.loads(row[9]) if row[9] else [],
            created_at=datetime.fromisoformat(row[10]),
            last_verified=datetime.fromisoformat(row[11]) if row[11] else None,
        )

    def list_facts(
        self,
        domain: str | None = None,
        language: str | None = None,
        subject: str | None = None,
        predicate: str | None = None,
        limit: int = 100,
    ) -> list[FactualFact]:
        """사실 목록을 조회합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT fact_id, subject, predicate, object, language, domain,
                       fact_type, verification_score, verification_count,
                       source_document_ids, created_at, last_verified
                FROM factual_facts WHERE 1=1
            """
            params: list = []

            if domain:
                query += " AND domain = ?"
                params.append(domain)
            if language:
                query += " AND language = ?"
                params.append(language)
            if subject:
                query += " AND subject = ?"
                params.append(subject)
            if predicate:
                query += " AND predicate = ?"
                params.append(predicate)

            query += " ORDER BY last_verified DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [self._row_to_fact(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update_fact(self, fact: FactualFact) -> None:
        """사실을 업데이트합니다."""
        self.save_fact(fact)

    def delete_fact(self, fact_id: str) -> bool:
        """사실을 삭제합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM factual_facts WHERE fact_id = ?", (fact_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

    def find_fact_by_triple(
        self,
        subject: str,
        predicate: str,
        obj: str,
        domain: str | None = None,
    ) -> FactualFact | None:
        """SPO 트리플로 사실을 검색합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT fact_id, subject, predicate, object, language, domain,
                       fact_type, verification_score, verification_count,
                       source_document_ids, created_at, last_verified
                FROM factual_facts
                WHERE subject = ? AND predicate = ? AND object = ?
            """
            params: list = [subject, predicate, obj]

            if domain:
                query += " AND domain = ?"
                params.append(domain)

            cursor.execute(query, params)
            row = cursor.fetchone()

            return self._row_to_fact(row) if row else None
        finally:
            conn.close()

    # =========================================================================
    # Experiential Layer - 학습된 패턴 (Phase 1)
    # =========================================================================

    def save_learning(self, learning: LearningMemory) -> str:
        """학습 메모리를 저장합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO learning_memories (
                    learning_id, run_id, domain, language,
                    entity_type_reliability, relation_type_reliability,
                    failed_patterns, successful_patterns,
                    faithfulness_by_entity_type, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    learning.learning_id,
                    learning.run_id,
                    learning.domain,
                    learning.language,
                    json.dumps(learning.entity_type_reliability),
                    json.dumps(learning.relation_type_reliability),
                    json.dumps(learning.failed_patterns),
                    json.dumps(learning.successful_patterns),
                    json.dumps(learning.faithfulness_by_entity_type),
                    learning.timestamp.isoformat(),
                ),
            )
            conn.commit()
            return learning.learning_id
        finally:
            conn.close()

    def get_learning(self, learning_id: str) -> LearningMemory:
        """학습 메모리를 조회합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT learning_id, run_id, domain, language,
                       entity_type_reliability, relation_type_reliability,
                       failed_patterns, successful_patterns,
                       faithfulness_by_entity_type, timestamp
                FROM learning_memories WHERE learning_id = ?
                """,
                (learning_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Learning not found: {learning_id}")

            return self._row_to_learning(row)
        finally:
            conn.close()

    def _row_to_learning(self, row: tuple) -> LearningMemory:
        """Convert database row to LearningMemory."""
        return LearningMemory(
            learning_id=row[0],
            run_id=row[1],
            domain=row[2],
            language=row[3],
            entity_type_reliability=json.loads(row[4]) if row[4] else {},
            relation_type_reliability=json.loads(row[5]) if row[5] else {},
            failed_patterns=json.loads(row[6]) if row[6] else [],
            successful_patterns=json.loads(row[7]) if row[7] else [],
            faithfulness_by_entity_type=json.loads(row[8]) if row[8] else {},
            timestamp=datetime.fromisoformat(row[9]),
        )

    def list_learnings(
        self,
        domain: str | None = None,
        language: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> list[LearningMemory]:
        """학습 메모리 목록을 조회합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT learning_id, run_id, domain, language,
                       entity_type_reliability, relation_type_reliability,
                       failed_patterns, successful_patterns,
                       faithfulness_by_entity_type, timestamp
                FROM learning_memories WHERE 1=1
            """
            params: list = []

            if domain:
                query += " AND domain = ?"
                params.append(domain)
            if language:
                query += " AND language = ?"
                params.append(language)
            if run_id:
                query += " AND run_id = ?"
                params.append(run_id)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [self._row_to_learning(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_aggregated_reliability(
        self,
        domain: str,
        language: str,
    ) -> dict[str, float]:
        """도메인/언어별 집계된 엔티티 타입 신뢰도를 조회합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT entity_type_reliability
                FROM learning_memories
                WHERE domain = ? AND language = ?
                ORDER BY timestamp DESC
                """,
                (domain, language),
            )
            rows = cursor.fetchall()

            if not rows:
                return {}

            # 엔티티 타입별 점수 집계
            aggregated: dict[str, list[float]] = {}
            for row in rows:
                reliability = json.loads(row[0]) if row[0] else {}
                for entity_type, score in reliability.items():
                    if entity_type not in aggregated:
                        aggregated[entity_type] = []
                    aggregated[entity_type].append(score)

            # 평균 계산
            return {
                entity_type: sum(scores) / len(scores) for entity_type, scores in aggregated.items()
            }
        finally:
            conn.close()

    # =========================================================================
    # Behavior Layer - Metacognitive Reuse (Phase 1)
    # =========================================================================

    def save_behavior(self, behavior: BehaviorEntry) -> str:
        """행동 엔트리를 저장합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO behavior_entries (
                    behavior_id, description, trigger_pattern, action_sequence,
                    success_rate, token_savings, applicable_languages, domain,
                    last_used, use_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    behavior.behavior_id,
                    behavior.description,
                    behavior.trigger_pattern,
                    json.dumps(behavior.action_sequence),
                    behavior.success_rate,
                    behavior.token_savings,
                    json.dumps(behavior.applicable_languages),
                    behavior.domain,
                    behavior.last_used.isoformat(),
                    behavior.use_count,
                    behavior.created_at.isoformat(),
                ),
            )
            conn.commit()
            return behavior.behavior_id
        finally:
            conn.close()

    def get_behavior(self, behavior_id: str) -> BehaviorEntry:
        """행동 엔트리를 조회합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT behavior_id, description, trigger_pattern, action_sequence,
                       success_rate, token_savings, applicable_languages, domain,
                       last_used, use_count, created_at
                FROM behavior_entries WHERE behavior_id = ?
                """,
                (behavior_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Behavior not found: {behavior_id}")

            return self._row_to_behavior(row)
        finally:
            conn.close()

    def _row_to_behavior(self, row: tuple) -> BehaviorEntry:
        """Convert database row to BehaviorEntry."""
        return BehaviorEntry(
            behavior_id=row[0],
            description=row[1],
            trigger_pattern=row[2] or "",
            action_sequence=json.loads(row[3]) if row[3] else [],
            success_rate=row[4],
            token_savings=row[5],
            applicable_languages=json.loads(row[6]) if row[6] else ["ko", "en"],
            domain=row[7],
            last_used=datetime.fromisoformat(row[8]),
            use_count=row[9],
            created_at=datetime.fromisoformat(row[10]),
        )

    def list_behaviors(
        self,
        domain: str | None = None,
        language: str | None = None,
        min_success_rate: float = 0.0,
        limit: int = 100,
    ) -> list[BehaviorEntry]:
        """행동 엔트리 목록을 조회합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT behavior_id, description, trigger_pattern, action_sequence,
                       success_rate, token_savings, applicable_languages, domain,
                       last_used, use_count, created_at
                FROM behavior_entries
                WHERE success_rate >= ?
            """
            params: list = [min_success_rate]

            if domain:
                query += " AND domain = ?"
                params.append(domain)

            query += " ORDER BY success_rate DESC, use_count DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            behaviors = [self._row_to_behavior(row) for row in rows]

            # 언어 필터링 (applicable_languages 필드 체크)
            if language:
                behaviors = [b for b in behaviors if b.is_applicable(language)]

            return behaviors
        finally:
            conn.close()

    def get_handbook(self, domain: str) -> BehaviorHandbook:
        """도메인별 행동 핸드북을 조회합니다."""
        behaviors = self.list_behaviors(domain=domain, limit=1000)
        handbook = BehaviorHandbook(domain=domain, behaviors=behaviors)
        return handbook

    def update_behavior(self, behavior: BehaviorEntry) -> None:
        """행동 엔트리를 업데이트합니다."""
        self.save_behavior(behavior)

    # =========================================================================
    # Working Layer - 세션 컨텍스트 (Phase 1)
    # =========================================================================

    def save_context(self, context: DomainMemoryContext) -> str:
        """워킹 메모리 컨텍스트를 저장합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO memory_contexts (
                    session_id, domain, language, active_entities,
                    entity_type_distribution, current_quality_metrics,
                    started_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    context.session_id,
                    context.domain,
                    context.language,
                    json.dumps(list(context.active_entities)),
                    json.dumps(context.entity_type_distribution),
                    json.dumps(context.current_quality_metrics),
                    context.started_at.isoformat(),
                    context.updated_at.isoformat(),
                ),
            )
            conn.commit()
            return context.session_id
        finally:
            conn.close()

    def get_context(self, session_id: str) -> DomainMemoryContext:
        """워킹 메모리 컨텍스트를 조회합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT session_id, domain, language, active_entities,
                       entity_type_distribution, current_quality_metrics,
                       started_at, updated_at
                FROM memory_contexts WHERE session_id = ?
                """,
                (session_id,),
            )
            row = cursor.fetchone()

            if not row:
                raise KeyError(f"Context not found: {session_id}")

            return DomainMemoryContext(
                session_id=row[0],
                domain=row[1],
                language=row[2],
                active_entities=set(json.loads(row[3])) if row[3] else set(),
                entity_type_distribution=json.loads(row[4]) if row[4] else {},
                current_quality_metrics=json.loads(row[5]) if row[5] else {},
                started_at=datetime.fromisoformat(row[6]),
                updated_at=datetime.fromisoformat(row[7]),
            )
        finally:
            conn.close()

    def update_context(self, context: DomainMemoryContext) -> None:
        """워킹 메모리 컨텍스트를 업데이트합니다."""
        self.save_context(context)

    def delete_context(self, session_id: str) -> bool:
        """워킹 메모리 컨텍스트를 삭제합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM memory_contexts WHERE session_id = ?", (session_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_statistics(self, domain: str | None = None) -> dict[str, int]:
        """메모리 통계를 조회합니다."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            domain_filter = " WHERE domain = ?" if domain else ""
            params = [domain] if domain else []

            # 각 테이블별 카운트
            cursor.execute(f"SELECT COUNT(*) FROM factual_facts{domain_filter}", params)
            facts_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM learning_memories{domain_filter}", params)
            learnings_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM behavior_entries{domain_filter}", params)
            behaviors_count = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM memory_contexts{domain_filter}", params)
            contexts_count = cursor.fetchone()[0]

            return {
                "facts": facts_count,
                "learnings": learnings_count,
                "behaviors": behaviors_count,
                "contexts": contexts_count,
            }
        finally:
            conn.close()

    # =========================================================================
    # Dynamics: Evolution - Phase 2 (Not Implemented)
    # =========================================================================

    def consolidate_facts(self, domain: str, language: str) -> int:
        """유사한 사실들을 통합합니다. (Phase 2)"""
        raise NotImplementedError("consolidate_facts will be implemented in Phase 2")

    def resolve_conflict(self, fact1: FactualFact, fact2: FactualFact) -> FactualFact:
        """충돌하는 사실을 해결합니다. (Phase 2)"""
        raise NotImplementedError("resolve_conflict will be implemented in Phase 2")

    def forget_obsolete(
        self,
        domain: str,
        max_age_days: int = 90,
        min_verification_count: int = 1,
        min_verification_score: float = 0.3,
    ) -> int:
        """오래되거나 신뢰도 낮은 메모리를 삭제합니다. (Phase 2)"""
        raise NotImplementedError("forget_obsolete will be implemented in Phase 2")

    def decay_verification_scores(self, domain: str, decay_rate: float = 0.95) -> int:
        """시간에 따라 검증 점수를 감소시킵니다. (Phase 2)"""
        raise NotImplementedError("decay_verification_scores will be implemented in Phase 2")

    # =========================================================================
    # Dynamics: Retrieval - Phase 2 (Not Implemented)
    # =========================================================================

    def search_facts(
        self,
        query: str,
        domain: str | None = None,
        language: str | None = None,
        limit: int = 10,
    ) -> list[FactualFact]:
        """키워드 기반 사실 검색. (Phase 2)"""
        raise NotImplementedError("search_facts will be implemented in Phase 2")

    def search_behaviors(
        self,
        context: str,
        domain: str,
        language: str,
        limit: int = 5,
    ) -> list[BehaviorEntry]:
        """컨텍스트 기반 행동 검색. (Phase 2)"""
        raise NotImplementedError("search_behaviors will be implemented in Phase 2")

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
        """하이브리드 메모리 검색. (Phase 2)"""
        raise NotImplementedError("hybrid_search will be implemented in Phase 2")

    # =========================================================================
    # Dynamics: Formation - Phase 3 (Not Implemented)
    # =========================================================================

    def extract_facts_from_evaluation(
        self, run_id: str, min_confidence: float = 0.7
    ) -> list[FactualFact]:
        """평가 결과에서 사실을 추출합니다. (Phase 3)"""
        raise NotImplementedError("extract_facts_from_evaluation will be implemented in Phase 3")

    def extract_patterns_from_evaluation(self, run_id: str) -> LearningMemory:
        """평가 결과에서 학습 패턴을 추출합니다. (Phase 3)"""
        raise NotImplementedError("extract_patterns_from_evaluation will be implemented in Phase 3")

    def extract_behaviors_from_evaluation(
        self, run_id: str, min_success_rate: float = 0.8
    ) -> list[BehaviorEntry]:
        """평가 결과에서 재사용 가능한 행동을 추출합니다. (Phase 3)"""
        raise NotImplementedError(
            "extract_behaviors_from_evaluation will be implemented in Phase 3"
        )
