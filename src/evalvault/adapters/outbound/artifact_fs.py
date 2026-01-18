from __future__ import annotations

from pathlib import Path

from evalvault.ports.outbound.artifact_fs_port import ArtifactFileSystemPort


class LocalArtifactFileSystemAdapter(ArtifactFileSystemPort):
    def exists(self, path: Path) -> bool:
        return path.exists()

    def is_dir(self, path: Path) -> bool:
        return path.is_dir()

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")
