"""Phase 14.3: PipelineOrchestrator 단위 테스트.

TDD Red Phase - 테스트 먼저 작성.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

# =============================================================================
# PipelineOrchestrator Tests
# =============================================================================


class TestPipelineOrchestrator:
    """PipelineOrchestrator 테스트 - 파이프라인 실행기."""

    def test_orchestrator_creation(self):
        """오케스트레이터 생성."""
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        assert orchestrator is not None

    def test_orchestrator_with_module_registry(self):
        """모듈 레지스트리와 함께 오케스트레이터 생성."""
        from evalvault.domain.entities.analysis_pipeline import ModuleCatalog
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        catalog = ModuleCatalog()
        orchestrator = PipelineOrchestrator(module_catalog=catalog)

        assert orchestrator.module_catalog is catalog

    def test_orchestrator_build_pipeline_from_intent(self):
        """의도로부터 파이프라인 빌드."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()
        context = AnalysisContext(query="형태소 분석을 확인해줘")

        pipeline = orchestrator.build_pipeline(
            intent=AnalysisIntent.VERIFY_MORPHEME,
            context=context,
        )

        assert pipeline is not None
        assert pipeline.intent == AnalysisIntent.VERIFY_MORPHEME
        assert len(pipeline.nodes) > 0

    def test_orchestrator_build_pipeline_from_query(self):
        """쿼리로부터 파이프라인 빌드 (의도 분류 포함)."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()
        context = AnalysisContext(query="형태소 분석이 제대로 되고 있는지 확인해줘")

        pipeline = orchestrator.build_pipeline_from_query(context)

        assert pipeline is not None
        assert pipeline.intent == AnalysisIntent.VERIFY_MORPHEME

    def test_orchestrator_register_module(self):
        """모듈 등록."""
        from evalvault.domain.entities.analysis_pipeline import ModuleMetadata
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        # Mock 모듈 생성
        mock_module = MagicMock()
        mock_module.module_id = "test_module"
        mock_module.metadata = ModuleMetadata(
            module_id="test_module",
            name="Test Module",
            description="테스트 모듈",
            input_types=["input"],
            output_types=["output"],
        )

        orchestrator.register_module(mock_module)

        assert orchestrator.get_module("test_module") is mock_module

    def test_orchestrator_get_module_not_found(self):
        """존재하지 않는 모듈 조회."""
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        module = orchestrator.get_module("nonexistent")

        assert module is None

    def test_orchestrator_execute_pipeline_simple(self):
        """단순 파이프라인 실행."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
            NodeExecutionStatus,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        # Mock 모듈 등록
        mock_module = MagicMock()
        mock_module.module_id = "test_module"
        mock_module.validate_inputs.return_value = True
        mock_module.execute.return_value = {"result": "success"}
        orchestrator.register_module(mock_module)

        # 단순 파이프라인 생성
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="node1", name="Node 1", module="test_module"),
            ],
        )
        context = AnalysisContext(query="테스트")

        result = orchestrator.execute(pipeline, context)

        assert result is not None
        assert result.pipeline_id == pipeline.pipeline_id
        assert result.is_complete
        assert "node1" in result.node_results
        assert result.node_results["node1"].status == NodeExecutionStatus.COMPLETED

    def test_orchestrator_execute_pipeline_with_dependencies(self):
        """의존성이 있는 파이프라인 실행."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        # Mock 모듈 등록
        mock_module_a = MagicMock()
        mock_module_a.module_id = "module_a"
        mock_module_a.validate_inputs.return_value = True
        mock_module_a.execute.return_value = {"data": "from_a"}

        mock_module_b = MagicMock()
        mock_module_b.module_id = "module_b"
        mock_module_b.validate_inputs.return_value = True
        mock_module_b.execute.return_value = {"data": "from_b"}

        orchestrator.register_module(mock_module_a)
        orchestrator.register_module(mock_module_b)

        # 의존성이 있는 파이프라인: a -> b
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="a", name="A", module="module_a"),
                AnalysisNode(id="b", name="B", module="module_b", depends_on=["a"]),
            ],
        )
        context = AnalysisContext(query="테스트")

        result = orchestrator.execute(pipeline, context)

        assert result.all_succeeded
        # b가 a의 출력을 입력으로 받았는지 확인
        mock_module_b.execute.assert_called()

    def test_orchestrator_execute_respects_topological_order(self):
        """위상 정렬 순서대로 실행하는지 확인."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()
        execution_order = []

        def make_module(module_id: str):
            mock = MagicMock()
            mock.module_id = module_id
            mock.validate_inputs.return_value = True

            def execute_side_effect(inputs, params=None):
                execution_order.append(module_id)
                return {"from": module_id}

            mock.execute.side_effect = execute_side_effect
            return mock

        # 모듈 등록
        orchestrator.register_module(make_module("m1"))
        orchestrator.register_module(make_module("m2"))
        orchestrator.register_module(make_module("m3"))

        # 파이프라인: m1 -> m2 -> m3
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="n3", name="N3", module="m3", depends_on=["n2"]),
                AnalysisNode(id="n1", name="N1", module="m1"),
                AnalysisNode(id="n2", name="N2", module="m2", depends_on=["n1"]),
            ],
        )
        context = AnalysisContext(query="테스트")

        orchestrator.execute(pipeline, context)

        # m1 -> m2 -> m3 순서로 실행되어야 함
        assert execution_order == ["m1", "m2", "m3"]

    def test_orchestrator_execute_handles_missing_module(self):
        """존재하지 않는 모듈 처리."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
            NodeExecutionStatus,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        # 모듈 등록하지 않고 파이프라인 실행
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="node1", name="Node 1", module="nonexistent_module"),
            ],
        )
        context = AnalysisContext(query="테스트")

        result = orchestrator.execute(pipeline, context)

        assert result.node_results["node1"].status == NodeExecutionStatus.FAILED
        assert "not found" in result.node_results["node1"].error.lower()

    def test_orchestrator_execute_handles_module_error(self):
        """모듈 실행 에러 처리."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
            NodeExecutionStatus,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        # 에러를 발생시키는 모듈
        mock_module = MagicMock()
        mock_module.module_id = "error_module"
        mock_module.validate_inputs.return_value = True
        mock_module.execute.side_effect = RuntimeError("Something went wrong")
        orchestrator.register_module(mock_module)

        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="node1", name="Node 1", module="error_module"),
            ],
        )
        context = AnalysisContext(query="테스트")

        result = orchestrator.execute(pipeline, context)

        assert result.node_results["node1"].status == NodeExecutionStatus.FAILED
        assert "Something went wrong" in result.node_results["node1"].error

    def test_orchestrator_execute_skips_dependent_nodes_on_failure(self):
        """선행 노드 실패 시 의존 노드 건너뛰기."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
            NodeExecutionStatus,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        # 첫 번째 모듈은 실패
        mock_module_a = MagicMock()
        mock_module_a.module_id = "module_a"
        mock_module_a.validate_inputs.return_value = True
        mock_module_a.execute.side_effect = RuntimeError("Failed")

        # 두 번째 모듈은 성공
        mock_module_b = MagicMock()
        mock_module_b.module_id = "module_b"
        mock_module_b.validate_inputs.return_value = True
        mock_module_b.execute.return_value = {"data": "success"}

        orchestrator.register_module(mock_module_a)
        orchestrator.register_module(mock_module_b)

        # a -> b 의존성
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="a", name="A", module="module_a"),
                AnalysisNode(id="b", name="B", module="module_b", depends_on=["a"]),
            ],
        )
        context = AnalysisContext(query="테스트")

        result = orchestrator.execute(pipeline, context)

        assert result.node_results["a"].status == NodeExecutionStatus.FAILED
        assert result.node_results["b"].status == NodeExecutionStatus.SKIPPED

    def test_orchestrator_execute_collects_final_output(self):
        """최종 출력 수집."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        mock_module = MagicMock()
        mock_module.module_id = "final_module"
        mock_module.validate_inputs.return_value = True
        mock_module.execute.return_value = {"summary": "최종 결과"}
        orchestrator.register_module(mock_module)

        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="final", name="Final", module="final_module"),
            ],
        )
        context = AnalysisContext(query="테스트")

        result = orchestrator.execute(pipeline, context)

        # 리프 노드의 출력이 최종 출력으로 수집됨
        assert result.final_output is not None
        assert result.final_output["final"]["summary"] == "최종 결과"

    def test_orchestrator_execute_measures_duration(self):
        """실행 시간 측정."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        mock_module = MagicMock()
        mock_module.module_id = "test_module"
        mock_module.validate_inputs.return_value = True
        mock_module.execute.return_value = {}
        orchestrator.register_module(mock_module)

        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="node1", name="Node 1", module="test_module"),
            ],
        )
        context = AnalysisContext(query="테스트")

        result = orchestrator.execute(pipeline, context)

        assert result.total_duration_ms is not None
        assert result.total_duration_ms >= 0
        assert result.node_results["node1"].duration_ms is not None

    def test_orchestrator_passes_context_to_modules(self):
        """모듈에 컨텍스트 전달."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        mock_module = MagicMock()
        mock_module.module_id = "test_module"
        mock_module.validate_inputs.return_value = True
        mock_module.execute.return_value = {}
        orchestrator.register_module(mock_module)

        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(
                    id="node1",
                    name="Node 1",
                    module="test_module",
                    params={"custom": "param"},
                ),
            ],
        )
        context = AnalysisContext(
            query="테스트",
            run_id="run-123",
            additional_params={"extra": "value"},
        )

        orchestrator.execute(pipeline, context)

        # execute가 호출되었는지 확인
        mock_module.execute.assert_called_once()
        call_args = mock_module.execute.call_args

        # 입력에 컨텍스트 정보가 포함되어 있어야 함
        inputs = call_args[0][0] if call_args[0] else call_args[1].get("inputs", {})
        assert "__context__" in inputs or "query" in inputs or inputs.get("__context__")

    def test_orchestrator_passes_node_params_to_module(self):
        """노드 파라미터를 모듈에 전달."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        mock_module = MagicMock()
        mock_module.module_id = "test_module"
        mock_module.validate_inputs.return_value = True
        mock_module.execute.return_value = {}
        orchestrator.register_module(mock_module)

        custom_params = {"threshold": 0.5, "mode": "strict"}
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(
                    id="node1",
                    name="Node 1",
                    module="test_module",
                    params=custom_params,
                ),
            ],
        )
        context = AnalysisContext(query="테스트")

        orchestrator.execute(pipeline, context)

        # params가 전달되었는지 확인
        call_args = mock_module.execute.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params")
        assert params == custom_params


# =============================================================================
# PipelineOrchestrator Async Tests
# =============================================================================


class TestPipelineOrchestratorAsync:
    """PipelineOrchestrator 비동기 실행 테스트."""

    @pytest.mark.asyncio
    async def test_orchestrator_execute_async(self):
        """비동기 파이프라인 실행."""
        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
            NodeExecutionStatus,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()

        mock_module = MagicMock()
        mock_module.module_id = "async_module"
        mock_module.validate_inputs.return_value = True
        mock_module.execute_async = AsyncMock(return_value={"result": "async_success"})
        orchestrator.register_module(mock_module)

        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="node1", name="Node 1", module="async_module"),
            ],
        )
        context = AnalysisContext(query="테스트")

        result = await orchestrator.execute_async(pipeline, context)

        assert result.is_complete
        assert result.node_results["node1"].status == NodeExecutionStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_orchestrator_execute_async_parallel_independent_nodes(self):
        """독립 노드 병렬 실행."""
        import asyncio

        from evalvault.domain.entities.analysis_pipeline import (
            AnalysisContext,
            AnalysisIntent,
            AnalysisNode,
            AnalysisPipeline,
        )
        from evalvault.domain.services.pipeline_orchestrator import (
            PipelineOrchestrator,
        )

        orchestrator = PipelineOrchestrator()
        execution_times = {}

        async def make_async_execute(module_id: str, delay: float):
            async def execute_async(inputs, params=None):
                start = asyncio.get_event_loop().time()
                await asyncio.sleep(delay)
                end = asyncio.get_event_loop().time()
                execution_times[module_id] = (start, end)
                return {"from": module_id}

            return execute_async

        # 독립적인 두 모듈 (병렬 실행 가능)
        mock_a = MagicMock()
        mock_a.module_id = "module_a"
        mock_a.validate_inputs.return_value = True
        mock_a.execute_async = AsyncMock(side_effect=lambda i, p=None: {"from": "a"})

        mock_b = MagicMock()
        mock_b.module_id = "module_b"
        mock_b.validate_inputs.return_value = True
        mock_b.execute_async = AsyncMock(side_effect=lambda i, p=None: {"from": "b"})

        # 두 모듈에 의존하는 모듈
        mock_c = MagicMock()
        mock_c.module_id = "module_c"
        mock_c.validate_inputs.return_value = True
        mock_c.execute_async = AsyncMock(side_effect=lambda i, p=None: {"from": "c"})

        orchestrator.register_module(mock_a)
        orchestrator.register_module(mock_b)
        orchestrator.register_module(mock_c)

        # a와 b는 독립, c는 둘 다에 의존
        pipeline = AnalysisPipeline(
            intent=AnalysisIntent.GENERATE_SUMMARY,
            nodes=[
                AnalysisNode(id="a", name="A", module="module_a"),
                AnalysisNode(id="b", name="B", module="module_b"),
                AnalysisNode(id="c", name="C", module="module_c", depends_on=["a", "b"]),
            ],
        )
        context = AnalysisContext(query="테스트")

        result = await orchestrator.execute_async(pipeline, context)

        assert result.all_succeeded
        # c는 a와 b 이후에 실행되어야 함


# =============================================================================
# AnalysisPipelineService Tests (High-level API)
# =============================================================================


class TestAnalysisPipelineService:
    """AnalysisPipelineService 테스트 - 고수준 API."""

    def test_service_creation(self):
        """서비스 생성."""
        from evalvault.domain.services.pipeline_orchestrator import (
            AnalysisPipelineService,
        )

        service = AnalysisPipelineService()

        assert service is not None

    def test_service_analyze_query(self):
        """쿼리 분석 - 원스텝 API."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_orchestrator import (
            AnalysisPipelineService,
        )

        service = AnalysisPipelineService()

        # 모듈 등록 (테스트용)
        mock_module = MagicMock()
        mock_module.module_id = "data_loader"
        mock_module.validate_inputs.return_value = True
        mock_module.execute.return_value = {"loaded": True}
        service.register_module(mock_module)

        mock_stats = MagicMock()
        mock_stats.module_id = "statistical_analyzer"
        mock_stats.validate_inputs.return_value = True
        mock_stats.execute.return_value = {"stats": {"mean": 0.8}}
        service.register_module(mock_stats)

        mock_report = MagicMock()
        mock_report.module_id = "summary_report"
        mock_report.validate_inputs.return_value = True
        mock_report.execute.return_value = {"report": "요약 보고서"}
        service.register_module(mock_report)

        result = service.analyze("결과를 요약해줘")

        assert result is not None
        assert result.intent == AnalysisIntent.GENERATE_SUMMARY

    def test_service_analyze_with_run_id(self):
        """run_id와 함께 분석."""
        from evalvault.domain.services.pipeline_orchestrator import (
            AnalysisPipelineService,
        )

        service = AnalysisPipelineService()

        # 모듈 등록
        mock_module = MagicMock()
        mock_module.module_id = "data_loader"
        mock_module.validate_inputs.return_value = True
        mock_module.execute.return_value = {"loaded": True}
        service.register_module(mock_module)

        mock_stats = MagicMock()
        mock_stats.module_id = "statistical_analyzer"
        mock_stats.validate_inputs.return_value = True
        mock_stats.execute.return_value = {"stats": {}}
        service.register_module(mock_stats)

        mock_report = MagicMock()
        mock_report.module_id = "summary_report"
        mock_report.validate_inputs.return_value = True
        mock_report.execute.return_value = {"report": "보고서"}
        service.register_module(mock_report)

        result = service.analyze("결과를 요약해줘", run_id="run-123")

        assert result is not None

    def test_service_get_intent_from_query(self):
        """쿼리에서 의도 추출."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_orchestrator import (
            AnalysisPipelineService,
        )

        service = AnalysisPipelineService()

        intent = service.get_intent("형태소 분석을 확인해줘")

        assert intent == AnalysisIntent.VERIFY_MORPHEME

    def test_service_get_available_intents(self):
        """사용 가능한 의도 목록."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_orchestrator import (
            AnalysisPipelineService,
        )

        service = AnalysisPipelineService()

        intents = service.get_available_intents()

        assert len(intents) == len(AnalysisIntent)
        assert AnalysisIntent.VERIFY_MORPHEME in intents

    def test_service_get_pipeline_template(self):
        """파이프라인 템플릿 조회."""
        from evalvault.domain.entities.analysis_pipeline import AnalysisIntent
        from evalvault.domain.services.pipeline_orchestrator import (
            AnalysisPipelineService,
        )

        service = AnalysisPipelineService()

        template = service.get_pipeline_template(AnalysisIntent.VERIFY_MORPHEME)

        assert template is not None
        assert template.intent == AnalysisIntent.VERIFY_MORPHEME
