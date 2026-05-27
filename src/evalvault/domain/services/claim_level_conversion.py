"""Claim-level result conversion.

Extracted from ``RagasEvaluator`` (D-S5f). Converts a Korean
``KoreanFaithfulnessChecker`` / ``FaithfulnessResult`` payload into the
domain ``ClaimLevelResult`` entity. Pure function — behaviour is identical
to the previous in-class implementation.
"""

from __future__ import annotations

from typing import Any

from evalvault.domain.entities import ClaimLevelResult, ClaimVerdict

# Partial-support threshold: coverage below this counts as "not_supported".
_PARTIAL_SUPPORT_THRESHOLD = 0.3


def convert_to_claim_level_result(faithfulness_result: Any, test_case_id: str) -> ClaimLevelResult:
    """Convert a KoreanFaithfulnessChecker result to a ClaimLevelResult.

    Args:
        faithfulness_result: FaithfulnessResult from KoreanNLPToolkit.
        test_case_id: Test case ID used for claim ID generation.

    Returns:
        ClaimLevelResult with converted claim verdicts.
    """
    claim_results = getattr(faithfulness_result, "claim_results", [])
    total_claims = getattr(faithfulness_result, "total_claims", len(claim_results))

    claims: list[ClaimVerdict] = []
    for idx, cr in enumerate(claim_results):
        claim_id = f"{test_case_id}-claim-{idx}" if test_case_id else f"claim-{idx}"
        claim_text = getattr(cr, "claim", "")
        is_faithful = getattr(cr, "is_faithful", False)
        coverage = getattr(cr, "coverage", 0.0)
        number_mismatch = getattr(cr, "number_mismatch", False)
        matched_keywords = getattr(cr, "matched_keywords", [])

        # Determine verdict string
        if is_faithful:
            verdict = "supported"
        elif number_mismatch:
            verdict = "not_supported"
        elif coverage >= _PARTIAL_SUPPORT_THRESHOLD:
            verdict = "partially_supported"
        else:
            verdict = "not_supported"

        # Build reason
        reason_parts = []
        if number_mismatch:
            reason_parts.append("숫자 불일치 발견")
        elif not is_faithful:
            reason_parts.append(f"키워드 매칭률 {coverage:.0%}")
        if matched_keywords:
            reason_parts.append(f"매칭된 키워드: {', '.join(matched_keywords[:5])}")

        claims.append(
            ClaimVerdict(
                claim_id=claim_id,
                claim_text=claim_text,
                verdict=verdict,
                confidence=coverage,
                reason=" | ".join(reason_parts) if reason_parts else None,
                source_context_indices=None,  # Korean NLP doesn't track source indices
            )
        )

    # Count verdicts
    not_supported = sum(1 for c in claims if c.verdict == "not_supported")
    partially_supported = sum(1 for c in claims if c.verdict == "partially_supported")
    supported = total_claims - not_supported - partially_supported

    return ClaimLevelResult(
        total_claims=total_claims,
        supported_claims=supported,
        not_supported_claims=not_supported,
        partially_supported_claims=partially_supported,
        claims=claims,
        extraction_method="korean_nlp",
    )
