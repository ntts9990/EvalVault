"""Phase 14.3: Pipeline Orchestrator.

DAG 기반 분석 파이프라인을 실행하는 오케스트레이터입니다.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisContext,
    AnalysisIntent,
    AnalysisNode,
    AnalysisPipeline,
    ModuleCatalog,
    NodeExecutionStatus,
    NodeResult,
    PipelineResult,
)
from evalvault.domain.services.intent_classifier import KeywordIntentClassifier
from evalvault.domain.services.pipeline_template_registry import PipelineTemplateRegistry

if TYPE_CHECKING:
    from evalvault.ports.outbound.analysis_module_port import AnalysisModulePort


# =============================================================================
# PipelineOrchestrator
# =============================================================================


@dataclass
class PipelineOrchestrator:
    """파이프라인 오케스트레이터.

    DAG 기반 분석 파이프라인을 빌드하고 실행합니다.

    Attributes:
        module_catalog: 모듈 메타데이터 카탈로그
        template_registry: 파이프라인 템플릿 레지스트리
        intent_classifier: 의도 분류기
    """

    module_catalog: ModuleCatalog = field(default_factory=ModuleCatalog)
    template_registry: PipelineTemplateRegistry = field(default_factory=PipelineTemplateRegistry)
    intent_classifier: KeywordIntentClassifier = field(default_factory=KeywordIntentClassifier)
    _modules: dict[str, AnalysisModulePort] = field(default_factory=dict)

    def register_module(self, module: AnalysisModulePort) -> None:
        """분석 모듈 등록.

        Args:
            module: 등록할 분석 모듈

        Note:
            BaseAnalysisModule 구현체는 module_id, name, metadata를 반드시
            채워야 하며, metadata는 ModuleCatalog를 통해 템플릿 점검/도구화에
            활용됩니다. 새 모듈을 추가할 때는 register_module()을 호출하여
            의존성 그래프에 반영해야 합니다.
        """
        self._modules[module.module_id] = module
        if hasattr(module, "metadata") and module.metadata:
            self.module_catalog.register(module.metadata)

    def list_registered_modules(self) -> list[str]:
        """등록된 모듈 ID 목록."""
        return list(self._modules.keys())

    def get_module(self, module_id: str) -> AnalysisModulePort | None:
        """모듈 조회.

        Args:
            module_id: 모듈 ID

        Returns:
            모듈 또는 None
        """
        return self._modules.get(module_id)

    def build_pipeline(
        self,
        intent: AnalysisIntent,
        context: AnalysisContext,
    ) -> AnalysisPipeline:
        """의도와 컨텍스트에 따라 파이프라인 빌드.

        Args:
            intent: 분석 의도
            context: 분석 컨텍스트

        Returns:
            구성된 파이프라인
        """
        template = self.template_registry.get_template(intent)
        if template:
            # 템플릿 복사하여 새 파이프라인 생성
            return AnalysisPipeline(
                intent=intent,
                nodes=list(template.nodes),
                edges=list(template.edges),
            )
        # 기본 파이프라인
        return AnalysisPipeline(intent=intent)

    def build_pipeline_from_query(self, context: AnalysisContext) -> AnalysisPipeline:
        """쿼리에서 의도를 추출하여 파이프라인 빌드.

        Args:
            context: 분석 컨텍스트 (query 포함)

        Returns:
            구성된 파이프라인
        """
        intent = self.intent_classifier.classify(context.query)
        return self.build_pipeline(intent, context)

    def execute(
        self,
        pipeline: AnalysisPipeline,
        context: AnalysisContext,
    ) -> PipelineResult:
        """파이프라인 동기 실행.

        Args:
            pipeline: 실행할 파이프라인
            context: 분석 컨텍스트

        Returns:
            파이프라인 실행 결과
        """
        start_time = time.time()
        result = PipelineResult(
            pipeline_id=pipeline.pipeline_id,
            intent=pipeline.intent,
        )

        # 위상 정렬 순서로 노드 실행
        execution_order = pipeline.topological_order()
        node_outputs: dict[str, Any] = {}
        failed_nodes: set[str] = set()

        for node_id in execution_order:
            node = pipeline.get_node(node_id)
            if not node:
                continue

            # 의존 노드가 실패했으면 건너뛰기
            if any(dep in failed_nodes for dep in node.depends_on):
                result.add_node_result(
                    NodeResult(
                        node_id=node_id,
                        status=NodeExecutionStatus.SKIPPED,
                        error="Dependency failed",
                    )
                )
                failed_nodes.add(node_id)
                continue

            # 노드 실행
            node_result = self._execute_node(node, context, node_outputs)
            result.add_node_result(node_result)

            if node_result.is_success:
                node_outputs[node_id] = node_result.output
            else:
                failed_nodes.add(node_id)

        # 최종 출력 수집 (리프 노드들의 출력)
        final_output = {}
        for node in pipeline.leaf_nodes:
            if node.id in node_outputs:
                final_output[node.id] = node_outputs[node.id]

        # 리프 노드가 없으면 마지막 실행 노드의 출력 사용
        if not final_output and execution_order:
            last_node_id = execution_order[-1]
            if last_node_id in node_outputs:
                final_output[last_node_id] = node_outputs[last_node_id]

        total_duration_ms = int((time.time() - start_time) * 1000)
        result.mark_complete(
            final_output=final_output if final_output else None,
            total_duration_ms=total_duration_ms,
        )

        return result

    def _execute_node(
        self,
        node: AnalysisNode,
        context: AnalysisContext,
        node_outputs: dict[str, Any],
    ) -> NodeResult:
        """개별 노드 실행.

        Args:
            node: 실행할 노드
            context: 분석 컨텍스트
            node_outputs: 이전 노드들의 출력

        Returns:
            노드 실행 결과
        """
        start_time = time.time()

        # 모듈 조회
        module = self.get_module(node.module)
        if not module:
            return NodeResult(
                node_id=node.id,
                status=NodeExecutionStatus.FAILED,
                error=f"Module not found: {node.module}",
            )

        # 입력 준비
        inputs = self._prepare_inputs(node, context, node_outputs)

        try:
            # 모듈 실행
            output = module.execute(inputs, node.params)
            duration_ms = int((time.time() - start_time) * 1000)

            return NodeResult(
                node_id=node.id,
                status=NodeExecutionStatus.COMPLETED,
                output=output,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return NodeResult(
                node_id=node.id,
                status=NodeExecutionStatus.FAILED,
                error=str(e),
                duration_ms=duration_ms,
            )

    def _prepare_inputs(
        self,
        node: AnalysisNode,
        context: AnalysisContext,
        node_outputs: dict[str, Any],
    ) -> dict[str, Any]:
        """노드 입력 준비.

        Args:
            node: 실행할 노드
            context: 분석 컨텍스트
            node_outputs: 이전 노드들의 출력

        Returns:
            입력 딕셔너리
        """
        inputs: dict[str, Any] = {
            "__context__": {
                "query": context.query,
                "run_id": context.run_id,
                "additional_params": context.additional_params,
            }
        }

        # 의존 노드의 출력 추가
        for dep_id in node.depends_on:
            if dep_id in node_outputs:
                inputs[dep_id] = node_outputs[dep_id]

        return inputs

    async def execute_async(
        self,
        pipeline: AnalysisPipeline,
        context: AnalysisContext,
    ) -> PipelineResult:
        """파이프라인 비동기 실행.

        독립적인 노드들은 병렬로 실행합니다.

        Args:
            pipeline: 실행할 파이프라인
            context: 분석 컨텍스트

        Returns:
            파이프라인 실행 결과
        """
        start_time = time.time()
        result = PipelineResult(
            pipeline_id=pipeline.pipeline_id,
            intent=pipeline.intent,
        )

        node_outputs: dict[str, Any] = {}
        failed_nodes: set[str] = set()
        completed_nodes: set[str] = set()

        # 노드를 레벨별로 그룹화 (동일 레벨 = 병렬 실행 가능)
        levels = self._group_nodes_by_level(pipeline)

        for level_nodes in levels:
            # 현재 레벨의 실행 가능한 노드들
            executable_nodes = []
            for node in level_nodes:
                # 의존 노드가 실패했으면 건너뛰기
                if any(dep in failed_nodes for dep in node.depends_on):
                    result.add_node_result(
                        NodeResult(
                            node_id=node.id,
                            status=NodeExecutionStatus.SKIPPED,
                            error="Dependency failed",
                        )
                    )
                    failed_nodes.add(node.id)
                else:
                    executable_nodes.append(node)

            # 병렬 실행
            if executable_nodes:
                tasks = [
                    self._execute_node_async(node, context, node_outputs)
                    for node in executable_nodes
                ]
                node_results = await asyncio.gather(*tasks)

                for node, node_result in zip(executable_nodes, node_results, strict=True):
                    result.add_node_result(node_result)
                    if node_result.is_success:
                        node_outputs[node.id] = node_result.output
                        completed_nodes.add(node.id)
                    else:
                        failed_nodes.add(node.id)

        # 최종 출력 수집
        final_output = {}
        for node in pipeline.leaf_nodes:
            if node.id in node_outputs:
                final_output[node.id] = node_outputs[node.id]

        if not final_output:
            # 가장 마지막에 완료된 노드의 출력 사용
            execution_order = pipeline.topological_order()
            for node_id in reversed(execution_order):
                if node_id in node_outputs:
                    final_output[node_id] = node_outputs[node_id]
                    break

        total_duration_ms = int((time.time() - start_time) * 1000)
        result.mark_complete(
            final_output=final_output if final_output else None,
            total_duration_ms=total_duration_ms,
        )

        return result

    async def _execute_node_async(
        self,
        node: AnalysisNode,
        context: AnalysisContext,
        node_outputs: dict[str, Any],
    ) -> NodeResult:
        """개별 노드 비동기 실행.

        Args:
            node: 실행할 노드
            context: 분석 컨텍스트
            node_outputs: 이전 노드들의 출력

        Returns:
            노드 실행 결과
        """
        start_time = time.time()

        module = self.get_module(node.module)
        if not module:
            return NodeResult(
                node_id=node.id,
                status=NodeExecutionStatus.FAILED,
                error=f"Module not found: {node.module}",
            )

        inputs = self._prepare_inputs(node, context, node_outputs)

        try:
            # 비동기 실행 메서드가 있으면 사용
            if hasattr(module, "execute_async"):
                output = await module.execute_async(inputs, node.params)
            else:
                # 동기 실행을 executor에서 실행
                loop = asyncio.get_event_loop()
                output = await loop.run_in_executor(
                    None, lambda: module.execute(inputs, node.params)
                )

            duration_ms = int((time.time() - start_time) * 1000)
            return NodeResult(
                node_id=node.id,
                status=NodeExecutionStatus.COMPLETED,
                output=output,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return NodeResult(
                node_id=node.id,
                status=NodeExecutionStatus.FAILED,
                error=str(e),
                duration_ms=duration_ms,
            )

    def _group_nodes_by_level(self, pipeline: AnalysisPipeline) -> list[list[AnalysisNode]]:
        """노드를 의존성 레벨별로 그룹화.

        같은 레벨의 노드들은 병렬 실행 가능합니다.

        Args:
            pipeline: 파이프라인

        Returns:
            레벨별 노드 그룹 목록
        """
        if not pipeline.nodes:
            return []

        # 노드 ID -> 레벨 매핑
        node_levels: dict[str, int] = {}

        # 루트 노드는 레벨 0
        for node in pipeline.root_nodes:
            node_levels[node.id] = 0

        # BFS로 레벨 계산
        changed = True
        while changed:
            changed = False
            for node in pipeline.nodes:
                if node.id in node_levels:
                    continue
                # 모든 의존 노드의 레벨이 계산되었는지 확인
                if all(dep in node_levels for dep in node.depends_on):
                    max_dep_level = max(node_levels[dep] for dep in node.depends_on)
                    node_levels[node.id] = max_dep_level + 1
                    changed = True

        # 레벨별로 그룹화
        max_level = max(node_levels.values()) if node_levels else 0
        levels: list[list[AnalysisNode]] = [[] for _ in range(max_level + 1)]

        for node in pipeline.nodes:
            if node.id in node_levels:
                levels[node_levels[node.id]].append(node)

        return levels


# =============================================================================
# AnalysisPipelineService (High-level API)
# =============================================================================


@dataclass
class AnalysisPipelineService:
    """분석 파이프라인 서비스.

    사용자 친화적인 고수준 API를 제공합니다.
    """

    _orchestrator: PipelineOrchestrator = field(default_factory=PipelineOrchestrator)

    def register_module(self, module: AnalysisModulePort) -> None:
        """모듈 등록.

        Args:
            module: 등록할 모듈
        """
        self._orchestrator.register_module(module)

    def analyze(
        self,
        query: str,
        run_id: str | None = None,
        dataset: Any | None = None,
        **kwargs: Any,
    ) -> PipelineResult:
        """쿼리 분석 실행.

        쿼리에서 의도를 추출하고, 적절한 파이프라인을 빌드하여 실행합니다.

        Args:
            query: 분석 요청 쿼리
            run_id: 분석 대상 실행 ID (선택)
            dataset: 분석 대상 데이터셋 (선택)
            **kwargs: 추가 파라미터

        Returns:
            분석 결과
        """
        context = AnalysisContext(
            query=query,
            run_id=run_id,
            dataset=dataset,
            additional_params=kwargs,
        )

        pipeline = self._orchestrator.build_pipeline_from_query(context)
        return self._orchestrator.execute(pipeline, context)

    def analyze_intent(
        self,
        intent: AnalysisIntent,
        *,
        query: str | None = None,
        run_id: str | None = None,
        dataset: Any | None = None,
        **kwargs: Any,
    ) -> PipelineResult:
        """의도를 명시하여 파이프라인을 실행."""
        context = AnalysisContext(
            query=query or intent.value,
            run_id=run_id,
            dataset=dataset,
            additional_params=kwargs,
        )
        pipeline = self._orchestrator.build_pipeline(intent, context)
        return self._orchestrator.execute(pipeline, context)

    async def analyze_async(
        self,
        query: str,
        run_id: str | None = None,
        dataset: Any | None = None,
        **kwargs: Any,
    ) -> PipelineResult:
        """쿼리 분석 비동기 실행.

        Args:
            query: 분석 요청 쿼리
            run_id: 분석 대상 실행 ID (선택)
            dataset: 분석 대상 데이터셋 (선택)
            **kwargs: 추가 파라미터

        Returns:
            분석 결과
        """
        context = AnalysisContext(
            query=query,
            run_id=run_id,
            dataset=dataset,
            additional_params=kwargs,
        )

        pipeline = self._orchestrator.build_pipeline_from_query(context)
        return await self._orchestrator.execute_async(pipeline, context)

    async def analyze_intent_async(
        self,
        intent: AnalysisIntent,
        *,
        query: str | None = None,
        run_id: str | None = None,
        dataset: Any | None = None,
        **kwargs: Any,
    ) -> PipelineResult:
        """의도를 명시하여 파이프라인을 비동기로 실행."""
        context = AnalysisContext(
            query=query or intent.value,
            run_id=run_id,
            dataset=dataset,
            additional_params=kwargs,
        )
        pipeline = self._orchestrator.build_pipeline(intent, context)
        return await self._orchestrator.execute_async(pipeline, context)

    def get_intent(self, query: str) -> AnalysisIntent:
        """쿼리에서 의도 추출.

        Args:
            query: 분석 요청 쿼리

        Returns:
            분류된 의도
        """
        return self._orchestrator.intent_classifier.classify(query)

    def get_available_intents(self) -> list[AnalysisIntent]:
        """사용 가능한 의도 목록.

        Returns:
            의도 목록
        """
        return list(AnalysisIntent)

    def get_pipeline_template(self, intent: AnalysisIntent) -> AnalysisPipeline | None:
        """의도에 대한 파이프라인 템플릿 조회.

        Args:
            intent: 분석 의도

        Returns:
            파이프라인 템플릿 또는 None
        """
        return self._orchestrator.template_registry.get_template(intent)

    def get_registered_modules(self) -> list[str]:
        """등록된 분석 모듈 ID 목록."""
        return self._orchestrator.list_registered_modules()
