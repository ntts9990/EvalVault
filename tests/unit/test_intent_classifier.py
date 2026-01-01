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

    def test_registry_add_keywords_to_new_intent(self):
        """새로운 의도에 키워드 추가."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()
        # Clear existing keywords for testing
        registry._keywords = {}

        # Add keywords to a new intent
        registry.add_keywords(AnalysisIntent.VERIFY_MORPHEME, ["새로운", "키워드"])

        keywords = registry.get_keywords(AnalysisIntent.VERIFY_MORPHEME)
        assert "새로운" in keywords
        assert "키워드" in keywords

    def test_registry_get_keywords_for_unknown_intent(self):
        """알 수 없는 의도에 대한 빈 키워드 반환."""
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()
        # Clear all keywords
        registry._keywords = {}

        # Should return empty set for unknown intent
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        keywords = registry.get_keywords(AnalysisIntent.VERIFY_MORPHEME)
        assert keywords == set()

    def test_registry_match_query_empty(self):
        """빈 쿼리에 대한 매칭."""
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()
        matches = registry.match_query("")

        # May return matches if any keywords match empty string, or empty
        assert isinstance(matches, list)

    def test_registry_match_query_case_insensitive(self):
        """대소문자 구분 없는 매칭."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()

        # Test with uppercase query
        matches = registry.match_query("EMBEDDING 분석")

        assert len(matches) > 0
        # Should match VERIFY_EMBEDDING intent
        intent_ids = [m[0] for m in matches]
        assert AnalysisIntent.VERIFY_EMBEDDING in intent_ids

    def test_registry_match_query_phrase_scoring(self):
        """긴 키워드(구)에 대한 높은 점수."""
        from evalvault.domain.services.intent_classifier import IntentKeywordRegistry

        registry = IntentKeywordRegistry()

        # "비교 보고서" is a phrase (2 words), should get higher score
        matches = registry.match_query("비교 보고서를 만들어줘")

        assert len(matches) > 0
        # First match should have score > 2 for phrase
        top_intent, top_score = matches[0]
        assert top_score >= 2


# =============================================================================
# IntentClassificationResult Tests
# =============================================================================


