"""
Memory System Integration
=========================

Integrates the agent infrastructure with the memory system
in agent/memory/ for persistent context and parallel coordination.

Reference: agent/memory/README.md
"""

import json
from datetime import datetime
from pathlib import Path

from config import AgentType, get_agent_config


class MemoryManager:
    """Manages agent memory for persistent context across sessions."""

    def __init__(self, project_dir: Path, agent_type: AgentType):
        self.project_dir = project_dir
        self.agent_type = agent_type
        self.config = get_agent_config(agent_type)

        # Paths
        self.memory_root = project_dir / "agent" / "memory"
        self.agent_memory = self.memory_root / "agents" / agent_type.value
        self.shared_memory = self.memory_root / "shared"
        self.templates = self.memory_root / "templates"

        # Ensure directories exist
        self.agent_memory.mkdir(parents=True, exist_ok=True)

    def get_latest_session(self) -> str | None:
        """Get the content of the latest session summary."""
        sessions = sorted(self.agent_memory.glob("session_*.md"))
        if sessions:
            return sessions[-1].read_text()
        return None

    def get_latest_work_log(self) -> str | None:
        """Get the content of the latest work log."""
        logs = sorted(self.agent_memory.glob("*_*.md"))
        # Filter out session files
        logs = [log for log in logs if not log.name.startswith("session_")]
        if logs:
            return logs[-1].read_text()
        return None

    def create_work_log(self, task_name: str) -> Path:
        """Create a new work log from template."""
        today = datetime.now().strftime("%Y-%m-%d")
        safe_name = task_name.lower().replace(" ", "-")[:30]
        filename = f"{today}_{safe_name}.md"
        work_log_path = self.agent_memory / filename

        # Load template
        template_path = self.templates / "work_log_template.md"
        if template_path.exists():
            content = template_path.read_text()
            # Replace placeholders
            content = content.replace("{agent-name}", self.agent_type.value)
            content = content.replace("[Task Name]", task_name)
            content = content.replace("YYYY-MM-DD", today)
        else:
            content = (
                f"# {task_name} Work Log\n\n**Agent**: {self.agent_type.value}\n**Date**: {today}\n"
            )

        work_log_path.write_text(content)
        return work_log_path

    def get_shared_decisions(self) -> str:
        """Get shared decisions document."""
        decisions_path = self.shared_memory / "decisions.md"
        if decisions_path.exists():
            return decisions_path.read_text()
        return ""

    def get_shared_dependencies(self) -> str:
        """Get shared dependencies document."""
        deps_path = self.shared_memory / "dependencies.md"
        if deps_path.exists():
            return deps_path.read_text()
        return ""

    def check_blocking_issues(self) -> list[dict]:
        """Check if there are any blocking issues for this agent."""
        deps_content = self.get_shared_dependencies()
        blocking = []

        # Parse dependencies.md for blocking issues
        # Look for lines like: | BLK-001 | Description | blocking_agent | this_agent | open |
        for line in deps_content.split("\n"):
            if f"| {self.agent_type.value} |" in line and "| open |" in line.lower():
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 4:
                    blocking.append(
                        {
                            "id": parts[0],
                            "description": parts[1],
                            "blocking_agent": parts[2],
                            "status": parts[4] if len(parts) > 4 else "open",
                        }
                    )

        return blocking

    def check_dependencies_ready(self) -> tuple[bool, list[str]]:
        """Check if all dependencies for this agent are ready.

        Returns:
            (ready, missing) tuple where ready is True if all deps are satisfied
        """
        from config import get_dependencies

        deps = get_dependencies(self.agent_type)
        missing = []

        for dep_type in deps:
            # Check if the dependency agent has completed its blocking work
            dep_memory = self.memory_root / "agents" / dep_type.value
            if not dep_memory.exists():
                missing.append(f"{dep_type.value} has not started work")
                continue

            # Check for completed session files
            sessions = list(dep_memory.glob("session_*.md"))
            if not sessions:
                missing.append(f"{dep_type.value} has no completed sessions")

        return len(missing) == 0, missing

    def get_context_for_prompt(self) -> str:
        """Generate context string for agent prompt based on memory."""
        context_parts = []

        # 1. Latest session/work log
        latest_session = self.get_latest_session()
        if latest_session:
            context_parts.append("## Previous Session Summary\n" + latest_session[:2000])

        latest_log = self.get_latest_work_log()
        if latest_log:
            context_parts.append("## Latest Work Log\n" + latest_log[:2000])

        # 2. Relevant decisions
        decisions = self.get_shared_decisions()
        if decisions:
            # Extract recent decisions (last 3)
            decision_blocks = decisions.split("### DEC-")
            recent = decision_blocks[-4:-1] if len(decision_blocks) > 3 else decision_blocks[1:]
            if recent:
                context_parts.append(
                    "## Recent Decisions\n" + "\n".join(["### DEC-" + d for d in recent])
                )

        # 3. Blocking issues
        blocking = self.check_blocking_issues()
        if blocking:
            context_parts.append("## Blocking Issues\n" + json.dumps(blocking, indent=2))

        # 4. Dependency status
        ready, missing = self.check_dependencies_ready()
        if not ready:
            context_parts.append(
                "## Dependency Status: NOT READY\n" + "\n".join(f"- {m}" for m in missing)
            )
        else:
            context_parts.append("## Dependency Status: READY\nAll dependencies satisfied.")

        return "\n\n---\n\n".join(context_parts)


