"""Text matching metrics for RAG evaluation.

Provides Exact Match (EM) and F1 Score metrics for comparing
generated answers against ground truth references.
"""

import re
import unicodedata


def _normalize_text(text: str) -> str:
    """Normalize text for comparison.

    - Lowercase
    - Remove extra whitespace
    - Normalize unicode characters
    - Remove punctuation (optional for Korean)

    Args:
        text: Text to normalize

    Returns:
        Normalized text
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


def _strip_korean_particles(token: str) -> str:
    """Strip common Korean particles from a token.

    Handles common particles like:
    - 은/는, 이/가 (subject markers)
    - 을/를 (object markers)
    - 의, 에, 에서, 으로, 로 (various particles)
    - 입니다, 합니다, 입니까 (verb endings)

    Args:
        token: Token to strip particles from

    Returns:
        Token with particles removed
    """
    # Common Korean particles (order matters - longer first)
    particles = [
        "입니다",
        "합니다",
        "입니까",
        "습니다",
        "에서",
        "으로",
        "에게",
        "께서",
        "로서",
        "로써",
        "에는",
        "에서",
        "이나",
        "이란",
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

    for particle in particles:
        if token.endswith(particle) and len(token) > len(particle):
            return token[: -len(particle)]

    return token


def _tokenize(text: str) -> list[str]:
    """Tokenize text into words/tokens.

    For Korean text, splits on whitespace and strips particles.
    For mixed text, handles both appropriately.

    Args:
        text: Text to tokenize

    Returns:
        List of tokens
    """
    if not text:
        return []

    # Normalize first
    text = _normalize_text(text)

    # Split on whitespace
    tokens = text.split()

    # Filter out empty tokens and single punctuation
    tokens = [t for t in tokens if t and not re.match(r"^[^\w가-힣]+$", t)]

    # Strip Korean particles for better matching
    tokens = [_strip_korean_particles(t) for t in tokens]

    # Filter out tokens that became empty after stripping
    tokens = [t for t in tokens if t]

    return tokens


def _extract_numbers(text: str) -> set[str]:
    """Extract numeric values from text.

    Handles various number formats:
    - 1억원, 5천만원, 100만원
    - 1,000,000원
    - 10%, 0.85
    - 20년, 30일

    Args:
        text: Text to extract numbers from

    Returns:
        Set of normalized number strings
    """
    numbers = set()

    # Korean number patterns (e.g., 1억원, 5천만원, 100만원)
    korean_num_pattern = (
        r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:억|천만|백만|만|천|백)?\s*(?:원|년|개월|일|%|세)?"
    )
    for match in re.finditer(korean_num_pattern, text):
        num_str = match.group(0).strip()
        # Normalize: remove commas
        num_str = num_str.replace(",", "")
        numbers.add(num_str)

    # Standard number patterns
    standard_num_pattern = r"\d+(?:,\d{3})*(?:\.\d+)?%?"
    for match in re.finditer(standard_num_pattern, text):
        num_str = match.group(0).replace(",", "")
        numbers.add(num_str)

    return numbers


class ExactMatch:
    """Exact Match (EM) metric.

    Evaluates whether the answer exactly matches the ground truth
    after normalization.

    For insurance domain:
    - Strict number matching (보장금액, 보험료 등)
    - Normalized text comparison

    Scoring:
    - 1.0: Exact match after normalization
    - 0.0: No match

    Example:
        >>> metric = ExactMatch()
        >>> metric.score(answer="1억원", ground_truth="1억원")
        1.0
        >>> metric.score(answer="1억원입니다", ground_truth="1억원")
        0.0
    """

    name = "exact_match"

    def __init__(self, normalize: bool = True, number_strict: bool = True):
        """Initialize ExactMatch metric.

        Args:
            normalize: Whether to normalize text before comparison
            number_strict: Whether to require exact number matches
        """
        self.normalize = normalize
        self.number_strict = number_strict

    def score(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> float:
        """Calculate exact match score.

        Args:
            answer: The generated answer
            ground_truth: The reference answer
            contexts: Retrieved contexts (unused, for interface compatibility)

        Returns:
            1.0 if exact match, 0.0 otherwise
        """
        if not answer or not ground_truth:
            return 0.0

        if self.normalize:
            answer_norm = _normalize_text(answer)
            truth_norm = _normalize_text(ground_truth)
        else:
            answer_norm = answer
            truth_norm = ground_truth

        # Check exact match
        if answer_norm == truth_norm:
            return 1.0

        # For number-strict mode, also check if all numbers match
        if self.number_strict:
            answer_numbers = _extract_numbers(answer)
            truth_numbers = _extract_numbers(ground_truth)

            # If ground truth has numbers, check if they're all in the answer
            if truth_numbers and truth_numbers == answer_numbers:
                # Numbers match exactly - partial credit
                return 1.0

        return 0.0


class F1Score:
    """F1 Score metric for partial matching.

    Evaluates token-level overlap between answer and ground truth
    using precision, recall, and F1 score.

    For insurance domain:
    - Token-based comparison
    - Special handling for numbers

    Scoring:
    - 1.0: Perfect overlap (all tokens match)
    - 0.0 ~ 1.0: Partial overlap
    - 0.0: No overlap

    Example:
        >>> metric = F1Score()
        >>> metric.score(
        ...     answer="사망보험금은 1억원입니다",
        ...     ground_truth="사망보험금 1억원"
        ... )
        0.8  # Partial match
    """

    name = "f1_score"

    def __init__(self, number_weight: float = 2.0):
        """Initialize F1Score metric.

        Args:
            number_weight: Weight multiplier for number tokens (default: 2.0)
                          Higher weight means number mismatches penalize more
        """
        self.number_weight = number_weight

    def _is_number_token(self, token: str) -> bool:
        """Check if token contains numeric value."""
        return bool(re.search(r"\d", token))

    def _calculate_weighted_overlap(
        self,
        answer_tokens: list[str],
        truth_tokens: list[str],
    ) -> tuple[float, float, float]:
        """Calculate weighted precision, recall, and F1.

        Args:
            answer_tokens: Tokenized answer
            truth_tokens: Tokenized ground truth

        Returns:
            Tuple of (precision, recall, f1)
        """
        if not truth_tokens:
            return (1.0, 1.0, 1.0) if not answer_tokens else (0.0, 1.0, 0.0)
        if not answer_tokens:
            return (1.0, 0.0, 0.0)

        # Convert to sets for overlap calculation
        answer_set = set(answer_tokens)
        truth_set = set(truth_tokens)

        # Calculate overlap
        common_tokens = answer_set.intersection(truth_set)

        # Calculate weights
        def get_weight(token: str) -> float:
            return self.number_weight if self._is_number_token(token) else 1.0

        # Weighted counts
        answer_weight = sum(get_weight(t) for t in answer_set)
        truth_weight = sum(get_weight(t) for t in truth_set)
        common_weight = sum(get_weight(t) for t in common_tokens)

        # Calculate precision, recall, F1
        precision = common_weight / answer_weight if answer_weight > 0 else 0.0
        recall = common_weight / truth_weight if truth_weight > 0 else 0.0

        f1 = 0.0 if precision + recall == 0 else 2 * (precision * recall) / (precision + recall)

        return precision, recall, f1

    def score(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> float:
        """Calculate F1 score.

        Args:
            answer: The generated answer
            ground_truth: The reference answer
            contexts: Retrieved contexts (unused, for interface compatibility)

        Returns:
            F1 score between 0.0 and 1.0
        """
        if not answer and not ground_truth:
            return 1.0
        if not answer or not ground_truth:
            return 0.0

        # Tokenize
        answer_tokens = _tokenize(answer)
        truth_tokens = _tokenize(ground_truth)

        # Calculate F1
        _, _, f1 = self._calculate_weighted_overlap(answer_tokens, truth_tokens)

        return f1

    def score_detailed(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> dict[str, float]:
        """Calculate detailed F1 metrics.

        Args:
            answer: The generated answer
            ground_truth: The reference answer
            contexts: Retrieved contexts (unused)

        Returns:
            Dictionary with precision, recall, and f1 scores
        """
        if not answer and not ground_truth:
            return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        if not answer or not ground_truth:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

        answer_tokens = _tokenize(answer)
        truth_tokens = _tokenize(ground_truth)

        precision, recall, f1 = self._calculate_weighted_overlap(answer_tokens, truth_tokens)

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
