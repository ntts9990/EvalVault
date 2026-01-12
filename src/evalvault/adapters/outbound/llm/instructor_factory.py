from __future__ import annotations

import asyncio
from typing import Any

import instructor

try:
    from ragas.llms.base import InstructorLLM as RagasInstructorLLM
except ImportError:
    RagasInstructorLLM = None

from ragas.llms.base import BaseRagasLLM, Generation, LLMResult


class _ClientRagasLLM(BaseRagasLLM):
    def __init__(self, client: Any, model: str, provider: str, model_args: dict[str, Any]):
        super().__init__()
        self._client = client
        self._model = model
        self._provider = provider
        self._model_args = model_args

    def generate_text(
        self,
        prompt: Any,
        n: int = 1,
        temperature: float | None = None,
        stop: list[str] | None = None,
        callbacks: Any = None,
    ) -> LLMResult:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            raise RuntimeError(
                "Sync ragas LLM call inside running event loop is not supported. "
                "Use agenerate_text() instead."
            )

        return asyncio.run(
            self.agenerate_text(
                prompt, n=n, temperature=temperature, stop=stop, callbacks=callbacks
            )
        )

    async def agenerate_text(
        self,
        prompt: Any,
        n: int = 1,
        temperature: float | None = None,
        stop: list[str] | None = None,
        callbacks: Any = None,
    ) -> LLMResult:
        prompt_text = prompt.to_string() if hasattr(prompt, "to_string") else str(prompt)

        if self._provider in {"openai", "azure", "ollama", "vllm", "litellm"}:
            kwargs: dict[str, Any] = dict(self._model_args)
            kwargs.setdefault("model", self._model)
            kwargs["messages"] = [{"role": "user", "content": prompt_text}]
            kwargs["n"] = max(1, n)
            if temperature is not None:
                kwargs["temperature"] = temperature
            if stop is not None:
                kwargs["stop"] = stop

            response = await self._client.chat.completions.create(**kwargs)
            generations = [
                Generation(
                    text=(choice.message.content or ""),
                    generation_info={"finish_reason": getattr(choice, "finish_reason", None)},
                )
                for choice in response.choices
            ]
            return LLMResult(generations=[generations])

        if self._provider == "anthropic":
            kwargs = dict(self._model_args)
            model = str(kwargs.pop("model", self._model))
            kwargs.setdefault("max_tokens", 8192)
            if temperature is not None:
                kwargs["temperature"] = temperature
            response = await self._client.messages.create(
                model=model,
                messages=[{"role": "user", "content": prompt_text}],
                **kwargs,
            )
            text = "".join(getattr(block, "text", "") for block in response.content)
            return LLMResult(generations=[[Generation(text=text)]])

        raise ValueError(
            f"Unsupported instructor provider '{self._provider}'. "
            "Supported providers: openai, anthropic, litellm."
        )


def create_instructor_llm(
    provider: str,
    model: str,
    client: Any,
    mode: instructor.Mode | None = None,
    **model_args: Any,
) -> Any:
    provider_name = provider.lower()

    if provider_name in {"openai", "azure", "ollama", "vllm"}:
        resolved_mode = mode or (
            instructor.Mode.JSON if provider_name in {"ollama", "vllm"} else instructor.Mode.TOOLS
        )
        patched_client = instructor.from_openai(client, mode=resolved_mode)
        provider_id = "openai"
    elif provider_name == "anthropic":
        patched_client = instructor.from_anthropic(client)
        provider_id = "anthropic"
    elif provider_name == "litellm":
        patched_client = instructor.from_litellm(client)
        provider_id = "litellm"
    else:
        raise ValueError(
            f"Unsupported instructor provider '{provider}'. "
            "Supported providers: openai, anthropic, litellm."
        )

    if RagasInstructorLLM is not None:
        return RagasInstructorLLM(
            client=patched_client, model=model, provider=provider_id, **model_args
        )

    return _ClientRagasLLM(
        client=patched_client, model=model, provider=provider_id, model_args=model_args
    )
