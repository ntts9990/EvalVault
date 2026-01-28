from __future__ import annotations

import asyncio
from dataclasses import dataclass

from evalvault.domain.entities.dataset import Dataset, TestCase
from evalvault.domain.entities.multiturn import (
    ConversationTurn,
    DriftAnalysis,
    MultiTurnEvaluationResult,
    MultiTurnTestCase,
    MultiTurnTurnResult,
)
from evalvault.domain.metrics.multiturn_metrics import (
    calculate_context_coherence,
    calculate_drift_rate,
    calculate_turn_faithfulness,
    calculate_turn_latency_p95,
)
from evalvault.domain.services.evaluator import RagasEvaluator
from evalvault.ports.inbound.multiturn_port import MultiTurnEvaluatorPort
from evalvault.ports.outbound.llm_port import LLMPort


@dataclass(frozen=True)
class _TurnMapping:
    test_case_id: str
    turn: ConversationTurn
    turn_index: int


class MultiTurnEvaluator(MultiTurnEvaluatorPort):
    MULTITURN_METRICS = {"turn_faithfulness", "context_coherence", "drift_rate", "turn_latency"}

    def __init__(
        self, *, evaluator: RagasEvaluator | None = None, llm: LLMPort | None = None
    ) -> None:
        self._evaluator = evaluator
        self._llm = llm

    def evaluate_conversation(
        self,
        conversation: MultiTurnTestCase,
        metrics: list[str],
    ) -> MultiTurnEvaluationResult:
        dataset, mappings = self._build_turn_dataset(conversation)
        base_metrics = [metric for metric in metrics if self._is_base_metric(metric)]
        if "turn_faithfulness" in metrics and "faithfulness" not in base_metrics:
            base_metrics.append("faithfulness")

        turn_results: list[MultiTurnTurnResult] = []
        scores_by_case: dict[str, dict[str, float]] = {}
        metadata_by_case: dict[str, dict[str, object]] = {
            mapping.test_case_id: {
                "conversation_id": conversation.conversation_id,
                "turn_index": mapping.turn_index,
                "turn_id": mapping.turn.turn_id,
                "role": mapping.turn.role,
            }
            for mapping in mappings
        }

        if base_metrics:
            if not self._evaluator or not self._llm:
                raise ValueError("MultiTurnEvaluator requires evaluator and llm for base metrics")
            evaluation = self._run_base_metrics(dataset, base_metrics)
            scores_by_case = {
                result.test_case_id: {metric.name: metric.score for metric in result.metrics}
                for result in evaluation.results
            }
            for result in evaluation.results:
                mapping = next((m for m in mappings if m.test_case_id == result.test_case_id), None)
                if not mapping:
                    continue
                turn_results.append(
                    MultiTurnTurnResult(
                        conversation_id=conversation.conversation_id,
                        turn_id=mapping.turn.turn_id,
                        turn_index=mapping.turn_index,
                        role=mapping.turn.role,
                        metrics=scores_by_case.get(result.test_case_id, {}),
                        passed=result.all_passed,
                        latency_ms=result.latency_ms,
                        metadata=dict(metadata_by_case.get(result.test_case_id, {})),
                    )
                )
        else:
            for mapping in mappings:
                turn_results.append(
                    MultiTurnTurnResult(
                        conversation_id=conversation.conversation_id,
                        turn_id=mapping.turn.turn_id,
                        turn_index=mapping.turn_index,
                        role=mapping.turn.role,
                        metrics={},
                        passed=False,
                        latency_ms=None,
                        metadata=dict(metadata_by_case.get(mapping.test_case_id, {})),
                    )
                )

        summary: dict[str, object] = {}
        if "turn_faithfulness" in metrics:
            summary["turn_faithfulness"] = calculate_turn_faithfulness(turn_results)
        if "context_coherence" in metrics:
            summary["context_coherence"] = calculate_context_coherence(conversation.turns)
        if "drift_rate" in metrics:
            summary["drift_rate"] = calculate_drift_rate(conversation.turns)
        if "turn_latency" in metrics:
            summary["turn_latency"] = calculate_turn_latency_p95(
                [result.latency_ms for result in turn_results]
            )

        summary["turn_count"] = len(turn_results)
        summary["conversation_id"] = conversation.conversation_id

        return MultiTurnEvaluationResult(
            conversation_id=conversation.conversation_id,
            turn_results=turn_results,
            summary=summary,
        )

    def detect_drift(
        self,
        conversation: MultiTurnTestCase,
        threshold: float = 0.1,
    ) -> DriftAnalysis:
        drift_score = calculate_drift_rate(conversation.turns)
        return DriftAnalysis(
            conversation_id=conversation.conversation_id,
            drift_score=drift_score,
            drift_threshold=threshold,
            drift_detected=drift_score >= threshold,
            notes=[],
        )

    def _run_base_metrics(self, dataset: Dataset, metrics: list[str]):
        return asyncio.run(
            self._evaluator.evaluate(
                dataset=dataset,
                metrics=metrics,
                llm=self._llm,
            )
        )

    def _is_base_metric(self, metric: str) -> bool:
        if metric in self.MULTITURN_METRICS:
            return False
        if metric in RagasEvaluator.METRIC_MAP:
            return True
        return metric in RagasEvaluator.CUSTOM_METRIC_MAP

    @staticmethod
    def _build_turn_dataset(conversation: MultiTurnTestCase) -> tuple[Dataset, list[_TurnMapping]]:
        test_cases: list[TestCase] = []
        mappings: list[_TurnMapping] = []
        last_user_content: str | None = None

        for index, turn in enumerate(conversation.turns, start=1):
            if turn.role == "user":
                last_user_content = turn.content
                continue
            question = last_user_content or ""
            test_case_id = f"{conversation.conversation_id}:{index}:{turn.turn_id}"
            test_case = TestCase(
                id=test_case_id,
                question=question,
                answer=turn.content,
                contexts=turn.contexts or [],
                ground_truth=turn.ground_truth,
                metadata={
                    "conversation_id": conversation.conversation_id,
                    "turn_index": index,
                    "turn_id": turn.turn_id,
                    "role": turn.role,
                },
            )
            test_cases.append(test_case)
            mappings.append(_TurnMapping(test_case_id=test_case_id, turn=turn, turn_index=index))

        dataset = Dataset(
            name=f"multiturn:{conversation.conversation_id}",
            version="1.0.0",
            test_cases=test_cases,
            metadata={"conversation_id": conversation.conversation_id},
        )
        return dataset, mappings
