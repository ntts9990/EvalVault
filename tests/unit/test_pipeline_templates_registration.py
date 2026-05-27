"""D-S4 smoke test: PipelineTemplateRegistry 등록 무결성.

per-category 모듈 분리 후에도 22개의 ``AnalysisIntent`` 가 모두
``PipelineTemplateRegistry`` 에 의해 등록·조회 가능한지 확인합니다.
"""

from __future__ import annotations

import pytest

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisIntent,
    AnalysisPipeline,
)
from evalvault.domain.services.pipeline_template_registry import (
    PipelineTemplateRegistry,
)

EXPECTED_INTENTS: tuple[AnalysisIntent, ...] = (
    # verify_*
    AnalysisIntent.VERIFY_MORPHEME,
    AnalysisIntent.VERIFY_EMBEDDING,
    AnalysisIntent.VERIFY_RETRIEVAL,
    # compare_*
    AnalysisIntent.COMPARE_SEARCH_METHODS,
    AnalysisIntent.COMPARE_MODELS,
    AnalysisIntent.COMPARE_RUNS,
    # analyze_*
    AnalysisIntent.ANALYZE_LOW_METRICS,
    AnalysisIntent.ANALYZE_PATTERNS,
    AnalysisIntent.ANALYZE_TRENDS,
    AnalysisIntent.ANALYZE_STATISTICAL,
    AnalysisIntent.ANALYZE_NLP,
    AnalysisIntent.ANALYZE_DATASET_FEATURES,
    AnalysisIntent.ANALYZE_CAUSAL,
    AnalysisIntent.ANALYZE_NETWORK,
    AnalysisIntent.ANALYZE_PLAYBOOK,
    # generate_*
    AnalysisIntent.GENERATE_HYPOTHESES,
    AnalysisIntent.GENERATE_SUMMARY,
    AnalysisIntent.GENERATE_DETAILED,
    AnalysisIntent.GENERATE_COMPARISON,
    # other (detect / forecast / benchmark)
    AnalysisIntent.DETECT_ANOMALIES,
    AnalysisIntent.FORECAST_PERFORMANCE,
    AnalysisIntent.BENCHMARK_RETRIEVAL,
)


@pytest.fixture(scope="module")
def registry() -> PipelineTemplateRegistry:
    return PipelineTemplateRegistry()


@pytest.mark.parametrize("intent", EXPECTED_INTENTS, ids=lambda i: i.value)
def test_get_template_resolves_every_expected_intent(
    registry: PipelineTemplateRegistry, intent: AnalysisIntent
) -> None:
    """등록된 모든 의도가 get_template/get 모두에서 인스턴스를 반환해야 한다."""
    template = registry.get_template(intent)
    assert template is not None, f"missing get_template for {intent}"
    assert isinstance(template, AnalysisPipeline)
    assert template.intent == intent
    assert template is registry.get(intent)


def test_list_all_covers_expected_intents(registry: PipelineTemplateRegistry) -> None:
    """list_all 결과가 기대 의도 22개를 빠짐없이 포함해야 한다."""
    registered = {intent for intent, _ in registry.list_all()}
    missing = set(EXPECTED_INTENTS) - registered
    extra = registered - set(EXPECTED_INTENTS)
    assert not missing, f"missing intents: {sorted(i.value for i in missing)}"
    assert not extra, f"unexpected extras: {sorted(i.value for i in extra)}"


def test_registry_register_overrides_existing_builder(
    registry: PipelineTemplateRegistry,
) -> None:
    """register() 콜백으로 동적 빌더 교체가 가능해야 한다 (D-S4 신규 API)."""
    intent = AnalysisIntent.VERIFY_MORPHEME
    original = registry.get_template(intent)
    sentinel = AnalysisPipeline(intent=intent, nodes=[])
    registry.register(intent, lambda: sentinel)
    try:
        assert registry.get_template(intent) is sentinel
    finally:
        # 모듈 스코프 fixture 이므로 원복하여 다른 테스트에 영향이 없도록 한다.
        assert original is not None
        registry.register(intent, lambda original=original: original)
        assert registry.get_template(intent) is original
