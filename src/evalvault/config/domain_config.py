"""Domain Memory configuration module.

Provides Pydantic models for domain-specific memory configuration
supporting multi-language (ko/en) and configurable learning settings.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class LanguageConfig(BaseModel):
    """Language-specific resource paths."""

    ko: str | None = None
    en: str | None = None

    def get(self, language: str) -> str | None:
        """Get resource path for a specific language."""
        return getattr(self, language, None)

    def languages(self) -> list[str]:
        """Return list of configured languages."""
        return [lang for lang in ["ko", "en"] if getattr(self, lang) is not None]


class FactualConfig(BaseModel):
    """Factual layer configuration.

    용어사전, 규정 문서 등 정적 도메인 지식 설정.
    """

    glossary: LanguageConfig = Field(default_factory=LanguageConfig)
    regulatory_rules: LanguageConfig | None = None
    shared: dict[str, str] = Field(default_factory=dict)


class ExperientialConfig(BaseModel):
    """Experiential layer configuration.

    학습된 패턴, 신뢰도 점수 등 경험적 지식 설정.
    """

    reliability_scores: LanguageConfig = Field(default_factory=LanguageConfig)
    failure_modes: str = "failures.json"
    behavior_handbook: str = "behaviors.json"


class WorkingConfig(BaseModel):
    """Working layer configuration.

    런타임 캐시, KG 바인딩 등 실행 시 설정.
    """

    run_cache: str = "${RUN_DIR}/memory.db"
    kg_binding: str | None = None
    max_cache_size_mb: int = 100


class LearningConfig(BaseModel):
    """Learning configuration.

    평가 후 자동 학습 관련 설정.
    """

    enabled: bool = True
    min_confidence_to_store: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to store extracted facts",
    )
    behavior_extraction: bool = True
    auto_apply: bool = True
    decay_rate: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Decay rate for verification scores over time",
    )
    forget_threshold_days: int = Field(
        default=90,
        ge=1,
        description="Days after which low-confidence facts are forgotten",
    )


class DomainMetadata(BaseModel):
    """Domain metadata."""

    domain: str
    version: str = "1.0.0"
    supported_languages: list[str] = Field(default_factory=lambda: ["ko", "en"])
    default_language: str = "ko"
    description: str = ""


class DomainMemoryConfig(BaseModel):
    """Domain memory configuration.

    도메인별 메모리 설정을 관리합니다.
    YAML 파일에서 로드되며, Factual/Experiential/Working 레이어와
    학습 설정을 포함합니다.

    Example:
        >>> config = load_domain_config("insurance")
        >>> print(config.metadata.domain)
        "insurance"
        >>> print(config.learning.enabled)
        True
    """

    metadata: DomainMetadata
    factual: FactualConfig = Field(default_factory=FactualConfig)
    experiential: ExperientialConfig = Field(default_factory=ExperientialConfig)
    working: WorkingConfig = Field(default_factory=WorkingConfig)
    learning: LearningConfig = Field(default_factory=LearningConfig)

    def get_glossary_path(self, language: str | None = None) -> str | None:
        """Get glossary file path for a language.

        Args:
            language: Language code (ko, en). Uses default if None.

        Returns:
            Path to glossary file or None if not configured.
        """
        lang = language or self.metadata.default_language
        return self.factual.glossary.get(lang)

    def get_reliability_path(self, language: str | None = None) -> str | None:
        """Get reliability scores file path for a language."""
        lang = language or self.metadata.default_language
        return self.experiential.reliability_scores.get(lang)

    def supports_language(self, language: str) -> bool:
        """Check if domain supports a language."""
        return language in self.metadata.supported_languages


def get_domains_config_dir() -> Path:
    """Get the domains configuration directory.

    Returns:
        Path to config/domains directory.
    """
    # Try to find config/domains relative to project root
    # Check common locations
    candidates = [
        Path("config/domains"),
        Path.cwd() / "config" / "domains",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Default to config/domains (will be created if needed)
    return Path("config/domains")


def load_domain_config(domain: str, config_dir: Path | None = None) -> DomainMemoryConfig:
    """Load domain configuration from YAML file.

    Args:
        domain: Domain name (e.g., 'insurance', 'medical')
        config_dir: Optional custom config directory path

    Returns:
        Loaded DomainMemoryConfig

    Raises:
        FileNotFoundError: If domain config file not found
        ValueError: If config file is invalid
    """
    if config_dir is None:
        config_dir = get_domains_config_dir()

    config_path = config_dir / domain / "memory.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Domain config not found: {config_path}. "
            f"Run 'evalvault domain-init {domain}' to create."
        )

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Empty config file: {config_path}")

    # Handle flat metadata format from YAML
    if "metadata" not in data and "domain" in data:
        # Convert flat format to nested
        metadata = {
            "domain": data.pop("domain"),
            "version": data.pop("version", "1.0.0"),
            "supported_languages": data.pop("supported_languages", ["ko", "en"]),
            "default_language": data.pop("default_language", "ko"),
            "description": data.pop("description", ""),
        }
        data["metadata"] = metadata

    return DomainMemoryConfig(**data)


def list_domains(config_dir: Path | None = None) -> list[str]:
    """List all configured domains.

    Args:
        config_dir: Optional custom config directory path

    Returns:
        List of domain names
    """
    if config_dir is None:
        config_dir = get_domains_config_dir()

    if not config_dir.exists():
        return []

    domains = []
    for path in config_dir.iterdir():
        if path.is_dir() and (path / "memory.yaml").exists():
            domains.append(path.name)

    return sorted(domains)


def generate_domain_template(
    domain: str,
    languages: list[str] | None = None,
    description: str = "",
) -> dict[str, Any]:
    """Generate a domain configuration template.

    Args:
        domain: Domain name
        languages: Supported languages (default: ["ko", "en"])
        description: Domain description

    Returns:
        Dictionary suitable for YAML serialization
    """
    if languages is None:
        languages = ["ko", "en"]

    default_language = languages[0] if languages else "ko"

    # Build language-specific configs
    glossary = {lang: f"terms_dictionary_{lang}.json" for lang in languages}
    reliability = {lang: f"reliability_{lang}.json" for lang in languages}

    template = {
        "metadata": {
            "domain": domain,
            "version": "1.0.0",
            "supported_languages": languages,
            "default_language": default_language,
            "description": description or f"{domain.capitalize()} domain memory configuration",
        },
        "factual": {
            "glossary": glossary,
            "shared": {},
        },
        "experiential": {
            "reliability_scores": reliability,
            "failure_modes": "failures.json",
            "behavior_handbook": "behaviors.json",
        },
        "working": {
            "run_cache": "${RUN_DIR}/memory.db",
            "max_cache_size_mb": 100,
        },
        "learning": {
            "enabled": True,
            "min_confidence_to_store": 0.6,
            "behavior_extraction": True,
            "auto_apply": True,
            "decay_rate": 0.95,
            "forget_threshold_days": 90,
        },
    }

    return template


def save_domain_config(
    domain: str,
    config: dict[str, Any] | DomainMemoryConfig,
    config_dir: Path | None = None,
) -> Path:
    """Save domain configuration to YAML file.

    Args:
        domain: Domain name
        config: Configuration dict or DomainMemoryConfig
        config_dir: Optional custom config directory path

    Returns:
        Path to saved config file
    """
    if config_dir is None:
        config_dir = get_domains_config_dir()

    domain_dir = config_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)

    config_path = domain_dir / "memory.yaml"

    data = config.model_dump(mode="json") if isinstance(config, DomainMemoryConfig) else config

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return config_path
