"""Ollama LLM adapter for air-gapped (폐쇄망) environments.

Ollama의 OpenAI 호환 API를 사용하여 Ragas와 통합합니다.
기존 OpenAIAdapter 코드를 최대한 재사용합니다.

지원 모델:
  - 평가 LLM: gemma3:1b (개발), gpt-oss-safeguard:20b (운영)
  - 임베딩: qwen3-embedding:0.6b (개발), qwen3-embedding:8b (운영)
"""

from typing import Any

import httpx
import instructor
from openai import AsyncOpenAI
from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings

from evalvault.adapters.outbound.llm.base import BaseLLMAdapter
from evalvault.adapters.outbound.llm.instructor_factory import create_instructor_llm
from evalvault.adapters.outbound.llm.token_aware_chat import ThinkingTokenTrackingAsyncOpenAI
from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import GenerationOptions, ThinkingConfig


class OllamaAdapter(BaseLLMAdapter):
    """Ollama LLM adapter using OpenAI-compatible API.

    폐쇄망 환경에서 로컬 Ollama 서버를 사용한 RAG 평가를 지원합니다.
    Ragas와의 호환성을 위해 OpenAI 호환 API를 사용합니다.

    Attributes:
        _ollama_model: 평가에 사용하는 LLM 모델명
        _embedding_model_name: 임베딩에 사용하는 모델명
        _base_url: Ollama 서버 URL
    """

    provider_name = "ollama"

    def __init__(self, settings: Settings):
        """Initialize Ollama adapter.

        Args:
            settings: Application settings containing Ollama configuration
        """
        self._settings = settings
        self._ollama_model = settings.ollama_model
        self._embedding_model_name = settings.ollama_embedding_model
        base_url = settings.ollama_base_url
        if not isinstance(base_url, str) or not base_url.strip():
            base_url = "http://localhost:11434"
        else:
            base_url = base_url.strip()
            if "://" not in base_url:
                base_url = f"http://{base_url}"
        self._base_url = base_url
        self._timeout = settings.ollama_timeout
        self._think_level = settings.ollama_think_level
        thinking_config = ThinkingConfig(
            enabled=settings.ollama_think_level is not None,
            think_level=settings.ollama_think_level,
        )
        super().__init__(
            model_name=f"ollama/{self._ollama_model}",
            thinking_config=thinking_config,
        )

        chat_kwargs: dict[str, Any] = {
            "api_key": "ollama",
            "base_url": f"{self._base_url}/v1",
        }

        ragas_client = ThinkingTokenTrackingAsyncOpenAI(
            usage_tracker=self._token_usage,
            think_level=self._think_level,
            provider_name="ollama",
            **chat_kwargs,
        )

        mode = instructor.Mode.TOOLS if self._supports_tools(settings) else instructor.Mode.JSON
        ragas_llm = create_instructor_llm(
            "ollama",
            self._ollama_model,
            ragas_client,
            mode=mode,
        )
        self._set_ragas_llm(ragas_llm)

        # Create separate client for embeddings (non-tracking)
        self._embedding_client = AsyncOpenAI(
            api_key="ollama",
            base_url=f"{self._base_url}/v1",
            http_client=httpx.AsyncClient(timeout=httpx.Timeout(self._timeout, connect=30.0)),
        )

        # Create Ragas embeddings using OpenAI-compatible API
        embeddings = RagasOpenAIEmbeddings(
            model=self._embedding_model_name,
            client=self._embedding_client,
        )
        self._set_ragas_embeddings(embeddings)

    def get_embedding_model_name(self) -> str:
        """Get the embedding model name being used.

        Returns:
            Embedding model identifier (e.g., 'qwen3-embedding:0.6b')
        """
        return self._embedding_model_name

    def _supports_tools(self, settings: Settings) -> bool:
        raw = settings.ollama_tool_models or ""
        allowlist = {item.strip().lower() for item in raw.split(",") if item.strip()}
        if not allowlist:
            return False
        model = self._ollama_model.lower()
        return any(model == entry or model.startswith(f"{entry}:") for entry in allowlist)

    def get_base_url(self) -> str:
        """Get the Ollama server URL.

        Returns:
            Ollama server base URL
        """
        return self._base_url

    def get_think_level(self) -> str | None:
        """Get the thinking level for models that support it.

        Returns:
            Thinking level (e.g., 'medium') or None
        """
        return self._think_level

    def get_thinking_config(self) -> ThinkingConfig:
        """Get thinking/reasoning configuration for this adapter.

        Returns:
            ThinkingConfig with Ollama thinking settings
        """
        return ThinkingConfig(
            enabled=self._think_level is not None,
            budget_tokens=None,  # Not used for Ollama
            think_level=self._think_level,
        )

    async def embed(
        self,
        texts: str | list[str],
        model: str | None = None,
        dimension: int | None = None,
    ) -> list[float] | list[list[float]]:
        """Generate embeddings using Ollama embed API with Matryoshka support.

        Qwen3-Embedding 모델은 Matryoshka Representation Learning을 지원하여
        가변 차원 임베딩을 생성할 수 있습니다.

        Args:
            texts: Single text or list of texts to embed
            model: Embedding model name (default: configured model)
            dimension: Matryoshka dimension for Qwen3-Embedding
                      - 0.6B model: 32~768 (recommended: 256 for dev)
                      - 8B model: 32~4096 (recommended: 1024 for prod)

        Returns:
            Single embedding if single text input, list of embeddings otherwise

        Example:
            >>> adapter = OllamaAdapter(settings)
            >>> # Single text
            >>> embedding = await adapter.embed("보험료 납입", dimension=256)
            >>> # Multiple texts
            >>> embeddings = await adapter.embed(["보험료", "보장금액"], dimension=256)
        """
        model = model or self._embedding_model_name
        is_single = isinstance(texts, str)
        text_list = [texts] if is_single else list(texts)

        embeddings: list[list[float]] = []
        batch_size = 64
        async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout, connect=30.0)) as client:
            for start in range(0, len(text_list), batch_size):
                batch = text_list[start : start + batch_size]
                response = await client.post(
                    f"{self._base_url}/v1/embeddings",
                    json={"model": model, "input": batch},
                    headers={"Authorization": "Bearer ollama"},
                )
                response.raise_for_status()
                payload = response.json()
                items = payload.get("data", []) if isinstance(payload, dict) else []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    embedding = item.get("embedding")
                    if not isinstance(embedding, list):
                        raise ValueError("Invalid embedding response from Ollama")
                    if dimension is not None and len(embedding) > dimension:
                        embedding = embedding[:dimension]
                    embeddings.append(embedding)

        return embeddings[0] if is_single else embeddings

    def embed_sync(
        self,
        texts: str | list[str],
        model: str | None = None,
        dimension: int | None = None,
    ) -> list[float] | list[list[float]]:
        """Synchronous version of embed() for non-async contexts.

        Args:
            texts: Single text or list of texts to embed
            model: Embedding model name (default: configured model)
            dimension: Matryoshka dimension for Qwen3-Embedding

        Returns:
            Single embedding if single text input, list of embeddings otherwise
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already in async context - use nest_asyncio if available
            try:
                import nest_asyncio

                nest_asyncio.apply()
                return loop.run_until_complete(self.embed(texts, model, dimension))
            except ImportError:
                # Create new event loop in thread
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.embed(texts, model, dimension))
                    return future.result()
        else:
            return asyncio.run(self.embed(texts, model, dimension))

    async def agenerate_text(
        self,
        prompt: str,
        *,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate text from a prompt (async).

        Uses the Ollama OpenAI-compatible API for simple text generation.

        Args:
            prompt: The prompt to generate text from

        Returns:
            Generated text string
        """
        api_kwargs: dict[str, Any] = {
            "model": self._ollama_model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if options and options.max_tokens is not None:
            api_kwargs["max_completion_tokens"] = options.max_tokens
        if options and options.temperature is not None:
            api_kwargs["temperature"] = options.temperature
        if options and options.top_p is not None:
            api_kwargs["top_p"] = options.top_p
        if options and options.n is not None:
            api_kwargs["n"] = options.n
        if options and options.seed is not None:
            api_kwargs["seed"] = options.seed
        response = await self._embedding_client.chat.completions.create(**api_kwargs)
        return response.choices[0].message.content or ""

    def generate_text(
        self,
        prompt: str,
        *,
        json_mode: bool = False,
        options: GenerationOptions | None = None,
    ) -> str:
        """Generate text from a prompt (sync).

        Args:
            prompt: The prompt to generate text from
            json_mode: If True, force JSON response format (not fully supported by all Ollama models)

        Returns:
            Generated text string
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            try:
                import nest_asyncio

                nest_asyncio.apply()
                return loop.run_until_complete(self.agenerate_text(prompt, options=options))
            except ImportError:
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.agenerate_text(prompt, options=options)
                    )
                    return future.result()
        else:
            return asyncio.run(self.agenerate_text(prompt, options=options))
