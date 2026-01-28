"""Phase 14.1: Analysis Pipeline 엔티티 단위 테스트.

TDD Red Phase - 테스트 먼저 작성.
"""

from __future__ import annotations

from datetime import datetime

# =============================================================================
# AnalysisIntent Tests
# =============================================================================


class TestAnalysisIntent:
    """AnalysisIntent enum 테스트."""

    def test_intent_has_verify_morpheme(self):
        """VERIFY_MORPHEME 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "VERIFY_MORPHEME")
        assert AnalysisIntent.VERIFY_MORPHEME.value == "verify_morpheme"

    def test_intent_has_verify_embedding(self):
        """VERIFY_EMBEDDING 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "VERIFY_EMBEDDING")
        assert AnalysisIntent.VERIFY_EMBEDDING.value == "verify_embedding"

    def test_intent_has_verify_retrieval(self):
        """VERIFY_RETRIEVAL 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "VERIFY_RETRIEVAL")
        assert AnalysisIntent.VERIFY_RETRIEVAL.value == "verify_retrieval"

    def test_intent_has_compare_search_methods(self):
        """COMPARE_SEARCH_METHODS 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "COMPARE_SEARCH_METHODS")
        assert AnalysisIntent.COMPARE_SEARCH_METHODS.value == "compare_search"

    def test_intent_has_compare_models(self):
        """COMPARE_MODELS 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "COMPARE_MODELS")
        assert AnalysisIntent.COMPARE_MODELS.value == "compare_models"

    def test_intent_has_compare_runs(self):
        """COMPARE_RUNS 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "COMPARE_RUNS")
        assert AnalysisIntent.COMPARE_RUNS.value == "compare_runs"

    def test_intent_has_analyze_low_metrics(self):
        """ANALYZE_LOW_METRICS 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "ANALYZE_LOW_METRICS")
        assert AnalysisIntent.ANALYZE_LOW_METRICS.value == "analyze_low_metrics"

    def test_intent_has_analyze_patterns(self):
        """ANALYZE_PATTERNS 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "ANALYZE_PATTERNS")
        assert AnalysisIntent.ANALYZE_PATTERNS.value == "analyze_patterns"

    def test_intent_has_analyze_trends(self):
        """ANALYZE_TRENDS 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "ANALYZE_TRENDS")
        assert AnalysisIntent.ANALYZE_TRENDS.value == "analyze_trends"

    def test_intent_has_benchmark_retrieval(self):
        """BENCHMARK_RETRIEVAL 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "BENCHMARK_RETRIEVAL")
        assert AnalysisIntent.BENCHMARK_RETRIEVAL.value == "benchmark_retrieval"

    def test_intent_has_generate_summary(self):
        """GENERATE_SUMMARY 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "GENERATE_SUMMARY")
        assert AnalysisIntent.GENERATE_SUMMARY.value == "generate_summary"

    def test_intent_has_generate_detailed(self):
        """GENERATE_DETAILED 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "GENERATE_DETAILED")
        assert AnalysisIntent.GENERATE_DETAILED.value == "generate_detailed"

    def test_intent_has_generate_comparison(self):
        """GENERATE_COMPARISON 의도 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert hasattr(AnalysisIntent, "GENERATE_COMPARISON")
        assert AnalysisIntent.GENERATE_COMPARISON.value == "generate_comparison"

    def test_intent_is_string_enum(self):
        """AnalysisIntent가 str Enum인지 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert isinstance(AnalysisIntent.VERIFY_MORPHEME.value, str)
        assert isinstance(AnalysisIntent.VERIFY_MORPHEME, str)

    def test_all_intents_count(self):
        """모든 의도가 22개인지 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent

        assert len(AnalysisIntent) == 22


# =============================================================================
# AnalysisIntentCategory Tests
# =============================================================================


class TestAnalysisIntentCategory:
    """AnalysisIntentCategory enum 테스트."""

    def test_category_has_verification(self):
        """VERIFICATION 카테고리 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntentCategory

        assert hasattr(AnalysisIntentCategory, "VERIFICATION")

    def test_category_has_comparison(self):
        """COMPARISON 카테고리 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntentCategory

        assert hasattr(AnalysisIntentCategory, "COMPARISON")

    def test_category_has_analysis(self):
        """ANALYSIS 카테고리 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntentCategory

        assert hasattr(AnalysisIntentCategory, "ANALYSIS")

    def test_category_has_report(self):
        """REPORT 카테고리 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntentCategory

        assert hasattr(AnalysisIntentCategory, "REPORT")


# =============================================================================
# AnalysisNode Tests
# =============================================================================


class TestAnalysisNode:
    """AnalysisNode dataclass 테스트."""

    def test_node_creation_minimal(self):
        """최소 필수 파라미터로 노드 생성."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisNode

        node = AnalysisNode(
            id="load_data",
            name="데이터 로드",
            module="data_loader",
        )

        assert node.id == "load_data"
        assert node.name == "데이터 로드"
        assert node.module == "data_loader"
        assert node.params == {}
        assert node.depends_on == []

    def test_node_creation_with_params(self):
        """파라미터와 함께 노드 생성."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisNode

        node = AnalysisNode(
            id="morpheme",
            name="형태소 분석",
            module="morpheme_analyzer",
            params={"lang": "ko", "backend": "kiwi"},
        )

        assert node.params == {"lang": "ko", "backend": "kiwi"}

    def test_node_creation_with_dependencies(self):
        """의존성과 함께 노드 생성."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisNode

        node = AnalysisNode(
            id="hybrid_rrf",
            name="RRF 하이브리드 검색",
            module="hybrid_rrf",
            depends_on=["bm25_search", "embedding_search"],
        )

        assert node.depends_on == ["bm25_search", "embedding_search"]

    def test_node_has_dependencies_property(self):
        """의존성 존재 여부 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisNode

        node_with_deps = AnalysisNode(id="a", name="A", module="m", depends_on=["b"])
        node_without_deps = AnalysisNode(id="b", name="B", module="m")

        assert node_with_deps.has_dependencies is True
        assert node_without_deps.has_dependencies is False

    def test_node_is_root_property(self):
        """루트 노드 여부 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisNode

        root_node = AnalysisNode(id="root", name="Root", module="m")
        child_node = AnalysisNode(id="child", name="Child", module="m", depends_on=["root"])

        assert root_node.is_root is True
        assert child_node.is_root is False


