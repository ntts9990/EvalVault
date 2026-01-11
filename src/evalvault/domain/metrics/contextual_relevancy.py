"""Contextual Relevancy metric for RAG evaluation.

Evaluates how well retrieved contexts are related to the question.
Unlike Context Precision (which requires ground_truth), this metric
is reference-free and directly measures question-context alignment.

This is the third axis of the RAG Triad (TruLens, Microsoft Azure AI):
1. Answer Relevancy: answer vs. question
2. Faithfulness: answer vs. contexts
3. Contextual Relevancy: contexts vs. question (this metric)
"""

from __future__ import annotations

import re
import unicodedata


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(text: str) -> set[str]:
    """Tokenize text into a set of words."""
    if not text:
        return set()
    text = _normalize_text(text)
    tokens = re.findall(r"[\w가-힣]+", text)
    return set(tokens)


def _strip_korean_endings(token: str) -> str:
    """Strip common Korean particles and endings."""
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


def _tokenize_with_stripping(text: str) -> set[str]:
    """Tokenize with Korean ending stripping."""
    if not text:
        return set()
    text = _normalize_text(text)
    tokens = re.findall(r"[\w가-힣]+", text)
    tokens = [_strip_korean_endings(t) for t in tokens]
    return {t for t in tokens if t}


# Stopwords to filter out (common words that don't carry meaning)
_STOPWORDS_KO = {
    "이",
    "그",
    "저",
    "것",
    "수",
    "등",
    "및",
    "더",
    "또",
    "또는",
    "하다",
    "있다",
    "되다",
    "않다",
    "없다",
    "같다",
    "위하다",
    "대하다",
    "통하다",
    "따르다",
    "관하다",
    "의하다",
}

_STOPWORDS_EN = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "must",
    "shall",
    "can",
    "and",
    "or",
    "but",
    "if",
    "then",
    "else",
    "when",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "once",
    "here",
    "there",
    "where",
    "why",
    "how",
    "all",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "these",
    "those",
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "ours",
    "ourselves",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
    "he",
    "him",
    "his",
    "himself",
    "she",
    "her",
    "hers",
    "herself",
    "it",
    "its",
    "itself",
    "they",
    "them",
    "their",
    "theirs",
    "themselves",
}

_STOPWORDS = _STOPWORDS_KO | _STOPWORDS_EN


def _tokenize_content_words(text: str) -> set[str]:
    """Tokenize and filter to content words only."""
    tokens = _tokenize_with_stripping(text)
    # Filter out stopwords and very short tokens
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 1}


def _calculate_relevancy(question: str, context: str) -> float:
    """Calculate relevancy score between question and context.

    Uses token overlap with emphasis on question terms appearing in context.

    Args:
        question: The user's question
        context: A retrieved context

    Returns:
        Relevancy score between 0.0 and 1.0
    """
    if not question or not context:
        return 0.0

    question_tokens = _tokenize_content_words(question)
    context_tokens = _tokenize_content_words(context)

    if not question_tokens:
        return 0.0

    # Calculate recall: what fraction of question tokens appear in context
    overlap = question_tokens.intersection(context_tokens)
    recall = len(overlap) / len(question_tokens)

    # Boost score if context has high coverage of question terms
    return min(recall, 1.0)


