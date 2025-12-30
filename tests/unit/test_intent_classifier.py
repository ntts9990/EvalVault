"""Phase 14.2: Intent Classifier 단위 테스트.

TDD Red Phase - 테스트 먼저 작성.
"""

from __future__ import annotations

# =============================================================================
# KeywordIntentClassifier Tests (Rule-based MVP)
# =============================================================================


class TestKeywordIntentClassifier:
    """KeywordIntentClassifier 테스트 - 키워드 기반 규칙 분류기."""

    def test_classify_verify_morpheme(self):
        """형태소 분석 검증 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        # 형태소 관련 쿼리
        queries = [
            "형태소 분석이 제대로 되고 있는지 확인해줘",
            "토큰화가 잘 되고 있는지 보고 싶어",
            "형태소 분석 결과를 검증해줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.VERIFY_MORPHEME, f"Failed for: {query}"

    def test_classify_verify_embedding(self):
        """임베딩 품질 검증 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "임베딩 품질을 확인하고 싶어",
            "벡터 표현이 적절한지 검증해줘",
            "임베딩 분포가 어떤지 분석해줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.VERIFY_EMBEDDING, f"Failed for: {query}"

    def test_classify_verify_retrieval(self):
        """검색 품질 검증 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "검색이 제대로 되고 있는지 확인해줘",
            "retrieval 품질을 검증하고 싶어",
            "컨텍스트 검색 결과를 확인해줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.VERIFY_RETRIEVAL, f"Failed for: {query}"

    def test_classify_compare_search_methods(self):
        """검색 방식 비교 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "RRF와 다른 하이브리드 방식의 성능을 비교하고 싶어",
            "BM25와 임베딩 검색을 비교해줘",
            "하이브리드 검색 방식들을 비교 분석해줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.COMPARE_SEARCH_METHODS, f"Failed for: {query}"

    def test_classify_compare_models(self):
        """모델 비교 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "GPT-4와 Claude 모델을 비교해줘",
            "모델별 성능 차이를 보고 싶어",
            "LLM 모델 성능 비교 분석",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.COMPARE_MODELS, f"Failed for: {query}"

    def test_classify_compare_runs(self):
        """실행 비교 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "이전 실행과 비교해줘",
            "두 평가 결과를 비교 분석해줘",
            "실행 결과의 차이를 보여줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.COMPARE_RUNS, f"Failed for: {query}"

    def test_classify_analyze_low_metrics(self):
        """낮은 메트릭 원인 분석 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "Context Recall이 낮은 이유를 분석해줘",
            "faithfulness가 떨어지는 원인이 뭐야",
            "메트릭이 낮은 케이스를 분석해줘",
            "왜 점수가 낮은지 알려줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.ANALYZE_LOW_METRICS, f"Failed for: {query}"

    def test_classify_analyze_patterns(self):
        """패턴 분석 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "패턴을 분석해줘",
            "질문 유형별 패턴을 보여줘",
            "어떤 패턴이 있는지 분석해줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.ANALYZE_PATTERNS, f"Failed for: {query}"

    def test_classify_analyze_trends(self):
        """추세 분석 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "시간에 따른 추세를 분석해줘",
            "트렌드 분석을 해줘",
            "성능 변화 추이를 보여줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.ANALYZE_TRENDS, f"Failed for: {query}"

    def test_classify_generate_summary(self):
        """요약 보고서 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "결과를 요약해줘",
            "요약 보고서를 만들어줘",
            "간단하게 정리해줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.GENERATE_SUMMARY, f"Failed for: {query}"

    def test_classify_generate_detailed(self):
        """상세 보고서 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "상세 보고서를 작성해줘",
            "자세한 분석 리포트를 만들어줘",
            "전체 평가 결과를 상세하게 보고서로 만들어줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.GENERATE_DETAILED, f"Failed for: {query}"

    def test_classify_generate_comparison(self):
        """비교 보고서 의도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        queries = [
            "비교 보고서를 만들어줘",
            "비교 리포트 생성해줘",
        ]

        for query in queries:
            intent = classifier.classify(query)
            assert intent == AnalysisIntent.GENERATE_COMPARISON, f"Failed for: {query}"

    def test_classify_with_confidence(self):
        """신뢰도와 함께 의도 분류."""
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        result = classifier.classify_with_confidence("형태소 분석을 확인해줘")

        assert result.confidence > 0
        assert result.confidence <= 1.0
        assert len(result.keywords) > 0

    def test_classify_with_confidence_high_confidence(self):
        """높은 신뢰도 분류."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        # 명확한 의도가 있는 쿼리
        result = classifier.classify_with_confidence("형태소 분석이 제대로 되고 있는지 확인해줘")

        assert result.intent == AnalysisIntent.VERIFY_MORPHEME
        assert result.is_confident  # 0.7 이상

    def test_classify_with_confidence_alternatives(self):
        """대안 의도 포함 분류."""
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        # 여러 의도와 관련될 수 있는 쿼리
        result = classifier.classify_with_confidence("검색 성능을 비교하고 분석해줘")

        # 주 의도 외에 대안 의도도 있을 수 있음
        assert result.intent is not None

    def test_extract_keywords(self):
        """키워드 추출."""
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        keywords = classifier.extract_keywords("형태소 분석이 제대로 되고 있는지 확인해줘")

        assert "형태소" in keywords or "분석" in keywords or "확인" in keywords

    def test_extract_keywords_multiple(self):
        """여러 키워드 추출."""
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        keywords = classifier.extract_keywords("RRF와 하이브리드 검색 방식을 비교 분석해줘")

        assert len(keywords) >= 1

    def test_default_intent_for_unknown_query(self):
        """알 수 없는 쿼리에 대한 기본 의도."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import KeywordIntentClassifier

        classifier = KeywordIntentClassifier()

        # 의도가 명확하지 않은 쿼리
        intent = classifier.classify("안녕하세요")

        # 기본값으로 요약 보고서 생성
        assert intent == AnalysisIntent.GENERATE_SUMMARY


