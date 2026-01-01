"""Ports for Korean NLP tooling used in benchmarks."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FaithfulnessClaimResultProtocol(Protocol):
    """Individual claim verification result."""

    coverage: float


@runtime_checkable
class FaithfulnessResultProtocol(Protocol):
    """Faithfulness evaluation result contract."""

    score: float
    faithful_claims: int
    total_claims: int
    claim_results: Sequence[FaithfulnessClaimResultProtocol] | None


@runtime_checkable
class RetrieverResultProtocol(Protocol):
    """Retriever result contract."""

    doc_id: str | int


class RetrieverPort(Protocol):
    """Retriever interface."""

    def search(self, query: str, top_k: int = 5) -> Sequence[RetrieverResultProtocol]:
        """Search documents."""


class KoreanNLPToolkitPort(Protocol):
    """Toolkit providing Korean NLP helpers."""

    def extract_keywords(self, text: str) -> Sequence[str]:
        """Extract keywords from text."""

    def check_faithfulness(
        self,
        answer: str,
        contexts: Sequence[str],
    ) -> FaithfulnessResultProtocol | None:
        """Check answer faithfulness."""

    def build_retriever(
        self,
        documents: Sequence[str],
        *,
        use_hybrid: bool,
        ollama_adapter: Any | None = None,
        embedding_profile: str | None = None,
        verbose: bool = False,
    ) -> RetrieverPort | None:
        """Create and index a retriever for the documents."""