class TaskManager:
    """Manages tasks from IMPROVEMENT_PLAN.md for the agent."""

    def __init__(self, project_dir: Path, agent_type: AgentType):
        self.project_dir = project_dir
        self.agent_type = agent_type
        self.config = get_agent_config(agent_type)
        self.feature_list_path = project_dir / self.config.feature_list_file

    def load_tasks(self) -> list[dict]:
        """Load tasks from feature_list.json."""
        if not self.feature_list_path.exists():
            return []

        try:
            with open(self.feature_list_path) as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save_tasks(self, tasks: list[dict]) -> None:
        """Save tasks to feature_list.json."""
        with open(self.feature_list_path, "w") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

    def get_next_task(self) -> dict | None:
        """Get the next incomplete task."""
        tasks = self.load_tasks()
        for task in tasks:
            if not task.get("passes", False):
                return task
        return None

    def mark_task_complete(self, task_description: str) -> None:
        """Mark a task as complete."""
        tasks = self.load_tasks()
        for task in tasks:
            if task.get("description") == task_description:
                task["passes"] = True
                task["completed_at"] = datetime.now().isoformat()
                break
        self.save_tasks(tasks)

    def get_progress(self) -> tuple[int, int]:
        """Get (completed, total) task counts."""
        tasks = self.load_tasks()
        completed = sum(1 for t in tasks if t.get("passes", False))
        return completed, len(tasks)

    def create_tasks_from_improvement_plan(self) -> list[dict]:
        """Create tasks from IMPROVEMENT_PLAN.md for this agent type."""
        tasks = []
        p_levels = self.config.p_levels

        # Map P-levels to task templates
        task_templates = {
            "P0": [
                {
                    "category": "architecture",
                    "description": "Verify domain ↔ adapter dependency inversion",
                    "steps": [
                        "Run: rg 'from evalvault.adapters' src/evalvault/domain",
                        "Ensure 0 results (no adapter imports in domain)",
                        "Document any violations found",
                    ],
                },
            ],
            "P1": [
                {
                    "category": "architecture",
                    "description": "Complete LLM Adapter integration (BaseLLMAdapter)",
                    "steps": [
                        "Review current LLM adapter implementations",
                        "Create BaseLLMAdapter with common logic",
                        "Refactor OpenAI/Azure/Anthropic adapters",
                        "Run tests to verify",
                    ],
                },
            ],
            "P3": [
                {
                    "category": "performance",
                    "description": "Implement LRU+TTL hybrid cache",
                    "steps": [
                        "Analyze current MemoryCacheAdapter",
                        "Implement HybridCache with LRU eviction",
                        "Add TTL support",
                        "Benchmark cache hit rate",
                    ],
                },
            ],
            "P5": [
                {
                    "category": "testing",
                    "description": "Optimize slow tests",
                    "steps": [
                        "Profile test execution time",
                        "Identify tests > 1s",
                        "Add @pytest.mark.slow markers",
                        "Improve mock usage",
                    ],
                },
            ],
            "P6": [
                {
                    "category": "documentation",
                    "description": "Create Phoenix integration tutorial",
                    "steps": [
                        "Write docs/tutorials/04-phoenix-integration.md",
                        "Include installation steps",
                        "Add code examples",
                        "Test instructions",
                    ],
                },
            ],
            "P7": [
                {
                    "category": "observability",
                    "description": "Integrate Phoenix basic tracing",
                    "steps": [
                        "Install arize-phoenix and openinference packages",
                        "Create setup_phoenix_instrumentation() function",
                        "Add CLI option --enable-phoenix",
                        "Test with simple evaluation",
                    ],
                },
                {
                    "category": "rag-data",
                    "description": "Implement RetrievalData entity",
                    "steps": [
                        "Create src/evalvault/domain/entities/retrieval.py",
                        "Define RetrievalData and RetrievedDocument dataclasses",
                        "Add Precision@K calculation method",
                        "Write unit tests",
                    ],
                },
            ],
        }

        for p_level in p_levels:
            if p_level in task_templates:
                for template in task_templates[p_level]:
                    # Only include tasks matching this agent's category
                    if template["category"] == self.agent_type.value or p_level == "All":
                        task = {
                            **template,
                            "passes": False,
                            "p_level": p_level,
                            "agent": self.agent_type.value,
                        }
                        tasks.append(task)

        return tasks


def setup_agent_memory(project_dir: Path, agent_type: AgentType) -> MemoryManager:
    """Set up memory manager for an agent."""
    return MemoryManager(project_dir, agent_type)


def get_agent_context(project_dir: Path, agent_type: AgentType) -> str:
    """Get full context for an agent including memory and tasks."""
    memory = MemoryManager(project_dir, agent_type)
    tasks = TaskManager(project_dir, agent_type)

    parts = []

    # Memory context
    memory_context = memory.get_context_for_prompt()
    if memory_context:
        parts.append(memory_context)

    # Task context
    next_task = tasks.get_next_task()
    completed, total = tasks.get_progress()

    parts.append(f"## Task Progress: {completed}/{total}")
    if next_task:
        parts.append(f"## Next Task\n{json.dumps(next_task, indent=2)}")
    else:
        parts.append("## All tasks complete!")

    return "\n\n---\n\n".join(parts)
