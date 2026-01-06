"""Example EvalVault method plugin implementation."""

from __future__ import annotations

from collections.abc import Sequence

from evalvault.domain.entities.method import MethodInput, MethodOutput
from evalvault.ports.outbound.method_port import MethodRuntime, RagMethodPort


class TemplateMethod(RagMethodPort):
    """Minimal example that echoes the question."""

    name = "template_method"
    version = "0.1.0"
    description = "Echo question as answer (example only)."
    tags = ("template", "example")

    def run(
        self,
        inputs: Sequence[MethodInput],
        *,
        runtime: MethodRuntime,
        config: dict | None = None,
    ) -> Sequence[MethodOutput]:
        outputs: list[MethodOutput] = []
        for case in inputs:
            outputs.append(
                MethodOutput(
                    id=case.id,
                    answer=case.question,
                    contexts=case.contexts,
                    metadata={"method": self.name},
                )
            )
        return outputs
