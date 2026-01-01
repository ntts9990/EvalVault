#!/usr/bin/env python3
"""
Autonomous Agent - Main Entry Point
====================================

Multi-purpose autonomous agent for EvalVault:
1. Legacy Mode: End-to-end testing of Web UI evaluation features
2. Improvement Mode: Run specific improvement agents (architecture, observability, etc.)
3. Coordinator Mode: Manage parallel agent workflow

Usage:
    # Legacy: Analyze and test existing project
    uv run python main.py --project-dir .. --analyze-first

    # Legacy: Resume last session
    uv run python main.py --project-dir .. --resume

    # Improvement: Run specific agent type
    uv run python main.py --project-dir .. --agent-type architecture
    uv run python main.py --project-dir .. --agent-type observability
    uv run python main.py --project-dir .. --agent-type performance

    # Coordinator: Manage all agents
    uv run python main.py --project-dir .. --agent-type coordinator

    # List available agent types
    uv run python main.py --list-agents

Reference:
- https://platform.claude.com/docs/en/agent-sdk/overview
- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- https://github.com/seolcoding/nonstop-agent (MIT License)
"""

import argparse
import asyncio
import os
from pathlib import Path

from agent import run_autonomous_agent, run_coordinator_agent
from config import AGENT_CONFIGS, AgentType

# Configuration
DEFAULT_MODEL = "claude-opus-4-5-20251101"

# Valid agent types for CLI
VALID_AGENT_TYPES = [t.value for t in AgentType]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-purpose autonomous agent for EvalVault improvements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Agent Types:
  architecture   - Code structure, dependency injection, Hexagonal Architecture
  observability  - Phoenix integration, OpenTelemetry, metrics collection
  rag-data       - Retrieval data collection, evaluation metrics
  performance    - Caching, batch processing, optimization
  testing        - Test optimization, coverage, profiling
  documentation  - Tutorials, API docs, examples
  coordinator    - Manage parallel agent workflow

Examples:
  # Run architecture agent
  python main.py --project-dir .. --agent-type architecture

  # Run coordinator to check all agent status
  python main.py --project-dir .. --agent-type coordinator

  # Legacy mode (Web UI testing)
  python main.py --project-dir .. --analyze-first
""",
    )

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path(".."),
        help="Directory for the project (default: ..)",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum number of agent iterations (default: unlimited)",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )

    parser.add_argument(
        "--analyze-first",
        action="store_true",
        help="Analyze existing project before starting (for existing codebases)",
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the last session (uses saved session ID)",
    )

    parser.add_argument(
        "--agent-type",
        type=str,
        choices=VALID_AGENT_TYPES,
        default=None,
        help="Specific agent type to run (default: legacy mode)",
    )

    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="List all available agent types and their descriptions",
    )

    return parser.parse_args()


def list_agents() -> None:
    """Print information about all available agent types."""
    print("\n" + "=" * 70)
    print("  AVAILABLE AGENT TYPES")
    print("=" * 70)
    print()

    for agent_type, config in AGENT_CONFIGS.items():
        print(f"  {agent_type.value:15} | {config.name}")
        print(f"  {' ':15} | {config.description}")
        print(f"  {' ':15} | P-Levels: {', '.join(config.p_levels)}")
        if config.dependencies:
            deps = ", ".join(d.value for d in config.dependencies)
            print(f"  {' ':15} | Dependencies: {deps}")
        print()

    print("=" * 70)
    print("\nUsage: python main.py --project-dir .. --agent-type <agent-type>")
    print()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Handle --list-agents
    if args.list_agents:
        list_agents()
        return

    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nGet your API key from: https://console.anthropic.com/")
        print("\nThen set it:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        return

    # Convert agent_type string to enum
    agent_type = None
    if args.agent_type:
        agent_type = AgentType(args.agent_type)

    # Run the agent
    try:
        if agent_type == AgentType.COORDINATOR:
            # Special handling for coordinator
            asyncio.run(
                run_coordinator_agent(
                    project_dir=args.project_dir,
                    model=args.model,
                )
            )
        else:
            asyncio.run(
                run_autonomous_agent(
                    project_dir=args.project_dir,
                    model=args.model,
                    max_iterations=args.max_iterations,
                    analyze_first=args.analyze_first,
                    resume=args.resume,
                    agent_type=agent_type,
                )
            )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        print("To resume, run with --resume flag")
        if agent_type:
            print(f"Agent type: {agent_type.value}")
    except Exception as e:
        print(f"\nFatal error: {e}")
        raise


if __name__ == "__main__":
    main()
