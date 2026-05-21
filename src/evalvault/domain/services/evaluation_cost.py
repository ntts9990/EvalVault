"""Cost calculation helpers for :class:`RagasEvaluator`.

This module hosts the model pricing table and the cost computation routine
that previously lived inline on ``RagasEvaluator``. The extraction is a pure
relocation (D-S5a): behavior, defaults, and floating-point arithmetic remain
byte-identical to the original implementation.

Cost is metadata only — it never participates in pass/fail verdicts (T2
discipline). Callers are expected to display or persist the returned USD
value; no decisions are derived here.
"""

from __future__ import annotations

# Estimated pricing (USD per 1M tokens) as of Jan 2025
# Format: (input_price, output_price)
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "gpt-5-nano": (5.00, 15.00),  # Hypothetical project model
    "openai/gpt-5-nano": (5.00, 15.00),
}


def calculate_cost(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    *,
    pricing: dict[str, tuple[float, float]] | None = None,
) -> float:
    """Calculate estimated cost in USD based on model pricing.

    Parameters
    ----------
    model_name:
        Identifier of the LLM used (e.g. ``"gpt-4o"`` or ``"openai/gpt-4o"``).
        Ollama models always return ``0.0``.
    prompt_tokens, completion_tokens:
        Token counts for the call being priced.
    pricing:
        Optional pricing table override. When ``None``, the module-level
        :data:`MODEL_PRICING` is used. ``RagasEvaluator`` forwards
        ``self.MODEL_PRICING`` so that subclasses can supply a custom table
        with the same semantics as before extraction.
    """
    if "ollama" in model_name:
        return 0.0
    table = pricing if pricing is not None else MODEL_PRICING
    # Find matching model key (exact or substring match)
    price_key = "openai/gpt-4o"  # Default fallback
    for key in table:
        if key in model_name or model_name in key:
            price_key = key
            break

    input_price, output_price = table.get(price_key, (0.0, 0.0))

    cost = (prompt_tokens / 1_000_000 * input_price) + (
        completion_tokens / 1_000_000 * output_price
    )
    return cost
