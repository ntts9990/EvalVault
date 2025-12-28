# Contributing to EvalVault

Thank you for your interest in contributing to EvalVault! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a welcoming and inclusive community.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/ntts9990/EvalVault/issues)
2. If not, create a new issue using the bug report template
3. Include:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)

### Suggesting Features

1. Check existing issues and discussions for similar suggestions
2. Create a new issue using the feature request template
3. Describe the use case and expected behavior

### Pull Requests

1. Fork the repository
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following our coding standards
4. Write or update tests as needed
5. Run the test suite:
   ```bash
   uv run pytest tests/ -v
   ```
6. Run linting:
   ```bash
   uv run ruff check src/
   uv run ruff format src/
   ```
7. Commit with a clear message
8. Push and create a Pull Request

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/EvalVault.git
cd EvalVault

# Install with development dependencies
uv sync --extra dev

# Copy environment configuration
cp .env.example .env
```

### Running Tests

```bash
# Run all tests (without API keys)
uv run pytest tests/ -v -m "not requires_openai and not requires_langfuse"

# Run unit tests only
uv run pytest tests/unit/ -v

# Run with coverage
uv run pytest tests/ --cov=src/evalvault --cov-report=html
```

> **Note**: Always use `uv run` to ensure the correct virtual environment is activated.

## Coding Standards

### Style Guide

- Follow PEP 8 with modifications defined in `pyproject.toml`
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use [ruff](https://github.com/astral-sh/ruff) for linting and formatting

### Commit Messages (Conventional Commits)

We use [Conventional Commits](https://www.conventionalcommits.org/) with automatic versioning:

| Type | Description | Version Impact |
|------|-------------|----------------|
| `feat:` | New feature | Minor (0.x.0) |
| `fix:` | Bug fix | Patch (0.0.x) |
| `perf:` | Performance improvement | Patch (0.0.x) |
| `docs:` | Documentation only | No release |
| `style:` | Formatting, no code change | No release |
| `refactor:` | Code restructuring | No release |
| `test:` | Adding/updating tests | No release |
| `chore:` | Maintenance tasks | No release |
| `ci:` | CI/CD changes | No release |
| `build:` | Build system changes | No release |

**Format**: `<type>(<scope>): <subject>`

**Examples**:
```bash
feat(metrics): Add custom insurance accuracy metric
fix(cli): Handle empty dataset gracefully
docs: Update installation guide
chore(deps): Bump ragas to 1.0.5
```

**Important**: When your PR is merged to `main`, the Release workflow automatically:
1. Analyzes commits to determine version bump
2. Creates a git tag (e.g., v1.0.1)
3. Publishes to PyPI
4. Creates a GitHub Release

### Documentation

- Add docstrings to public functions and classes
- Update README.md if adding new features
- Korean comments are acceptable for domain-specific logic
- English for public API documentation

## Architecture

EvalVault follows **Hexagonal Architecture** (Ports & Adapters). When contributing:

1. **Domain Layer** (`src/evalvault/domain/`): Core business logic, no external dependencies
2. **Ports** (`src/evalvault/ports/`): Interface definitions
3. **Adapters** (`src/evalvault/adapters/`): External service implementations

New adapters should:
- Implement the appropriate port interface
- Include unit tests with mocked dependencies
- Be registered in the appropriate factory/registry

## Testing Guidelines

- Write tests **before** implementation (TDD)
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Use `@pytest.mark.requires_openai` for tests needing real API
- Use `@pytest.mark.requires_langfuse` for tests needing Langfuse
- Aim for high coverage but prioritize meaningful tests

## Questions?

- Open a [Discussion](https://github.com/ntts9990/EvalVault/discussions)
- Check existing issues and documentation

Thank you for contributing!
