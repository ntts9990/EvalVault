"""Insurance domain-specific evaluation metrics."""

import json
import re
from pathlib import Path


class InsuranceTermAccuracy:
    """보험 용어 정확성 메트릭.

    답변에 사용된 보험 용어들이 주어진 컨텍스트에 근거하고 있는지 평가합니다.

    Scoring:
    - 1.0: 답변의 모든 보험 용어가 컨텍스트에서 확인됨
    - 0.0 ~ 1.0: 부분적으로 확인됨
    - 0.0: 답변의 보험 용어가 컨텍스트에 없음
    """

    name = "insurance_term_accuracy"

    def __init__(self, terms_dict_path: str | Path | None = None):
        """Initialize InsuranceTermAccuracy metric.

        Args:
            terms_dict_path: Path to terms dictionary JSON file.
                           If None, uses default dictionary.
        """
        if terms_dict_path is None:
            terms_dict_path = Path(__file__).parent / "terms_dictionary.json"
        else:
            terms_dict_path = Path(terms_dict_path)

        with open(terms_dict_path, encoding="utf-8") as f:
            self.terms_dict = json.load(f)

    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing extra whitespace.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = re.sub(r"\s+", "", text)
        return text

    def _find_term_matches(self, text: str) -> set[str]:
        """Find all insurance terms (canonical forms) in text.

        Args:
            text: Text to search for insurance terms

        Returns:
            Set of canonical term names found in text
        """
        matched_terms = set()
        text_lower = text.lower()
        text_normalized = self._normalize_text(text)

        for canonical_term, term_data in self.terms_dict.items():
            # Check canonical form
            if canonical_term in text or canonical_term in text_normalized:
                matched_terms.add(canonical_term)
                continue

            # Check Korean variants
            for variant in term_data["variants"]:
                variant_normalized = self._normalize_text(variant)
                if variant in text or variant_normalized in text_normalized:
                    matched_terms.add(canonical_term)
                    break

            # Check English variants (case-insensitive)
            if "english" in term_data:
                for eng_term in term_data["english"]:
                    if eng_term.lower() in text_lower:
                        matched_terms.add(canonical_term)
                        break

        return matched_terms

    def _calculate_accuracy(self, answer: str, contexts: list[str]) -> float:
        """Calculate insurance term accuracy.

        Args:
            answer: The answer text to evaluate
            contexts: List of context strings

        Returns:
            Accuracy score between 0.0 and 1.0
        """
        # Find terms in answer
        answer_terms = self._find_term_matches(answer)

        # If no insurance terms in answer, return perfect score
        if not answer_terms:
            return 1.0

        # If contexts are empty, return 0 (can't verify)
        if not contexts:
            return 0.0

        # Find terms in all contexts (union)
        context_terms = set()
        for context in contexts:
            context_terms.update(self._find_term_matches(context))

        # Calculate how many answer terms are supported by contexts
        verified_terms = answer_terms.intersection(context_terms)
        accuracy = len(verified_terms) / len(answer_terms)

        return accuracy

    def score(self, answer: str, contexts: list[str]) -> float:
        """Calculate insurance term accuracy score.

        Args:
            answer: The answer text to evaluate
            contexts: List of context strings

        Returns:
            Accuracy score between 0.0 and 1.0
        """
        return self._calculate_accuracy(answer, contexts)
