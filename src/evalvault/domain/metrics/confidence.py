"""Confidence Score metric for RAG evaluation.

Estimates the confidence level of RAG system answers based on
multiple signals: context coverage, answer specificity, and
consistency with available evidence.

This metric is crucial for Human-in-the-Loop systems where
low-confidence answers should be escalated to human review.
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


# Hedging patterns indicating uncertainty
_HEDGING_PATTERNS_KO = [
    r"아마도?",
    r"아마",
    r"아마\s*도",
    r"아마\s*그럴\s*것",
    r"것\s*같습니다",
    r"것\s*같아요",
    r"것\s*같다",
    r"듯\s*합니다",
    r"듯\s*해요",
    r"듯\s*하다",
    r"수도?\s*있",
    r"가능성이?\s*있",
    r"확실하지\s*않",
    r"잘\s*모르",
    r"불확실",
    r"추정",
    r"예상",
    r"생각됩니다",
    r"보입니다",
    r"판단됩니다",
]

_HEDGING_PATTERNS_EN = [
    r"maybe",
    r"perhaps",
    r"possibly",
    r"might",
    r"could\s+be",
    r"may\s+be",
    r"probably",
    r"likely",
    r"i\s+think",
    r"i\s+believe",
    r"it\s+seems",
    r"apparently",
    r"uncertain",
    r"unclear",
    r"not\s+sure",
    r"unsure",
    r"approximately",
    r"roughly",
    r"around",
    r"about",
]

# Definitive patterns indicating high confidence
_DEFINITIVE_PATTERNS_KO = [
    r"확실히",
    r"분명히",
    r"명확히",
    r"반드시",
    r"틀림없이",
    r"정확히",
    r"바로",
    r"입니다$",
    r"합니다$",
]

_DEFINITIVE_PATTERNS_EN = [
    r"definitely",
    r"certainly",
    r"clearly",
    r"precisely",
    r"exactly",
    r"specifically",
    r"absolutely",
    r"undoubtedly",
]

# Number patterns
_NUMBER_PATTERN = re.compile(
    r"\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:억|천만|백만|만|천|백)?\s*원|%|년|개월|일|세|명|개)?"
)


class ConfidenceScore:
    """Confidence Score metric for RAG evaluation.

    Estimates the confidence level of a RAG system's answer based on:

    1. **Context Coverage** (40%): How well the answer is supported by contexts
       - Token overlap between answer and contexts
       - Higher overlap suggests better evidence support

    2. **Answer Specificity** (30%): How specific and detailed the answer is
       - Presence of specific information (numbers, dates)
       - Answer length (neither too short nor excessively long)
       - Absence of hedging language, presence of definitive language

    3. **Consistency** (30%): How consistent the answer is with available evidence
       - If ground_truth available: overlap with ground_truth
       - Penalizes hedging language

    Use case:
    - Low confidence (< 0.7) answers should be escalated to human review
    - High confidence (>= 0.85) answers can be auto-approved
    - Medium confidence (0.7 - 0.85) should be monitored

    Example:
        >>> metric = ConfidenceScore()
        >>> metric.score(
        ...     answer="보장금액은 1억원입니다.",
        ...     ground_truth="1억원",
        ...     contexts=["해당 보험의 사망 보장금액은 1억원입니다."]
        ... )
        0.85  # High confidence - specific, supported by context
    """

    name = "confidence_score"

    def __init__(
        self,
        coverage_weight: float = 0.4,
        specificity_weight: float = 0.3,
        consistency_weight: float = 0.3,
        min_answer_length: int = 5,
        optimal_answer_length: int = 50,
        max_answer_length: int = 500,
    ):
        """Initialize ConfidenceScore metric.

        Args:
            coverage_weight: Weight for context coverage score (default: 0.4)
            specificity_weight: Weight for answer specificity score (default: 0.3)
            consistency_weight: Weight for consistency score (default: 0.3)
            min_answer_length: Minimum answer length for full score (default: 5)
            optimal_answer_length: Optimal answer length (default: 50)
            max_answer_length: Maximum answer length before penalty (default: 500)
        """
        self.coverage_weight = coverage_weight
        self.specificity_weight = specificity_weight
        self.consistency_weight = consistency_weight
        self.min_answer_length = min_answer_length
        self.optimal_answer_length = optimal_answer_length
        self.max_answer_length = max_answer_length

        # Compile patterns
        self._hedging_ko = [re.compile(p, re.IGNORECASE) for p in _HEDGING_PATTERNS_KO]
        self._hedging_en = [re.compile(p, re.IGNORECASE) for p in _HEDGING_PATTERNS_EN]
        self._definitive_ko = [re.compile(p, re.IGNORECASE) for p in _DEFINITIVE_PATTERNS_KO]
        self._definitive_en = [re.compile(p, re.IGNORECASE) for p in _DEFINITIVE_PATTERNS_EN]

    def _calculate_context_coverage(self, answer: str, contexts: list[str]) -> float:
        """Calculate how well the answer is supported by contexts.

        Returns:
            Coverage score between 0.0 and 1.0
        """
        if not answer or not contexts:
            return 0.0

        answer_tokens = _tokenize_with_stripping(answer)
        if not answer_tokens:
            return 0.0

        # Combine all context tokens
        context_tokens = set()
        for ctx in contexts:
            context_tokens.update(_tokenize_with_stripping(ctx))

        if not context_tokens:
            return 0.0

        # Calculate overlap (what fraction of answer tokens are in contexts)
        overlap = answer_tokens.intersection(context_tokens)
        coverage = len(overlap) / len(answer_tokens)

        return min(coverage, 1.0)

    def _detect_hedging(self, text: str) -> float:
        """Detect hedging language in text.

        Returns:
            Score between 0.0 (no hedging) and 1.0 (heavy hedging)
        """
        if not text:
            return 0.0

        hedging_count = 0

        # Check Korean patterns
        for pattern in self._hedging_ko:
            if pattern.search(text):
                hedging_count += 1

        # Check English patterns
        for pattern in self._hedging_en:
            if pattern.search(text):
                hedging_count += 1

        # Normalize by total possible patterns checked
        # Cap at 1.0, with diminishing returns after first few matches
        if hedging_count == 0:
            return 0.0
        elif hedging_count == 1:
            return 0.3
        elif hedging_count == 2:
            return 0.5
        elif hedging_count <= 4:
            return 0.7
        else:
            return 0.9

    def _detect_definitiveness(self, text: str) -> float:
        """Detect definitive language in text.

        Returns:
            Score between 0.0 (no definitive language) and 1.0 (strong assertions)
        """
        if not text:
            return 0.0

        definitive_count = 0

        # Check Korean patterns
        for pattern in self._definitive_ko:
            if pattern.search(text):
                definitive_count += 1

        # Check English patterns
        for pattern in self._definitive_en:
            if pattern.search(text):
                definitive_count += 1

        # Score based on matches (return 0.7 for 3+ matches)
        scores = {0: 0.0, 1: 0.3, 2: 0.5}
        return scores.get(definitive_count, 0.7)

    def _count_specific_details(self, text: str) -> int:
        """Count specific details (numbers, dates) in text.

        Returns:
            Count of specific details found
        """
        if not text:
            return 0

        # Count number patterns
        numbers = _NUMBER_PATTERN.findall(text)

        return len(numbers)

    def _calculate_length_score(self, text: str) -> float:
        """Calculate score based on answer length.

        Too short or too long answers get penalized.

        Returns:
            Score between 0.0 and 1.0
        """
        if not text:
            return 0.0

        length = len(text)

        if length < self.min_answer_length:
            # Very short - low confidence
            return 0.3
        elif length <= self.optimal_answer_length:
            # Good length range - high confidence
            return 1.0
        elif length <= self.max_answer_length:
            # Longer than optimal but acceptable
            # Gradually decrease score
            excess = length - self.optimal_answer_length
            max_excess = self.max_answer_length - self.optimal_answer_length
            penalty = (excess / max_excess) * 0.3
            return 1.0 - penalty
        else:
            # Very long - moderate penalty
            return 0.6

    def _calculate_specificity(self, answer: str) -> float:
        """Calculate answer specificity score.

        Based on:
        - Presence of specific details (numbers, dates)
        - Answer length
        - Hedging vs definitive language

        Returns:
            Specificity score between 0.0 and 1.0
        """
        if not answer:
            return 0.0

        # Length score (30% of specificity)
        length_score = self._calculate_length_score(answer)

        # Detail score - presence of specific information (40% of specificity)
        detail_count = self._count_specific_details(answer)
        if detail_count == 0:
            detail_score = 0.4  # Base score for no specific details
        elif detail_count == 1:
            detail_score = 0.7
        elif detail_count == 2:
            detail_score = 0.85
        else:
            detail_score = 1.0

        # Language score - hedging vs definitive (30% of specificity)
        hedging_level = self._detect_hedging(answer)
        definitiveness = self._detect_definitiveness(answer)

        # Hedging reduces score, definitiveness increases it
        language_score = 0.5 + (definitiveness * 0.5) - (hedging_level * 0.3)
        language_score = max(0.0, min(1.0, language_score))

        # Combine
        specificity = (length_score * 0.3) + (detail_score * 0.4) + (language_score * 0.3)

        return specificity

    def _calculate_consistency(
        self, answer: str, ground_truth: str | None, contexts: list[str] | None
    ) -> float:
        """Calculate consistency score.

        If ground_truth is available, checks overlap with ground_truth.
        Otherwise, relies on context coverage as proxy.

        Returns:
            Consistency score between 0.0 and 1.0
        """
        if not answer:
            return 0.0

        # If ground_truth available, use it
        if ground_truth:
            answer_tokens = _tokenize_with_stripping(answer)
            truth_tokens = _tokenize_with_stripping(ground_truth)

            if not truth_tokens:
                return 0.5  # Neutral if ground_truth is empty

            if not answer_tokens:
                return 0.0

            # Calculate recall - how much of ground_truth is in answer
            overlap = answer_tokens.intersection(truth_tokens)
            recall = len(overlap) / len(truth_tokens)

            # Also check precision
            precision = len(overlap) / len(answer_tokens) if answer_tokens else 0.0

            # F1-like combination
            if recall + precision > 0:
                consistency = 2 * (precision * recall) / (precision + recall)
            else:
                consistency = 0.0

            return consistency

        # If no ground_truth, use context coverage as proxy
        if contexts:
            return self._calculate_context_coverage(answer, contexts)

        # No evidence available - moderate confidence
        return 0.5

    def score(
        self,
        answer: str,
        ground_truth: str | None = None,
        contexts: list[str] | None = None,
    ) -> float:
        """Calculate confidence score.

        Args:
            answer: The generated answer to evaluate
            ground_truth: Optional reference answer (improves accuracy)
            contexts: Optional list of retrieved contexts

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not answer:
            return 0.0

        # Calculate component scores
        coverage_score = self._calculate_context_coverage(answer, contexts or [])
        specificity_score = self._calculate_specificity(answer)
        consistency_score = self._calculate_consistency(answer, ground_truth, contexts)

        # Weighted combination
        confidence = (
            self.coverage_weight * coverage_score
            + self.specificity_weight * specificity_score
            + self.consistency_weight * consistency_score
        )

        return round(confidence, 4)

    def score_detailed(
        self,
        answer: str,
        ground_truth: str | None = None,
        contexts: list[str] | None = None,
    ) -> dict:
        """Calculate detailed confidence metrics.

        Args:
            answer: The generated answer to evaluate
            ground_truth: Optional reference answer
            contexts: Optional list of retrieved contexts

        Returns:
            Dictionary with confidence score and component breakdowns
        """
        if not answer:
            return {
                "confidence_score": 0.0,
                "coverage_score": 0.0,
                "specificity_score": 0.0,
                "consistency_score": 0.0,
                "hedging_level": 0.0,
                "definitiveness_level": 0.0,
                "detail_count": 0,
                "answer_length": 0,
                "escalation_recommended": True,
            }

        # Calculate all components
        coverage_score = self._calculate_context_coverage(answer, contexts or [])
        specificity_score = self._calculate_specificity(answer)
        consistency_score = self._calculate_consistency(answer, ground_truth, contexts)

        hedging_level = self._detect_hedging(answer)
        definitiveness_level = self._detect_definitiveness(answer)
        detail_count = self._count_specific_details(answer)

        # Final confidence
        confidence = (
            self.coverage_weight * coverage_score
            + self.specificity_weight * specificity_score
            + self.consistency_weight * consistency_score
        )
        confidence = round(confidence, 4)

        # Escalation recommendation
        escalation_recommended = confidence < 0.7

        return {
            "confidence_score": confidence,
            "coverage_score": round(coverage_score, 4),
            "specificity_score": round(specificity_score, 4),
            "consistency_score": round(consistency_score, 4),
            "hedging_level": round(hedging_level, 4),
            "definitiveness_level": round(definitiveness_level, 4),
            "detail_count": detail_count,
            "answer_length": len(answer),
            "escalation_recommended": escalation_recommended,
        }

    def should_escalate(
        self,
        answer: str,
        ground_truth: str | None = None,
        contexts: list[str] | None = None,
        threshold: float = 0.7,
    ) -> bool:
        """Determine if answer should be escalated to human review.

        Args:
            answer: The generated answer
            ground_truth: Optional reference answer
            contexts: Optional list of contexts
            threshold: Confidence threshold for escalation (default: 0.7)

        Returns:
            True if confidence is below threshold (should escalate)
        """
        confidence = self.score(answer, ground_truth, contexts)
        return confidence < threshold
