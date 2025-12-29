"""Tests for NLP analysis domain entities."""

import pytest

from evalvault.domain.entities.analysis import (
    KeywordInfo,
    NLPAnalysis,
    QuestionType,
    QuestionTypeStats,
    TextStats,
    TopicCluster,
)


class TestTextStats:
    """TextStats 엔티티 테스트."""

    def test_create_text_stats(self):
        """TextStats 생성 테스트."""
        stats = TextStats(
            char_count=1000,
            word_count=150,
            sentence_count=10,
            avg_word_length=5.5,
            unique_word_ratio=0.8,
        )

        assert stats.char_count == 1000
        assert stats.word_count == 150
        assert stats.sentence_count == 10
        assert stats.avg_word_length == 5.5
        assert stats.unique_word_ratio == 0.8

    def test_text_stats_avg_sentence_length(self):
        """평균 문장 길이 계산 테스트."""
        stats = TextStats(
            char_count=500,
            word_count=100,
            sentence_count=5,
            avg_word_length=4.0,
            unique_word_ratio=0.7,
        )

        # 평균 문장 길이 = word_count / sentence_count
        assert stats.avg_sentence_length == pytest.approx(20.0)

    def test_text_stats_avg_sentence_length_zero_sentences(self):
        """문장이 0개일 때 평균 문장 길이 테스트."""
        stats = TextStats(
            char_count=0,
            word_count=0,
            sentence_count=0,
            avg_word_length=0.0,
            unique_word_ratio=0.0,
        )

        assert stats.avg_sentence_length == 0.0


class TestQuestionType:
    """QuestionType enum 테스트."""

    def test_question_type_values(self):
        """QuestionType 값 테스트."""
        assert QuestionType.FACTUAL.value == "factual"
        assert QuestionType.REASONING.value == "reasoning"
        assert QuestionType.COMPARATIVE.value == "comparative"
        assert QuestionType.PROCEDURAL.value == "procedural"
        assert QuestionType.OPINION.value == "opinion"


class TestQuestionTypeStats:
    """QuestionTypeStats 엔티티 테스트."""

    def test_create_question_type_stats(self):
        """QuestionTypeStats 생성 테스트."""
        stats = QuestionTypeStats(
            question_type=QuestionType.FACTUAL,
            count=50,
            percentage=0.5,
            avg_scores={"faithfulness": 0.85, "answer_relevancy": 0.78},
        )

        assert stats.question_type == QuestionType.FACTUAL
        assert stats.count == 50
        assert stats.percentage == 0.5
        assert stats.avg_scores["faithfulness"] == 0.85

    def test_question_type_stats_default_avg_scores(self):
        """기본 avg_scores 테스트."""
        stats = QuestionTypeStats(
            question_type=QuestionType.REASONING,
            count=10,
            percentage=0.1,
        )

        assert stats.avg_scores == {}


class TestKeywordInfo:
    """KeywordInfo 엔티티 테스트."""

    def test_create_keyword_info(self):
        """KeywordInfo 생성 테스트."""
        info = KeywordInfo(
            keyword="보험",
            frequency=25,
            tfidf_score=0.75,
            avg_metric_scores={"faithfulness": 0.9},
        )

        assert info.keyword == "보험"
        assert info.frequency == 25
        assert info.tfidf_score == 0.75
        assert info.avg_metric_scores["faithfulness"] == 0.9

    def test_keyword_info_default_avg_metric_scores(self):
        """기본 avg_metric_scores 테스트."""
        info = KeywordInfo(
            keyword="coverage",
            frequency=10,
            tfidf_score=0.5,
        )

        assert info.avg_metric_scores is None

    def test_keyword_info_with_empty_scores(self):
        """빈 avg_metric_scores 테스트."""
        info = KeywordInfo(
            keyword="test",
            frequency=5,
            tfidf_score=0.3,
            avg_metric_scores={},
        )

        assert info.avg_metric_scores == {}


class TestTopicCluster:
    """TopicCluster 엔티티 테스트."""

    def test_create_topic_cluster(self):
        """TopicCluster 생성 테스트."""
        cluster = TopicCluster(
            cluster_id=0,
            keywords=["보험료", "납입", "기간"],
            document_count=15,
            avg_scores={"faithfulness": 0.82, "context_recall": 0.75},
            representative_questions=["보험료 납입 기간은?", "월 보험료는 얼마인가요?"],
        )

        assert cluster.cluster_id == 0
        assert "보험료" in cluster.keywords
        assert cluster.document_count == 15
        assert cluster.avg_scores["faithfulness"] == 0.82
        assert len(cluster.representative_questions) == 2

    def test_topic_cluster_default_values(self):
        """TopicCluster 기본값 테스트."""
        cluster = TopicCluster(
            cluster_id=1,
            keywords=["test"],
            document_count=5,
        )

        assert cluster.avg_scores == {}
        assert cluster.representative_questions == []


