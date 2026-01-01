"""EvalVault package bootstrap."""

from __future__ import annotations

import sys
from pathlib import Path


def _maybe_use_local_virtualenv() -> None:
    """Ensure `.venv` site-packages are on sys.path when running via system Python.

    Some contributors run the globally installed ``evalvault`` entrypoint while
    managing dependencies through ``uv sync`` (which installs into ``.venv``).
    This helper detects that workspace-local virtual environment and prepends
    its site-packages directory so optional extras (phoenix, anthropic, etc.)
    remain importable without manually activating the virtualenv.
    """

    module_path = Path(__file__).resolve()
    repo_root = module_path.parent.parent.parent
    venv_dir = repo_root / ".venv"
    if not venv_dir.exists():
        return

    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    candidate_paths = [
        venv_dir / "lib" / python_version / "site-packages",  # POSIX
        venv_dir / "Lib" / "site-packages",  # Windows
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            path_str = str(candidate)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
            break


_maybe_use_local_virtualenv()
