"""Unit tests for agent types configuration."""

from evalvault.config.agent_types import (
    ALL_AGENT_CONFIGS,
    DEVELOPMENT_AGENT_CONFIGS,
    OPERATION_AGENT_CONFIGS,
    AgentMode,
    AgentType,
    get_agent_config,
    get_critical_files,
    get_file_ownership,
    get_parallel_groups,
)


class TestAgentType:
    """Tests for AgentType enum."""

    def test_development_agents_returns_correct_types(self):
        """Development agents should include architecture, observability, etc."""
        dev_agents = AgentType.development_agents()

        assert AgentType.ARCHITECTURE in dev_agents
        assert AgentType.OBSERVABILITY in dev_agents
        assert AgentType.PERFORMANCE in dev_agents
        assert AgentType.TESTING in dev_agents
        assert AgentType.DOCUMENTATION in dev_agents
        assert AgentType.COORDINATOR in dev_agents

    def test_operation_agents_returns_correct_types(self):
        """Operation agents should include quality-monitor, domain-expert, etc."""
        op_agents = AgentType.operation_agents()

        assert AgentType.QUALITY_MONITOR in op_agents
        assert AgentType.DOMAIN_EXPERT in op_agents
        assert AgentType.TESTSET_CURATOR in op_agents
        assert AgentType.REPORT_GENERATOR in op_agents

    def test_development_and_operation_agents_are_disjoint(self):
        """Development and operation agents should not overlap."""
        dev_agents = set(AgentType.development_agents())
        op_agents = set(AgentType.operation_agents())

        assert dev_agents.isdisjoint(op_agents)

    def test_all_agents_are_categorized(self):
        """All agent types should be in either development or operation mode."""
        all_agents = set(AgentType)
        categorized = set(AgentType.development_agents()) | set(AgentType.operation_agents())

        assert all_agents == categorized

    def test_get_mode_for_development_agent(self):
        """get_mode should return DEVELOPMENT for dev agents."""
        assert AgentType.get_mode(AgentType.ARCHITECTURE) == AgentMode.DEVELOPMENT
        assert AgentType.get_mode(AgentType.TESTING) == AgentMode.DEVELOPMENT

    def test_get_mode_for_operation_agent(self):
        """get_mode should return OPERATION for op agents."""
        assert AgentType.get_mode(AgentType.QUALITY_MONITOR) == AgentMode.OPERATION
        assert AgentType.get_mode(AgentType.DOMAIN_EXPERT) == AgentMode.OPERATION


class TestAgentConfig:
    """Tests for AgentConfig and configuration retrieval."""

    def test_all_agent_configs_have_required_fields(self):
        """All agent configs should have name, description, and mode."""
        for agent_type, config in ALL_AGENT_CONFIGS.items():
            assert config.agent_type == agent_type
            assert config.name
            assert config.description
            assert config.mode in [AgentMode.DEVELOPMENT, AgentMode.OPERATION]

    def test_get_agent_config_returns_correct_config(self):
        """get_agent_config should return the correct configuration."""
        config = get_agent_config(AgentType.ARCHITECTURE)

        assert config.agent_type == AgentType.ARCHITECTURE
        assert config.name == "Architecture Agent"
        assert config.mode == AgentMode.DEVELOPMENT

    def test_get_agent_config_for_operation_agent(self):
        """get_agent_config should work for operation agents."""
        config = get_agent_config(AgentType.QUALITY_MONITOR)

        assert config.agent_type == AgentType.QUALITY_MONITOR
        assert config.mode == AgentMode.OPERATION
        assert "RagasEvaluator" in config.evalvault_services

    def test_development_configs_have_p_levels(self):
        """Development agent configs should have p_levels defined."""
        for agent_type, config in DEVELOPMENT_AGENT_CONFIGS.items():
            # Skip coordinator which has "All"
            if agent_type != AgentType.COORDINATOR:
                assert config.p_levels or agent_type == AgentType.WEB_UI_TESTING

    def test_operation_configs_have_evalvault_services(self):
        """Most operation agent configs should specify evalvault services."""
        configs_with_services = 0
        for config in OPERATION_AGENT_CONFIGS.values():
            if config.evalvault_services:
                configs_with_services += 1

        # Most operation agents should have services
        assert configs_with_services >= 5


class TestParallelGroups:
    """Tests for parallel execution groups."""

    def test_get_parallel_groups_returns_dict(self):
        """get_parallel_groups should return a dictionary."""
        groups = get_parallel_groups()

        assert isinstance(groups, dict)
        assert len(groups) > 0

    def test_get_parallel_groups_for_development_mode(self):
        """get_parallel_groups with DEVELOPMENT mode should return dev groups."""
        groups = get_parallel_groups(AgentMode.DEVELOPMENT)

        assert all(key.startswith("dev_") for key in groups)
        assert "dev_independent" in groups
        assert "dev_sequential" in groups

    def test_get_parallel_groups_for_operation_mode(self):
        """get_parallel_groups with OPERATION mode should return op groups."""
        groups = get_parallel_groups(AgentMode.OPERATION)

        assert all(key.startswith("op_") for key in groups)
        assert "op_independent" in groups

    def test_independent_group_agents_can_run_in_parallel(self):
        """Agents in independent groups should not have low independence."""
        groups = get_parallel_groups(AgentMode.DEVELOPMENT)

        for agent_type in groups.get("dev_independent", []):
            config = get_agent_config(agent_type)
            # Independent group agents should not be "low" (reserved for coordinator)
            assert config.independence in ("high", "medium")


class TestFileOwnership:
    """Tests for file ownership rules."""

    def test_get_file_ownership_returns_rules(self):
        """get_file_ownership should return ownership rules."""
        ownership = get_file_ownership()

        assert isinstance(ownership, dict)
        assert AgentType.ARCHITECTURE in ownership

    def test_architecture_agent_has_domain_access(self):
        """Architecture agent should have access to domain folder."""
        ownership = get_file_ownership()
        arch_rules = ownership.get(AgentType.ARCHITECTURE, {})

        assert "src/evalvault/domain/" in arch_rules.get("allowed", [])

    def test_testing_agent_cannot_modify_source(self):
        """Testing agent should not directly modify source code."""
        ownership = get_file_ownership()
        test_rules = ownership.get(AgentType.TESTING, {})

        assert "src/evalvault/" in test_rules.get("forbidden", [])


class TestCriticalFiles:
    """Tests for critical files list."""

    def test_get_critical_files_includes_pyproject(self):
        """Critical files should include pyproject.toml."""
        critical = get_critical_files()

        assert "pyproject.toml" in critical

    def test_get_critical_files_includes_improvement_plan(self):
        """Critical files should include IMPROVEMENT_PLAN.md."""
        critical = get_critical_files()

        assert "docs/IMPROVEMENT_PLAN.md" in critical
