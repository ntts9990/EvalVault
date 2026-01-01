"""
Agent Session Logic
===================

Core agent interaction functions for running autonomous coding sessions.
Supports both legacy Web UI testing mode and new improvement agent types.

Reference:
- https://platform.claude.com/docs/en/agent-sdk/python
- https://platform.claude.com/docs/en/agent-sdk/sessions
- https://github.com/seolcoding/nonstop-agent (MIT License)
"""

import asyncio
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
)
from client import create_client
from memory_integration import MemoryManager, TaskManager, get_agent_context
from progress import (
    load_session_id,
    print_all_agents_status,
    print_progress_summary,
    print_session_header,
    save_session_id,
    update_session_memory,
)
from prompts import (
    copy_spec_to_project,
    get_agent_prompt,
    get_coding_prompt,
    get_existing_project_prompt,
    get_initializer_prompt,
)

from config import AgentType, get_agent_config

# Configuration
AUTO_CONTINUE_DELAY_SECONDS = 3
SESSION_FILE = "claude_session.json"


def get_prompt_for_agent_type(
    agent_type: AgentType,
    project_dir: Path,
) -> str:
    """Get the appropriate prompt for an agent type with memory context.

    Args:
        agent_type: Type of agent
        project_dir: Project directory

    Returns:
        Formatted prompt with memory context
    """
    # Get memory context
    memory_context = get_agent_context(project_dir, agent_type)

    # Get agent-specific prompt
    return get_agent_prompt(agent_type, memory_context)


async def run_agent_session(
    client: ClaudeSDKClient,
    message: str,
    project_dir: Path,
) -> tuple[str, str, str | None]:
    """
    Run a single agent session using Claude Agent SDK.

    Args:
        client: Claude SDK client
        message: The prompt to send
        project_dir: Project directory path

    Returns:
        (status, response_text, session_id) where status is:
        - "continue" if agent should continue working
        - "error" if an error occurred
    """
    print("Sending prompt to Claude Agent SDK...\n")

    session_id = None

    try:
        await client.query(message)

        response_text = ""
        async for msg in client.receive_response():
            # Capture session ID from init message
            if hasattr(msg, "subtype") and msg.subtype == "init":
                if hasattr(msg, "session_id"):
                    session_id = msg.session_id
                elif hasattr(msg, "data"):
                    session_id = msg.data.get("session_id")

            # Handle AssistantMessage (text and tool use)
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
                        print(block.text, end="", flush=True)
                    elif isinstance(block, ToolUseBlock):
                        print(f"\n[Tool: {block.name}]", flush=True)
                        if hasattr(block, "input"):
                            input_str = str(block.input)
                            if len(input_str) > 200:
                                print(f"   Input: {input_str[:200]}...", flush=True)
                            else:
                                print(f"   Input: {input_str}", flush=True)

            # Handle tool results
            elif hasattr(msg, "content"):
                for block in msg.content if isinstance(msg.content, list) else []:
                    if isinstance(block, ToolResultBlock):
                        is_error = getattr(block, "is_error", False)
                        result_content = getattr(block, "content", "")

                        if "blocked" in str(result_content).lower():
                            print(f"   [BLOCKED] {result_content}", flush=True)
                        elif is_error:
                            error_str = str(result_content)[:500]
                            print(f"   [Error] {error_str}", flush=True)
                        else:
                            print("   [Done]", flush=True)

            # Handle result message
            if isinstance(msg, ResultMessage) and hasattr(msg, "session_id"):
                session_id = msg.session_id

        print("\n" + "-" * 70 + "\n")

        # Save session ID for future resumption
        if session_id:
            save_session_id(project_dir, session_id)

        return "continue", response_text, session_id

    except Exception as e:
        print(f"Error during agent session: {e}")
        return "error", str(e), session_id


