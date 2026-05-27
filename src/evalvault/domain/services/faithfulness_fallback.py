"""Faithfulness fallback scoring helper for :class:`RagasEvaluator`.

This module hosts the secondary-LLM faithfulness evaluation path that
previously lived inline on ``RagasEvaluator``. The extraction is a pure
relocation (D-S5b): behaviour, log messages, exception handling, and the
public surface of :class:`RagasEvaluator` remain byte-identical.

The fallback is invoked when the primary Ragas judge returns ``None``/NaN
or otherwise fails to produce a numeric verdict. A dedicated fallback LLM
(supplied by :class:`LLMFactoryPort.create_faithfulness_fallback`) is used
to re-score with the standard Ragas faithfulness metric. If even that
fails, control returns to the Korean NLP fallback that the evaluator
already owns.

Fallback verdicts are T2 (evaluation gate) just like the primary path —
this module never derives promote/rollback semantics.

Note: no LLM-facing prompt strings live in or move through this module.
The Ragas metric class itself owns its prompts; we only swap the LLM
backing it. The "prompt discipline" requirement (memory
``feedback_llm_prompt_discipline.md``) is therefore trivially preserved.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable
from typing import Any

from ragas import SingleTurnSample

from evalvault.ports.outbound.llm_factory_port import LLMFactoryPort
from evalvault.ports.outbound.llm_port import LLMPort

logger = logging.getLogger(__name__)


class FaithfulnessFallback:
    """Encapsulates the faithfulness fallback LLM/metric lifecycle.

    State (cached LLM, cached metric, failure/log flags) is owned by this
    helper so :class:`RagasEvaluator` no longer has to track it inline.
    All public-method behaviour mirrors the original evaluator methods.
    """

    def __init__(
        self,
        *,
        llm_factory: LLMFactoryPort | None,
        metric_map: dict[str, Any],
        metric_args: dict[str, list[str]],
        summarize_error: Callable[[Exception], str],
        korean_fallback: Callable[[SingleTurnSample], float | None],
    ) -> None:
        self._llm_factory = llm_factory
        self._metric_map = metric_map
        self._metric_args = metric_args
        self._summarize_error = summarize_error
        self._korean_fallback = korean_fallback
        self._fallback_llm: LLMPort | None = None
        self._fallback_metric: Any = None
        self._failed = False
        self._logged = False

    @property
    def failed(self) -> bool:
        return self._failed

    async def score(
        self,
        sample: SingleTurnSample,
        provider: str | None,
        model: str | None,
    ) -> float | None:
        metric = self._get_metric(provider, model)
        if metric is None:
            return self._korean_fallback(sample)

        try:
            if hasattr(metric, "ascore"):
                all_args = {
                    "user_input": sample.user_input,
                    "response": sample.response,
                    "retrieved_contexts": sample.retrieved_contexts,
                    "reference": sample.reference,
                }
                required_args = self._metric_args.get(
                    metric.name,
                    ["user_input", "response", "retrieved_contexts"],
                )
                kwargs = {k: v for k, v in all_args.items() if k in required_args and v is not None}
                result = await metric.ascore(**kwargs)
            elif hasattr(metric, "single_turn_ascore"):
                result = await metric.single_turn_ascore(sample)
            else:
                raise AttributeError(f"{metric.__class__.__name__} does not support scoring API.")

            if hasattr(result, "value"):
                score_value = result.value
            elif hasattr(result, "score"):
                score_value = result.score
            else:
                score_value = result

            if score_value is None:
                raise ValueError("Metric returned None")
            score_value = float(score_value)
            if math.isnan(score_value):
                raise ValueError("Metric returned NaN")
            return score_value
        except Exception as exc:
            if not self._failed:
                logger.warning(
                    "Faithfulness fallback LLM failed (%s). Using Korean fallback.",
                    self._summarize_error(exc),
                )
                self._failed = True
            return self._korean_fallback(sample)

    def _get_metric(self, provider: str | None, model: str | None) -> Any:
        if self._failed:
            return None
        if self._fallback_metric is not None:
            return self._fallback_metric

        llm = self._get_llm(provider, model)
        if llm is None:
            return None

        metric_class = self._metric_map.get("faithfulness")
        if not metric_class:
            return None
        try:
            self._fallback_metric = metric_class(llm=llm.as_ragas_llm())
            return self._fallback_metric
        except Exception as exc:
            if not self._failed:
                logger.warning(
                    "Faithfulness fallback metric init failed (%s).",
                    self._summarize_error(exc),
                )
                self._failed = True
            return None

    def _get_llm(self, provider: str | None, model: str | None) -> LLMPort | None:
        if self._failed:
            return None
        if self._fallback_llm is not None:
            return self._fallback_llm
        if self._llm_factory is None:
            return None

        try:
            llm = self._llm_factory.create_faithfulness_fallback(provider, model)
        except Exception as exc:
            if not self._failed:
                logger.warning(
                    "Faithfulness fallback LLM init failed (%s).",
                    self._summarize_error(exc),
                )
                self._failed = True
            return None

        if llm is None:
            return None

        self._fallback_llm = llm
        if not self._logged:
            provider_name = getattr(llm, "provider_name", None)
            model_name = llm.get_model_name()
            logger.warning(
                "Faithfulness fallback LLM enabled: %s/%s",
                provider_name,
                model_name,
            )
            self._logged = True
        return llm


__all__ = ["FaithfulnessFallback"]