# =============================================================================
# IntentKeywordRegistry Tests
# =============================================================================


class TestIntentKeywordRegistry:
    """IntentKeywordRegistry 테스트 - 의도별 키워드 매핑 레지스트리."""

    def test_registry_has_all_intents(self):
        """모든 의도에 대한 키워드가 등록되어 있는지 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()

        for intent in AnalysisIntent:
            keywords = registry.get_keywords(intent)
            assert len(keywords) > 0, f"No keywords for {intent}"

    def test_registry_get_keywords_for_verify_morpheme(self):
        """VERIFY_MORPHEME 의도의 키워드 조회."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()
        keywords = registry.get_keywords(AnalysisIntent.VERIFY_MORPHEME)

        assert "형태소" in keywords
        assert "토큰" in keywords or "토큰화" in keywords

    def test_registry_match_intent(self):
        """쿼리에서 의도 매칭."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()

        matches = registry.match_query("형태소 분석을 확인하고 싶어")

        assert len(matches) > 0
        # 매칭 결과는 (AnalysisIntent, score) 튜플
        assert any(m[0] == AnalysisIntent.VERIFY_MORPHEME for m in matches)

    def test_registry_match_intent_scored(self):
        """의도 매칭 점수 확인."""
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()

        matches = registry.match_query("형태소 분석을 확인하고 싶어")

        # 점수가 높은 순으로 정렬되어야 함
        if len(matches) > 1:
            assert matches[0][1] >= matches[1][1]

    def test_registry_add_custom_keywords(self):
        """커스텀 키워드 추가."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()

        # 커스텀 키워드 추가
        registry.add_keywords(AnalysisIntent.VERIFY_MORPHEME, ["커스텀", "테스트"])

        keywords = registry.get_keywords(AnalysisIntent.VERIFY_MORPHEME)
        assert "커스텀" in keywords
        assert "테스트" in keywords


# =============================================================================
# PipelineTemplateRegistry Tests
# =============================================================================


class TestPipelineTemplateRegistry:
    """PipelineTemplateRegistry 테스트 - 의도별 파이프라인 템플릿."""

    def test_registry_has_template_for_verify_morpheme(self):
        """VERIFY_MORPHEME 의도의 파이프라인 템플릿."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        template = registry.get_template(AnalysisIntent.VERIFY_MORPHEME)

        assert template is not None
        assert len(template.nodes) > 0

    def test_registry_has_template_for_compare_search(self):
        """COMPARE_SEARCH_METHODS 의도의 파이프라인 템플릿."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        template = registry.get_template(AnalysisIntent.COMPARE_SEARCH_METHODS)

        assert template is not None
        # 검색 비교에는 최소 데이터 로드, 검색 실행, 비교 노드가 필요
        assert len(template.nodes) >= 3

    def test_template_has_valid_dag(self):
        """템플릿이 유효한 DAG인지 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()

        for intent in AnalysisIntent:
            template = registry.get_template(intent)
            if template:
                assert template.validate(), f"Invalid DAG for {intent}"

    def test_template_topological_order(self):
        """템플릿의 위상 정렬 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        template = registry.get_template(AnalysisIntent.VERIFY_MORPHEME)

        order = template.topological_order()

        # 순서가 노드 수와 일치해야 함 (순환 없음)
        assert len(order) == template.node_count

    def test_list_all_templates(self):
        """모든 템플릿 목록 조회."""
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        templates = registry.list_all()

        assert len(templates) > 0
