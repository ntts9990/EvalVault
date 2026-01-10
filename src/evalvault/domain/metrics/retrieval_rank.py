"""Retrieval ranking metrics for RAG evaluation.

Provides MRR (Mean Reciprocal Rank) and NDCG (Normalized Discounted
Cumulative Gain) metrics for evaluating the quality of retrieved
context rankings.

These metrics measure how well the retrieval system ranks relevant
contexts - critical for RAG systems where context order affects
answer quality.
"""

from __future__ import annotations

import math
import re
import unicodedata


def _normalize_text(text: str) -> str:
    """Normalize text for comparison.

    Args:
        text: Text to normalize

    Returns:
        Normalized text (lowercase, whitespace cleaned, unicode normalized)
    """
    if not text:
        return ""

    # Normalize unicode (NFC for Korean)
    text = unicodedata.normalize("NFC", text)

    # Lowercase
    text = text.lower()

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _strip_korean_endings(token: str) -> str:
    """Strip common Korean particles and endings from a token.

    Args:
        token: Token to strip endings from

    Returns:
        Token with endings removed
    """
    # Common Korean endings (order matters - longer first)
    endings = [
        "입니다",
        "습니다",
        "됩니다",
        "입니까",
        "에서는",
        "으로서",
        "으로써",
        "에게서",
        "로서",
        "로써",
        "부터",
        "까지",
        "에서",
        "으로",
        "에게",
        "께서",
        "에는",
        "이나",
        "이란",
        "이며",
        "이고",
        "이다",
        "로",
        "는",
        "은",
        "이",
        "가",
        "을",
        "를",
        "의",
        "에",
        "와",
        "과",
        "도",
    ]

    for ending in endings:
        if token.endswith(ending) and len(token) > len(ending):
            return token[: -len(ending)]

    return token


def _tokenize(text: str) -> set[str]:
    """Tokenize text into a set of words.

    Handles Korean text by stripping common particles and endings.

    Args:
        text: Text to tokenize

    Returns:
        Set of tokens
    """
    if not text:
        return set()

    text = _normalize_text(text)

    # Split on whitespace and punctuation
    tokens = re.findall(r"[\w가-힣]+", text)

    # Strip Korean endings from each token
    tokens = [_strip_korean_endings(t) for t in tokens]

    # Filter out empty tokens
    tokens = [t for t in tokens if t]

    return set(tokens)


def _calculate_relevance(context: str, ground_truth: str) -> float:
    """Calculate relevance score between context and ground truth.

    Uses token overlap (Jaccard-like) to determine how relevant
    a context is to the ground truth answer.

    Args:
        context: Retrieved context
        ground_truth: Reference answer

    Returns:
        Relevance score between 0.0 and 1.0
    """
    if not context or not ground_truth:
        return 0.0

    context_tokens = _tokenize(context)
    truth_tokens = _tokenize(ground_truth)

    if not truth_tokens:
        return 0.0

    # Calculate how many ground truth tokens are in context
    overlap = context_tokens.intersection(truth_tokens)

    # Use recall-based relevance (how much of ground truth is covered)
    recall = len(overlap) / len(truth_tokens)

    return recall


