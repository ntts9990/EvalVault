"""
Progress Tracking Utilities
===========================

Functions for tracking and displaying progress of the autonomous agent.
Integrated with the memory system for persistent context.

Reference: https://github.com/seolcoding/nonstop-agent (MIT License)
"""

import json
from datetime import datetime
from pathlib import Path

from config import AgentType, get_agent_config

SESSION_FILE = "claude_session.json"


def count_passing_tests(project_dir: Path) -> tuple[int, int]:
    """
    Count passing and total tests in feature_list.json.

    Args:
        project_dir: Directory containing feature_list.json

    Returns:
        (passing_count, total_count)
    """
    tests_file = project_dir / "feature_list.json"

    if not tests_file.exists():
        return 0, 0

    try:
        with open(tests_file) as f:
            tests = json.load(f)

        total = len(tests)
        passing = sum(1 for test in tests if test.get("passes", False))

        return passing, total
    except (OSError, json.JSONDecodeError):
        return 0, 0


def count_agent_tasks(project_dir: Path, agent_type: AgentType) -> tuple[int, int]:
    """Count tasks for a specific agent type.

    Args:
        project_dir: Project directory
        agent_type: Type of agent

    Returns:
        (completed, total) task counts for this agent
    """
    tests_file = project_dir / "feature_list.json"

    if not tests_file.exists():
        return 0, 0

    try:
        with open(tests_file) as f:
            tests = json.load(f)

        agent_tests = [t for t in tests if t.get("agent") == agent_type.value]
        total = len(agent_tests)
        completed = sum(1 for t in agent_tests if t.get("passes", False))

        return completed, total
    except (OSError, json.JSONDecodeError):
        return 0, 0


def print_session_header(
    session_num: int, session_type: str, agent_type: AgentType | None = None
) -> None:
    """Print a formatted header for the session."""
    type_labels = {
        "analysis": "EXISTING PROJECT ANALYSIS",
        "initializer": "INITIALIZER AGENT",
        "coding": "CODING AGENT",
        # New improvement agent types
        "architecture": "ARCHITECTURE AGENT",
        "observability": "OBSERVABILITY AGENT",
        "rag-data": "RAG DATA AGENT",
        "performance": "PERFORMANCE AGENT",
        "testing": "TESTING AGENT",
        "documentation": "DOCUMENTATION AGENT",
        "coordinator": "COORDINATOR AGENT",
    }

    if agent_type:
        label = type_labels.get(agent_type.value, agent_type.value.upper())
        config = get_agent_config(agent_type)
        description = config.description
    else:
        label = type_labels.get(session_type, session_type.upper())
        description = ""

    print("\n" + "=" * 70)
    print(f"  SESSION {session_num}: {label}")
    if description:
        print(f"  {description}")
    print("=" * 70)
    print()


def print_progress_summary(project_dir: Path, agent_type: AgentType | None = None) -> None:
    """Print a summary of current progress."""
    if agent_type:
        # Agent-specific progress
        completed, total = count_agent_tasks(project_dir, agent_type)
        config = get_agent_config(agent_type)

        print(f"\n{config.name} Progress:")
        if total > 0:
            percentage = (completed / total) * 100
            print(f"  Tasks: {completed}/{total} ({percentage:.1f}%)")
        else:
            print("  No tasks assigned yet")

        # Check dependencies
        deps = config.dependencies
        if deps:
            print(f"  Dependencies: {', '.join(d.value for d in deps)}")
    else:
        # Overall progress
        passing, total = count_passing_tests(project_dir)

        if total > 0:
            percentage = (passing / total) * 100
            print(f"\nProgress: {passing}/{total} tests passing ({percentage:.1f}%)")
        else:
            print("\nProgress: feature_list.json not yet created")


def print_all_agents_status(project_dir: Path) -> None:
    """Print status of all agents."""
    print("\n" + "=" * 70)
    print("  ALL AGENTS STATUS")
    print("=" * 70)

    agent_types = [
        AgentType.ARCHITECTURE,
        AgentType.OBSERVABILITY,
        AgentType.RAG_DATA,
        AgentType.PERFORMANCE,
        AgentType.TESTING,
        AgentType.DOCUMENTATION,
    ]

    for agent_type in agent_types:
        completed, total = count_agent_tasks(project_dir, agent_type)
        config = get_agent_config(agent_type)

        if total > 0:
            percentage = (completed / total) * 100
            status = f"{completed}/{total} ({percentage:.0f}%)"
        else:
            status = "No tasks"

        independence = config.independence
        print(f"  {agent_type.value:15} | {status:15} | Independence: {independence}")

    print("=" * 70)


def save_session_id(
    project_dir: Path, session_id: str, agent_type: AgentType | None = None
) -> None:
    """Save session ID for later resumption."""
    session_file = project_dir / SESSION_FILE
    try:
        # Load existing data
        existing = {}
        if session_file.exists():
            with open(session_file) as f:
                existing = json.load(f)

        # Update with new session
        existing["session_id"] = session_id
        existing["updated_at"] = datetime.now().isoformat()

        if agent_type:
            existing["agent_type"] = agent_type.value
            existing.setdefault("agent_sessions", {})[agent_type.value] = session_id

        with open(session_file, "w") as f:
            json.dump(existing, f, indent=2)

    except OSError as e:
        print(f"Warning: Could not save session ID: {e}")


def load_session_id(project_dir: Path, agent_type: AgentType | None = None) -> str | None:
    """Load saved session ID."""
    session_file = project_dir / SESSION_FILE
    if session_file.exists():
        try:
            with open(session_file) as f:
                data = json.load(f)

            # If agent type specified, try to get agent-specific session
            if agent_type:
                agent_sessions = data.get("agent_sessions", {})
                if agent_type.value in agent_sessions:
                    return agent_sessions[agent_type.value]

            return data.get("session_id")
        except (OSError, json.JSONDecodeError):
            pass
    return None


def update_session_memory(project_dir: Path, agent_type: AgentType, summary: str) -> None:
    """Update the agent's memory with session summary.

    Args:
        project_dir: Project directory
        agent_type: Type of agent
        summary: Summary of the session
    """
    memory_dir = project_dir / "agent" / "memory" / "agents" / agent_type.value
    memory_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    session_file = memory_dir / f"session_{today}.md"

    timestamp = datetime.now().strftime("%H:%M")

    content = f"""# Session Summary - {datetime.now().strftime("%Y-%m-%d")}

## Update at {timestamp}

{summary}

---

"""

    # Append to existing or create new
    mode = "a" if session_file.exists() else "w"
    with open(session_file, mode) as f:
        f.write(content)
