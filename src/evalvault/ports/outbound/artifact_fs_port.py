from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ArtifactFileSystemPort(Protocol):
    def exists(self, path: Path) -> bool: ...

    def is_dir(self, path: Path) -> bool: ...

    def read_text(self, path: Path) -> str: ...
