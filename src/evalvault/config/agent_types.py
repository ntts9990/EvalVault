"""
Agent Types and Configuration
=============================

Shared agent type definitions for both development and operation modes.

## Usage Modes

1. **Development Mode** (agent/ folder)
   - Used by developers to improve EvalVault code
   - External tool, not shipped with PyPI package
   - Uses Claude Agent SDK

2. **Operation Mode** (evalvault CLI)
   - Used by end users to automate evaluation workflows
   - Part of the core product, shipped with PyPI
   - Uses EvalVault's domain services

## OSS Distribution Notes

- This module is part of the core evalvault package
- Development tools in agent/ folder are NOT included in PyPI distribution
- Operation agents are available via `evalvault agent` CLI commands
"""

from dataclasses import dataclass, field
from enum import Enum


class AgentMode(str, Enum):
    """Agent operation modes.

    - DEVELOPMENT: For improving EvalVault code (agent/ folder)
    - OPERATION: For automating evaluation workflows (evalvault CLI)
    """

    DEVELOPMENT = "development"
    OPERATION = "operation"


class AgentType(str, Enum):
    """Available agent types.

    Development mode agents:
    - ARCHITECTURE through COORDINATOR: Code improvement agents

    Operation mode agents:
    - QUALITY_MONITOR through DATA_VALIDATOR: Evaluation automation agents
    """

    # ========================================
    # Development Mode Agents (agent/ folder)
    # ========================================
    ARCHITECTURE = "architecture"
    OBSERVABILITY = "observability"
    RAG_DATA = "rag-data"
    PERFORMANCE = "performance"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    COORDINATOR = "coordinator"
    WEB_UI_TESTING = "web-ui-testing"

    # ========================================
    # Operation Mode Agents (evalvault CLI)
    # ========================================
    QUALITY_MONITOR = "quality-monitor"
    DOMAIN_EXPERT = "domain-expert"
    TESTSET_CURATOR = "testset-curator"
    EVAL_COORDINATOR = "eval-coordinator"
    EXPERIMENT_ANALYST = "experiment-analyst"
    REPORT_GENERATOR = "report-generator"
    DATA_VALIDATOR = "data-validator"

    @classmethod
    def development_agents(cls) -> list["AgentType"]:
        """Get all development mode agents."""
        return [
            cls.ARCHITECTURE,
            cls.OBSERVABILITY,
            cls.RAG_DATA,
            cls.PERFORMANCE,
            cls.TESTING,
            cls.DOCUMENTATION,
            cls.COORDINATOR,
            cls.WEB_UI_TESTING,
        ]

    @classmethod
    def operation_agents(cls) -> list["AgentType"]:
        """Get all operation mode agents."""
        return [
            cls.QUALITY_MONITOR,
            cls.DOMAIN_EXPERT,
            cls.TESTSET_CURATOR,
            cls.EVAL_COORDINATOR,
            cls.EXPERIMENT_ANALYST,
            cls.REPORT_GENERATOR,
            cls.DATA_VALIDATOR,
        ]

    @classmethod
    def get_mode(cls, agent_type: "AgentType") -> AgentMode:
        """Get the mode for a given agent type."""
        if agent_type in cls.development_agents():
            return AgentMode.DEVELOPMENT
        return AgentMode.OPERATION


@dataclass
class AgentConfig:
    """Configuration for an agent type.

    Attributes:
        agent_type: The agent type enum value
        name: Human-readable name
        description: Brief description of the agent's purpose
        mode: Whether this is a development or operation agent
        p_levels: Priority levels this agent handles (from IMPROVEMENT_PLAN.md)
        independence: How independently this agent can run ("high", "medium", "low")
        dependencies: Other agents this one depends on
        primary_files: Main files/directories this agent works with
        evalvault_services: EvalVault services this agent uses (for operation mode)
    """

    agent_type: AgentType
    name: str
    description: str
    mode: AgentMode = AgentMode.OPERATION

    # Priority levels from IMPROVEMENT_PLAN.md
    p_levels: list[str] = field(default_factory=list)

    # Independence level for parallel execution
    independence: str = "high"

    # Dependencies on other agents
    dependencies: list[AgentType] = field(default_factory=list)

    # Files this agent primarily works with
    primary_files: list[str] = field(default_factory=list)

    # EvalVault services this agent uses (for operation mode)
    evalvault_services: list[str] = field(default_factory=list)


# ========================================
# Development Mode Agent Configurations
# ========================================

