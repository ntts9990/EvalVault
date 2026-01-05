"""Model configuration with YAML profiles support.

최근 트렌드에 맞춘 설정 관리:
- YAML 기반 프로필 설정
- 환경별 모델 분리 (dev/prod)
- pydantic 검증
- 환경변수 오버라이드 지원
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM 모델 설정."""

    provider: Literal["openai", "ollama", "vllm"] = Field(
        description="LLM provider: 'openai', 'ollama', or 'vllm'"
    )
    model: str = Field(description="Model name")
    options: dict | None = Field(
        default=None, description="Provider-specific options (e.g., think_level)"
    )


class EmbeddingConfig(BaseModel):
    """임베딩 모델 설정."""

    provider: Literal["openai", "ollama", "vllm"] = Field(
        description="Embedding provider: 'openai', 'ollama', or 'vllm'"
    )
    model: str = Field(description="Embedding model name")


class ProfileConfig(BaseModel):
    """단일 프로필 설정."""

    description: str = Field(default="")
    llm: LLMConfig
    embedding: EmbeddingConfig


class ModelConfig(BaseModel):
    """전체 모델 설정.

    모델 프로필만 정의합니다. 인프라 설정(서버 URL 등)은 .env에서 관리합니다.
    """

    profiles: dict[str, ProfileConfig]

    def get_profile(self, name: str) -> ProfileConfig:
        """프로필 설정 반환.

        Args:
            name: 프로필 이름 (dev, prod, openai)

        Returns:
            ProfileConfig 인스턴스

        Raises:
            KeyError: 프로필이 존재하지 않을 때
        """
        if name not in self.profiles:
            available = ", ".join(self.profiles.keys())
            raise KeyError(f"Profile '{name}' not found. Available: {available}")
        return self.profiles[name]


def find_config_file() -> Path | None:
    """설정 파일 경로 탐색.

    탐색 순서:
    1. 현재 디렉토리의 evalvault.yaml
    2. 현재 디렉토리의 config/models.yaml
    3. 프로젝트 루트의 config/models.yaml
    """
    search_paths = [
        Path.cwd() / "evalvault.yaml",
        Path.cwd() / "config" / "models.yaml",
        Path(__file__).parent.parent.parent.parent / "config" / "models.yaml",
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def load_model_config(config_path: Path | str | None = None) -> ModelConfig:
    """모델 설정 파일 로드.

    Args:
        config_path: 설정 파일 경로 (없으면 자동 탐색)

    Returns:
        ModelConfig 인스턴스

    Raises:
        FileNotFoundError: 설정 파일을 찾을 수 없을 때
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None:
        raise FileNotFoundError(
            "Model config file not found. Create 'config/models.yaml' or 'evalvault.yaml'"
        )

    config_path = Path(config_path)

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return ModelConfig(**data)


# 캐시된 설정 인스턴스
_model_config: ModelConfig | None = None


def get_model_config() -> ModelConfig:
    """전역 모델 설정 인스턴스 반환 (캐시됨)."""
    global _model_config
    if _model_config is None:
        _model_config = load_model_config()
    return _model_config


def reset_model_config() -> None:
    """설정 캐시 초기화 (테스트용)."""
    global _model_config
    _model_config = None
