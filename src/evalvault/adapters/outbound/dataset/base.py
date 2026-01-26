"""Base dataset loader implementation."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from evalvault.domain.entities.dataset import Dataset


class BaseDatasetLoader(ABC):
    """Base class for dataset loaders with common functionality.

    Cross-platform compatible:
    - Uses pathlib.Path for all path operations
    - Normalizes paths with resolve() for consistent behavior
    - Handles both forward and backward slashes
    """

    @abstractmethod
    def load(self, file_path: str | Path) -> Dataset:
        """Load dataset from a file.

        Args:
            file_path: Path to the dataset file

        Returns:
            Dataset object containing test cases

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        pass

    @abstractmethod
    def supports(self, file_path: str | Path) -> bool:
        """Check if this loader supports the given file format.

        Args:
            file_path: Path to check

        Returns:
            True if supported, False otherwise
        """
        pass

    def _normalize_path(self, file_path: str | Path) -> Path:
        """Normalize file path for cross-platform compatibility.

        Converts to absolute path and resolves symlinks.
        Handles both forward and backward slashes.

        Args:
            file_path: Path to normalize (can be str or Path)

        Returns:
            Normalized absolute Path object
        """
        path = Path(file_path)

        # Convert to absolute path if relative
        if not path.is_absolute():
            path = Path.cwd() / path

        # Resolve symlinks and normalize (handles . and ..)
        # Note: resolve() may fail on Windows for non-existent paths
        # so we only resolve if the file exists
        try:
            return path.resolve()
        except OSError:
            # Fallback: just return the absolute path without resolving
            return path.absolute()

    def _validate_file_exists(self, file_path: str | Path) -> Path:
        """Validate that file exists and return normalized path.

        Args:
            file_path: Path to the file

        Returns:
            Normalized Path object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = self._normalize_path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        return path

    def _parse_contexts(self, contexts_str: str) -> list[str]:
        """Parse contexts from string format.

        Supports:
        - JSON array format: ["context1", "context2"]
        - Pipe-separated format: context1|context2|context3

        Args:
            contexts_str: String containing contexts

        Returns:
            List of context strings
        """
        if not contexts_str or (isinstance(contexts_str, float) and str(contexts_str) == "nan"):
            return []

        contexts_str = str(contexts_str).strip()

        # Try JSON format first
        if contexts_str.startswith("["):
            try:
                return json.loads(contexts_str)
            except json.JSONDecodeError:
                pass

        # Fall back to pipe-separated format
        return [ctx.strip() for ctx in contexts_str.split("|")]

    def _parse_metadata_cell(self, raw: Any) -> dict[str, Any]:
        if raw is None or (isinstance(raw, float) and str(raw) == "nan"):
            return {}
        text = str(raw).strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid metadata JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("metadata must be a JSON object")
        return parsed

    def _parse_summary_tags_cell(self, raw: Any) -> list[str]:
        if raw is None or (isinstance(raw, float) and str(raw) == "nan"):
            return []
        if isinstance(raw, list):
            return [str(item).strip().lower() for item in raw if str(item).strip()]
        text = str(raw).strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [str(item).strip().lower() for item in parsed if str(item).strip()]
        delimiter = "," if "," in text else "|" if "|" in text else None
        parts = text.split(delimiter) if delimiter else [text]
        return [part.strip().lower() for part in parts if part.strip()]

    def _parse_summary_intent_cell(self, raw: Any) -> str | None:
        if raw is None or (isinstance(raw, float) and str(raw) == "nan"):
            return None
        text = str(raw).strip()
        return text or None

    def _get_default_name(self, file_path: Path) -> str:
        """Get default dataset name from file path.

        Args:
            file_path: Path to the file

        Returns:
            Dataset name (filename without extension)
        """
        return file_path.stem

    def _get_default_version(self) -> str:
        """Get default dataset version.

        Returns:
            Default version string
        """
        return "1.0.0"
