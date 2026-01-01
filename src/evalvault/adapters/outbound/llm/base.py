"""Shared helpers for LLM adapters."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from evalvault.ports.outbound.llm_port import LLMPort, ThinkingConfig


@dataclass
class TokenUsage:
    """Thread-safe token usage tracker shared by adapters."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, prompt: int, completion: int, total: int | None = None) -> None:
        """Add token counts (thread-safe)."""
        with self._lock:
            self.prompt_tokens += prompt
            self.completion_tokens += completion
            self.total_tokens += total if total is not None else prompt + completion

    def reset(self) -> None:
        """Reset all counters."""
        with self._lock:
            self.prompt_tokens = 0
            self.completion_tokens = 0
            self.total_tokens = 0

    def get_and_reset(self) -> tuple[int, int, int]:
        """Get current counts and reset (atomic operation)."""
        with self._lock:
            result = (self.prompt_tokens, self.completion_tokens, self.total_tokens)
            self.prompt_tokens = 0
            self.completion_tokens = 0
            self.total_tokens = 0
            return result


class BaseLLMAdapter(LLMPort):
    """Common functionality for LLM adapters."""

    def __init__(
        self,
        *,
        model_name: str,
        thinking_config: ThinkingConfig | None = None,
    ):
        self._model_name = model_name
        self._ragas_llm: Any | None = None
        self._ragas_embeddings: Any | None = None
        self._token_usage = TokenUsage()
        self._thinking_config = thinking_config or ThinkingConfig(enabled=False)

    # -- Helpers for subclasses -------------------------------------------------
    def _set_ragas_llm(self, llm: Any) -> None:
        self._ragas_llm = llm

    def _set_ragas_embeddings(self, embeddings: Any) -> None:
        self._ragas_embeddings = embeddings

    def _set_thinking_config(self, config: ThinkingConfig) -> None:
        self._thinking_config = config

    def _record_token_usage(self, prompt: int, completion: int, total: int | None = None) -> None:
        self._token_usage.add(prompt, completion, total)

    # -- LLMPort implementations ------------------------------------------------
    def get_model_name(self) -> str:
        return self._model_name

    def as_ragas_llm(self):
        if self._ragas_llm is None:
            raise ValueError("LLM not initialized. Call _set_ragas_llm() in the adapter.")
        return self._ragas_llm

    def as_ragas_embeddings(self):
        if self._ragas_embeddings is None:
            raise ValueError("Embeddings not configured for this adapter.")
        return self._ragas_embeddings

    def get_thinking_config(self) -> ThinkingConfig:
        return self._thinking_config

    def get_token_usage(self) -> tuple[int, int, int]:
        return (
            self._token_usage.prompt_tokens,
            self._token_usage.completion_tokens,
            self._token_usage.total_tokens,
        )

    def get_and_reset_token_usage(self) -> tuple[int, int, int]:
        return self._token_usage.get_and_reset()

    def reset_token_usage(self) -> None:
        self._token_usage.reset()
