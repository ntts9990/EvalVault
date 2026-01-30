"""Application settings using pydantic-settings."""

from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict

from evalvault.config.secret_manager import (
    SecretProviderError,
    build_secret_provider,
    is_secret_reference,
    resolve_secret_reference,
)


def _detect_repo_root(start: Path, max_depth: int = 6) -> Path | None:
    current = start
    for _ in range(max_depth):
        if (current / "pyproject.toml").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


def _resolve_storage_path(path_value: str) -> str:
    if not path_value or path_value == ":memory:":
        return path_value
    candidate = Path(path_value).expanduser()
    if candidate.is_absolute():
        return str(candidate)
    repo_root = _detect_repo_root(Path.cwd())
    base = repo_root if repo_root is not None else Path.cwd()
    return str((base / candidate).resolve())


def _ensure_http_scheme(url_value: str) -> str:
    value = url_value.strip()
    if not value:
        return url_value
    if "://" in value:
        return value
    return f"http://{value}"


def is_production_profile(profile_name: str | None) -> bool:
    return (profile_name or "").strip().lower() == "prod"


def _parse_cors_origins(cors_origins: str | None) -> list[str]:
    if not cors_origins:
        return []
    return [origin.strip() for origin in cors_origins.split(",") if origin.strip()]


def resolve_tracker_providers(provider: str | None) -> list[str]:
    if not provider:
        return []
    normalized = provider.strip().lower()
    if normalized in {"none", "off", "disabled"}:
        return ["none"]
    aliases = {
        "all": ["mlflow", "phoenix"],
        "default": ["mlflow", "phoenix"],
    }
    if normalized in aliases:
        return aliases[normalized]
    separators = [",", "+", "/", "|"]
    for sep in separators:
        normalized = normalized.replace(sep, ",")
    providers = [p.strip() for p in normalized.split(",") if p.strip()]
    if not providers:
        return []
    if "none" in providers and len(providers) > 1:
        raise ValueError("tracker_provider cannot combine 'none' with other providers")
    deduped: list[str] = []
    for entry in providers:
        if entry not in deduped:
            deduped.append(entry)
    return deduped


SECRET_REFERENCE_FIELDS = (
    "api_auth_tokens",
    "knowledge_read_tokens",
    "knowledge_write_tokens",
    "openai_api_key",
    "anthropic_api_key",
    "azure_api_key",
    "vllm_api_key",
    "langfuse_public_key",
    "langfuse_secret_key",
    "phoenix_api_token",
    "postgres_password",
    "postgres_connection_string",
)