# =============================================================================
# AnalysisContext Tests
# =============================================================================


class TestAnalysisContext:
    """AnalysisContext dataclass 테스트."""

    def test_context_creation_minimal(self):
        """최소 필수 파라미터로 컨텍스트 생성."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisContext

        ctx = AnalysisContext(query="형태소 분석이 제대로 되고 있는지 확인")

        assert ctx.query == "형태소 분석이 제대로 되고 있는지 확인"
        assert ctx.run_id is None
        assert ctx.dataset is None
        assert ctx.additional_params == {}

    def test_context_creation_with_run_id(self):
        """run_id와 함께 컨텍스트 생성."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisContext

        ctx = AnalysisContext(
            query="결과 분석해줘",
            run_id="run-123",
        )

        assert ctx.run_id == "run-123"

    def test_context_creation_with_dataset(self):
        """dataset과 함께 컨텍스트 생성."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisContext

        mock_dataset = {"test_cases": []}
        ctx = AnalysisContext(
            query="데이터셋 분석",
            dataset=mock_dataset,
        )

        assert ctx.dataset == mock_dataset

    def test_context_creation_with_additional_params(self):
        """추가 파라미터와 함께 컨텍스트 생성."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisContext

        ctx = AnalysisContext(
            query="메트릭 분석",
            additional_params={"target_metric": "faithfulness", "threshold": 0.5},
        )

        assert ctx.additional_params["target_metric"] == "faithfulness"
        assert ctx.additional_params["threshold"] == 0.5

    def test_context_has_run_id_property(self):
        """run_id 존재 여부 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisContext

        ctx_with_run = AnalysisContext(query="q", run_id="r1")
        ctx_without_run = AnalysisContext(query="q")

        assert ctx_with_run.has_run_id is True
        assert ctx_without_run.has_run_id is False

    def test_context_has_dataset_property(self):
        """dataset 존재 여부 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisContext

        ctx_with_ds = AnalysisContext(query="q", dataset={"data": []})
        ctx_without_ds = AnalysisContext(query="q")

        assert ctx_with_ds.has_dataset is True
        assert ctx_without_ds.has_dataset is False


# =============================================================================
# AnalysisPipeline Tests
# =============================================================================


