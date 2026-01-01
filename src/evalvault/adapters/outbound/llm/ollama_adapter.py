"""Ollama LLM adapter for air-gapped (폐쇄망) environments.

Ollama의 OpenAI 호환 API를 사용하여 Ragas와 통합합니다.
기존 OpenAIAdapter 코드를 최대한 재사용합니다.

지원 모델:
  - 평가 LLM: gemma3:1b (개발), gpt-oss-safeguard:20b (운영)
  - 임베딩: qwen3-embedding:0.6b (개발), qwen3-embedding:8b (운영)
"""

from typing import Any

import httpx
from openai import AsyncOpenAI
from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings
from ragas.llms import llm_factory

from evalvault.adapters.outbound.llm.base import BaseLLMAdapter, TokenUsage
from evalvault.adapters.outbound.llm.openai_adapter import TokenTrackingAsyncOpenAI
from evalvault.config.settings import Settings
from evalvault.ports.outbound.llm_port import ThinkingConfig


class ThinkingTokenTrackingAsyncOpenAI(TokenTrackingAsyncOpenAI):
    """TokenTrackingAsyncOpenAI extended with thinking parameter injection.

    Ollama의 thinking 기능을 지원하는 모델(gpt-oss-safeguard:20b 등)에
    think_level 파라미터를 자동으로 주입합니다.
    """

    def __init__(
        self,
        usage_tracker: TokenUsage,
        think_level: str | None = None,
        **kwargs: Any,
    ):
        """Initialize thinking-aware client.

        Args:
            usage_tracker: Token usage tracker
            think_level: Thinking level (e.g., 'medium') or None
            **kwargs: Additional arguments passed to AsyncOpenAI
        """
        # Set think_level BEFORE calling super().__init__()
        # because _create_tracking_chat() needs it during initialization
        self._think_level = think_level
        super().__init__(usage_tracker=usage_tracker, **kwargs)

    def _create_tracking_chat(self) -> Any:
        """Create a chat wrapper that tracks token usage and injects thinking params."""
        think_level = self._think_level

        class ThinkingTrackingCompletions:
            def __init__(inner_self, completions: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._completions = completions
                inner_self._tracker = tracker

            async def create(inner_self, **kwargs: Any) -> Any:  # noqa: N805
                # Inject thinking parameters if configured
                if think_level is not None:
                    # Ollama expects thinking params in extra_body.options
                    extra_body = kwargs.get("extra_body", {})
                    options = extra_body.get("options", {})
                    options["think_level"] = think_level
                    extra_body["options"] = options
                    kwargs["extra_body"] = extra_body

                # Call the original method and track usage
                response = await inner_self._completions.create(**kwargs)

                # Extract usage from response
                if hasattr(response, "usage") and response.usage:
                    inner_self._tracker.add(
                        prompt=response.usage.prompt_tokens or 0,
                        completion=response.usage.completion_tokens or 0,
                        total=response.usage.total_tokens or 0,
                    )
                return response

        class ThinkingTrackingChat:
            def __init__(inner_self, chat: Any, tracker: TokenUsage):  # noqa: N805
                inner_self._chat = chat
                inner_self.completions = ThinkingTrackingCompletions(chat.completions, tracker)

        return ThinkingTrackingChat(self._original_chat, self._usage_tracker)


class OllamaAdapter(BaseLLMAdapter):
    """Ollama LLM adapter using OpenAI-compatible API.

    폐쇄망 환경에서 로컬 Ollama 서버를 사용한 RAG 평가를 지원합니다.
    Ragas와의 호환성을 위해 OpenAI 호환 API를 사용합니다.

    Attributes:
        _ollama_model: 평가에 사용하는 LLM 모델명
        _embedding_model_name: 임베딩에 사용하는 모델명
        _base_url: Ollama 서버 URL
    """

    def __init__(self, settings: Settings):
        """Initialize Ollama adapter.

        Args:
            settings: Application settings containing Ollama configuration
        """
        self._settings = settings
        self._ollama_model = settings.ollama_model
        self._embedding_model_name = settings.ollama_embedding_model
        self._base_url = settings.ollama_base_url
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

        # Create HTTP client with custom timeout for Ollama
        http_client = httpx.AsyncClient(timeout=httpx.Timeout(self._timeout, connect=30.0))

        # Create OpenAI-compatible client pointing to Ollama
        # Ollama doesn't require a real API key
        # Use ThinkingTokenTrackingAsyncOpenAI to inject thinking parameters
        self._client = ThinkingTokenTrackingAsyncOpenAI(
            usage_tracker=self._token_usage,
            think_level=self._think_level,
            api_key="ollama",  # Dummy key for Ollama
            base_url=f"{self._base_url}/v1",
            http_client=http_client,
        )

        # Create Ragas LLM using OpenAI provider with Ollama backend
        ragas_llm = llm_factory(
            model=self._ollama_model,
            provider="openai",
            client=self._client,
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
        text_list = [texts] if is_single else texts

        embeddings = []
        async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout, connect=30.0)) as client:
            for text in text_list:
                payload: dict[str, Any] = {
                    "model": model,
                    "prompt": text,
                }

                # Matryoshka dimension support for Qwen3-Embedding
                if dimension is not None:
                    payload["options"] = {"num_ctx": 8192}
                    # Truncate embedding to specified dimension after generation
                    # Ollama doesn't support dimension parameter directly,
                    # so we truncate the output embedding
                    payload["_truncate_dim"] = dimension

                response = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={k: v for k, v in payload.items() if not k.startswith("_")},
                )
                response.raise_for_status()
                result = response.json()
                embedding = result["embedding"]

                # Apply Matryoshka truncation if specified
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
