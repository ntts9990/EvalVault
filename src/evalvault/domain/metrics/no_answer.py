"""No-answer accuracy metric for RAG evaluation.

Evaluates whether the model correctly abstains from answering
when the information is not available in the context.
This is critical for preventing hallucinations in insurance domain.
"""

import re

# Korean no-answer patterns
_KOREAN_NO_ANSWER_PATTERNS = [
    r"정보\s*없",
    r"정보.{0,3}없",  # 정보가 없습니다, 정보는 없습니다
    r"답변\s*불가",
    r"알\s*수\s*없",
    r"확인\s*불가",
    r"찾을\s*수\s*없",
    r"제공\s*불가",
    r"문서에\s*없",
    r"내용이?\s*없",
    r"해당\s*정보.{0,3}없",  # 해당 정보가 없습니다
    r"관련\s*정보.{0,3}없",
    r"언급.{0,10}(?:없|않)",  # 언급되어 있지 않습니다, 언급 없음
    r"명시.{0,10}(?:없|않)",  # 명시되어 있지 않습니다, 명시 없음
    r"기재\s*없",
    r"포함\s*없",
    r"존재하지\s*않",
    r"나와\s*있지\s*않",
    r"나타나\s*있지\s*않",
    r"확인되지\s*않",
    r"파악\s*불가",
    r"드리기\s*어렵",
    r"답변\s*드리기\s*어렵",
    r"말씀\s*드리기\s*어렵",
    r"없음$",  # ends with 없음
]

# English no-answer patterns
_ENGLISH_NO_ANSWER_PATTERNS = [
    r"no\s+answer",
    r"no\s+information",
    r"not\s+found",
    r"not\s+available",
    r"cannot\s+answer",
    r"can\s*not\s+answer",
    r"unable\s+to\s+answer",
    r"don'?t\s+know",
    r"do\s+not\s+know",
    r"not\s+mentioned",
    r"not\s+specified",
    r"not\s+provided",
    r"no\s+relevant",
    r"insufficient\s+information",
    r"cannot\s+determine",
    r"can\s*not\s+determine",
    r"unknown",
    r"n/?a\b",
    r"none\b",
]

# Combined pattern (compiled for efficiency)
_NO_ANSWER_PATTERN = re.compile(
    "|".join(_KOREAN_NO_ANSWER_PATTERNS + _ENGLISH_NO_ANSWER_PATTERNS),
    re.IGNORECASE,
)


def _is_no_answer(text: str) -> bool:
    """Check if text indicates a no-answer response.

    Detects various Korean and English patterns that indicate
    the system is abstaining from providing an answer.

    Args:
        text: Text to check

    Returns:
        True if the text indicates no-answer, False otherwise
    """
    if not text or not text.strip():
        # Empty response could be considered no-answer
        return True

    text_lower = text.lower().strip()

    # Check for explicit no-answer markers
    if _NO_ANSWER_PATTERN.search(text_lower):
        return True

    # Very short responses are often no-answer
    # (but not if they contain numbers which might be valid answers)
    if len(text_lower) < 10 and not re.search(r"\d", text_lower):
        # Check for common short no-answer phrases
        short_no_answers = {"없음", "불가", "모름", "none", "n/a", "na", "-", "—"}
        if text_lower in short_no_answers:
            return True

    return False


