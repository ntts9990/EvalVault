"""PostgreSQL adapter for Domain Memory storage.

Based on "Memory in the Age of AI Agents: A Survey" framework:
- Phase 1: Basic CRUD for Factual, Experiential, Working layers
- Phase 2: Evolution dynamics (consolidate, forget, decay)
- Phase 3: Formation dynamics (extraction from evaluations)
- Phase 5: Forms expansion (Planar/Hierarchical)
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path

import psycopg

from evalvault.domain.entities.memory import (
    BehaviorEntry,
    BehaviorHandbook,
    DomainMemoryContext,
    FactualFact,
    LearningMemory,
)

logger = logging.getLogger(__name__)


def _coerce_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


class PostgresDomainMemoryAdapter:
    """PostgreSQL 기반 도메인 메모리 저장 어댑터.

    Implements DomainMemoryPort using PostgreSQL for persistent storage.
    """

    def __init__(self, connection_string: str | None = None):
        """Initialize PostgreSQL domain memory adapter.

        Args:
            connection_string: PostgreSQL connection string
                (e.g., "host=localhost port=5432 dbname=evalvault user=postgres password=...")
        """
        self.connection_string = connection_string or (
            "host=localhost port=5432 dbname=evalvault user=postgres password="
        )
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        schema_path = Path(__file__).parent / "postgres_domain_memory_schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema_sql = f.read()

        try:
            with psycopg.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
                conn.commit()
        except psycopg.Error as e:
            logger.error("Failed to initialize PostgreSQL schema: %s", e)
            raise

    def _get_connection(self) -> psycopg.Connection:
        """Get a database connection."""
        return psycopg.connect(self.connection_string)

    def _row_to_fact(self, row: tuple) -> FactualFact:
        """Convert database row to FactualFact."""
        fact_id = row[0]
        abstraction_level = row[12] if len(row) > 12 else 0

        return FactualFact(
            fact_id=fact_id,
            subject=row[1],
            predicate=row[2],
            object=row[3],
            language=row[4],
            domain=row[5],
            fact_type=row[6],
            verification_score=row[7],
            verification_count=row[8],
            source_document_ids=json.loads(row[9]) if row[9] else [],
            created_at=_coerce_datetime(row[10]),
            last_verified=_coerce_datetime(row[11]) if row[11] else None,
            abstraction_level=abstraction_level,
        )

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
            timestamp=_coerce_datetime(row[9]),
        )

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
            last_used=_coerce_datetime(row[8]),
            use_count=row[9],
            created_at=_coerce_datetime(row[10]),
        )

    def save_fact(self, fact: FactualFact) -> str:
        """사실을 저장합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO factual_facts (
                        fact_id, subject, predicate, object, language, domain,
                        fact_type, verification_score, verification_count,
                        source_document_ids, created_at, last_verified, abstraction_level
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (fact_id) DO UPDATE SET
                        subject = EXCLUDED.subject,
                        predicate = EXCLUDED.predicate,
                        object = EXCLUDED.object,
                        language = EXCLUDED.language,
                        domain = EXCLUDED.domain,
                        fact_type = EXCLUDED.fact_type,
                        verification_score = EXCLUDED.verification_score,
                        verification_count = EXCLUDED.verification_count,
                        source_document_ids = EXCLUDED.source_document_ids,
                        last_verified = EXCLUDED.last_verified,
                        abstraction_level = EXCLUDED.abstraction_level
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
                        fact.abstraction_level,
                    ),
                )

                if fact.kg_entity_id:
                    cur.execute(
                        """
                        INSERT INTO fact_kg_bindings (fact_id, kg_entity_id, kg_relation_type)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (fact_id, kg_entity_id) DO UPDATE SET
                            kg_relation_type = EXCLUDED.kg_relation_type
                        """,
                        (fact.fact_id, fact.kg_entity_id, fact.kg_relation_type),
                    )

                if fact.parent_fact_id:
                    cur.execute(
                        """
                        INSERT INTO fact_hierarchy (parent_fact_id, child_fact_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (fact.parent_fact_id, fact.fact_id),
                    )

            conn.commit()
            return fact.fact_id
        finally:
            conn.close()

    def get_fact(self, fact_id: str) -> FactualFact:
        """사실을 조회합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_id, subject, predicate, object, language, domain,
                           fact_type, verification_score, verification_count,
                           source_document_ids, created_at, last_verified, abstraction_level
                    FROM factual_facts WHERE fact_id = %s
                    """,
                    (fact_id,),
                )
                row = cur.fetchone()

                if not row:
                    raise KeyError(f"Fact not found: {fact_id}")

                return self._row_to_fact(row)
        finally:
            conn.close()

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
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT fact_id, subject, predicate, object, language, domain,
                           fact_type, verification_score, verification_count,
                           source_document_ids, created_at, last_verified, abstraction_level
                    FROM factual_facts WHERE 1=1
                """
                params: list = []

                if domain:
                    query += " AND domain = %s"
                    params.append(domain)
                if language:
                    query += " AND language = %s"
                    params.append(language)
                if subject:
                    query += " AND subject = %s"
                    params.append(subject)
                if predicate:
                    query += " AND predicate = %s"
                    params.append(predicate)

                query += " ORDER BY last_verified DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)
                return [self._row_to_fact(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def update_fact(self, fact: FactualFact) -> None:
        """사실을 업데이트합니다."""
        self.save_fact(fact)

    def delete_fact(self, fact_id: str) -> bool:
        """사실을 삭제합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM factual_facts WHERE fact_id = %s", (fact_id,))
                deleted = cur.rowcount > 0
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
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT fact_id, subject, predicate, object, language, domain,
                           fact_type, verification_score, verification_count,
                           source_document_ids, created_at, last_verified, abstraction_level
                    FROM factual_facts
                    WHERE subject = %s AND predicate = %s AND object = %s
                """
                params: list = [subject, predicate, obj]

                if domain:
                    query += " AND domain = %s"
                    params.append(domain)

                cur.execute(query, params)
                row = cur.fetchone()

                return self._row_to_fact(row) if row else None
        finally:
            conn.close()

    def save_learning(self, learning: LearningMemory) -> str:
        """학습 메모리를 저장합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO learning_memories (
                        learning_id, run_id, domain, language,
                        entity_type_reliability, relation_type_reliability,
                        failed_patterns, successful_patterns,
                        faithfulness_by_entity_type, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (learning_id) DO UPDATE SET
                        run_id = EXCLUDED.run_id,
                        domain = EXCLUDED.domain,
                        language = EXCLUDED.language,
                        entity_type_reliability = EXCLUDED.entity_type_reliability,
                        relation_type_reliability = EXCLUDED.relation_type_reliability,
                        failed_patterns = EXCLUDED.failed_patterns,
                        successful_patterns = EXCLUDED.successful_patterns,
                        faithfulness_by_entity_type = EXCLUDED.faithfulness_by_entity_type,
                        timestamp = EXCLUDED.timestamp
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
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT learning_id, run_id, domain, language,
                           entity_type_reliability, relation_type_reliability,
                           failed_patterns, successful_patterns,
                           faithfulness_by_entity_type, timestamp
                    FROM learning_memories WHERE learning_id = %s
                    """,
                    (learning_id,),
                )
                row = cur.fetchone()

                if not row:
                    raise KeyError(f"Learning not found: {learning_id}")

                return self._row_to_learning(row)
        finally:
            conn.close()

    def list_learnings(
        self,
        domain: str | None = None,
        language: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
    ) -> list[LearningMemory]:
        """학습 메모리 목록을 조회합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT learning_id, run_id, domain, language,
                           entity_type_reliability, relation_type_reliability,
                           failed_patterns, successful_patterns,
                           faithfulness_by_entity_type, timestamp
                    FROM learning_memories WHERE 1=1
                """
                params: list = []

                if domain:
                    query += " AND domain = %s"
                    params.append(domain)
                if language:
                    query += " AND language = %s"
                    params.append(language)
                if run_id:
                    query += " AND run_id = %s"
                    params.append(run_id)

                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)
                return [self._row_to_learning(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def get_aggregated_reliability(
        self,
        domain: str,
        language: str,
    ) -> dict[str, float]:
        """도메인/언어별 집계된 엔티티 타입 신뢰도를 조회합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT entity_type_reliability
                    FROM learning_memories
                    WHERE domain = %s AND language = %s
                    ORDER BY timestamp DESC
                    """,
                    (domain, language),
                )
                rows = cur.fetchall()

                if not rows:
                    return {}

                aggregated: dict[str, list[float]] = {}
                for row in rows:
                    reliability = json.loads(row[0]) if row[0] else {}
                    for entity_type, score in reliability.items():
                        if entity_type not in aggregated:
                            aggregated[entity_type] = []
                        aggregated[entity_type].append(score)

                return {
                    entity_type: sum(scores) / len(scores)
                    for entity_type, scores in aggregated.items()
                }
        finally:
            conn.close()

    def save_behavior(self, behavior: BehaviorEntry) -> str:
        """행동 엔트리를 저장합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO behavior_entries (
                        behavior_id, description, trigger_pattern, action_sequence,
                        success_rate, token_savings, applicable_languages, domain,
                        last_used, use_count, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (behavior_id) DO UPDATE SET
                        description = EXCLUDED.description,
                        trigger_pattern = EXCLUDED.trigger_pattern,
                        action_sequence = EXCLUDED.action_sequence,
                        success_rate = EXCLUDED.success_rate,
                        token_savings = EXCLUDED.token_savings,
                        applicable_languages = EXCLUDED.applicable_languages,
                        domain = EXCLUDED.domain,
                        last_used = EXCLUDED.last_used,
                        use_count = EXCLUDED.use_count,
                        created_at = EXCLUDED.created_at
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
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT behavior_id, description, trigger_pattern, action_sequence,
                           success_rate, token_savings, applicable_languages, domain,
                           last_used, use_count, created_at
                    FROM behavior_entries WHERE behavior_id = %s
                    """,
                    (behavior_id,),
                )
                row = cur.fetchone()

                if not row:
                    raise KeyError(f"Behavior not found: {behavior_id}")

                return self._row_to_behavior(row)
        finally:
            conn.close()

    def list_behaviors(
        self,
        domain: str | None = None,
        language: str | None = None,
        min_success_rate: float = 0.0,
        limit: int = 100,
    ) -> list[BehaviorEntry]:
        """행동 엔트리 목록을 조회합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT behavior_id, description, trigger_pattern, action_sequence,
                           success_rate, token_savings, applicable_languages, domain,
                           last_used, use_count, created_at
                    FROM behavior_entries
                    WHERE success_rate >= %s
                """
                params: list = [min_success_rate]

                if domain:
                    query += " AND domain = %s"
                    params.append(domain)

                query += " ORDER BY success_rate DESC, use_count DESC LIMIT %s"
                params.append(limit)

                cur.execute(query, params)
                rows = cur.fetchall()

                behaviors = [self._row_to_behavior(row) for row in rows]

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

    def save_context(self, context: DomainMemoryContext) -> str:
        """워킹 메모리 컨텍스트를 저장합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO memory_contexts (
                        session_id, domain, language, active_entities,
                        entity_type_distribution, current_quality_metrics,
                        started_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        domain = EXCLUDED.domain,
                        language = EXCLUDED.language,
                        active_entities = EXCLUDED.active_entities,
                        entity_type_distribution = EXCLUDED.entity_type_distribution,
                        current_quality_metrics = EXCLUDED.current_quality_metrics,
                        updated_at = EXCLUDED.updated_at
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
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT session_id, domain, language, active_entities,
                           entity_type_distribution, current_quality_metrics,
                           started_at, updated_at
                    FROM memory_contexts WHERE session_id = %s
                    """,
                    (session_id,),
                )
                row = cur.fetchone()

                if not row:
                    raise KeyError(f"Context not found: {session_id}")

                return DomainMemoryContext(
                    session_id=row[0],
                    domain=row[1],
                    language=row[2],
                    active_entities=set(json.loads(row[3])) if row[3] else set(),
                    entity_type_distribution=json.loads(row[4]) if row[4] else {},
                    current_quality_metrics=json.loads(row[5]) if row[5] else {},
                    started_at=_coerce_datetime(row[6]),
                    updated_at=_coerce_datetime(row[7]),
                )
        finally:
            conn.close()

    def update_context(self, context: DomainMemoryContext) -> None:
        """워킹 메모리 컨텍스트를 업데이트합니다."""
        self.save_context(context)

    def delete_context(self, session_id: str) -> bool:
        """워킹 메모리 컨텍스트를 삭제합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM memory_contexts WHERE session_id = %s", (session_id,))
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

    def get_statistics(self, domain: str | None = None) -> dict[str, int]:
        """메모리 통계를 조회합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                domain_filter = " WHERE domain = %s" if domain else ""
                params = [domain] if domain else []

                cur.execute(f"SELECT COUNT(*) FROM factual_facts{domain_filter}", params)
                facts_count = cur.fetchone()[0]

                cur.execute(f"SELECT COUNT(*) FROM learning_memories{domain_filter}", params)
                learnings_count = cur.fetchone()[0]

                cur.execute(f"SELECT COUNT(*) FROM behavior_entries{domain_filter}", params)
                behaviors_count = cur.fetchone()[0]

                cur.execute(f"SELECT COUNT(*) FROM memory_contexts{domain_filter}", params)
                contexts_count = cur.fetchone()[0]

                return {
                    "facts": facts_count,
                    "learnings": learnings_count,
                    "behaviors": behaviors_count,
                    "contexts": contexts_count,
                }
        finally:
            conn.close()

    def consolidate_facts(self, domain: str, language: str) -> int:
        """유사한 사실들을 통합합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT subject, predicate, object, array_agg(fact_id) as fact_ids,
                           COUNT(*) as cnt
                    FROM factual_facts
                    WHERE domain = %s AND language = %s
                    GROUP BY subject, predicate, object
                    HAVING COUNT(*) > 1
                    """,
                    (domain, language),
                )
                duplicates = cur.fetchall()

                consolidated_count = 0

                for row in duplicates:
                    subject, predicate, obj, fact_ids, count = row

                    cur.execute(
                        """
                        SELECT fact_id, verification_score, verification_count,
                               source_document_ids, created_at, last_verified
                        FROM factual_facts
                        WHERE fact_id = ANY(%s)
                        ORDER BY verification_score DESC, verification_count DESC
                        """,
                        (fact_ids,),
                    )
                    facts_data = cur.fetchall()

                    primary_id = facts_data[0][0]
                    total_score = sum(f[1] for f in facts_data) / len(facts_data)
                    total_count = sum(f[2] for f in facts_data)

                    all_sources: set[str] = set()
                    for f in facts_data:
                        if f[3]:
                            sources = json.loads(f[3])
                            all_sources.update(sources)

                    latest_verified = max(f[5] for f in facts_data if f[5])

                    cur.execute(
                        """
                        UPDATE factual_facts
                        SET verification_score = %s,
                            verification_count = %s,
                            source_document_ids = %s,
                            last_verified = %s
                        WHERE fact_id = %s
                        """,
                        (
                            min(total_score, 1.0),
                            total_count,
                            json.dumps(list(all_sources)),
                            latest_verified,
                            primary_id,
                        ),
                    )

                    other_ids = [fid for fid in fact_ids if fid != primary_id]
                    if other_ids:
                        cur.execute(
                            "DELETE FROM factual_facts WHERE fact_id = ANY(%s)",
                            (other_ids,),
                        )
                        consolidated_count += len(other_ids)

                        self._log_evolution(
                            cur,
                            "consolidate",
                            "fact",
                            primary_id,
                            {"merged_ids": other_ids, "new_score": total_score},
                        )

            conn.commit()
            return consolidated_count
        finally:
            conn.close()

    def _log_evolution(
        self,
        cur: psycopg.cursor.Cursor,
        operation: str,
        target_type: str,
        target_id: str,
        details: dict,
    ) -> None:
        """Evolution 로그를 기록합니다."""
        cur.execute(
            """
            INSERT INTO memory_evolution_log (operation, target_type, target_id, details)
            VALUES (%s, %s, %s, %s)
            """,
            (operation, target_type, target_id, json.dumps(details)),
        )

    def resolve_conflict(self, fact1: FactualFact, fact2: FactualFact) -> FactualFact:
        """충돌하는 사실을 해결합니다."""
        from math import log

        def calculate_priority(fact: FactualFact) -> float:
            base_score = fact.verification_score
            count_factor = log(fact.verification_count + 1) + 1
            recency_days = (datetime.now() - (fact.last_verified or fact.created_at)).days
            recency_factor = 1.0 / (1 + recency_days / 30)
            return base_score * count_factor * recency_factor

        priority1 = calculate_priority(fact1)
        priority2 = calculate_priority(fact2)

        winner = fact1 if priority1 >= priority2 else fact2
        loser = fact2 if priority1 >= priority2 else fact1

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE factual_facts SET fact_type = %s WHERE fact_id = %s",
                    ("contradictory", loser.fact_id),
                )
                self._log_evolution(
                    cur,
                    "resolve_conflict",
                    "fact",
                    winner.fact_id,
                    {
                        "loser_id": loser.fact_id,
                        "winner_priority": priority1 if priority1 >= priority2 else priority2,
                        "loser_priority": priority2 if priority1 >= priority2 else priority1,
                    },
                )
            conn.commit()
        finally:
            conn.close()

        return winner

    def forget_obsolete(
        self,
        domain: str,
        max_age_days: int = 90,
        min_verification_count: int = 1,
        min_verification_score: float = 0.3,
    ) -> int:
        """오래되거나 신뢰도 낮은 메모리를 삭제합니다."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cutoff_date = datetime.now().isoformat()

                cur.execute(
                    """
                    SELECT fact_id FROM factual_facts
                    WHERE domain = %s
                    AND (
                        (EXTRACT(DAY FROM %s::timestamp - last_verified) > %s
                         AND verification_count < %s)
                        OR verification_score < %s
                    )
                    """,
                    (
                        domain,
                        cutoff_date,
                        max_age_days,
                        min_verification_count,
                        min_verification_score,
                    ),
                )
                to_delete = [row[0] for row in cur.fetchall()]

                if not to_delete:
                    return 0

                for fact_id in to_delete:
                    self._log_evolution(
                        cur,
                        "forget",
                        "fact",
                        fact_id,
                        {
                            "max_age_days": max_age_days,
                            "min_verification_count": min_verification_count,
                            "min_verification_score": min_verification_score,
                        },
                    )

                cur.execute(
                    """
                    DELETE FROM factual_facts
                    WHERE domain = %s
                    AND (
                        (EXTRACT(DAY FROM %s::timestamp - last_verified) > %s
                         AND verification_count < %s)
                        OR verification_score < %s
                    )
                    """,
                    (
                        domain,
                        cutoff_date,
                        max_age_days,
                        min_verification_count,
                        min_verification_score,
                    ),
                )
                deleted_count = cur.rowcount
            conn.commit()
            return deleted_count
        finally:
            conn.close()

    def decay_verification_scores(self, domain: str, decay_rate: float = 0.95) -> int:
        """시간에 따라 검증 점수를 감소시킵니다."""
        if not 0.0 <= decay_rate <= 1.0:
            raise ValueError("decay_rate must be between 0.0 and 1.0")

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                min_days_since_verified = 7
                cutoff_date = datetime.now().isoformat()

                cur.execute(
                    """
                    SELECT fact_id, verification_score
                    FROM factual_facts
                    WHERE domain = %s
                    AND EXTRACT(DAY FROM %s::timestamp - last_verified) > %s
                    AND verification_score > 0.1
                    """,
                    (domain, cutoff_date, min_days_since_verified),
                )
                to_decay = cur.fetchall()

                if not to_decay:
                    return 0

                for fact_id, current_score in to_decay:
                    new_score = max(current_score * decay_rate, 0.1)
                    cur.execute(
                        """
                        UPDATE factual_facts
                        SET verification_score = %s
                        WHERE fact_id = %s
                        """,
                        (new_score, fact_id),
                    )
                    self._log_evolution(
                        cur,
                        "decay",
                        "fact",
                        fact_id,
                        {
                            "old_score": current_score,
                            "new_score": new_score,
                            "decay_rate": decay_rate,
                        },
                    )

            conn.commit()
            return len(to_decay)
        finally:
            conn.close()

    def search_facts(
        self,
        query: str,
        domain: str | None = None,
        language: str | None = None,
        limit: int = 10,
    ) -> list[FactualFact]:
        """키워드 기반 사실 검색 (ILIKE)."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                search_term = f"%{query}%"

                query_sql = """
                    SELECT fact_id, subject, predicate, object, language, domain,
                           fact_type, verification_score, verification_count,
                           source_document_ids, created_at, last_verified, abstraction_level
                    FROM factual_facts
                    WHERE (subject ILIKE %s OR predicate ILIKE %s OR object ILIKE %s)
                """
                params: list = [search_term, search_term, search_term]

                if domain:
                    query_sql += " AND domain = %s"
                    params.append(domain)
                if language:
                    query_sql += " AND language = %s"
                    params.append(language)

                query_sql += " ORDER BY verification_score DESC LIMIT %s"
                params.append(limit)

                cur.execute(query_sql, params)
                return [self._row_to_fact(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def search_behaviors(
        self,
        context: str,
        domain: str,
        language: str,
        limit: int = 5,
    ) -> list[BehaviorEntry]:
        """컨텍스트 기반 행동 검색."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                search_term = f"%{context}%"

                cur.execute(
                    """
                    SELECT behavior_id, description, trigger_pattern, action_sequence,
                           success_rate, token_savings, applicable_languages, domain,
                           last_used, use_count, created_at
                    FROM behavior_entries
                    WHERE domain = %s
                    AND (description ILIKE %s OR trigger_pattern ILIKE %s)
                    ORDER BY success_rate DESC
                    LIMIT %s
                    """,
                    (domain, search_term, search_term, limit * 3),
                )
                results = [self._row_to_behavior(row) for row in cur.fetchall()]

                cur.execute(
                    """
                    SELECT behavior_id, description, trigger_pattern, action_sequence,
                           success_rate, token_savings, applicable_languages, domain,
                           last_used, use_count, created_at
                    FROM behavior_entries
                    WHERE domain = %s
                    AND trigger_pattern IS NOT NULL
                    AND trigger_pattern != ''
                    ORDER BY success_rate DESC
                    """,
                    (domain,),
                )
                all_behaviors = [self._row_to_behavior(row) for row in cur.fetchall()]

                for behavior in all_behaviors:
                    if behavior in results:
                        continue
                    if not behavior.is_applicable(language):
                        continue
                    try:
                        if re.search(behavior.trigger_pattern, context, re.IGNORECASE):
                            results.append(behavior)
                    except re.error:
                        continue

                results = [b for b in results if b.is_applicable(language)]
                results = sorted(results, key=lambda b: b.success_rate, reverse=True)

                return results[:limit]
        finally:
            conn.close()

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
        """하이브리드 메모리 검색."""
        facts = self.search_facts(query, domain, language, int(limit * fact_weight))
        behaviors = self.search_behaviors(query, domain, language, int(limit * behavior_weight))
        learnings = self.list_learnings(domain, language, limit=int(limit * learning_weight))

        return {
            "facts": facts,
            "behaviors": behaviors,
            "learnings": learnings,
        }
