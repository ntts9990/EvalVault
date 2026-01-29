# EvalVault Development Agents

Development mode agents for improving EvalVault code quality and features.

Reference: https://github.com/seolcoding/nonstop-agent (MIT License)

## Architecture

EvalVault uses a **hybrid agent architecture**:

```
evalvault (PyPI Package)              agent/ (Development Only)
├── config/agent_types.py  ◄─────────┤ config.py (imports & adds prompts)
│   ├── AgentType enum               │ main.py
│   ├── AgentConfig                  │ agent.py
│   ├── Development configs          │ prompts/
│   └── Operation configs            └── memory/
│
└── CLI: evalvault agent list/info/run
```

- **Shared Types**: `src/evalvault/config/agent_types.py` - Used by both modes
- **Development Agents**: `agent/` folder - For code improvements
- **Operation Agents**: Via CLI `evalvault agent run` - For evaluation automation

## Agent Modes

### Development Mode (This Folder)

Agents for improving EvalVault codebase based on the current roadmap and engineering standards (see `docs/handbook/CHAPTERS/08_roadmap.md`, `docs/handbook/INDEX.md`):

| Agent Type | Focus | P-Levels |
|------------|-------|----------|
| `architecture` | Code structure, dependency injection, Hexagonal Architecture | P0, P1, P2 |
| `observability` | Phoenix integration, OpenTelemetry, metrics collection | P7 |
| `rag-data` | Retrieval data collection, evaluation metrics | P7 |
| `performance` | Caching, batch processing, optimization | P3 |
| `testing` | Test optimization, coverage, profiling | P5 |
| `documentation` | Tutorials, API docs, examples | P6 |
| `coordinator` | Manage parallel agent workflow, conflict resolution | All |

### Operation Mode (Via CLI)

Agents for automating evaluation workflows:

```bash
# List operation agents
evalvault agent list

# Show agent info
evalvault agent info quality-monitor

# Run agent
evalvault agent run quality-monitor --domain insurance
```

| Agent Type | Focus |
|------------|-------|
| `quality-monitor` | Scheduled evaluation, regression detection |
| `domain-expert` | Domain terminology learning, reliability scoring |
| `testset-curator` | Gap analysis, test case generation |
| `report-generator` | Automated report generation |

## Prerequisites

### 1. Anthropic API Key

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 2. Install Dependencies

```bash
cd agent/
uv add claude-agent-sdk
```

## Usage

### List Available Agents

```bash
cd agent/
uv run python main.py --list-agents
```

### Run Specific Agent Type (Recommended)

```bash
# Architecture agent - code structure improvements
uv run python main.py --project-dir .. --agent-type architecture

# Observability agent - Phoenix integration
uv run python main.py --project-dir .. --agent-type observability

# Performance agent - caching and optimization
uv run python main.py --project-dir .. --agent-type performance

# Testing agent - test optimization
uv run python main.py --project-dir .. --agent-type testing
```

### Run Coordinator Agent

Manage all agents, resolve conflicts, generate reports:

```bash
uv run python main.py --project-dir .. --agent-type coordinator
```

### Legacy Mode (Web UI Testing)

```bash
# Analyze existing project first
uv run python main.py --project-dir .. --analyze-first

# Continue existing session
uv run python main.py --project-dir ..

# Resume from last session
uv run python main.py --project-dir .. --resume
```

### Limit Iterations

```bash
uv run python main.py --project-dir .. --agent-type architecture --max-iterations 5
```

## Memory System

Each agent maintains persistent memory in `agent/memory/`:

```
agent/memory/
├── agents/
│   ├── architecture/     # Architecture agent logs
│   ├── observability/    # Observability agent logs
│   ├── rag-data/         # RAG data agent logs
│   ├── performance/      # Performance agent logs
│   ├── testing/          # Testing agent logs
│   ├── documentation/    # Documentation agent logs
│   └── coordinator/      # Coordinator agent logs
├── shared/
│   ├── decisions.md      # Cross-agent decisions (ADR format)
│   └── dependencies.md   # Task dependencies and blocking issues
└── templates/
    ├── work_log_template.md
    └── coordinator_guide.md
```

### Memory Features

- **Session Summaries**: Auto-saved after each session
- **Work Logs**: Detailed task progress tracking
- **Shared Decisions**: Architecture Decision Records (ADR)
- **Dependency Tracking**: Cross-agent blocking issues

