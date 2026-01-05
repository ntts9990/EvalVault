"""Application settings using pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Profile Configuration (YAML 기반 모델 프로필)
    evalvault_profile: str | None = Field(
        default=None,
        description="Model profile name (dev, prod, openai). Overrides individual settings.",
    )

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated list of allowed CORS origins.",
    )

    # LLM Provider Selection
    llm_provider: str = Field(
        default="openai",
        description="LLM provider: 'openai', 'ollama', or 'vllm'",
    )

    # OpenAI Configuration
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_base_url: str | None = Field(
        default=None, description="Custom OpenAI API base URL (optional)"
    )
    openai_model: str = Field(default="gpt-4o", description="OpenAI model to use for evaluation")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )

    # Ollama Configuration (폐쇄망용)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL",
    )
    ollama_model: str = Field(
        default="gemma3:1b",
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

    # MLflow Configuration (optional)
    mlflow_tracking_uri: str | None = Field(default=None, description="MLflow tracking server URI")
    mlflow_experiment_name: str = Field(default="evalvault", description="MLflow experiment name")

    # Phoenix Configuration (optional - RAG observability)
    phoenix_endpoint: str = Field(
        default="http://localhost:6006/v1/traces",
        description="Phoenix OTLP endpoint for traces",
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
        default="langfuse",
        description="Tracker provider: 'langfuse', 'mlflow', or 'phoenix'",
    )

    # PostgreSQL Configuration (optional)
    postgres_host: str | None = Field(default=None, description="PostgreSQL server host")
    postgres_port: int = Field(default=5432, description="PostgreSQL server port")
    postgres_database: str = Field(default="evalvault", description="PostgreSQL database name")
    postgres_user: str | None = Field(default=None, description="PostgreSQL user")
    postgres_password: str | None = Field(default=None, description="PostgreSQL password")
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

    try:
        model_config = get_model_config()
        profile = model_config.get_profile(profile_name)

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

    except FileNotFoundError:
        # 설정 파일이 없으면 프로필 무시
        pass

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

    return _settings


def reset_settings() -> None:
    """설정 캐시 초기화 (테스트용)."""
    global _settings
    _settings = None


# For backward compatibility
settings = get_settings()