class TestAnalysisPipeline:
    """AnalysisPipeline dataclass 테스트."""

    def test_pipeline_creation_minimal(self):
        """최소 필수 파라미터로 파이프라인 생성."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisPipeline,
        )

        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )

        assert pipeline.intent == AnalysisIntent.VERIFY_MORPHEME
        assert pipeline.nodes == []
        assert pipeline.edges == []
        assert pipeline.pipeline_id is not None
        assert isinstance(pipeline.created_at, datetime)

    def test_pipeline_creation_with_nodes(self):
        """노드와 함께 파이프라인 생성."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        nodes = [
            AnalysisNode(id="a", name="A", module="m1"),
            AnalysisNode(id="b", name="B", module="m2", depends_on=["a"]),
        ]

        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            nodes=nodes,
        )

        assert len(pipeline.nodes) == 2
        assert pipeline.nodes[0].id == "a"
        assert pipeline.nodes[1].id == "b"

    def test_pipeline_creation_with_edges(self):
        """엣지와 함께 파이프라인 생성."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisPipeline,
        )

        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.COMPARE_SEARCH_METHODS,
            edges=[("a", "b"), ("b", "c")],
        )

        assert pipeline.edges == [("a", "b"), ("b", "c")]

    def test_pipeline_get_node_by_id(self):
        """ID로 노드 조회."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        nodes = [
            AnalysisNode(id="a", name="A", module="m1"),
            AnalysisNode(id="b", name="B", module="m2"),
        ]
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            nodes=nodes,
        )

        node_a = pipeline.get_node("a")
        node_b = pipeline.get_node("b")
        node_c = pipeline.get_node("c")

        assert node_a is not None
        assert node_a.name == "A"
        assert node_b is not None
        assert node_b.name == "B"
        assert node_c is None

    def test_pipeline_root_nodes_property(self):
        """루트 노드 목록 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        nodes = [
            AnalysisNode(id="a", name="A", module="m1"),
            AnalysisNode(id="b", name="B", module="m2"),
            AnalysisNode(id="c", name="C", module="m3", depends_on=["a", "b"]),
        ]
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.COMPARE_SEARCH_METHODS,
            nodes=nodes,
        )

        roots = pipeline.root_nodes
        assert len(roots) == 2
        assert {n.id for n in roots} == {"a", "b"}

    def test_pipeline_leaf_nodes_property(self):
        """리프 노드 목록 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        nodes = [
            AnalysisNode(id="a", name="A", module="m1"),
            AnalysisNode(id="b", name="B", module="m2", depends_on=["a"]),
            AnalysisNode(id="c", name="C", module="m3", depends_on=["a"]),
        ]
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            nodes=nodes,
            edges=[("a", "b"), ("a", "c")],
        )

        leaves = pipeline.leaf_nodes
        # b와 c가 리프 노드 (다른 노드가 의존하지 않음)
        assert len(leaves) == 2
        assert {n.id for n in leaves} == {"b", "c"}

    def test_pipeline_node_count_property(self):
        """노드 개수 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        nodes = [
            AnalysisNode(id="a", name="A", module="m"),
            AnalysisNode(id="b", name="B", module="m"),
        ]
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            nodes=nodes,
        )

        assert pipeline.node_count == 2

    def test_pipeline_topological_order(self):
        """위상 정렬된 실행 순서."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        # a -> b -> d
        #  \-> c -/
        nodes = [
            AnalysisNode(id="a", name="A", module="m"),
            AnalysisNode(id="b", name="B", module="m", depends_on=["a"]),
            AnalysisNode(id="c", name="C", module="m", depends_on=["a"]),
            AnalysisNode(id="d", name="D", module="m", depends_on=["b", "c"]),
        ]
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.COMPARE_SEARCH_METHODS,
            nodes=nodes,
        )

        order = pipeline.topological_order()

        # a는 항상 첫 번째
        assert order[0] == "a"
        # d는 항상 마지막
        assert order[-1] == "d"
        # b, c는 a 이후, d 이전
        assert order.index("b") > order.index("a")
        assert order.index("c") > order.index("a")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_pipeline_validate_no_cycles(self):
        """순환 의존성 없음 검증."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        # 순환 없는 정상 파이프라인
        nodes = [
            AnalysisNode(id="a", name="A", module="m"),
            AnalysisNode(id="b", name="B", module="m", depends_on=["a"]),
        ]
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            nodes=nodes,
        )

        assert pipeline.validate() is True

    def test_pipeline_validate_detects_cycles(self):
        """순환 의존성 감지."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        # a -> b -> c -> a (순환)
        nodes = [
            AnalysisNode(id="a", name="A", module="m", depends_on=["c"]),
            AnalysisNode(id="b", name="B", module="m", depends_on=["a"]),
            AnalysisNode(id="c", name="C", module="m", depends_on=["b"]),
        ]
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            nodes=nodes,
        )

        assert pipeline.validate() is False

    def test_pipeline_add_node(self):
        """노드 추가."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        pipeline = AnalysisPipeline(intent=AnalysisIntent.VERIFY_MORPHEME)
        node = AnalysisNode(id="a", name="A", module="m")

        pipeline.add_node(node)

        assert pipeline.node_count == 1
        assert pipeline.get_node("a") is not None

    def test_pipeline_add_edge(self):
        """엣지 추가."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )

        nodes = [
            AnalysisNode(id="a", name="A", module="m"),
            AnalysisNode(id="b", name="B", module="m"),
        ]
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            nodes=nodes,
        )

        pipeline.add_edge("a", "b")

        assert ("a", "b") in pipeline.edges


