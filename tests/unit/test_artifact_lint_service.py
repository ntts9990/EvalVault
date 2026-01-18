from __future__ import annotations

from pathlib import Path

from evalvault.domain.services.artifact_lint_service import ArtifactLintService
from evalvault.ports.outbound.artifact_fs_port import ArtifactFileSystemPort


class StubArtifactFs(ArtifactFileSystemPort):
    def __init__(self, files: dict[str, str], dirs: set[str]) -> None:
        self._files = files
        self._dirs = dirs

    def exists(self, path: Path) -> bool:
        value = str(path)
        return value in self._files or value in self._dirs

    def is_dir(self, path: Path) -> bool:
        return str(path) in self._dirs

    def read_text(self, path: Path) -> str:
        return self._files[str(path)]


def test_lint_missing_index() -> None:
    artifacts_dir = Path("/tmp/artifacts")
    fs = StubArtifactFs(files={}, dirs={str(artifacts_dir)})

    service = ArtifactLintService(fs)
    summary = service.lint(artifacts_dir)

    assert summary.status == "error"
    assert any(issue.code == "artifacts.index.missing" for issue in summary.issues)


def test_lint_missing_node_path_warning() -> None:
    artifacts_dir = Path("/tmp/artifacts")
    index_path = artifacts_dir / "index.json"
    node_path = artifacts_dir / "node.json"
    fs = StubArtifactFs(
        files={
            str(index_path): '{"pipeline_id":"p1","nodes":[{"node_id":"n1","path":"node.json"}]}',
        },
        dirs={str(artifacts_dir)},
    )

    service = ArtifactLintService(fs)
    summary = service.lint(artifacts_dir)

    assert summary.status == "warning"
    assert any(issue.path == str(node_path) for issue in summary.issues)


def test_lint_missing_node_path_strict_error() -> None:
    artifacts_dir = Path("/tmp/artifacts")
    index_path = artifacts_dir / "index.json"
    fs = StubArtifactFs(
        files={
            str(index_path): '{"pipeline_id":"p1","nodes":[{"node_id":"n1","path":"node.json"}]}',
        },
        dirs={str(artifacts_dir)},
    )

    service = ArtifactLintService(fs)
    summary = service.lint(artifacts_dir, strict=True)

    assert summary.status == "error"
    assert any(issue.code == "artifacts.index.node.path.missing" for issue in summary.issues)