def _validate_production_settings(settings: "Settings") -> None:
    if not is_production_profile(settings.evalvault_profile):
        return

    missing: list[str] = []

    if not settings.api_auth_tokens:
        missing.append("API_AUTH_TOKENS")

    if settings.llm_provider == "openai" and not settings.openai_api_key:
        missing.append("OPENAI_API_KEY")

    providers = resolve_tracker_providers(settings.tracker_provider)
    if "langfuse" in providers:
        if not settings.langfuse_public_key:
            missing.append("LANGFUSE_PUBLIC_KEY")
        if not settings.langfuse_secret_key:
            missing.append("LANGFUSE_SECRET_KEY")

    if "mlflow" in providers and not settings.mlflow_tracking_uri:
        missing.append("MLFLOW_TRACKING_URI")

    if (
        settings.postgres_connection_string is None
        and settings.postgres_host
        and not settings.postgres_password
    ):
        missing.append("POSTGRES_PASSWORD")

    cors_origins = _parse_cors_origins(settings.cors_origins)
    if not cors_origins:
        missing.append("CORS_ORIGINS")
    else:
        localhost_origins = {"localhost", "127.0.0.1"}
        for origin in cors_origins:
            if any(host in origin for host in localhost_origins):
                raise ValueError("Production profile forbids localhost in CORS_ORIGINS.")

    if missing:
        raise ValueError(
            "Missing required settings for prod profile: " + ", ".join(sorted(set(missing)))
        )


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    _secret_cache: dict[str, str] = PrivateAttr(default_factory=dict)

    # Profile Configuration (YAML 기반 모델 프로필)
    evalvault_profile: str | None = Field(
        default=None,
        description="Model profile name (dev, prod, openai). Overrides individual settings.",
    )

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated list of allowed CORS origins.",
    )
    secret_provider: str | None = Field(
        default=None,
        description="Secret provider name for secret:// references (env/aws/gcp/vault).",
    )
    secret_cache_enabled: bool = Field(
        default=True,
        description="Cache resolved secret references in memory.",
    )
    api_auth_tokens: str | None = Field(
        default=None,
        description=(
            "Comma-separated list of API bearer tokens for FastAPI auth. "
            "Leave empty to disable authentication."
        ),
    )
    knowledge_read_tokens: str | None = Field(
        default=None,
        description="Comma-separated read tokens for knowledge endpoints.",
    )
    knowledge_write_tokens: str | None = Field(
        default=None,
        description="Comma-separated write tokens for knowledge endpoints.",
    )
    rate_limit_enabled: bool = Field(
        default=False,
        description="Enable API rate limiting for /api routes.",
    )
    rate_limit_requests: int = Field(
        default=120,
        description="Max requests allowed within rate_limit_window_seconds.",
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        description="Window size for rate limit checks in seconds.",
    )
    rate_limit_block_threshold: int = Field(
        default=10,
        description="Log suspicious activity after this many rate limit blocks.",
    )
    evalvault_db_path: str = Field(
        default="data/db/evalvault.db",
        description="SQLite database path for API/CLI storage.",
    )
    db_backend: str = Field(
        default="postgres",
        description="Storage backend: 'postgres' or 'sqlite'.",
    )
    evalvault_memory_db_path: str = Field(
        default="data/db/evalvault_memory.db",
        description="SQLite database path for Domain Memory storage.",
    )

    def model_post_init(self, __context: Any) -> None:
        self.evalvault_db_path = _resolve_storage_path(self.evalvault_db_path)
        self.evalvault_memory_db_path = _resolve_storage_path(self.evalvault_memory_db_path)
        self.ollama_base_url = _ensure_http_scheme(self.ollama_base_url)
        self._resolve_secret_references()

    def _resolve_secret_references(self) -> None:
        secret_values = [
            value
            for value in (getattr(self, field, None) for field in SECRET_REFERENCE_FIELDS)
            if isinstance(value, str)
        ]
        if not any(is_secret_reference(value) for value in secret_values):
            return
        try:
            provider = build_secret_provider(self.secret_provider)
        except SecretProviderError as exc:
            raise ValueError(str(exc)) from exc
        cache = self._secret_cache if self.secret_cache_enabled else None
        for field in SECRET_REFERENCE_FIELDS:
            value = getattr(self, field, None)
            if isinstance(value, str) and is_secret_reference(value):
                resolved = resolve_secret_reference(value, provider, cache)
                setattr(self, field, resolved)

    # LLM Provider Selection
    llm_provider: str = Field(
        default="ollama",
        description="LLM provider: 'openai', 'ollama', or 'vllm'",
    )
    faithfulness_fallback_provider: str | None = Field(
        default=None,
        description="Optional LLM provider for faithfulness fallback evaluation.",
    )
    faithfulness_fallback_model: str | None = Field(
        default=None,
        description="Optional model name for faithfulness fallback evaluation.",
    )

    # OpenAI Configuration
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_base_url: str | None = Field(
        default=None, description="Custom OpenAI API base URL (optional)"
    )
    openai_model: str = Field(
        default="gpt-5-mini",
        description="OpenAI model to use for evaluation",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )

    # Ollama Configuration (폐쇄망용)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )
    ollama_model: str = Field(
        default="qwen3:14b",
        description="Ollama model name for evaluation",
    )
    ollama_embedding_model: str = Field(
        default="qwen3-embedding:0.6b",
        description="Ollama embedding model",
    )
    ollama_timeout: int = Field(
        default=120,
        description="Ollama request timeout in seconds",
    )
    ollama_think_level: str | None = Field(
        default=None,
        description="Thinking level for models that support it (e.g., 'medium')",
    )
    ollama_tool_models: str | None = Field(
        default=None,
        description="Comma-separated list of Ollama models that support tool/function calling.",
    )

    # Tokenizer Cache Configuration (for lm-eval benchmarks)
    tokenizer_cache_path: str | None = Field(
        default="data/tokenizers",
        description="Local cache path for HuggingFace tokenizers (used by lm-eval benchmarks)",
    )

    # vLLM Configuration (OpenAI-compatible server)
    vllm_base_url: str = Field(
        default="http://localhost:8001/v1",
        description="vLLM OpenAI-compatible base URL",
    )
    vllm_api_key: str | None = Field(
        default=None,
        description="vLLM API key (optional, depends on server setup)",
    )
    vllm_model: str = Field(
        default="gpt-oss-120b",
        description="vLLM model name for evaluation",
    )
    vllm_embedding_model: str = Field(
        default="qwen3-embedding:0.6b",
        description="vLLM embedding model name",
    )
    vllm_embedding_base_url: str | None = Field(
        default=None,
        description="Optional base URL for vLLM embeddings (defaults to vllm_base_url)",
    )
    vllm_timeout: int = Field(
        default=120,
        description="vLLM request timeout in seconds",
    )

    # Azure OpenAI Configuration (optional)
    azure_api_key: str | None = Field(default=None, description="Azure OpenAI API key")
    azure_endpoint: str | None = Field(default=None, description="Azure OpenAI endpoint URL")
    azure_deployment: str | None = Field(default=None, description="Azure deployment name")
    azure_embedding_deployment: str | None = Field(
        default=None, description="Azure embedding deployment name"
    )
    azure_api_version: str = Field(default="2024-02-15-preview", description="Azure API version")

    # Anthropic Configuration (optional)
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Anthropic Claude model to use for evaluation",
    )
    anthropic_thinking_budget: int | None = Field(
        default=None,
        description="Token budget for extended thinking (e.g., 10000). None to disable.",
    )

    # Langfuse Configuration (optional)
    langfuse_public_key: str | None = Field(default=None, description="Langfuse public key")
    langfuse_secret_key: str | None = Field(default=None, description="Langfuse secret key")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com", description="Langfuse host URL"
    )

    mcp_enabled: bool = Field(
        default=False,
        description="Enable MCP JSON-RPC endpoint over HTTP.",
    )
    mcp_protocol_version: str = Field(
        default="2025-11-25",
        description="MCP protocol version to advertise.",
    )
    mcp_server_version: str = Field(
        default="0.1.0",
        description="EvalVault MCP server version.",
    )
    mcp_auth_tokens: str | None = Field(
        default=None,
        description="Comma-separated bearer tokens for MCP endpoint (required).",
    )
    mcp_allowed_tools: str | None = Field(
        default=None,
        description="Comma-separated allowlist of MCP tool names.",
    )

    # MLflow Configuration (optional)
    mlflow_tracking_uri: str | None = Field(default=None, description="MLflow tracking server URI")
    mlflow_experiment_name: str = Field(default="evalvault", description="MLflow experiment name")

    # Phoenix Configuration (optional - RAG observability)
    phoenix_endpoint: str = Field(
        default="http://localhost:6006/v1/traces",
        description="Phoenix OTLP endpoint for traces",
    )
    phoenix_project_name: str = Field(
        default="evalvault",
        description="Phoenix project name for grouping traces",
    )
    phoenix_annotations_enabled: bool = Field(
        default=True,
        description="Enable automatic Phoenix span annotations",
    )
    phoenix_api_token: str | None = Field(
        default=None,
        description="Phoenix API token for cloud deployments (optional)",
    )
    phoenix_enabled: bool = Field(
        default=False,
        description="Enable Phoenix instrumentation for automatic LLM tracing",
    )
    phoenix_sample_rate: float = Field(
        default=1.0,
        description="Sampling rate for Phoenix traces (0.0~1.0).",
        ge=0.0,
        le=1.0,
    )

    # Tracker Provider Selection
    tracker_provider: str = Field(
        default="mlflow+phoenix",
        description="Tracker provider: 'langfuse', 'mlflow', 'phoenix', 'none', or combinations",
    )

    # Cluster map configuration
    cluster_map_auto_enabled: bool = Field(
        default=True,
        description="Auto-generate cluster maps after evaluation runs.",
    )
    cluster_map_embedding_mode: str = Field(
        default="tfidf",
        description="Cluster map embedding mode ('tfidf' or 'model').",
    )
    cluster_map_min_cluster_size: int = Field(
        default=3,
        description="Minimum cluster size when generating cluster maps.",
    )
    cluster_map_max_clusters: int = Field(
        default=10,
        description="Maximum cluster count when generating cluster maps.",
    )
    cluster_map_text_max_chars: int = Field(
        default=800,
        description="Max characters per test case when generating cluster maps.",
    )

    # PostgreSQL Configuration (optional)
    postgres_host: str | None = Field(
        default=None,
        validation_alias=AliasChoices("POSTGRES_HOST", "EVALVAULT_DB_HOST"),
        description="PostgreSQL server host",
    )
    postgres_port: int = Field(
        default=5432,
        validation_alias=AliasChoices("POSTGRES_PORT", "EVALVAULT_DB_PORT"),
        description="PostgreSQL server port",
    )
    postgres_database: str = Field(
        default="evalvault",
        validation_alias=AliasChoices("POSTGRES_DATABASE", "EVALVAULT_DB_NAME"),
        description="PostgreSQL database name",
    )
    postgres_user: str | None = Field(
        default=None,
        validation_alias=AliasChoices("POSTGRES_USER", "EVALVAULT_DB_USER"),
        description="PostgreSQL user",
    )
    postgres_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("POSTGRES_PASSWORD", "EVALVAULT_DB_PASSWORD"),
        description="PostgreSQL password",
    )
    postgres_connection_string: str | None = Field(
        default=None, description="PostgreSQL connection string (overrides other postgres settings)"
    )