class TestNLPAnalysis:
    """NLPAnalysis 엔티티 테스트."""

    def test_create_nlp_analysis_minimal(self):
        """최소 NLPAnalysis 생성 테스트."""
        analysis = NLPAnalysis(run_id="run-001")

        assert analysis.run_id == "run-001"
        assert analysis.question_stats is None
        assert analysis.answer_stats is None
        assert analysis.context_stats is None
        assert analysis.question_types == []
        assert analysis.top_keywords == []
        assert analysis.topic_clusters == []
        assert analysis.insights == []

    def test_create_nlp_analysis_full(self):
        """전체 속성을 갖는 NLPAnalysis 생성 테스트."""
        question_stats = TextStats(
            char_count=500,
            word_count=100,
            sentence_count=5,
            avg_word_length=4.5,
            unique_word_ratio=0.8,
        )
        answer_stats = TextStats(
            char_count=1000,
            word_count=200,
            sentence_count=10,
            avg_word_length=4.8,
            unique_word_ratio=0.75,
        )
        context_stats = TextStats(
            char_count=2000,
            word_count=400,
            sentence_count=20,
            avg_word_length=4.6,
            unique_word_ratio=0.7,
        )

        question_types = [
            QuestionTypeStats(
                question_type=QuestionType.FACTUAL,
                count=30,
                percentage=0.6,
                avg_scores={"faithfulness": 0.85},
            ),
            QuestionTypeStats(
                question_type=QuestionType.REASONING,
                count=20,
                percentage=0.4,
                avg_scores={"faithfulness": 0.75},
            ),
        ]

        top_keywords = [
            KeywordInfo(keyword="보험", frequency=20, tfidf_score=0.8),
            KeywordInfo(keyword="보장", frequency=15, tfidf_score=0.7),
        ]

        topic_clusters = [
            TopicCluster(
                cluster_id=0,
                keywords=["보험", "보장"],
                document_count=10,
                avg_scores={"faithfulness": 0.8},
            ),
        ]

        analysis = NLPAnalysis(
            run_id="run-001",
            question_stats=question_stats,
            answer_stats=answer_stats,
            context_stats=context_stats,
            question_types=question_types,
            top_keywords=top_keywords,
            topic_clusters=topic_clusters,
            insights=["High vocabulary diversity in questions"],
        )

        assert analysis.run_id == "run-001"
        assert analysis.question_stats.word_count == 100
        assert analysis.answer_stats.char_count == 1000
        assert analysis.context_stats.sentence_count == 20
        assert len(analysis.question_types) == 2
        assert len(analysis.top_keywords) == 2
        assert len(analysis.topic_clusters) == 1
        assert len(analysis.insights) == 1

    def test_nlp_analysis_has_text_stats_property(self):
        """has_text_stats 속성 테스트."""
        # Without stats
        analysis = NLPAnalysis(run_id="run-001")
        assert analysis.has_text_stats is False

        # With stats
        analysis_with_stats = NLPAnalysis(
            run_id="run-002",
            question_stats=TextStats(
                char_count=100,
                word_count=20,
                sentence_count=2,
                avg_word_length=4.0,
                unique_word_ratio=0.9,
            ),
        )
        assert analysis_with_stats.has_text_stats is True

    def test_nlp_analysis_has_question_type_analysis_property(self):
        """has_question_type_analysis 속성 테스트."""
        # Without question types
        analysis = NLPAnalysis(run_id="run-001")
        assert analysis.has_question_type_analysis is False

        # With question types
        analysis_with_types = NLPAnalysis(
            run_id="run-002",
            question_types=[
                QuestionTypeStats(
                    question_type=QuestionType.FACTUAL,
                    count=10,
                    percentage=1.0,
                ),
            ],
        )
        assert analysis_with_types.has_question_type_analysis is True

    def test_nlp_analysis_has_keyword_analysis_property(self):
        """has_keyword_analysis 속성 테스트."""
        # Without keywords
        analysis = NLPAnalysis(run_id="run-001")
        assert analysis.has_keyword_analysis is False

        # With keywords
        analysis_with_keywords = NLPAnalysis(
            run_id="run-002",
            top_keywords=[
                KeywordInfo(keyword="test", frequency=5, tfidf_score=0.5),
            ],
        )
        assert analysis_with_keywords.has_keyword_analysis is True

    def test_nlp_analysis_dominant_question_type(self):
        """dominant_question_type 속성 테스트."""
        # No question types
        analysis = NLPAnalysis(run_id="run-001")
        assert analysis.dominant_question_type is None

        # With question types
        analysis_with_types = NLPAnalysis(
            run_id="run-002",
            question_types=[
                QuestionTypeStats(
                    question_type=QuestionType.FACTUAL,
                    count=30,
                    percentage=0.6,
                ),
                QuestionTypeStats(
                    question_type=QuestionType.REASONING,
                    count=20,
                    percentage=0.4,
                ),
            ],
        )
        assert analysis_with_types.dominant_question_type == QuestionType.FACTUAL