async def run_autonomous_agent(
    project_dir: Path,
    model: str,
    max_iterations: int | None = None,
    analyze_first: bool = False,
    resume: bool = False,
    agent_type: AgentType | None = None,
) -> None:
    """
    Run the autonomous agent loop.

    Args:
        project_dir: Directory for the project
        model: Claude model to use
        max_iterations: Maximum number of iterations (None for unlimited)
        analyze_first: Whether to analyze existing project first
        resume: Whether to resume from last session
        agent_type: Optional specific agent type (architecture, observability, etc.)
                   If None, runs legacy Web UI testing mode
    """
    # Header based on mode
    if agent_type:
        config = get_agent_config(agent_type)
        print("\n" + "=" * 70)
        print(f"  {config.name.upper()}")
        print(f"  {config.description}")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("  AUTONOMOUS AGENT (Legacy Mode)")
        print("=" * 70)

    print(f"\nProject directory: {project_dir}")
    print(f"Model: {model}")
    if max_iterations:
        print(f"Max iterations: {max_iterations}")
    else:
        print("Max iterations: Unlimited")
    if analyze_first:
        print("Mode: Analyze existing project first")
    if resume:
        print("Mode: Resume from last session")
    if agent_type:
        print(f"Agent type: {agent_type.value}")
    print()

    project_dir.mkdir(parents=True, exist_ok=True)

    # Initialize memory manager for improvement agents
    memory_manager = None
    task_manager = None
    if agent_type:
        memory_manager = MemoryManager(project_dir, agent_type)
        task_manager = TaskManager(project_dir, agent_type)

        # Check dependencies for this agent
        ready, missing = memory_manager.check_dependencies_ready()
        if not ready:
            print("=" * 70)
            print("  WARNING: DEPENDENCIES NOT READY")
            print("=" * 70)
            for m in missing:
                print(f"  - {m}")
            print()
            print("You may want to run the dependency agent first, or continue anyway.")
            print()

        # Check for blocking issues
        blocking = memory_manager.check_blocking_issues()
        if blocking:
            print("=" * 70)
            print("  WARNING: BLOCKING ISSUES DETECTED")
            print("=" * 70)
            for b in blocking:
                print(f"  - {b['id']}: {b['description']}")
            print()

        # Show task progress
        completed, total = task_manager.get_progress()
        if total > 0:
            pct = (completed / total) * 100
            print(f"Task Progress: {completed}/{total} ({pct:.1f}%)")
        else:
            print("No tasks loaded yet. Will initialize from IMPROVEMENT_PLAN.md")

    # Check for session resumption
    resume_session_id = None
    if resume:
        resume_session_id = load_session_id(project_dir, agent_type)
        if resume_session_id:
            print(f"Resuming session: {resume_session_id}")
        else:
            print("No previous session found, starting fresh")

    # Determine session type (for legacy mode)
    tests_file = project_dir / "feature_list.json"
    is_first_run = not tests_file.exists() and not resume_session_id
    needs_analysis = analyze_first and is_first_run

    if not agent_type:
        # Legacy mode messages
        if needs_analysis:
            print("=" * 70)
            print("  EXISTING PROJECT ANALYSIS MODE")
            print("  Will analyze, run tests, then create feature_list.json")
            print("=" * 70)
            print()
        elif is_first_run:
            print("Fresh start - will use initializer agent")
            print()
            print("=" * 70)
            print("  NOTE: First session may take 10-20+ minutes!")
            print("  The agent is generating detailed test cases.")
            print("=" * 70)
            print()
            copy_spec_to_project(project_dir)
        else:
            print("Continuing existing project")
            print_progress_summary(project_dir)

    # Main loop
    iteration = 0
    current_session_id = resume_session_id

    while True:
        iteration += 1

        if max_iterations and iteration > max_iterations:
            print(f"\nReached max iterations ({max_iterations})")
            break

        # Determine prompt type and get prompt
        if agent_type:
            # Improvement agent mode
            prompt_type = agent_type.value
            prompt = get_prompt_for_agent_type(agent_type, project_dir)
        else:
            # Legacy mode
            if needs_analysis:
                prompt_type = "analysis"
                needs_analysis = False
            elif is_first_run:
                prompt_type = "initializer"
                is_first_run = False
            else:
                prompt_type = "coding"

            # Choose legacy prompt
            if prompt_type == "analysis":
                prompt = get_existing_project_prompt()
            elif prompt_type == "initializer":
                prompt = get_initializer_prompt()
            else:
                prompt = get_coding_prompt()

        print_session_header(iteration, prompt_type, agent_type)

        # Create client (with optional session resumption)
        client = create_client(
            project_dir, model, resume_session_id=current_session_id if iteration == 1 else None
        )

        async with client:
            status, response, session_id = await run_agent_session(client, prompt, project_dir)
            if session_id:
                current_session_id = session_id
                save_session_id(project_dir, session_id, agent_type)

        # Update memory with session summary (for improvement agents)
        if agent_type and memory_manager and response:
            # Extract a brief summary from response (first 500 chars)
            summary = response[:500] + "..." if len(response) > 500 else response
            update_session_memory(project_dir, agent_type, summary)

        if status == "continue":
            print(f"\nAgent will auto-continue in {AUTO_CONTINUE_DELAY_SECONDS}s...")
            print_progress_summary(project_dir, agent_type)
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)
        elif status == "error":
            print("\nSession encountered an error, retrying...")
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)

        if max_iterations is None or iteration < max_iterations:
            print("\nPreparing next session...\n")
            await asyncio.sleep(1)

    # Final summary
    print("\n" + "=" * 70)
    print("  SESSION COMPLETE")
    print("=" * 70)
    print(f"\nLast session ID: {current_session_id}")
    print("To resume later: --resume")

    if agent_type:
        print_progress_summary(project_dir, agent_type)
        # Also show all agents status for context
        print_all_agents_status(project_dir)
    else:
        print_progress_summary(project_dir)

    print("\nDone!")


async def run_coordinator_agent(
    project_dir: Path,
    model: str,
) -> None:
    """
    Run the coordinator agent to manage parallel workflow.

    The coordinator:
    - Checks status of all agents
    - Resolves blocking issues
    - Handles merge conflicts
    - Generates progress reports

    Args:
        project_dir: Directory for the project
        model: Claude model to use
    """
    print("\n" + "=" * 70)
    print("  COORDINATOR AGENT")
    print("  Managing parallel agent workflow")
    print("=" * 70)

    # Show status of all agents
    print_all_agents_status(project_dir)

    # Run single coordination session
    await run_autonomous_agent(
        project_dir=project_dir,
        model=model,
        max_iterations=1,
        agent_type=AgentType.COORDINATOR,
    )
