import pytest

from evalvault.domain.metrics.entity_preservation import EntityPreservation


def test_entity_preservation_full_match() -> None:
    metric = EntityPreservation()
    contexts = [
        "면책 사유는 제외되며 자기부담 20%가 적용됩니다.",
        "보장 조건은 30일 이후부터 가능합니다.",
    ]
    answer = "면책 제외 조건이며 자기부담 20%와 30일 적용을 요약했습니다."

    score = metric.score(answer=answer, contexts=contexts)

    assert score == pytest.approx(1.0)


def test_entity_preservation_missing_keyword() -> None:
    metric = EntityPreservation()
    contexts = ["면책 사유는 제외되며 자기부담 20%가 적용됩니다."]
    answer = "자기부담 20%가 적용됩니다."

    score = metric.score(answer=answer, contexts=contexts)

    assert score == pytest.approx(0.5)


def test_entity_preservation_currency_normalization() -> None:
    metric = EntityPreservation()
    contexts = ["보험금 한도는 3만원입니다."]
    answer = "보험금 한도는 30000원입니다."

    score = metric.score(answer=answer, contexts=contexts)

    assert score == pytest.approx(1.0)


def test_entity_preservation_empty_contexts() -> None:
    metric = EntityPreservation()

    score = metric.score(answer="요약입니다.", contexts=[])

    assert score == pytest.approx(0.0)
