"""Port for RAG method plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from evalvault.config.settings import Settings
from evalvault.domain.entities.method import MethodInput, MethodOutput
from evalvault.ports.outbound.llm_port import LLMPort


@dataclass
class MethodRuntime:
    """Runtime context shared with method plugins."""

    run_id: str
    settings: Settings
    documents: Sequence[str] | None = None
    document_ids: Sequence[str] | None = None
    input_path: str | None = None
    docs_path: str | None = None
    output_path: str | None = None
    config_path: str | None = None
    artifacts_dir: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    llm: LLMPort | None = None


class RagMethodPort(ABC):
    """Outbound port for method plugins that generate RAG answers."""

    name: str = "unknown"
    version: str = "0.1.0"
    description: str = ""
    tags: Sequence[str] = ()

    @abstractmethod
    def run(
        self,
        inputs: Sequence[MethodInput],
        *,
        runtime: MethodRuntime,
        config: dict[str, Any] | None = None,
    ) -> Sequence[MethodOutput]:
        """Run the method for each input and return outputs."""
        raise NotImplementedError