# Global settings instance (lazy initialization)
_settings: Settings | None = None


def apply_profile(settings: Settings, profile_name: str) -> Settings:
    """프로필 설정을 Settings에 적용.

    모델 프로필(config/models.yaml)에서 모델명만 가져오고,
    인프라 설정(서버 URL, 타임아웃 등)은 .env에서 유지합니다.

    Args:
        settings: 기존 Settings 인스턴스
        profile_name: 프로필 이름 (dev, prod, openai)

    Returns:
        프로필이 적용된 Settings 인스턴스
    """
    from evalvault.config.model_config import get_model_config

    normalized = profile_name.strip() if isinstance(profile_name, str) else profile_name
    if not normalized:
        return settings

    model_config = None
    try:
        model_config = get_model_config()
        profile = model_config.get_profile(normalized)

        # LLM 설정 적용 (모델명과 provider만)
        settings.llm_provider = profile.llm.provider

        if profile.llm.provider == "ollama":
            settings.ollama_model = profile.llm.model
            if profile.llm.options and "think_level" in profile.llm.options:
                settings.ollama_think_level = profile.llm.options["think_level"]
            # 인프라 설정(ollama_base_url, ollama_timeout)은 .env에서 가져옴
        elif profile.llm.provider == "openai":
            settings.openai_model = profile.llm.model
        elif profile.llm.provider == "vllm":
            settings.vllm_model = profile.llm.model

        # 임베딩 설정 적용 (모델명만)
        if profile.embedding.provider == "ollama":
            settings.ollama_embedding_model = profile.embedding.model
        elif profile.embedding.provider == "openai":
            settings.openai_embedding_model = profile.embedding.model
        elif profile.embedding.provider == "vllm":
            settings.vllm_embedding_model = profile.embedding.model

    except FileNotFoundError as exc:
        raise ValueError(
            "Model profile config not found. Create 'config/models.yaml' or 'evalvault.yaml' "
            f"to use profile '{normalized}'."
        ) from exc
    except KeyError as exc:
        available = ", ".join(sorted(model_config.profiles.keys())) if model_config else ""
        raise ValueError(
            f"Unknown profile '{normalized}'. Available profiles: {available}"
        ) from exc

    return settings