DEVELOPMENT_AGENT_CONFIGS: dict[AgentType, AgentConfig] = {
    AgentType.ARCHITECTURE: AgentConfig(
        agent_type=AgentType.ARCHITECTURE,
        name="Architecture Agent",
        description="Code structure, dependency injection, Hexagonal Architecture",
        mode=AgentMode.DEVELOPMENT,
        p_levels=["P0", "P1", "P2"],
        independence="high",
        primary_files=[
            "src/evalvault/domain/",
            "src/evalvault/ports/",
            "src/evalvault/adapters/",
        ],
    ),
    AgentType.OBSERVABILITY: AgentConfig(
        agent_type=AgentType.OBSERVABILITY,
        name="Observability Agent",
        description="Phoenix integration, OpenTelemetry, metrics collection",
        mode=AgentMode.DEVELOPMENT,
        p_levels=["P7"],
        independence="medium",
        primary_files=["src/evalvault/adapters/outbound/tracker/"],
    ),
    AgentType.RAG_DATA: AgentConfig(
        agent_type=AgentType.RAG_DATA,
        name="RAG Data Agent",
        description="RAG data collection, retrieval/generation tracking",
        mode=AgentMode.DEVELOPMENT,
        p_levels=["P7"],
        independence="medium",
        dependencies=[AgentType.OBSERVABILITY],
        primary_files=["src/evalvault/domain/entities/"],
    ),
    AgentType.PERFORMANCE: AgentConfig(
        agent_type=AgentType.PERFORMANCE,
        name="Performance Agent",
        description="Caching, batch processing, async optimization",
        mode=AgentMode.DEVELOPMENT,
        p_levels=["P3"],
        independence="high",
        primary_files=["src/evalvault/adapters/outbound/cache/"],
    ),
    AgentType.TESTING: AgentConfig(
        agent_type=AgentType.TESTING,
        name="Testing Agent",
        description="Test optimization, coverage, mock improvements",
        mode=AgentMode.DEVELOPMENT,
        p_levels=["P5"],
        independence="medium",
        primary_files=["tests/"],
    ),
    AgentType.DOCUMENTATION: AgentConfig(
        agent_type=AgentType.DOCUMENTATION,
        name="Documentation Agent",
        description="Tutorials, API docs, user guides",
        mode=AgentMode.DEVELOPMENT,
        p_levels=["P6"],
        independence="high",
        primary_files=["docs/"],
    ),
    AgentType.COORDINATOR: AgentConfig(
        agent_type=AgentType.COORDINATOR,
        name="Coordinator Agent",
        description="Integration management, conflict resolution, progress tracking",
        mode=AgentMode.DEVELOPMENT,
        p_levels=["All"],
        independence="low",
        primary_files=["agent/memory/", "docs/IMPROVEMENT_PLAN.md"],
    ),
    AgentType.WEB_UI_TESTING: AgentConfig(
        agent_type=AgentType.WEB_UI_TESTING,
        name="Web UI Testing Agent",
        description="Integration tests for Web UI (legacy)",
        mode=AgentMode.DEVELOPMENT,
        independence="high",
        primary_files=["src/evalvault/adapters/inbound/web/", "tests/integration/"],
    ),
}


# ========================================
# Operation Mode Agent Configurations
# ========================================

OPERATION_AGENT_CONFIGS: dict[AgentType, AgentConfig] = {
    AgentType.QUALITY_MONITOR: AgentConfig(
        agent_type=AgentType.QUALITY_MONITOR,
        name="Quality Monitor",
        description="Scheduled evaluation, regression detection, alerting",
        mode=AgentMode.OPERATION,
        independence="high",
        evalvault_services=["RagasEvaluator", "BenchmarkRunner", "AnalysisService"],
    ),
    AgentType.DOMAIN_EXPERT: AgentConfig(
        agent_type=AgentType.DOMAIN_EXPERT,
        name="Domain Expert",
        description="Domain terminology learning, reliability scoring",
        mode=AgentMode.OPERATION,
        independence="high",
        evalvault_services=["DomainLearningHook", "EntityExtractor"],
    ),
    AgentType.TESTSET_CURATOR: AgentConfig(
        agent_type=AgentType.TESTSET_CURATOR,
        name="Testset Curator",
        description="Gap analysis, test case generation, distribution balancing",
        mode=AgentMode.OPERATION,
        independence="medium",
        dependencies=[AgentType.QUALITY_MONITOR],
        evalvault_services=["TestsetGenerator", "KGGenerator", "AnalysisService"],
    ),
    AgentType.EVAL_COORDINATOR: AgentConfig(
        agent_type=AgentType.EVAL_COORDINATOR,
        name="Evaluation Coordinator",
        description="Multi-domain evaluation orchestration",
        mode=AgentMode.OPERATION,
        independence="low",
        evalvault_services=["RagasEvaluator", "ExperimentManager"],
    ),
    AgentType.EXPERIMENT_ANALYST: AgentConfig(
        agent_type=AgentType.EXPERIMENT_ANALYST,
        name="Experiment Analyst",
        description="A/B test analysis, statistical significance testing",
        mode=AgentMode.OPERATION,
        independence="medium",
        evalvault_services=["ExperimentManager", "AnalysisService"],
    ),
    AgentType.REPORT_GENERATOR: AgentConfig(
        agent_type=AgentType.REPORT_GENERATOR,
        name="Report Generator",
        description="Automated report generation, stakeholder notifications",
        mode=AgentMode.OPERATION,
        independence="high",
        evalvault_services=["AnalysisService", "ImprovementGuideService"],
    ),
    AgentType.DATA_VALIDATOR: AgentConfig(
        agent_type=AgentType.DATA_VALIDATOR,
        name="Data Validator",
        description="Dataset quality validation, schema checking",
        mode=AgentMode.OPERATION,
        independence="high",
        evalvault_services=[],
    ),
}