class TestIntentClassificationResult:
    """IntentClassificationResult 테스트 - 분류 결과 데이터 클래스."""

    def test_result_creation(self):
        """결과 생성."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.ports.outbound.intent_classifier_port import (
            IntentClassificationResult,
        )

        result = IntentClassificationResult(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            confidence=0.85,
            keywords=["형태소", "분석"],
            alternative_intents=[
                (AnalysisIntent.VERIFY_EMBEDDING, 0.6),
            ],
        )

        assert result.intent == AnalysisIntent.VERIFY_MORPHEME
        assert result.confidence == 0.85
        assert result.keywords == ["형태소", "분석"]
        assert len(result.alternative_intents) == 1

    def test_result_is_confident_property_true(self):
        """신뢰도 0.7 이상일 때 is_confident=True."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.ports.outbound.intent_classifier_port import (
            IntentClassificationResult,
        )

        result = IntentClassificationResult(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            confidence=0.75,
        )

        assert result.is_confident is True

    def test_result_is_confident_property_false(self):
        """신뢰도 0.7 미만일 때 is_confident=False."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.ports.outbound.intent_classifier_port import (
            IntentClassificationResult,
        )

        result = IntentClassificationResult(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            confidence=0.65,
        )

        assert result.is_confident is False

    def test_result_is_confident_boundary(self):
        """신뢰도 정확히 0.7일 때 is_confident=True."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.ports.outbound.intent_classifier_port import (
            IntentClassificationResult,
        )

        result = IntentClassificationResult(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            confidence=0.7,
        )

        assert result.is_confident is True

    def test_result_has_alternatives_true(self):
        """대안 의도가 있을 때 has_alternatives=True."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.ports.outbound.intent_classifier_port import (
            IntentClassificationResult,
        )

        result = IntentClassificationResult(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            confidence=0.8,
            alternative_intents=[
                (AnalysisIntent.VERIFY_EMBEDDING, 0.5),
            ],
        )

        assert result.has_alternatives is True

    def test_result_has_alternatives_false(self):
        """대안 의도가 없을 때 has_alternatives=False."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.ports.outbound.intent_classifier_port import (
            IntentClassificationResult,
        )

        result = IntentClassificationResult(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            confidence=0.9,
            alternative_intents=[],
        )

        assert result.has_alternatives is False

    def test_result_default_values(self):
        """기본값 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.ports.outbound.intent_classifier_port import (
            IntentClassificationResult,
        )

        result = IntentClassificationResult(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            confidence=0.5,
        )

        assert result.keywords == []
        assert result.alternative_intents == []

    def test_result_with_multiple_alternatives(self):
        """여러 대안 의도."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.ports.outbound.intent_classifier_port import (
            IntentClassificationResult,
        )

        result = IntentClassificationResult(
            intent=AnalysisIntent.COMPARE_SEARCH_METHODS,
            confidence=0.6,
            alternative_intents=[
                (AnalysisIntent.COMPARE_MODELS, 0.5),
                (AnalysisIntent.COMPARE_RUNS, 0.4),
                (AnalysisIntent.ANALYZE_LOW_METRICS, 0.3),
            ],
        )

        assert len(result.alternative_intents) == 3
        assert result.alternative_intents[0][0] == AnalysisIntent.COMPARE_MODELS
        assert result.alternative_intents[0][1] == 0.5


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

    def test_registry_has_all_intents(self):
        """모든 의도에 대한 템플릿이 등록되어 있는지 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()

        for intent in AnalysisIntent:
            template = registry.get_template(intent)
            assert template is not None, f"No template for {intent}"
            assert template.intent == intent

    def test_analyze_low_metrics_template_structure(self):
        """ANALYZE_LOW_METRICS 템플릿 구조 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        template = registry.get_template(AnalysisIntent.ANALYZE_LOW_METRICS)

        assert template is not None
        # This template should have multiple analysis stages
        assert len(template.nodes) >= 4
        # Should include data loading, evaluation, and analysis nodes
        node_ids = {n.id for n in template.nodes}
        assert "load_data" in node_ids
        assert "report" in node_ids

    def test_compare_search_template_has_parallel_nodes(self):
        """COMPARE_SEARCH_METHODS 템플릿에 병렬 노드가 있는지 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        template = registry.get_template(AnalysisIntent.COMPARE_SEARCH_METHODS)

        assert template is not None
        # Should have BM25 and embedding search that can run in parallel
        node_ids = {n.id for n in template.nodes}
        assert "bm25_search" in node_ids
        assert "embedding_search" in node_ids

        # These should depend on different parent nodes or same root
        bm25_node = template.get_node("bm25_search")
        embedding_node = template.get_node("embedding_search")

        # Verify neither depends on the other (parallel execution possible)
        assert "embedding_search" not in bm25_node.depends_on
        assert "bm25_search" not in embedding_node.depends_on

    def test_generate_detailed_template_has_multiple_analysis_paths(self):
        """GENERATE_DETAILED 템플릿에 여러 분석 경로가 있는지 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        template = registry.get_template(AnalysisIntent.GENERATE_DETAILED)

        assert template is not None
        # Should include statistics, NLP, and causal analysis
        node_modules = {n.module for n in template.nodes}
        assert "statistical_analyzer" in node_modules
        assert "nlp_analyzer" in node_modules
        assert "causal_analyzer" in node_modules

    def test_template_root_nodes(self):
        """템플릿의 루트 노드 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        template = registry.get_template(AnalysisIntent.VERIFY_MORPHEME)

        roots = template.root_nodes
        assert len(roots) >= 1
        # First node should be a data loader typically
        root_modules = {n.module for n in roots}
        assert "data_loader" in root_modules

    def test_template_leaf_nodes(self):
        """템플릿의 리프 노드 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        template = registry.get_template(AnalysisIntent.GENERATE_SUMMARY)

        leaves = template.leaf_nodes
        assert len(leaves) >= 1
        # Last node should be a report generator
        leaf_ids = {n.id for n in leaves}
        assert "report" in leaf_ids

    def test_all_templates_are_valid_dags(self):
        """모든 템플릿이 유효한 DAG인지 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()

        for intent in AnalysisIntent:
            template = registry.get_template(intent)
            assert template.validate(), f"Invalid DAG for {intent}"
            # Topological order should include all nodes
            order = template.topological_order()
            assert len(order) == len(template.nodes), f"Incomplete order for {intent}"

    def test_list_all_returns_tuples(self):
        """list_all이 (intent, pipeline) 튜플 목록을 반환하는지 확인."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisPipeline,
        )
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()
        templates = registry.list_all()

        for item in templates:
            assert isinstance(item, tuple)
            assert len(item) == 2
            intent, pipeline = item
            assert isinstance(intent, AnalysisIntent)
            assert isinstance(pipeline, AnalysisPipeline)

    def test_template_nodes_have_valid_dependencies(self):
        """템플릿 노드의 의존성이 유효한지 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_template_registry import (
            PipelineTemplateRegistry,
        )

        registry = PipelineTemplateRegistry()

        for intent in AnalysisIntent:
            template = registry.get_template(intent)
            node_ids = {n.id for n in template.nodes}

            for node in template.nodes:
                for dep_id in node.depends_on:
                    assert dep_id in node_ids, f"Invalid dependency {dep_id} in {intent} template"