# =============================================================================
# NodeExecutionStatus Tests
# =============================================================================


class TestNodeExecutionStatus:
    """NodeExecutionStatus enum 테스트."""

    def test_status_has_pending(self):
        """PENDING 상태 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import NodeExecutionStatus

        assert hasattr(NodeExecutionStatus, "PENDING")

    def test_status_has_running(self):
        """RUNNING 상태 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import NodeExecutionStatus

        assert hasattr(NodeExecutionStatus, "RUNNING")

    def test_status_has_completed(self):
        """COMPLETED 상태 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import NodeExecutionStatus

        assert hasattr(NodeExecutionStatus, "COMPLETED")

    def test_status_has_failed(self):
        """FAILED 상태 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import NodeExecutionStatus

        assert hasattr(NodeExecutionStatus, "FAILED")

    def test_status_has_skipped(self):
        """SKIPPED 상태 존재 확인."""
        from evalvault.domain.entities.analysis_pipeline import NodeExecutionStatus

        assert hasattr(NodeExecutionStatus, "SKIPPED")


# =============================================================================
# NodeResult Tests
# =============================================================================


class TestNodeResult:
    """NodeResult dataclass 테스트."""

    def test_node_result_creation_success(self):
        """성공 결과 생성."""
        from evalvault.domain.entities.analysis_pipeline import (
            NodeExecutionStatus,
            NodeResult,
        )

        result = NodeResult(
            node_id="morpheme",
            status=NodeExecutionStatus.COMPLETED,
            output={"tokens": ["형태소", "분석"]},
        )

        assert result.node_id == "morpheme"
        assert result.status == NodeExecutionStatus.COMPLETED
        assert result.output == {"tokens": ["형태소", "분석"]}
        assert result.error is None
        assert result.duration_ms is None

    def test_node_result_creation_failure(self):
        """실패 결과 생성."""
        from evalvault.domain.entities.analysis_pipeline import (
            NodeExecutionStatus,
            NodeResult,
        )

        result = NodeResult(
            node_id="morpheme",
            status=NodeExecutionStatus.FAILED,
            error="Module not found",
        )

        assert result.status == NodeExecutionStatus.FAILED
        assert result.error == "Module not found"
        assert result.output is None

    def test_node_result_creation_with_duration(self):
        """실행 시간과 함께 결과 생성."""
        from evalvault.domain.entities.analysis_pipeline import (
            NodeExecutionStatus,
            NodeResult,
        )

        result = NodeResult(
            node_id="analysis",
            status=NodeExecutionStatus.COMPLETED,
            output={"score": 0.85},
            duration_ms=1500,
        )

        assert result.duration_ms == 1500

    def test_node_result_is_success_property(self):
        """성공 여부 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import (
            NodeExecutionStatus,
            NodeResult,
        )

        success = NodeResult(
            node_id="a",
            status=NodeExecutionStatus.COMPLETED,
            output={},
        )
        failure = NodeResult(
            node_id="b",
            status=NodeExecutionStatus.FAILED,
            error="err",
        )

        assert success.is_success is True
        assert failure.is_success is False

    def test_node_result_is_failure_property(self):
        """실패 여부 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import (
            NodeExecutionStatus,
            NodeResult,
        )

        success = NodeResult(
            node_id="a",
            status=NodeExecutionStatus.COMPLETED,
            output={},
        )
        failure = NodeResult(
            node_id="b",
            status=NodeExecutionStatus.FAILED,
            error="err",
        )

        assert success.is_failure is False
        assert failure.is_failure is True


