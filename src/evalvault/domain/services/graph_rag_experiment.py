"""GraphRAG experiment helper for baseline vs graph comparison."""

from __future__ import annotations

from dataclasses import dataclass

from evalvault.domain.entities import Dataset, EvaluationRun, TestCase
from evalvault.domain.entities.analysis import ComparisonResult
from evalvault.domain.entities.graph_rag import KnowledgeSubgraph
from evalvault.domain.services.analysis_service import AnalysisService
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.ports.outbound.graph_retriever_port import GraphRetrieverPort
from evalvault.ports.outbound.korean_nlp_port import RetrieverPort
from evalvault.ports.outbound.llm_port import LLMPort


@dataclass
class GraphRAGExperimentResult:
    baseline_run: EvaluationRun
    graph_run: EvaluationRun
    comparisons: list[ComparisonResult]
    graph_subgraphs: dict[str, KnowledgeSubgraph]
    graph_contexts: dict[str, str]


class GraphRAGExperiment:
    """Compare baseline retrieval with GraphRAG context generation."""

    def __init__(
        self,
        *,
        evaluator: RagasEvaluator,
        analysis_service: AnalysisService,
    ) -> None:
        self._evaluator = evaluator
        self._analysis = analysis_service

    async def run_comparison(
        self,
        *,
        dataset: Dataset,
        baseline_retriever: RetrieverPort,
        graph_retriever: GraphRetrieverPort,
        metrics: list[str],
        llm: LLMPort,
        thresholds: dict[str, float] | None = None,
        retriever_top_k: int = 5,
        graph_max_hops: int = 2,
        graph_max_nodes: int = 20,
        parallel: bool = False,
        batch_size: int = 5,
        prompt_overrides: dict[str, str] | None = None,
        claim_level: bool = False,
        language: str | None = None,
    ) -> GraphRAGExperimentResult:
        baseline_dataset = self._clone_dataset(dataset)
        graph_dataset = self._clone_dataset(dataset)

        graph_subgraphs, graph_contexts = self._apply_graph_contexts(
            graph_dataset,
            graph_retriever,
            max_hops=graph_max_hops,
            max_nodes=graph_max_nodes,
        )

        baseline_run = await self._evaluator.evaluate(
            baseline_dataset,
            metrics,
            llm,
            thresholds=thresholds,
            parallel=parallel,
            batch_size=batch_size,
            retriever=baseline_retriever,
            retriever_top_k=retriever_top_k,
            prompt_overrides=prompt_overrides,
            claim_level=claim_level,
            language=language,
        )

        graph_run = await self._evaluator.evaluate(
            graph_dataset,
            metrics,
            llm,
            thresholds=thresholds,
            parallel=parallel,
            batch_size=batch_size,
            retriever=None,
            prompt_overrides=prompt_overrides,
            claim_level=claim_level,
            language=language,
        )

        comparisons = self._analysis.compare_runs(
            baseline_run,
            graph_run,
            metrics=metrics,
        )

        return GraphRAGExperimentResult(
            baseline_run=baseline_run,
            graph_run=graph_run,
            comparisons=comparisons,
            graph_subgraphs=graph_subgraphs,
            graph_contexts=graph_contexts,
        )

    @staticmethod
    def _clone_dataset(dataset: Dataset) -> Dataset:
        test_cases = [
            TestCase(
                id=case.id,
                question=case.question,
                answer=case.answer,
                contexts=list(case.contexts),
                ground_truth=case.ground_truth,
                metadata=dict(case.metadata),
            )
            for case in dataset.test_cases
        ]
        return Dataset(
            name=dataset.name,
            version=dataset.version,
            test_cases=test_cases,
            metadata=dict(dataset.metadata),
            source_file=dataset.source_file,
            thresholds=dict(dataset.thresholds),
        )

    @staticmethod
    def _apply_graph_contexts(
        dataset: Dataset,
        graph_retriever: GraphRetrieverPort,
        *,
        max_hops: int,
        max_nodes: int,
    ) -> tuple[dict[str, KnowledgeSubgraph], dict[str, str]]:
        subgraphs: dict[str, KnowledgeSubgraph] = {}
        contexts: dict[str, str] = {}
        for case in dataset.test_cases:
            if case.contexts and any(context.strip() for context in case.contexts):
                continue
            subgraph = graph_retriever.build_subgraph(
                case.question,
                max_hops=max_hops,
                max_nodes=max_nodes,
            )
            context_text = graph_retriever.generate_context(subgraph)
            if context_text:
                case.contexts = [context_text]
                contexts[case.id] = context_text
            subgraphs[case.id] = subgraph
        return subgraphs, contexts


__all__ = ["GraphRAGExperiment", "GraphRAGExperimentResult"]
