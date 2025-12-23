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

    # OpenAI Configuration
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    openai_base_url: str | None = Field(
        default=None, description="Custom OpenAI API base URL (optional)"
    )
    openai_model: str = Field(
        default="gpt-5-nano", description="OpenAI model to use for evaluation"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI embedding model"
    )

    # Ragas Evaluation Thresholds (SLA)
    threshold_faithfulness: float = Field(default=0.7, ge=0.0, le=1.0)
    threshold_answer_relevancy: float = Field(default=0.7, ge=0.0, le=1.0)
    threshold_context_precision: float = Field(default=0.7, ge=0.0, le=1.0)
    threshold_context_recall: float = Field(default=0.7, ge=0.0, le=1.0)

    # Langfuse Configuration (optional)
    langfuse_public_key: str | None = Field(default=None, description="Langfuse public key")
    langfuse_secret_key: str | None = Field(default=None, description="Langfuse secret key")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", description="Langfuse host URL")

    def get_threshold(self, metric_name: str) -> float:
        """Get threshold for a specific metric.

        Args:
            metric_name: Metric name (e.g., 'faithfulness', 'answer_relevancy')

        Returns:
            Threshold value (0.0 ~ 1.0)
        """
        threshold_attr = f"threshold_{metric_name}"
        return getattr(self, threshold_attr, 0.7)

    def get_all_thresholds(self) -> dict[str, float]:
        """Get all metric thresholds as a dictionary.

        Returns:
            Dictionary of metric names to threshold values
        """
        return {
            "faithfulness": self.threshold_faithfulness,
            "answer_relevancy": self.threshold_answer_relevancy,
            "context_precision": self.threshold_context_precision,
            "context_recall": self.threshold_context_recall,
        }


# Global settings instance (lazy initialization)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create global settings instance.

    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# For backward compatibility
settings = get_settings()