# =============================================================================
# PipelineResult Tests
# =============================================================================


class TestPipelineResult:
    """PipelineResult dataclass 테스트."""

    def test_pipeline_result_creation(self):
        """파이프라인 결과 생성."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            PipelineResult,
        )

        result = PipelineResult(
            pipeline_id="pipe-123",
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )

        assert result.pipeline_id == "pipe-123"
        assert result.intent == AnalysisIntent.VERIFY_MORPHEME
        assert result.node_results == {}
        assert result.final_output is None
        assert result.total_duration_ms is None
        assert isinstance(result.started_at, datetime)
        assert result.finished_at is None

    def test_pipeline_result_add_node_result(self):
        """노드 결과 추가."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            NodeExecutionStatus,
            NodeResult,
            PipelineResult,
        )

        pipeline_result = PipelineResult(
            pipeline_id="pipe-123",
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )

        node_result = NodeResult(
            node_id="a",
            status=NodeExecutionStatus.COMPLETED,
            output={"data": "value"},
        )

        pipeline_result.add_node_result(node_result)

        assert "a" in pipeline_result.node_results
        assert pipeline_result.node_results["a"].output == {"data": "value"}

    def test_pipeline_result_get_node_result(self):
        """노드 결과 조회."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            NodeExecutionStatus,
            NodeResult,
            PipelineResult,
        )

        pipeline_result = PipelineResult(
            pipeline_id="pipe-123",
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )
        pipeline_result.add_node_result(
            NodeResult(
                node_id="a",
                status=NodeExecutionStatus.COMPLETED,
                output={"x": 1},
            )
        )

        result_a = pipeline_result.get_node_result("a")
        result_b = pipeline_result.get_node_result("b")

        assert result_a is not None
        assert result_a.output == {"x": 1}
        assert result_b is None

    def test_pipeline_result_is_complete_property(self):
        """완료 여부 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            PipelineResult,
        )

        incomplete = PipelineResult(
            pipeline_id="p1",
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )
        complete = PipelineResult(
            pipeline_id="p2",
            intent=AnalysisIntent.VERIFY_MORPHEME,
            finished_at=datetime.now(),
        )

        assert incomplete.is_complete is False
        assert complete.is_complete is True

    def test_pipeline_result_success_count_property(self):
        """성공 노드 수 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            NodeExecutionStatus,
            NodeResult,
            PipelineResult,
        )

        pipeline_result = PipelineResult(
            pipeline_id="pipe-123",
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )
        pipeline_result.add_node_result(
            NodeResult(node_id="a", status=NodeExecutionStatus.COMPLETED, output={})
        )
        pipeline_result.add_node_result(
            NodeResult(node_id="b", status=NodeExecutionStatus.COMPLETED, output={})
        )
        pipeline_result.add_node_result(
            NodeResult(node_id="c", status=NodeExecutionStatus.FAILED, error="err")
        )

        assert pipeline_result.success_count == 2

    def test_pipeline_result_failure_count_property(self):
        """실패 노드 수 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            NodeExecutionStatus,
            NodeResult,
            PipelineResult,
        )

        pipeline_result = PipelineResult(
            pipeline_id="pipe-123",
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )
        pipeline_result.add_node_result(
            NodeResult(node_id="a", status=NodeExecutionStatus.COMPLETED, output={})
        )
        pipeline_result.add_node_result(
            NodeResult(node_id="b", status=NodeExecutionStatus.FAILED, error="e1")
        )
        pipeline_result.add_node_result(
            NodeResult(node_id="c", status=NodeExecutionStatus.FAILED, error="e2")
        )

        assert pipeline_result.failure_count == 2

    def test_pipeline_result_all_succeeded_property(self):
        """모든 노드 성공 여부 프로퍼티."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            NodeExecutionStatus,
            NodeResult,
            PipelineResult,
        )

        all_success = PipelineResult(
            pipeline_id="p1",
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )
        all_success.add_node_result(
            NodeResult(node_id="a", status=NodeExecutionStatus.COMPLETED, output={})
        )
        all_success.add_node_result(
            NodeResult(node_id="b", status=NodeExecutionStatus.COMPLETED, output={})
        )

        some_failed = PipelineResult(
            pipeline_id="p2",
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )
        some_failed.add_node_result(
            NodeResult(node_id="a", status=NodeExecutionStatus.COMPLETED, output={})
        )
        some_failed.add_node_result(
            NodeResult(node_id="b", status=NodeExecutionStatus.FAILED, error="err")
        )

        assert all_success.all_succeeded is True
        assert some_failed.all_succeeded is False

    def test_pipeline_result_mark_complete(self):
        """완료 표시."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisIntent,
            PipelineResult,
        )

        result = PipelineResult(
            pipeline_id="p1",
            intent=AnalysisIntent.VERIFY_MORPHEME,
        )

        result.mark_complete(
            final_output={"summary": "분석 완료"},
            total_duration_ms=5000,
        )

        assert result.is_complete is True
        assert result.finished_at is not None
        assert result.final_output == {"summary": "분석 완료"}
        assert result.total_duration_ms == 5000


