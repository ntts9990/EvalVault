"""Configuration module."""

from evalvault.config.agent_types import (
    AgentConfig,
    AgentMode,
    AgentType,
    get_agent_config,
    get_parallel_groups,
)
from evalvault.config.domain_config import (
    DomainMemoryConfig,
    DomainMetadata,
    ExperientialConfig,
    FactualConfig,
    LanguageConfig,
    LearningConfig,
    WorkingConfig,
    generate_domain_template,
    list_domains,
    load_domain_config,
    save_domain_config,
)
from evalvault.config.model_config import (
    ModelConfig,
    ProfileConfig,
    get_model_config,
    load_model_config,
)
from evalvault.config.settings import Settings, get_settings, reset_settings, settings

__all__ = [
    # Settings
    "Settings",
    "settings",
    "get_settings",
    "reset_settings",
    # Model config
    "ModelConfig",
    "ProfileConfig",
    "get_model_config",
    "load_model_config",
    # Domain memory config
    "DomainMemoryConfig",
    "DomainMetadata",
    "FactualConfig",
    "ExperientialConfig",
    "WorkingConfig",
    "LearningConfig",
    "LanguageConfig",
    "load_domain_config",
    "list_domains",
    "generate_domain_template",
    "save_domain_config",
    # Agent config
    "AgentType",
    "AgentMode",
    "AgentConfig",
    "get_agent_config",
    "get_parallel_groups",
]
