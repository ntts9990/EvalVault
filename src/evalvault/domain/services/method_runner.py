"""Service for running method plugins against base datasets."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from evalvault.domain.entities import Dataset, TestCase
from evalvault.domain.entities.method import MethodInputDataset, MethodOutput
from evalvault.ports.outbound.method_port import MethodRuntime, RagMethodPort


@dataclass
class MethodRunResult:
    """Result of executing a method plugin."""

    dataset: Dataset
    retrieval_metadata: dict[str, dict[str, Any]]
    method_metadata: dict[str, Any]
    outputs: list[MethodOutput]


class MethodRunnerService:
    """Run a method plugin and build an evaluation-ready Dataset."""

    async def run(
        self,
        *,
        method: RagMethodPort,
        input_dataset: MethodInputDataset,
        runtime: MethodRuntime,
        config: dict[str, Any] | None = None,
    ) -> MethodRunResult:
        outputs = method.run(input_dataset.test_cases, runtime=runtime, config=config)
        if inspect.isawaitable(outputs):
            outputs = await outputs

        outputs_list = list(outputs)
        output_map: dict[str, MethodOutput] = {}
        for output in outputs_list:
            output_map[output.id] = output

        test_cases: list[TestCase] = []
        retrieval_metadata: dict[str, dict[str, Any]] = {}

        for case in input_dataset.test_cases:
            output = output_map.get(case.id)
            if output is None:
                metadata = dict(case.metadata)
                metadata["method_missing_output"] = True
                test_cases.append(
                    TestCase(
                        id=case.id,
                        question=case.question,
                        answer="",
                        contexts=case.contexts,
                        ground_truth=case.ground_truth,
                        metadata=metadata,
                    )
                )
                continue

            metadata = dict(case.metadata)
            metadata.update(output.metadata or {})

            test_cases.append(
                TestCase(
                    id=case.id,
                    question=case.question,
                    answer=output.answer,
                    contexts=output.contexts,
                    ground_truth=case.ground_truth,
                    metadata=metadata,
                )
            )
            if output.retrieval_metadata:
                retrieval_metadata[case.id] = output.retrieval_metadata

        method_metadata = {
            "name": method.name,
            "version": getattr(method, "version", None),
            "run_id": runtime.run_id,
            "source": runtime.metadata.get("source") if runtime.metadata else None,
            "config": config or {},
        }
        runtime_metadata = dict(runtime.metadata or {})
        if runtime_metadata:
            method_metadata["runtime"] = runtime_metadata

        dataset_metadata = dict(input_dataset.metadata)
        dataset_metadata["method"] = method_metadata

        dataset = Dataset(
            name=input_dataset.name,
            version=input_dataset.version,
            test_cases=test_cases,
            metadata=dataset_metadata,
            source_file=input_dataset.source_file,
            thresholds=input_dataset.thresholds,
        )

        return MethodRunResult(
            dataset=dataset,
            retrieval_metadata=retrieval_metadata,
            method_metadata=method_metadata,
            outputs=outputs_list,
        )
