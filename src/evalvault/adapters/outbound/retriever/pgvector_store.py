from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PgvectorResult:
    doc_id: int
    content: str
    score: float


class PgvectorStore:
    def __init__(
        self,
        conn_string: str,
        *,
        distance: str = "cosine",
        index_type: str = "hnsw",
        index_lists: int = 100,
        hnsw_m: int = 16,
        hnsw_ef_construction: int = 64,
    ) -> None:
        self._conn_string = conn_string
        self._distance = distance
        self._index_type = index_type
        self._index_lists = index_lists
        self._hnsw_m = hnsw_m
        self._hnsw_ef_construction = hnsw_ef_construction

    def _vector_ops(self) -> str:
        if self._distance == "ip":
            return "vector_ip_ops"
        if self._distance == "l2":
            return "vector_l2_ops"
        return "vector_cosine_ops"

    def _connect(self) -> psycopg.Connection:
        conn = psycopg.connect(self._conn_string, row_factory=dict_row)
        try:
            from pgvector.psycopg import register_vector

            register_vector(conn)
        except Exception as exc:  # pragma: no cover - runtime dependency
            logger.warning("Failed to register pgvector type: %s", exc)
        return conn

    def ensure_schema(self, *, dimension: int) -> None:
        sql = f"""
        CREATE EXTENSION IF NOT EXISTS vector;

        CREATE TABLE IF NOT EXISTS rag_documents (
            id BIGSERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            doc_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR({dimension}),
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_rag_documents_source ON rag_documents(source);
        CREATE INDEX IF NOT EXISTS idx_rag_documents_doc_id ON rag_documents(doc_id);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_rag_documents_source_doc_id
            ON rag_documents(source, doc_id);
        """
        with self._connect() as conn:
            conn.execute(sql)
            if self._index_type != "none":
                opclass = self._vector_ops()
                if self._index_type == "ivfflat":
                    index_sql = (
                        "CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding "
                        f"ON rag_documents USING ivfflat (embedding {opclass}) "
                        f"WITH (lists = {self._index_lists});"
                    )
                    try:
                        conn.execute(index_sql)
                    except Exception as exc:  # pragma: no cover - runtime dependency
                        logger.warning("Failed to create ivfflat index: %s", exc)
                elif self._index_type == "hnsw":
                    index_sql = (
                        "CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding "
                        f"ON rag_documents USING hnsw (embedding {opclass}) "
                        f"WITH (m = {self._hnsw_m}, ef_construction = {self._hnsw_ef_construction});"
                    )
                    try:
                        conn.execute(index_sql)
                    except Exception as exc:  # pragma: no cover - runtime dependency
                        logger.warning("Failed to create hnsw index: %s", exc)
            conn.commit()

    def get_source_state(self, *, source: str) -> tuple[str | None, int]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT source_hash, COUNT(*) AS total
                FROM rag_documents
                WHERE source = %s
                GROUP BY source_hash
                ORDER BY total DESC
                LIMIT 1
                """,
                (source,),
            ).fetchone()
        if not row:
            return None, 0
        return row["source_hash"], int(row["total"])

    def replace_documents(
        self,
        *,
        source: str,
        source_hash: str,
        documents: Iterable[str],
        embeddings: Iterable[list[float]],
    ) -> None:
        rows = list(zip(documents, embeddings, strict=True))
        with self._connect() as conn:
            conn.execute("DELETE FROM rag_documents WHERE source = %s", (source,))
            with conn.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO rag_documents (source, source_hash, doc_id, content, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [
                        (source, source_hash, index, content, embedding)
                        for index, (content, embedding) in enumerate(rows)
                    ],
                )
            conn.commit()

    def search(
        self, *, source: str, query_embedding: list[float], top_k: int
    ) -> list[PgvectorResult]:
        if self._distance == "ip":
            operator = "<#>"
        elif self._distance == "l2":
            operator = "<->"
        else:
            operator = "<=>"

        sql = (
            f"SELECT doc_id, content, embedding {operator} %s::vector AS score "
            f"FROM rag_documents WHERE source = %s ORDER BY embedding {operator} %s::vector LIMIT %s"
        )

        with self._connect() as conn:
            rows = conn.execute(sql, (query_embedding, source, query_embedding, top_k)).fetchall()

        return [
            PgvectorResult(
                doc_id=int(row["doc_id"]), content=row["content"], score=float(row["score"])
            )
            for row in rows
        ]
