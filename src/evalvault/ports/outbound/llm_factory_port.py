from __future__ import annotations

from typing import Protocol

from evalvault.ports.outbound.llm_port import LLMPort


class LLMFactoryPort(Protocol):
    def create_faithfulness_fallback(
        self,
        active_provider: str | None,
        active_model: str | None,
    ) -> LLMPort | None: ...