# =============================================================================
# Port Interface Tests
# =============================================================================


class TestAnalysisPipelinePort:
    """AnalysisPipelinePort 인터페이스 테스트."""

    def test_port_is_protocol(self):
        """Protocol 클래스인지 확인."""
        from typing import Protocol

        from evalvault.ports.inbound.analysis_pipeline_port import AnalysisPipelinePort

        assert issubclass(AnalysisPipelinePort, Protocol)

    def test_port_has_execute_method(self):
        """execute 메서드 존재 확인."""
        from evalvault.ports.inbound.analysis_pipeline_port import AnalysisPipelinePort

        assert hasattr(AnalysisPipelinePort, "execute")

    def test_port_has_build_pipeline_method(self):
        """build_pipeline 메서드 존재 확인."""
        from evalvault.ports.inbound.analysis_pipeline_port import AnalysisPipelinePort

        assert hasattr(AnalysisPipelinePort, "build_pipeline")


class TestAnalysisModulePort:
    """AnalysisModulePort 인터페이스 테스트."""

    def test_port_is_protocol(self):
        """Protocol 클래스인지 확인."""
        from typing import Protocol

        from evalvault.ports.outbound.analysis_module_port import AnalysisModulePort

        assert issubclass(AnalysisModulePort, Protocol)

    def test_port_has_module_id_property(self):
        """module_id 프로퍼티 존재 확인."""
        from evalvault.ports.outbound.analysis_module_port import AnalysisModulePort

        assert hasattr(AnalysisModulePort, "module_id")

    def test_port_has_execute_method(self):
        """execute 메서드 존재 확인."""
        from evalvault.ports.outbound.analysis_module_port import AnalysisModulePort

        assert hasattr(AnalysisModulePort, "execute")

    def test_port_has_validate_inputs_method(self):
        """validate_inputs 메서드 존재 확인."""
        from evalvault.ports.outbound.analysis_module_port import AnalysisModulePort

        assert hasattr(AnalysisModulePort, "validate_inputs")


class TestIntentClassifierPort:
    """IntentClassifierPort 인터페이스 테스트."""

    def test_port_is_protocol(self):
        """Protocol 클래스인지 확인."""
        from typing import Protocol

        from evalvault.ports.outbound.intent_classifier_port import IntentClassifierPort

        assert issubclass(IntentClassifierPort, Protocol)

    def test_port_has_classify_method(self):
        """classify 메서드 존재 확인."""
        from evalvault.ports.outbound.intent_classifier_port import IntentClassifierPort

        assert hasattr(IntentClassifierPort, "classify")

    def test_port_has_classify_with_confidence_method(self):
        """classify_with_confidence 메서드 존재 확인."""
        from evalvault.ports.outbound.intent_classifier_port import IntentClassifierPort

        assert hasattr(IntentClassifierPort, "classify_with_confidence")


# =============================================================================
# ModuleMetadata Tests (분석 모듈 메타데이터)
# =============================================================================


