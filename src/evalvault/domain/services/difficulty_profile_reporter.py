from __future__ import annotations

from pathlib import Path

from evalvault.ports.outbound.difficulty_profile_port import DifficultyProfileWriterPort


class DifficultyProfileReporter:
    def __init__(self, writer: DifficultyProfileWriterPort) -> None:
        self._writer = writer

    def write(
        self,
        *,
        output_path: Path,
        artifacts_dir: Path,
        envelope: dict[str, object],
        artifacts: dict[str, object],
    ) -> dict[str, object]:
        return self._writer.write_profile(
            output_path=output_path,
            artifacts_dir=artifacts_dir,
            envelope=envelope,
            artifacts=artifacts,
        )
