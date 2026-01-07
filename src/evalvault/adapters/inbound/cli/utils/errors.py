"""Enhanced error handling utilities for CLI with actionable guidance."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from .console import print_cli_error


def handle_missing_api_key(console: Console, provider: str = "openai") -> None:
    """Display helpful error message for missing API keys.

    Args:
        console: Rich console instance
        provider: LLM provider name (openai, anthropic, etc.)
    """
    provider_upper = provider.upper()

    fixes = [
        f"Add {provider_upper}_API_KEY to your .env file:",
        f"  echo '{provider_upper}_API_KEY=your-key-here' >> .env",
        "",
        "Alternative: Use local models with Ollama:",
        "  uv run evalvault run --profile dev dataset.json",
    ]

    print_cli_error(
        console,
        f"{provider_upper}_API_KEY is not set",
        fixes=fixes,
    )


def handle_invalid_dataset(
    console: Console,
    path: Path,
    error: Exception,
) -> None:
    """Display helpful error message for dataset loading failures.

    Args:
        console: Rich console instance
        path: Path to the dataset file
        error: The exception that occurred
    """
    error_msg = str(error)

    fixes = [
        "Check file format and path:",
        f"  File: {path}",
        f"  Extension: {path.suffix}",
        "",
        "Supported formats: .csv, .json, .xlsx",
        "",
        "Verify dataset schema matches documentation:",
        "  Required fields: question, answer, contexts",
        "",
        "Example JSON structure:",
        "  {",
        '    "test_cases": [',
        "      {",
        '        "question": "...",',
        '        "answer": "...",',
        '        "contexts": ["..."]',
        "      }",
        "    ]",
        "  }",
    ]

    print_cli_error(
        console,
        f"Failed to load dataset: {path.name}",
        details=error_msg,
        fixes=fixes,
    )


def handle_evaluation_error(
    console: Console,
    error: Exception,
    *,
    verbose: bool = False,
) -> None:
    """Display helpful error message for evaluation failures.

    Args:
        console: Rich console instance
        error: The exception that occurred
        verbose: Whether to show detailed error information
    """
    error_msg = str(error)
    error_type = type(error).__name__

    # Common error patterns and fixes
    if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
        fixes = [
            "Check your API key configuration:",
            "  1. Verify the key is set in .env",
            "  2. Ensure the key is valid and not expired",
            "  3. Check account quota and billing status",
        ]
    elif "rate" in error_msg.lower() or "quota" in error_msg.lower():
        fixes = [
            "Rate limit exceeded. Try these options:",
            "  1. Wait a few minutes and retry",
            "  2. Reduce batch size: --batch-size 3",
            "  3. Disable parallel processing: remove --parallel",
            "  4. Use a different model with higher limits",
        ]
    elif "timeout" in error_msg.lower():
        fixes = [
            "Request timed out. Try these solutions:",
            "  1. Check your internet connection",
            "  2. Reduce batch size for smaller requests",
            "  3. Use streaming mode for large datasets: --stream",
        ]
    else:
        fixes = [
            "Troubleshooting steps:",
            "  1. Verify LLM API key and quota status",
            "  2. Check dataset schema is valid",
            "  3. Try with a smaller dataset first",
            "  4. Run with --verbose for detailed logs",
        ]

    details = f"{error_type}: {error_msg}" if verbose else error_msg

    print_cli_error(
        console,
        "Evaluation failed",
        details=details,
        fixes=fixes,
    )


def handle_storage_error(
    console: Console,
    path: Path,
    error: Exception,
) -> None:
    """Display helpful error message for storage/database failures.

    Args:
        console: Rich console instance
        path: Path where storage failed
        error: The exception that occurred
    """
    fixes = [
        "Check file permissions and disk space:",
        f"  Path: {path}",
        "",
        "Verify you have write permissions:",
        f"  ls -la {path.parent}",
        "",
        "Check if file is locked by another process:",
        "  lsof | grep evalvault",
        "",
        "Try a different output location:",
        "  --output ~/results.json",
        "  --db ./data/db/evalvault.db",
    ]

    print_cli_error(
        console,
        f"Failed to save to: {path.name}",
        details=str(error),
        fixes=fixes,
    )


__all__ = [
    "handle_missing_api_key",
    "handle_invalid_dataset",
    "handle_evaluation_error",
    "handle_storage_error",
]