class TestModuleMetadata:
    """ModuleMetadata dataclass 테스트 - 의도 분류기가 모듈 선택 시 참조."""

    def test_metadata_creation(self):
        """메타데이터 생성."""
        from evalvault.domain.entities.analysis_pipeline import ModuleMetadata

        metadata = ModuleMetadata(
            module_id="morpheme",
            name="형태소 분석기",
            description="kiwipiepy 기반 한국어 형태소 분석. 토큰화, 품사 태깅 수행.",
            input_types=["text", "documents"],
            output_types=["tokens", "pos_tags"],
        )

        assert metadata.module_id == "morpheme"
        assert metadata.name == "형태소 분석기"
        assert "kiwipiepy" in metadata.description
        assert "text" in metadata.input_types
        assert "tokens" in metadata.output_types

    def test_metadata_with_dependencies(self):
        """의존성이 있는 모듈 메타데이터."""
        from evalvault.domain.entities.analysis_pipeline import ModuleMetadata

        metadata = ModuleMetadata(
            module_id="hybrid_rrf",
            name="RRF 하이브리드 검색",
            description="Reciprocal Rank Fusion 방식의 하이브리드 검색",
            input_types=["bm25_scores", "embedding_scores"],
            output_types=["hybrid_scores"],
            requires=["morpheme", "bm25", "embedding"],
        )

        assert metadata.requires == ["morpheme", "bm25", "embedding"]

    def test_metadata_with_optional_dependencies(self):
        """선택적 의존성이 있는 모듈 메타데이터."""
        from evalvault.domain.entities.analysis_pipeline import ModuleMetadata

        metadata = ModuleMetadata(
            module_id="report",
            name="보고서 생성기",
            description="분석 결과를 보고서로 변환",
            input_types=["analysis_results"],
            output_types=["markdown", "html"],
            optional_requires=["llm"],  # LLM 요약은 선택적
        )

        assert metadata.optional_requires == ["llm"]

    def test_metadata_with_tags(self):
        """태그가 있는 모듈 메타데이터 (의도 분류 힌트)."""
        from evalvault.domain.entities.analysis_pipeline import ModuleMetadata

        metadata = ModuleMetadata(
            module_id="morpheme",
            name="형태소 분석기",
            description="형태소 분석",
            input_types=["text"],
            output_types=["tokens"],
            tags=["korean", "nlp", "tokenization", "verification"],
        )

        assert "korean" in metadata.tags
        assert "verification" in metadata.tags

    def test_metadata_matches_intent_keywords(self):
        """의도 키워드 매칭 메서드."""
        from evalvault.domain.entities.analysis_pipeline import ModuleMetadata

        metadata = ModuleMetadata(
            module_id="morpheme",
            name="형태소 분석기",
            description="kiwipiepy 기반 한국어 형태소 분석. 토큰화, 품사 태깅.",
            input_types=["text"],
            output_types=["tokens"],
            tags=["korean", "nlp", "tokenization"],
        )

        # 쿼리 키워드와 매칭
        assert metadata.matches_keywords(["형태소", "분석"]) is True
        assert metadata.matches_keywords(["토큰"]) is True
        assert metadata.matches_keywords(["임베딩"]) is False

    def test_metadata_relevance_score(self):
        """의도와의 관련성 점수 계산."""
        from evalvault.domain.entities.analysis_pipeline import ModuleMetadata

        metadata = ModuleMetadata(
            module_id="morpheme",
            name="형태소 분석기",
            description="한국어 형태소 분석 및 토큰화",
            input_types=["text"],
            output_types=["tokens"],
            tags=["korean", "morpheme", "tokenization"],
        )

        # 관련 키워드가 많을수록 높은 점수
        score_high = metadata.relevance_score(["형태소", "분석", "토큰"])
        score_low = metadata.relevance_score(["임베딩"])

        assert score_high > score_low
        assert score_high > 0
        assert score_low == 0


# =============================================================================
# ModuleCatalog Tests (분석 모듈 카탈로그)
# =============================================================================


