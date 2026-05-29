"""Path-safety helpers for untrusted filesystem inputs at the web API boundary.

These mirror the containment rules already enforced at the MCP boundary
(``evalvault.adapters.inbound.mcp.tools._ensure_allowed_path``): an untrusted
path must resolve **inside** the project's ``data/``, ``tests/fixtures/`` or
``reports/`` trees, and an uploaded filename is reduced to a bare basename so an
attacker-controlled multipart ``filename`` cannot escape its target directory.

The web routers historically passed request-supplied filenames and paths
straight to filesystem sinks (``open``/``write_bytes``/dataset loaders), which
allowed path traversal (arbitrary file read/write). Routing every untrusted
value through these helpers closes that gap regardless of whether API
authentication is configured.
"""

from __future__ import annotations

from pathlib import Path


class UnsafePathError(ValueError):
    """Raised when an untrusted filename or path fails containment checks."""


def safe_upload_filename(filename: str | None) -> str:
    """Return a safe bare basename for an uploaded file, or raise.

    Uploaded files are written into a fixed server directory, so the client
    only ever needs to supply a plain name (e.g. ``insurance-qa.json``). Any
    path separator, parent reference, NUL byte, or empty value is rejected so a
    crafted ``filename`` like ``../../evil.py`` or ``/etc/cron.d/x`` cannot
    redirect the write outside that directory.

    Raises:
        UnsafePathError: if the filename is missing or not a bare basename.
    """
    if not filename:
        raise UnsafePathError("Missing filename")
    if "/" in filename or "\\" in filename or "\x00" in filename:
        raise UnsafePathError(f"Filename must not contain path separators: {filename!r}")
    name = Path(filename).name
    if name != filename or name in {"", ".", ".."}:
        raise UnsafePathError(f"Invalid filename: {filename!r}")
    return name


def _find_repo_root() -> Path | None:
    current = Path.cwd().resolve()
    for _ in range(6):
        if (current / "pyproject.toml").exists():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


def allowed_roots() -> list[Path]:
    """Directories an untrusted path is permitted to resolve inside.

    Kept in sync with the MCP boundary's allow-list (data/, tests/fixtures/,
    reports/) so both inbound adapters enforce the same containment.
    """
    repo_root = _find_repo_root()
    base = repo_root if repo_root is not None else Path.cwd()
    return [
        (base / "data").resolve(),
        (base / "tests" / "fixtures").resolve(),
        (base / "reports").resolve(),
    ]


def ensure_within_allowed(path: Path) -> None:
    """Raise UnsafePathError unless ``path`` resolves inside an allowed root."""
    roots = allowed_roots()
    if not any(path.is_relative_to(root) for root in roots):
        raise UnsafePathError(
            "Path is outside the allowed directories (data/, tests/fixtures/, reports/)."
        )


def resolve_user_path(raw: str | Path | None, *, must_exist: bool = True) -> Path:
    """Resolve an untrusted path and confine it to the allowed roots.

    Args:
        raw: The request-supplied path (relative or absolute).
        must_exist: When True, also require that the resolved file exists.

    Returns:
        The resolved, contained ``Path``.

    Raises:
        UnsafePathError: if the path is empty, escapes the allowed roots, or
            (when ``must_exist``) does not exist.
    """
    if raw is None or str(raw) == "":
        raise UnsafePathError("Empty path")
    resolved = Path(raw).expanduser().resolve()
    ensure_within_allowed(resolved)
    if must_exist and not resolved.exists():
        raise UnsafePathError(f"Path does not exist: {raw!r}")
    return resolved
