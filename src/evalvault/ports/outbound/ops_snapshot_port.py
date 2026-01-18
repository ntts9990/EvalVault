from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class OpsSnapshotWriterPort(Protocol):
    def write_snapshot(self, path: Path, payload: dict[str, Any]) -> None: ...
