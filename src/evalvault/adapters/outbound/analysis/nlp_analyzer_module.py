"""Phase 14.4: NLP Analyzer Module.

NLPAnalysisAdapter를 파이프라인 노드로 연결합니다.
"""

from __future__ import annotations

from typing import Any

from evalvault.adapters.outbound.analysis.base_module import BaseAnalysisModule
from evalvault.adapters.outbound.analysis.common import (
    AnalysisDataProcessor,
    BaseAnalysisAdapter,
)
from evalvault.adapters.outbound.analysis.nlp_adapter import NLPAnalysisAdapter
from evalvault.adapters.outbound.analysis.pipeline_helpers import get_upstream_output
from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.analysis import (
    KeywordInfo,
    NLPAnalysis,
    QuestionTypeStats,
    TopicCluster,
)


class NLPAnalyzerModule(BaseAnalysisModule):
    """NLP 분석 모듈.

    데이터 로더가 제공한 EvaluationRun을 기반으로 텍스트/질문/키워드 분석을 수행합니다.
    """

    module_id = "nlp_analyzer"
    name = "NLP 분석기"
    description = "질문/답변 텍스트 통계와 키워드, 질문 유형을 분석합니다."
    input_types = ["run"]
    output_types = ["nlp_analysis", "insights"]
    requires = ["data_loader"]
    tags = ["analysis", "nlp"]

    def __init__(self, adapter: NLPAnalysisAdapter | None = None) -> None:
        self._adapter = adapter or NLPAnalysisAdapter()
        self._processor = AnalysisDataProcessor()

    def execute(
        self,
        inputs: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """NLP 분석 실행."""
        loader_output = get_upstream_output(inputs, "load_data", "data_loader") or {}
        run = loader_output.get("run")

        if not isinstance(run, EvaluationRun):
            return self._empty_output()

        params = params or {}
        analysis = self._adapter.analyze(
            run,
            include_text_stats=params.get("include_text_stats", True),
            include_question_types=params.get("include_question_types", True),
            include_keywords=params.get("include_keywords", True),
            include_topic_clusters=params.get("include_topic_clusters", False),
            top_k_keywords=params.get("top_k_keywords", 20),
            min_cluster_size=params.get("min_cluster_size", 3),
        )

        question_types = self._serialize_question_types(analysis.question_types)
        keywords = self._serialize_keywords(analysis.top_keywords)
        topic_clusters = self._serialize_topic_clusters(analysis.topic_clusters)
        statistics = self._build_statistics(analysis, question_types, keywords, topic_clusters)

        return self._build_output(
            analysis,
            summary=self._build_summary(analysis),
            statistics=statistics,
            insights=analysis.insights,
            extra={
                "question_types": question_types,
                "top_keywords": keywords,
                "topic_clusters": topic_clusters,
            },
        )

    def _empty_output(self) -> dict[str, Any]:
        """입력 데이터가 없을 때의 기본 출력."""
        return self._build_output(
            None,
            summary={},
            statistics={},
            insights=[],
            extra={
                "question_types": [],
                "top_keywords": [],
                "topic_clusters": [],
            },
        )

    def _build_summary(self, analysis: NLPAnalysis) -> dict[str, Any]:
        """요약 데이터 생성."""
        summary: dict[str, Any] = {
            "run_id": analysis.run_id,
            "has_text_stats": analysis.has_text_stats,
            "has_question_type_analysis": analysis.has_question_type_analysis,
            "has_keyword_analysis": analysis.has_keyword_analysis,
        }

        if analysis.question_stats:
            summary["question_stats_preview"] = analysis.question_stats.avg_sentence_length
        if analysis.answer_stats:
            summary["answer_stats_preview"] = analysis.answer_stats.avg_sentence_length
        if analysis.context_stats:
            summary["context_count"] = analysis.context_stats.sentence_count

        if analysis.dominant_question_type:
            summary["dominant_question_type"] = analysis.dominant_question_type.value

        if analysis.top_keywords:
            summary["top_keywords_preview"] = [kw.keyword for kw in analysis.top_keywords[:5]]

        if analysis.topic_clusters:
            summary["topic_cluster_count"] = len(analysis.topic_clusters)

        return summary

    def _build_statistics(
        self,
        analysis: NLPAnalysis,
        serialized_question_types: list[dict[str, Any]],
        serialized_keywords: list[dict[str, Any]],
        serialized_topic_clusters: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """텍스트/질문 유형/키워드 정보를 statistics 섹션으로 정리."""
        processor = self._processor
        text_stats: dict[str, Any] = {}

        if analysis.question_stats:
            text_stats["questions"] = processor.to_serializable(analysis.question_stats)
        if analysis.answer_stats:
            text_stats["answers"] = processor.to_serializable(analysis.answer_stats)
        if analysis.context_stats:
            text_stats["contexts"] = processor.to_serializable(analysis.context_stats)

        statistics: dict[str, Any] = {}
        if text_stats:
            statistics["text_stats"] = text_stats
        if serialized_question_types:
            statistics["question_type_distribution"] = serialized_question_types
        if serialized_keywords:
            statistics["keywords"] = serialized_keywords
        if serialized_topic_clusters:
            statistics["topic_clusters"] = serialized_topic_clusters

        return statistics

    def _build_output(
        self,
        analysis: NLPAnalysis | None,
        *,
        summary: dict[str, Any],
        statistics: dict[str, Any],
        insights: list[str],
        extra: dict[str, Any],
    ) -> dict[str, Any]:
        """어댑터 mock 여부와 관계없이 공통 포맷 생성."""
        if isinstance(self._adapter, BaseAnalysisAdapter):
            return self._adapter.build_module_output(
                analysis,
                summary=summary,
                statistics=statistics,
                insights=insights,
                extra=extra,
            )
        return self._processor.build_output_payload(
            analysis,
            summary=summary,
            statistics=statistics,
            insights=insights,
            extra=extra,
        )

    def _serialize_question_types(self, stats: list[QuestionTypeStats]) -> list[dict[str, Any]]:
        """질문 유형 통계를 직렬화."""
        serialized = []
        for item in stats:
            serialized.append(
                {
                    "question_type": item.question_type.value,
                    "count": item.count,
                    "percentage": item.percentage,
                    "avg_scores": item.avg_scores,
                }
            )
        return serialized

    def _serialize_keywords(self, keywords: list[KeywordInfo]) -> list[dict[str, Any]]:
        """키워드 정보를 직렬화."""
        serialized = []
        for kw in keywords:
            serialized.append(
                {
                    "keyword": kw.keyword,
                    "frequency": kw.frequency,
                    "tfidf_score": kw.tfidf_score,
                    "avg_metric_scores": kw.avg_metric_scores,
                }
            )
        return serialized

    def _serialize_topic_clusters(self, clusters: list[TopicCluster]) -> list[dict[str, Any]]:
        """토픽 클러스터를 직렬화."""
        serialized = []
        for cluster in clusters:
            serialized.append(
                {
                    "cluster_id": cluster.cluster_id,
                    "keywords": list(cluster.keywords),
                    "document_count": cluster.document_count,
                    "avg_scores": cluster.avg_scores,
                    "representative_questions": cluster.representative_questions[:4],
                }
            )
        return serialized
