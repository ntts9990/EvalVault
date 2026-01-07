"""Method plugin entities for the evaluation testbed."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MethodInput:
    """Single input case for a method plugin."""

    __test__ = False

    id: str
    question: str
    ground_truth: str | None = None
    contexts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MethodOutput:
    """Method output for a single test case."""

    __test__ = False

    id: str
    answer: str
    contexts: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    retrieval_metadata: dict[str, Any] | None = None


@dataclass
class MethodInputDataset:
    """Dataset container for method inputs (question-first format)."""

    __test__ = False

    name: str
    version: str
    test_cases: list[MethodInput]
    metadata: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, float] = field(default_factory=dict)
    source_file: str | None = None

    def __len__(self) -> int:
        return len(self.test_cases)

    def __iter__(self):
        return iter(self.test_cases)