class ContextualRelevancy:
    """Contextual Relevancy metric for RAG evaluation.

    Evaluates how well retrieved contexts are related to the question.
    This is a reference-free metric that directly measures question-context
    alignment without requiring ground_truth.

    Unlike Context Precision (contexts vs. ground_truth), this metric
    evaluates contexts vs. question, making it useful when ground_truth
    is not available.

    This completes the RAG Triad:
    1. Answer Relevancy: answer vs. question
    2. Faithfulness: answer vs. contexts
    3. Contextual Relevancy: contexts vs. question (this metric)

    Calculation:
    - For each context, compute token overlap with question
    - Return average relevancy across all contexts
    - Optionally use @k to limit to top k contexts

    Example:
        >>> metric = ContextualRelevancy()
        >>> metric.score(
        ...     question="이 보험의 보장금액은 얼마인가요?",
        ...     contexts=[
        ...         "해당 보험의 사망 보장금액은 1억원입니다.",  # Relevant
        ...         "회사 소개 페이지입니다.",  # Irrelevant
        ...     ]
        ... )
        0.5  # One relevant, one irrelevant
    """

    name = "contextual_relevancy"

    def __init__(
        self,
        k: int | None = None,
        relevance_threshold: float = 0.35,
    ):
        """Initialize ContextualRelevancy metric.

        Args:
            k: Only consider top k contexts (None = all)
            relevance_threshold: Minimum score to consider context relevant (default: 0.3)
        """
        self.k = k
        self.relevance_threshold = relevance_threshold

    def score(
        self,
        question: str,
        answer: str | None = None,  # Not used, for interface compatibility
        ground_truth: str | None = None,  # Not used, reference-free
        contexts: list[str] | None = None,
    ) -> float:
        """Calculate contextual relevancy score.

        Args:
            question: The user's question
            answer: Not used (for interface compatibility)
            ground_truth: Not used (reference-free metric)
            contexts: List of retrieved contexts

        Returns:
            Average relevancy score between 0.0 and 1.0
        """
        if not question or not contexts:
            return 0.0

        # Limit to top k contexts if specified
        eval_contexts = contexts[: self.k] if self.k else contexts

        if not eval_contexts:
            return 0.0

        # Calculate relevancy for each context
        relevancy_scores = [_calculate_relevancy(question, ctx) for ctx in eval_contexts]

        # Return average
        return round(sum(relevancy_scores) / len(relevancy_scores), 4)

    def score_detailed(
        self,
        question: str,
        answer: str | None = None,
        ground_truth: str | None = None,
        contexts: list[str] | None = None,
    ) -> dict:
        """Calculate detailed contextual relevancy metrics.

        Args:
            question: The user's question
            answer: Not used (for interface compatibility)
            ground_truth: Not used (reference-free metric)
            contexts: List of retrieved contexts

        Returns:
            Dictionary with detailed relevancy information
        """
        if not question or not contexts:
            return {
                "contextual_relevancy": 0.0,
                "relevancy_scores": [],
                "relevant_count": 0,
                "total_contexts": 0,
                "k": self.k,
                "precision": 0.0,
            }

        # Limit to top k contexts if specified
        eval_contexts = contexts[: self.k] if self.k else contexts

        if not eval_contexts:
            return {
                "contextual_relevancy": 0.0,
                "relevancy_scores": [],
                "relevant_count": 0,
                "total_contexts": 0,
                "k": self.k,
                "precision": 0.0,
            }

        # Calculate relevancy for each context
        relevancy_scores = [round(_calculate_relevancy(question, ctx), 4) for ctx in eval_contexts]

        # Count relevant contexts
        relevant_count = sum(1 for score in relevancy_scores if score >= self.relevance_threshold)

        # Calculate average
        avg_relevancy = sum(relevancy_scores) / len(relevancy_scores)

        # Precision: fraction of contexts that are relevant
        precision = relevant_count / len(eval_contexts)

        return {
            "contextual_relevancy": round(avg_relevancy, 4),
            "relevancy_scores": relevancy_scores,
            "relevant_count": relevant_count,
            "total_contexts": len(eval_contexts),
            "k": self.k,
            "precision": round(precision, 4),
        }

    def get_relevant_contexts(
        self,
        question: str,
        contexts: list[str],
        threshold: float | None = None,
    ) -> list[tuple[int, str, float]]:
        """Get contexts that are relevant to the question.

        Args:
            question: The user's question
            contexts: List of retrieved contexts
            threshold: Minimum relevancy score (default: self.relevance_threshold)

        Returns:
            List of (index, context, score) tuples for relevant contexts
        """
        if not question or not contexts:
            return []

        threshold = threshold if threshold is not None else self.relevance_threshold

        results = []
        for i, ctx in enumerate(contexts):
            score = _calculate_relevancy(question, ctx)
            if score >= threshold:
                results.append((i, ctx, round(score, 4)))

        # Sort by score descending
        results.sort(key=lambda x: x[2], reverse=True)
        return results
