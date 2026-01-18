from __future__ import annotations

from pathlib import Path
from typing import Protocol


class DifficultyProfileWriterPort(Protocol):
    def write_profile(
        self,
        *,
        output_path: Path,
        artifacts_dir: Path,
        envelope: dict[str, object],
        artifacts: dict[str, object],
    ) -> dict[str, object]: ...
