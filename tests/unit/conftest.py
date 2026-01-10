"""Unit test fixtures and configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file for unit tests
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


def get_test_model():
    """Get the model name from environment, with fallback for CI."""
    return os.environ.get("OPENAI_MODEL", "gpt-5-mini")
