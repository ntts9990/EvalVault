"""
Prompt Loading Utilities
========================

Functions for loading prompt templates from the prompts directory.
Supports both legacy Web UI testing prompts and new improvement agent prompts.

Reference: https://github.com/seolcoding/nonstop-agent (MIT License)
"""

import shutil
from pathlib import Path

from config import AgentType, get_agent_config

PROMPTS_DIR = Path(__file__).parent / "prompts"
IMPROVEMENT_PROMPTS_DIR = PROMPTS_DIR / "improvement"


def load_prompt(name: str, subdir: str | None = None) -> str:
    """Load a prompt template from the prompts directory.

    Args:
        name: Name of the prompt file (without .md extension)
        subdir: Optional subdirectory (e.g., "improvement")

    Returns:
        Content of the prompt file
    """
    prompt_path = PROMPTS_DIR / subdir / f"{name}.md" if subdir else PROMPTS_DIR / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")

    return prompt_path.read_text()


# Legacy prompts (Web UI testing)
def get_initializer_prompt() -> str:
    """Load the initializer prompt (legacy Web UI testing)."""
    return load_prompt("initializer_prompt")


def get_coding_prompt() -> str:
    """Load the coding agent prompt (legacy Web UI testing)."""
    return load_prompt("coding_prompt")


def get_existing_project_prompt() -> str:
    """Load the existing project analysis prompt (legacy)."""
    return load_prompt("existing_project_prompt")


def copy_spec_to_project(project_dir: Path) -> None:
    """Copy the app spec file into the project directory."""
    spec_source = PROMPTS_DIR / "app_spec.txt"
    spec_dest = project_dir / "app_spec.txt"
    if spec_source.exists() and not spec_dest.exists():
        shutil.copy(spec_source, spec_dest)
        print("Copied app_spec.txt to project directory")


# New improvement agent prompts
def get_agent_prompt(agent_type: AgentType, memory_context: str = "") -> str:
    """Get the prompt for a specific agent type.

    Args:
        agent_type: Type of agent (architecture, observability, etc.)
        memory_context: Optional context from memory system

    Returns:
        Formatted prompt for the agent
    """
    config = get_agent_config(agent_type)

    # Try to load specific prompt first
    prompt_name = f"{agent_type.value}_prompt"
    try:
        base_content = load_prompt(prompt_name, subdir="improvement")
    except FileNotFoundError:
        # Fall back to base prompt with substitutions
        base_content = load_prompt("base_prompt", subdir="improvement")

        # Apply substitutions
        base_content = base_content.replace("{AGENT_NAME}", config.name)
        base_content = base_content.replace("{AGENT_TYPE}", agent_type.value)
        base_content = base_content.replace("{FOCUS_AREAS}", config.description)
        base_content = base_content.replace("{P_LEVELS}", ", ".join(config.p_levels))

        # Determine commit prefix
        prefix_map = {
            AgentType.ARCHITECTURE: "refactor",
            AgentType.OBSERVABILITY: "feat",
            AgentType.RAG_DATA: "feat",
            AgentType.PERFORMANCE: "perf",
            AgentType.TESTING: "test",
            AgentType.DOCUMENTATION: "docs",
            AgentType.COORDINATOR: "chore",
        }
        commit_prefix = prefix_map.get(agent_type, "chore")
        base_content = base_content.replace("{COMMIT_PREFIX}", commit_prefix)

    # Add memory context
    if memory_context:
        base_content = base_content.replace("{MEMORY_CONTEXT}", memory_context)
    else:
        base_content = base_content.replace("{MEMORY_CONTEXT}", "No previous context available.")

    return base_content


def get_coordinator_prompt() -> str:
    """Get the coordinator agent prompt."""
    return get_agent_prompt(AgentType.COORDINATOR)


def get_architecture_prompt(memory_context: str = "") -> str:
    """Get the architecture agent prompt."""
    return get_agent_prompt(AgentType.ARCHITECTURE, memory_context)


def get_observability_prompt(memory_context: str = "") -> str:
    """Get the observability agent prompt."""
    return get_agent_prompt(AgentType.OBSERVABILITY, memory_context)


def get_rag_data_prompt(memory_context: str = "") -> str:
    """Get the RAG data agent prompt."""
    return get_agent_prompt(AgentType.RAG_DATA, memory_context)


def get_performance_prompt(memory_context: str = "") -> str:
    """Get the performance agent prompt."""
    return get_agent_prompt(AgentType.PERFORMANCE, memory_context)


def get_testing_prompt(memory_context: str = "") -> str:
    """Get the testing agent prompt."""
    return get_agent_prompt(AgentType.TESTING, memory_context)


def get_documentation_prompt(memory_context: str = "") -> str:
    """Get the documentation agent prompt."""
    return get_agent_prompt(AgentType.DOCUMENTATION, memory_context)