class MRR:
    """Mean Reciprocal Rank (MRR) metric.

    Evaluates retrieval quality by measuring the rank of the first
    relevant context. Higher MRR means relevant contexts appear
    earlier in the ranking.

    For RAG systems:
    - MRR = 1.0: First context is relevant
    - MRR = 0.5: Second context is first relevant
    - MRR = 0.0: No relevant context found

    Relevance is determined by token overlap between context and
    ground truth. A context is considered relevant if its relevance
    score exceeds the threshold.

    Example:
        >>> metric = MRR()
        >>> metric.score(
        ...     answer="답변",
        ...     ground_truth="1억원",
        ...     contexts=["관련없는 내용", "보장금액은 1억원입니다", "기타"]
        ... )
        0.5  # First relevant at rank 2 -> 1/2
    """

    name = "mrr"

    def __init__(self, relevance_threshold: float = 0.3, k: int | None = None):
        """Initialize MRR metric.

        Args:
            relevance_threshold: Minimum relevance score to consider
                                 a context as relevant (default: 0.3)
            k: Maximum rank to consider. If None, considers all contexts.
               MRR@K only looks at top K results.
        """
        self.relevance_threshold = relevance_threshold
        self.k = k

    def score(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> float:
        """Calculate MRR score.

        Args:
            answer: The generated answer (unused, for interface compatibility)
            ground_truth: The reference answer used to determine relevance
            contexts: Retrieved contexts in ranked order (first = highest rank)

        Returns:
            Reciprocal rank of first relevant context (1/rank), or 0.0 if
            no relevant context found
        """
        if not contexts or not ground_truth:
            return 0.0

        # Limit to top K if specified
        search_contexts = contexts[: self.k] if self.k else contexts

        # Find first relevant context
        for rank, context in enumerate(search_contexts, start=1):
            relevance = _calculate_relevance(context, ground_truth)
            if relevance >= self.relevance_threshold:
                return 1.0 / rank

        return 0.0

    def score_detailed(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> dict:
        """Calculate detailed MRR metrics.

        Args:
            answer: The generated answer
            ground_truth: The reference answer
            contexts: Retrieved contexts in ranked order

        Returns:
            Dictionary with MRR score and additional info
        """
        if not contexts or not ground_truth:
            return {
                "mrr": 0.0,
                "first_relevant_rank": None,
                "num_relevant": 0,
                "relevance_scores": [],
            }

        search_contexts = contexts[: self.k] if self.k else contexts
        relevance_scores = []
        first_relevant_rank = None
        num_relevant = 0

        for rank, context in enumerate(search_contexts, start=1):
            relevance = _calculate_relevance(context, ground_truth)
            relevance_scores.append(relevance)

            if relevance >= self.relevance_threshold:
                num_relevant += 1
                if first_relevant_rank is None:
                    first_relevant_rank = rank

        mrr = 1.0 / first_relevant_rank if first_relevant_rank else 0.0

        return {
            "mrr": mrr,
            "first_relevant_rank": first_relevant_rank,
            "num_relevant": num_relevant,
            "relevance_scores": relevance_scores,
        }


class NDCG:
    """Normalized Discounted Cumulative Gain (NDCG) metric.

    Evaluates retrieval quality by measuring how well relevant contexts
    are ranked, with higher positions weighted more heavily.

    Unlike MRR which only considers the first relevant result, NDCG
    considers all relevant results and their positions.

    For RAG systems:
    - NDCG = 1.0: Perfect ranking (all relevant contexts at top)
    - NDCG = 0.0: No relevant contexts or worst possible ranking

    Scoring formula:
    - DCG = sum(relevance_i / log2(i + 1)) for i = 1 to k
    - IDCG = DCG with ideal ranking (sorted by relevance)
    - NDCG = DCG / IDCG

    Example:
        >>> metric = NDCG()
        >>> metric.score(
        ...     answer="답변",
        ...     ground_truth="1억원",
        ...     contexts=["보장금액 1억원", "관련없음", "1억원 지급"]
        ... )
        0.95  # Good ranking - relevant at positions 1 and 3
    """

    name = "ndcg"

    def __init__(self, k: int = 10, use_graded: bool = True):
        """Initialize NDCG metric.

        Args:
            k: Number of top results to consider (NDCG@K)
            use_graded: If True, use graded relevance scores (0.0-1.0).
                        If False, use binary relevance (0 or 1).
        """
        self.k = k
        self.use_graded = use_graded

    def _dcg(self, relevances: list[float]) -> float:
        """Calculate Discounted Cumulative Gain.

        Args:
            relevances: List of relevance scores in rank order

        Returns:
            DCG score
        """
        dcg = 0.0
        for i, rel in enumerate(relevances, start=1):
            if i > self.k:
                break
            dcg += rel / math.log2(i + 1)
        return dcg

    def _idcg(self, relevances: list[float]) -> float:
        """Calculate Ideal DCG (perfect ranking).

        Args:
            relevances: List of relevance scores (any order)

        Returns:
            IDCG score (DCG with optimal ranking)
        """
        # Sort by relevance descending for ideal ranking
        sorted_relevances = sorted(relevances, reverse=True)
        return self._dcg(sorted_relevances)

    def score(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> float:
        """Calculate NDCG score.

        Args:
            answer: The generated answer (unused, for interface compatibility)
            ground_truth: The reference answer used to determine relevance
            contexts: Retrieved contexts in ranked order

        Returns:
            NDCG score between 0.0 and 1.0
        """
        if not contexts or not ground_truth:
            return 0.0

        # Calculate relevance for each context
        relevances = []
        for context in contexts[: self.k]:
            rel = _calculate_relevance(context, ground_truth)
            if not self.use_graded:
                # Binary relevance: threshold at 0.3
                rel = 1.0 if rel >= 0.3 else 0.0
            relevances.append(rel)

        # Calculate NDCG
        dcg = self._dcg(relevances)
        idcg = self._idcg(relevances)

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def score_detailed(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> dict:
        """Calculate detailed NDCG metrics.

        Args:
            answer: The generated answer
            ground_truth: The reference answer
            contexts: Retrieved contexts in ranked order

        Returns:
            Dictionary with NDCG, DCG, IDCG, and relevance info
        """
        if not contexts or not ground_truth:
            return {
                "ndcg": 0.0,
                "dcg": 0.0,
                "idcg": 0.0,
                "relevances": [],
                "k": self.k,
            }

        relevances = []
        for context in contexts[: self.k]:
            rel = _calculate_relevance(context, ground_truth)
            if not self.use_graded:
                rel = 1.0 if rel >= 0.3 else 0.0
            relevances.append(rel)

        dcg = self._dcg(relevances)
        idcg = self._idcg(relevances)
        ndcg = dcg / idcg if idcg > 0 else 0.0

        return {
            "ndcg": ndcg,
            "dcg": dcg,
            "idcg": idcg,
            "relevances": relevances,
            "k": self.k,
        }


class HitRate:
    """Hit Rate (Recall@K) metric.

    Measures whether at least one relevant context appears in
    the top K results.

    For RAG systems:
    - Hit Rate = 1.0: At least one relevant context in top K
    - Hit Rate = 0.0: No relevant context in top K

    This is a simpler metric than MRR/NDCG but useful for
    quick evaluation of retrieval coverage.

    Example:
        >>> metric = HitRate(k=3)
        >>> metric.score(
        ...     answer="답변",
        ...     ground_truth="1억원",
        ...     contexts=["관련없음", "관련없음", "보장금액 1억원"]
        ... )
        1.0  # Relevant context found in top 3
    """

    name = "hit_rate"

    def __init__(self, k: int = 10, relevance_threshold: float = 0.3):
        """Initialize Hit Rate metric.

        Args:
            k: Number of top results to consider
            relevance_threshold: Minimum relevance score to count as a hit
        """
        self.k = k
        self.relevance_threshold = relevance_threshold

    def score(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> float:
        """Calculate Hit Rate score.

        Args:
            answer: The generated answer (unused, for interface compatibility)
            ground_truth: The reference answer used to determine relevance
            contexts: Retrieved contexts in ranked order

        Returns:
            1.0 if any relevant context in top K, 0.0 otherwise
        """
        if not contexts or not ground_truth:
            return 0.0

        for context in contexts[: self.k]:
            relevance = _calculate_relevance(context, ground_truth)
            if relevance >= self.relevance_threshold:
                return 1.0

        return 0.0

    def score_detailed(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> dict:
        """Calculate detailed Hit Rate metrics.

        Args:
            answer: The generated answer
            ground_truth: The reference answer
            contexts: Retrieved contexts in ranked order

        Returns:
            Dictionary with hit rate and relevance info
        """
        if not contexts or not ground_truth:
            return {
                "hit_rate": 0.0,
                "hit_position": None,
                "k": self.k,
                "relevance_scores": [],
            }

        relevance_scores = []
        hit_position = None

        for i, context in enumerate(contexts[: self.k], start=1):
            rel = _calculate_relevance(context, ground_truth)
            relevance_scores.append(rel)
            if rel >= self.relevance_threshold and hit_position is None:
                hit_position = i

        return {
            "hit_rate": 1.0 if hit_position else 0.0,
            "hit_position": hit_position,
            "k": self.k,
            "relevance_scores": relevance_scores,
        }