# Combined configurations
ALL_AGENT_CONFIGS: dict[AgentType, AgentConfig] = {
    **DEVELOPMENT_AGENT_CONFIGS,
    **OPERATION_AGENT_CONFIGS,
}


def get_agent_config(agent_type: AgentType) -> AgentConfig:
    """Get configuration for an agent type.

    Args:
        agent_type: The agent type to get configuration for

    Returns:
        AgentConfig for the specified type

    Raises:
        KeyError: If agent type is not found
    """
    return ALL_AGENT_CONFIGS[agent_type]


def get_parallel_groups(mode: AgentMode | None = None) -> dict[str, list[AgentType]]:
    """Get agent groups that can run in parallel.

    Args:
        mode: Filter by mode (None for all)

    Returns:
        Dict mapping group names to lists of agent types
    """
    groups = {
        # Development mode groups
        "dev_independent": [
            AgentType.PERFORMANCE,
            AgentType.TESTING,
            AgentType.DOCUMENTATION,
        ],
        "dev_sequential": [
            AgentType.OBSERVABILITY,
            AgentType.RAG_DATA,
        ],
        "dev_architecture": [AgentType.ARCHITECTURE],
        # Operation mode groups
        "op_independent": [
            AgentType.QUALITY_MONITOR,
            AgentType.DOMAIN_EXPERT,
            AgentType.REPORT_GENERATOR,
            AgentType.DATA_VALIDATOR,
        ],
        "op_dependent": [
            AgentType.TESTSET_CURATOR,
            AgentType.EXPERIMENT_ANALYST,
        ],
        "op_coordinator": [AgentType.EVAL_COORDINATOR],
    }

    if mode == AgentMode.DEVELOPMENT:
        return {k: v for k, v in groups.items() if k.startswith("dev_")}
    elif mode == AgentMode.OPERATION:
        return {k: v for k, v in groups.items() if k.startswith("op_")}
    return groups


def get_file_ownership() -> dict[AgentType, dict[str, list[str]]]:
    """Get file ownership rules for conflict prevention.

    Returns:
        Dict mapping agent types to allowed/forbidden paths
    """
    return {
        AgentType.ARCHITECTURE: {
            "allowed": [
                "src/evalvault/domain/",
                "src/evalvault/adapters/outbound/llm/",
                "src/evalvault/adapters/outbound/storage/",
            ],
            "forbidden": ["src/evalvault/adapters/inbound/web/"],
        },
        AgentType.OBSERVABILITY: {
            "allowed": ["src/evalvault/adapters/outbound/tracker/"],
            "forbidden": ["src/evalvault/domain/services/"],
        },
        AgentType.PERFORMANCE: {
            "allowed": ["src/evalvault/adapters/outbound/cache/"],
            "forbidden": ["src/evalvault/domain/entities/"],
        },
        AgentType.TESTING: {
            "allowed": ["tests/"],
            "forbidden": ["src/evalvault/"],
        },
        AgentType.DOCUMENTATION: {
            "allowed": ["docs/"],
            "forbidden": ["src/"],
        },
        AgentType.RAG_DATA: {
            "allowed": ["src/evalvault/domain/entities/"],
            "forbidden": [],
        },
    }


def get_critical_files() -> list[str]:
    """Get files that require coordinator approval to modify."""
    return [
        "pyproject.toml",
        "src/evalvault/__init__.py",
        "src/evalvault/config/settings.py",
        "docs/IMPROVEMENT_PLAN.md",
        "docs/AGENT_STRATEGY.md",
    ]
