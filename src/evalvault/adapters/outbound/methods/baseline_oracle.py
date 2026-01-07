"""Baseline method plugin that uses ground truth as the answer."""

from __future__ import annotations

from collections.abc import Sequence

from evalvault.domain.entities.method import MethodInput, MethodOutput
from evalvault.ports.outbound.method_port import MethodRuntime, RagMethodPort


class BaselineOracleMethod(RagMethodPort):
    """Return ground-truth answers as a sanity-check baseline."""

    name = "baseline_oracle"
    version = "0.1.0"
    description = "Use ground truth as the answer when available."
    tags = ("baseline", "oracle")

    def run(
        self,
        inputs: Sequence[MethodInput],
        *,
        runtime: MethodRuntime,
        config: dict | None = None,
    ) -> Sequence[MethodOutput]:
        outputs: list[MethodOutput] = []
        for case in inputs:
            answer = case.ground_truth or ""
            metadata = dict(case.metadata)
            metadata.setdefault("method", self.name)
            if not case.ground_truth:
                metadata["oracle_missing_ground_truth"] = True
            outputs.append(
                MethodOutput(
                    id=case.id,
                    answer=answer,
                    contexts=case.contexts,
                    metadata=metadata,
                )
            )
        return outputs