## Parallel Execution

### Group A: Fully Independent (Can Run Together)

```bash
# These agents have no dependencies
uv run python main.py --project-dir .. --agent-type performance &
uv run python main.py --project-dir .. --agent-type testing &
uv run python main.py --project-dir .. --agent-type documentation &
```

### Group B: Sequential Dependencies

```
observability → rag-data
(rag-data needs Phoenix integration first)
```

### Group C: Internal Dependencies

`architecture` has internal task ordering (P0 → P1 → P2)

## File Structure

```
agent/
├── main.py                 # Entry point
├── agent.py                # Session logic
├── client.py               # Claude SDK client
├── config.py               # Agent type configurations
├── memory_integration.py   # Memory system integration
├── progress.py             # Progress tracking
├── security.py             # Command validation
├── prompts.py              # Prompt loading
├── requirements.txt        # Dependencies
├── memory/                 # Persistent memory system
│   ├── agents/             # Per-agent memory
│   ├── shared/             # Cross-agent coordination
│   └── templates/          # Work log templates
└── prompts/
    ├── app_spec.txt                    # Application specification
    ├── initializer_prompt.md           # First session prompt (legacy)
    ├── coding_prompt.md                # Coding session prompt (legacy)
    ├── existing_project_prompt.md      # Analysis session prompt (legacy)
    └── improvement/
        ├── base_prompt.md              # Base template for agents
        ├── architecture_prompt.md      # Architecture agent prompt
        ├── observability_prompt.md     # Observability agent prompt
        └── coordinator_prompt.md       # Coordinator agent prompt
```

## Progress Tracking

### feature_list.json

Task tracking with agent assignment:

```json
[
  {
    "category": "architecture",
    "description": "Complete LLM Adapter integration",
    "steps": [...],
    "agent": "architecture",
    "p_level": "P1",
    "passes": false
  }
]
```

### Agent-Specific Progress

```bash
# Check specific agent progress
cat agent/memory/agents/architecture/session_*.md

# Check all agent status
uv run python main.py --project-dir .. --agent-type coordinator
```

## Security

The agent uses allowlist-based command validation:

**Allowed:**
- File operations: `ls`, `cat`, `mkdir`, `cp`
- Python: `uv`, `pytest`, `ruff`
- Git: `git add`, `git commit`
- Testing: `pytest`, `coverage`

**Blocked:**
- Destructive operations: `rm`, `dd`, `format`
- Network operations: `curl`, `wget`, `nc`
- System changes: `sudo`, `su`

Customize in `security.py` if needed.

## Troubleshooting

### Agent gets stuck

```bash
uv run python main.py --project-dir .. --agent-type architecture --resume
```

### Check blocking issues

```bash
cat agent/memory/shared/dependencies.md | grep "open"
```

### View recent decisions

```bash
cat agent/memory/shared/decisions.md | tail -50
```

### Run coordinator for status

```bash
uv run python main.py --project-dir .. --agent-type coordinator
```

## Integration with Project Docs

The agent system follows the project documentation and current engineering standards (see `docs/INDEX.md`):

| Priority | Agent | Tasks |
|----------|-------|-------|
| P0 | architecture | Dependency inversion, extras reorg |
| P1 | architecture | LLM adapter integration |
| P2 | architecture | CLI module split, Web UI restructuring |
| P3 | performance | LRU+TTL cache, batch processing |
| P5 | testing | Slow test optimization |
| P6 | documentation | Phoenix tutorial, API docs |
| P7 | observability, rag-data | Phoenix integration, retrieval metrics |

## References

- [Claude Agent SDK Docs](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Effective Harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Docs Index](../docs/INDEX.md)
- [Handbook](../docs/handbook/INDEX.md)
- [Open RAG Trace Spec](../docs/architecture/open-rag-trace-spec.md)
- [Agent Types Configuration](../src/evalvault/config/agent_types.py)
- [nonstop-agent](https://github.com/seolcoding/nonstop-agent)

---

## Quick Start

### Development Mode (Code Improvements)

```bash
cd agent/
export ANTHROPIC_API_KEY='your-key'
uv add claude-agent-sdk
uv run python main.py --list-agents
uv run python main.py --project-dir .. --agent-type architecture
```

### Operation Mode (Evaluation Automation)

```bash
# From project root
evalvault agent list
evalvault agent run quality-monitor --domain insurance --dry-run
```