class TestModuleCatalog:
    """ModuleCatalog 테스트 - 사용 가능한 분석 모듈 레지스트리."""

    def test_catalog_register_module(self):
        """모듈 등록."""
        from evalvault.domain.entities.analysis_pipeline import (
            ModuleCatalog,
            ModuleMetadata,
        )

        catalog = ModuleCatalog()
        metadata = ModuleMetadata(
            module_id="test_module",
            name="테스트 모듈",
            description="테스트용",
            input_types=["input"],
            output_types=["output"],
        )

        catalog.register(metadata)

        assert catalog.get("test_module") is not None

    def test_catalog_get_module(self):
        """모듈 조회."""
        from evalvault.domain.entities.analysis_pipeline import (
            ModuleCatalog,
            ModuleMetadata,
        )

        catalog = ModuleCatalog()
        catalog.register(
            ModuleMetadata(
                module_id="m1",
                name="M1",
                description="desc",
                input_types=[],
                output_types=[],
            )
        )

        assert catalog.get("m1") is not None
        assert catalog.get("nonexistent") is None

    def test_catalog_list_all(self):
        """전체 모듈 목록."""
        from evalvault.domain.entities.analysis_pipeline import (
            ModuleCatalog,
            ModuleMetadata,
        )

        catalog = ModuleCatalog()
        catalog.register(
            ModuleMetadata(
                module_id="m1",
                name="M1",
                description="d",
                input_types=[],
                output_types=[],
            )
        )
        catalog.register(
            ModuleMetadata(
                module_id="m2",
                name="M2",
                description="d",
                input_types=[],
                output_types=[],
            )
        )

        all_modules = catalog.list_all()

        assert len(all_modules) == 2
        assert {m.module_id for m in all_modules} == {"m1", "m2"}

    def test_catalog_find_by_tag(self):
        """태그로 모듈 검색."""
        from evalvault.domain.entities.analysis_pipeline import (
            ModuleCatalog,
            ModuleMetadata,
        )

        catalog = ModuleCatalog()
        catalog.register(
            ModuleMetadata(
                module_id="m1",
                name="M1",
                description="d",
                input_types=[],
                output_types=[],
                tags=["korean", "nlp"],
            )
        )
        catalog.register(
            ModuleMetadata(
                module_id="m2",
                name="M2",
                description="d",
                input_types=[],
                output_types=[],
                tags=["search"],
            )
        )

        korean_modules = catalog.find_by_tag("korean")
        search_modules = catalog.find_by_tag("search")

        assert len(korean_modules) == 1
        assert korean_modules[0].module_id == "m1"
        assert len(search_modules) == 1
        assert search_modules[0].module_id == "m2"

    def test_catalog_find_by_keywords(self):
        """키워드로 모듈 검색 (의도 분류기 활용)."""
        from evalvault.domain.entities.analysis_pipeline import (
            ModuleCatalog,
            ModuleMetadata,
        )

        catalog = ModuleCatalog()
        catalog.register(
            ModuleMetadata(
                module_id="morpheme",
                name="형태소 분석기",
                description="한국어 형태소 분석",
                input_types=["text"],
                output_types=["tokens"],
                tags=["korean", "morpheme"],
            )
        )
        catalog.register(
            ModuleMetadata(
                module_id="bm25",
                name="BM25 검색",
                description="키워드 기반 BM25 검색",
                input_types=["query", "documents"],
                output_types=["scores"],
                tags=["search", "bm25"],
            )
        )

        # 형태소 관련 키워드로 검색
        results = catalog.find_by_keywords(["형태소", "분석"])

        assert len(results) >= 1
        assert results[0].module_id == "morpheme"

    def test_catalog_get_dependencies(self):
        """모듈의 의존성 트리 조회."""
        from evalvault.domain.entities.analysis_pipeline import (
            ModuleCatalog,
            ModuleMetadata,
        )

        catalog = ModuleCatalog()
        catalog.register(
            ModuleMetadata(
                module_id="data_loader",
                name="Data Loader",
                description="데이터 로드",
                input_types=[],
                output_types=["dataset"],
            )
        )
        catalog.register(
            ModuleMetadata(
                module_id="morpheme",
                name="Morpheme",
                description="형태소 분석",
                input_types=["text"],
                output_types=["tokens"],
                requires=["data_loader"],
            )
        )
        catalog.register(
            ModuleMetadata(
                module_id="bm25",
                name="BM25",
                description="검색",
                input_types=["tokens"],
                output_types=["scores"],
                requires=["morpheme"],
            )
        )

        deps = catalog.get_dependencies("bm25")

        # bm25 -> morpheme -> data_loader
        assert "morpheme" in deps
        assert "data_loader" in deps
