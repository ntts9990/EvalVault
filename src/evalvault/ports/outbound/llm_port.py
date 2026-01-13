"""LLM adapter port for Ragas evaluation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ThinkingConfig:
    """Configuration for reasoning/thinking models.

    Unified interface for reasoning capabilities across different providers:
    - Anthropic: Extended thinking with budget_tokens
    - Ollama: Thinking with think_level (low, medium, high)
    """

    enabled: bool = False
    budget_tokens: int | None = None  # Anthropic: max tokens for thinking
    think_level: str | None = None  # Ollama: thinking level (low, medium, high)

    def to_anthropic_param(self) -> dict[str, Any] | None:
        """Convert to Anthropic API thinking parameter."""
        if not self.enabled:
            return None
        return {
            "type": "enabled",
            "budget_tokens": self.budget_tokens or 10000,
        }

    def to_ollama_options(self) -> dict[str, Any] | None:
        """Convert to Ollama options parameter."""
        if not self.enabled or not self.think_level:
            return None
        return {"think_level": self.think_level}


@dataclass
class GenerationOptions:
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    n: int | None = None
    seed: int | None = None


class LLMPort(ABC):
    """LLM adapter interface for Ragas metrics evaluation.

    This port provides the necessary abstraction for LLM calls
    that will be used by Ragas metrics.
    """

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name being used.

        Returns:
            Model identifier (e.g., 'gpt-5-mini')
        """
        pass

    @abstractmethod
    def as_ragas_llm(self) -> Any:
        """Return the LLM instance compatible with Ragas.

        Ragas expects langchain LLM instances. This method should
        return the appropriate LangChain LLM wrapper.

        Returns:
            LangChain-compatible LLM instance for Ragas
        """
        pass

    def as_ragas_embeddings(self) -> Any:
        raise NotImplementedError("as_ragas_embeddings not implemented")

    def get_token_usage(self) -> tuple[int, int, int]:
        raise NotImplementedError("get_token_usage not implemented")

    def get_and_reset_token_usage(self) -> tuple[int, int, int]:
        raise NotImplementedError("get_and_reset_token_usage not implemented")

    def reset_token_usage(self) -> None:
        raise NotImplementedError("reset_token_usage not implemented")

    def get_thinking_config(self) -> ThinkingConfig:
        """Get thinking/reasoning configuration for this adapter.

        Override in adapters that support reasoning models.
        Default implementation returns disabled config.

        Returns:
            ThinkingConfig with provider-specific settings
        """
        return ThinkingConfig(enabled=False)

    def supports_thinking(self) -> bool:
        """Check if this adapter supports thinking/reasoning mode.

        Returns:
            True if thinking mode is available and enabled
        """
        return self.get_thinking_config().enabled

    async def agenerate_text(
        self,
        prompt: str,
        *,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate text from a prompt (async).

        Simple text generation for use cases like report generation,
        not for Ragas evaluation.

        Args:
            prompt: The prompt to generate text from

        Returns:
            Generated text string

        Raises:
            NotImplementedError: If not implemented by adapter
        """
        raise NotImplementedError("agenerate_text not implemented")

    def generate_text(
        self,
        prompt: str,
        *,
        json_mode: bool = False,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate text from a prompt (sync).

        Simple text generation for use cases like report generation,
        not for Ragas evaluation.

        Args:
            prompt: The prompt to generate text from
            json_mode: If True, force JSON response format

        Returns:
            Generated text string

        Raises:
            NotImplementedError: If not implemented by adapter
        """
        raise NotImplementedError("generate_text not implemented")
