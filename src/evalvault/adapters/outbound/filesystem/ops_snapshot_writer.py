from __future__ import annotations

from pathlib import Path
from typing import Any

from evalvault.adapters.inbound.cli.utils.analysis_io import write_json
from evalvault.ports.outbound.ops_snapshot_port import OpsSnapshotWriterPort


class OpsSnapshotWriter(OpsSnapshotWriterPort):
    def write_snapshot(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, payload)
