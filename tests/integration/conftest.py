"""Integration test fixtures and configuration."""

import os
from datetime import datetime
from pathlib import Path

import pytest

# Load .env file for integration tests
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Persistent storage path for E2E test results
E2E_RESULTS_DIR = Path(__file__).parent.parent.parent / "data" / "e2e_results"


def get_test_model():
    """Get the model name from environment, with fallback for CI."""
    return os.environ.get("OPENAI_MODEL", "gpt-5-mini")


def _add_timestamp_to_path(path_str: str) -> str:
    """Add timestamp suffix to a file path.

    Example: reports/e2e_report.html -> reports/e2e_report_20251224_112345.html
    """
    path = Path(path_str)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_name = f"{path.stem}_{timestamp}{path.suffix}"
    return str(path.parent / new_name)


def pytest_configure(config):
    """Configure custom pytest markers and add timestamps to report filenames."""
    config.addinivalue_line("markers", "requires_openai: marks tests that require OpenAI API key")
    config.addinivalue_line(
        "markers", "requires_langfuse: marks tests that require Langfuse credentials"
    )
    config.addinivalue_line(
        "markers", "requires_phoenix: marks tests that require Phoenix/OpenTelemetry dependencies"
    )

    # Add timestamp suffix to HTML report filename
    if hasattr(config.option, "htmlpath") and config.option.htmlpath:
        config.option.htmlpath = _add_timestamp_to_path(config.option.htmlpath)

    # Add timestamp suffix to JUnit XML report filename
    if hasattr(config.option, "xmlpath") and config.option.xmlpath:
        config.option.xmlpath = _add_timestamp_to_path(config.option.xmlpath)


@pytest.fixture
def has_openai_key():
    """Check if OpenAI API key is available."""
    return bool(os.environ.get("OPENAI_API_KEY"))


@pytest.fixture
def has_langfuse_keys():
    """Check if Langfuse credentials are available."""
    return bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))


@pytest.fixture(scope="session")
def e2e_results_db():
    """Persistent SQLite database for E2E test evaluation results.

    This database persists across test runs, allowing you to track
    evaluation results history over time.

    Location: data/e2e_results/e2e_evaluations.db
    """
    from evalvault.adapters.outbound.storage.sqlite_adapter import SQLiteStorageAdapter

    E2E_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    db_path = E2E_RESULTS_DIR / "e2e_evaluations.db"
    return SQLiteStorageAdapter(str(db_path))


@pytest.fixture(scope="session")
def e2e_results_path():
    """Path to E2E results directory."""
    E2E_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return E2E_RESULTS_DIR


def pytest_runtest_setup(item):
    """Skip tests based on required credentials."""
    # Check for requires_openai marker
    if item.get_closest_marker("requires_openai") and not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("Requires OPENAI_API_KEY environment variable")

    # Check for requires_langfuse marker
    if item.get_closest_marker("requires_langfuse") and not (
        os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")
    ):
        pytest.skip("Requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")

    # Check for requires_phoenix marker
    if item.get_closest_marker("requires_phoenix"):
        try:
            import opentelemetry  # noqa: F401
        except ImportError:
            pytest.skip("Requires OpenTelemetry dependencies (uv sync --extra phoenix)")