class NoAnswerAccuracy:
    """No-answer accuracy metric.

    Evaluates whether the model correctly handles cases where
    the answer is not available in the provided context.

    This metric is crucial for preventing hallucinations:
    - When ground_truth indicates "no answer", the model should abstain
    - When ground_truth has an answer, the model should NOT abstain

    Scoring:
    - 1.0: Correct behavior (both abstain OR both provide answer)
    - 0.0: Incorrect behavior (mismatch between expected and actual)

    Detailed classification:
    - true_abstention: Both correctly indicate no answer
    - false_abstention: Model abstains when answer exists
    - hallucination: Model answers when should abstain
    - true_answer: Both provide an answer (correctness checked by other metrics)

    Example:
        >>> metric = NoAnswerAccuracy()
        >>> metric.score(answer="정보 없음", ground_truth="정보 없음")
        1.0
        >>> metric.score(answer="1억원입니다", ground_truth="정보 없음")
        0.0  # Hallucination detected
    """

    name = "no_answer_accuracy"

    def __init__(
        self,
        custom_patterns: list[str] | None = None,
        strict_mode: bool = False,
    ):
        """Initialize NoAnswerAccuracy metric.

        Args:
            custom_patterns: Additional regex patterns to detect no-answer
            strict_mode: If True, requires explicit no-answer marker;
                        If False (default), uses broader detection
        """
        self.strict_mode = strict_mode

        if custom_patterns:
            # Compile pattern with custom additions
            all_patterns = (
                _KOREAN_NO_ANSWER_PATTERNS + _ENGLISH_NO_ANSWER_PATTERNS + custom_patterns
            )
            self._pattern = re.compile("|".join(all_patterns), re.IGNORECASE)
        else:
            self._pattern = _NO_ANSWER_PATTERN

    def _check_no_answer(self, text: str) -> bool:
        """Check if text is a no-answer response.

        Args:
            text: Text to check

        Returns:
            True if no-answer, False otherwise
        """
        if not text or not text.strip():
            return True

        text_lower = text.lower().strip()

        if self._pattern.search(text_lower):
            return True

        # Broader detection for non-strict mode
        if not self.strict_mode and len(text_lower) < 10 and not re.search(r"\d", text_lower):
            short_no_answers = {"없음", "불가", "모름", "none", "n/a", "na", "-", "—"}
            if text_lower in short_no_answers:
                return True

        return False

    def score(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> float:
        """Calculate no-answer accuracy score.

        Args:
            answer: The generated answer
            ground_truth: The reference answer (may indicate "no answer")
            contexts: Retrieved contexts (unused, for interface compatibility)

        Returns:
            1.0 if behavior matches expectation, 0.0 otherwise
        """
        answer_is_no_answer = self._check_no_answer(answer)
        truth_is_no_answer = self._check_no_answer(ground_truth)

        # Both should match: either both no-answer or both have answer
        if answer_is_no_answer == truth_is_no_answer:
            return 1.0
        return 0.0

    def score_detailed(
        self,
        answer: str,
        ground_truth: str,
        contexts: list[str] | None = None,
    ) -> dict:
        """Calculate detailed no-answer accuracy metrics.

        Args:
            answer: The generated answer
            ground_truth: The reference answer
            contexts: Retrieved contexts (unused)

        Returns:
            Dictionary with classification and details
        """
        answer_is_no_answer = self._check_no_answer(answer)
        truth_is_no_answer = self._check_no_answer(ground_truth)

        # Determine classification
        if truth_is_no_answer and answer_is_no_answer:
            classification = "true_abstention"
            score = 1.0
            description = "Correctly abstained from answering"
        elif truth_is_no_answer and not answer_is_no_answer:
            classification = "hallucination"
            score = 0.0
            description = "Hallucination: provided answer when should abstain"
        elif not truth_is_no_answer and answer_is_no_answer:
            classification = "false_abstention"
            score = 0.0
            description = "False abstention: abstained when answer was available"
        else:
            classification = "true_answer"
            score = 1.0
            description = "Correctly attempted to answer"

        return {
            "score": score,
            "classification": classification,
            "description": description,
            "answer_is_no_answer": answer_is_no_answer,
            "ground_truth_is_no_answer": truth_is_no_answer,
        }


# Utility function for external use
def is_no_answer(text: str) -> bool:
    """Check if text indicates a no-answer response.

    This is a convenience function for external use.

    Args:
        text: Text to check

    Returns:
        True if the text indicates no-answer, False otherwise
    """
    return _is_no_answer(text)
