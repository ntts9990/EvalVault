"""Tests for method plugin utilities."""

from __future__ import annotations

import asyncio
import json

import pytest

from evalvault.adapters.outbound.dataset.method_input_loader import MethodInputDatasetLoader
from evalvault.adapters.outbound.methods.registry import MethodRegistry
from evalvault.config.settings import Settings
from evalvault.domain.entities.method import MethodInput, MethodInputDataset, MethodOutput
from evalvault.domain.services.method_runner import MethodRunnerService
from evalvault.ports.outbound.method_port import MethodRuntime, RagMethodPort


class DummyMethod(RagMethodPort):
    """Dummy method for testing the runner."""

    name = "dummy_method"
    version = "0.0.1"

    def run(
        self,
        inputs: list[MethodInput],
        *,
        runtime: MethodRuntime,
        config: dict | None = None,
    ) -> list[MethodOutput]:
        outputs: list[MethodOutput] = []
        for case in inputs:
            if case.id != "tc-001":
                continue
            outputs.append(
                MethodOutput(
                    id=case.id,
                    answer="dummy-answer",
                    contexts=["dummy-context"],
                    metadata={"method": self.name},
                    retrieval_metadata={"retriever": "dummy"},
                )
            )
        return outputs


def test_method_input_loader_parses_contexts_and_thresholds(tmp_path):
    payload = {
        "name": "method-input",
        "version": "1.2.3",
        "thresholds": {
            "faithfulness": 0.7,
        },
        "test_cases": [
            {
                "id": "tc-001",
                "question": "Q1",
                "contexts": "ctx-a|ctx-b",
                "ground_truth": "A1",
                "metadata": {"source": "test"},
            },
            {
                "id": "tc-002",
                "question": "Q2",
                "contexts": ["ctx-c"],
            },
        ],
    }
    path = tmp_path / "method_input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    loader = MethodInputDatasetLoader()
    dataset = loader.load(path)

    assert dataset.name == "method-input"
    assert dataset.version == "1.2.3"
    assert dataset.thresholds["faithfulness"] == pytest.approx(0.7)
    assert dataset.test_cases[0].contexts == ["ctx-a", "ctx-b"]
    assert dataset.test_cases[1].contexts == ["ctx-c"]


def test_method_input_loader_rejects_invalid_threshold(tmp_path):
    payload = {
        "test_cases": [{"id": "tc-001", "question": "Q1"}],
        "thresholds": {"faithfulness": "high"},
    }
    path = tmp_path / "invalid_threshold.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    loader = MethodInputDatasetLoader()
    with pytest.raises(ValueError, match="Invalid threshold value"):
        loader.load(path)


def test_method_registry_loads_internal_config(tmp_path):
    config_path = tmp_path / "methods.yaml"
    config_path.write_text(
        "\n".join(
            [
                "methods:",
                "  baseline_oracle:",
                "    class_path: "
                '"evalvault.adapters.outbound.methods.baseline_oracle:BaselineOracleMethod"',
                '    description: "Use ground truth as the answer when available."',
                "    tags: [baseline, oracle]",
            ]
        ),
        encoding="utf-8",
    )

    registry = MethodRegistry(config_path=config_path)
    spec = registry.get_spec("baseline_oracle")

    assert spec.source == "internal"
    assert spec.name == "baseline_oracle"
    assert spec.error is None

    method = registry.get_method("baseline_oracle")
    assert method.name == "baseline_oracle"


def test_method_runner_builds_dataset_and_metadata():
    input_dataset = MethodInputDataset(
        name="method-input",
        version="1.0.0",
        test_cases=[
            MethodInput(
                id="tc-001",
                question="Q1",
                ground_truth="A1",
                contexts=["ctx-1"],
                metadata={"trace": "alpha"},
            ),
            MethodInput(
                id="tc-002",
                question="Q2",
                ground_truth="A2",
                contexts=["ctx-2"],
            ),
        ],
        metadata={"source": "fixture"},
    )
    runtime = MethodRuntime(
        run_id="run-123",
        settings=Settings(),
        metadata={"source": "test"},
    )

    result = asyncio.run(
        MethodRunnerService().run(
            method=DummyMethod(),
            input_dataset=input_dataset,
            runtime=runtime,
        )
    )

    assert result.dataset.name == "method-input"
    assert result.dataset.metadata["method"]["name"] == "dummy_method"
    assert result.retrieval_metadata["tc-001"]["retriever"] == "dummy"

    first_case = result.dataset.test_cases[0]
    assert first_case.answer == "dummy-answer"
    assert first_case.metadata["trace"] == "alpha"
    assert first_case.metadata["method"] == "dummy_method"

    second_case = result.dataset.test_cases[1]
    assert second_case.answer == ""
    assert second_case.metadata["method_missing_output"] is True