def get_settings() -> Settings:
    """Get or create global settings instance.

    프로필이 지정된 경우 (EVALVAULT_PROFILE 환경변수) 해당 프로필 설정을 적용합니다.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()

        # 프로필이 지정된 경우 적용
        if _settings.evalvault_profile:
            _settings = apply_profile(_settings, _settings.evalvault_profile)

        _validate_production_settings(_settings)

    return _settings


def apply_runtime_overrides(overrides: dict[str, object]) -> Settings:
    """런타임 설정을 갱신하고 동일한 인스턴스를 유지합니다.

    API에서 전달된 변경 사항을 적용한 뒤, 전역 설정 인스턴스를
    갱신해 동일 참조를 유지합니다.
    """
    settings = get_settings()
    payload = settings.model_dump()
    payload.update(overrides)

    profile_value = payload.get("evalvault_profile")
    if isinstance(profile_value, str) and not profile_value.strip():
        payload["evalvault_profile"] = None

    model_override_keys = {
        "llm_provider",
        "openai_model",
        "openai_embedding_model",
        "ollama_model",
        "ollama_embedding_model",
        "vllm_model",
        "vllm_embedding_model",
    }
    if any(key in overrides for key in model_override_keys):
        payload["evalvault_profile"] = None

    updated = Settings.model_validate(payload)
    if updated.evalvault_profile:
        updated = apply_profile(updated, updated.evalvault_profile)
    _validate_production_settings(updated)
    for key, value in updated.model_dump().items():
        setattr(settings, key, value)

    return settings


def reset_settings() -> None:
    """설정 캐시 초기화 (테스트용)."""
    global _settings
    _settings = None


# For backward compatibility
settings = get_settings()
