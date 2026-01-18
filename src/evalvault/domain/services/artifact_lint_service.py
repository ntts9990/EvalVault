from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from evalvault.ports.outbound.artifact_fs_port import ArtifactFileSystemPort

logger = logging.getLogger(__name__)


LintLevel = Literal["error", "warning"]
LintStatus = Literal["ok", "warning", "error"]


@dataclass(frozen=True)
class ArtifactLintIssue:
    level: LintLevel
    code: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class ArtifactLintSummary:
    status: LintStatus
    issues: list[ArtifactLintIssue]
    artifacts_dir: Path
    index_path: Path
    started_at: datetime
    finished_at: datetime
    duration_ms: int
    strict: bool


class ArtifactLintService:
    def __init__(self, fs: ArtifactFileSystemPort) -> None:
        self._fs = fs

    def lint(self, artifacts_dir: Path, *, strict: bool = False) -> ArtifactLintSummary:
        started_at = datetime.now(UTC)
        issues: list[ArtifactLintIssue] = []
        index_path = artifacts_dir / "index.json"
        logger.info("Artifact lint started: %s", artifacts_dir)

        try:
            self._validate_dir(artifacts_dir, issues)
            if not self._fs.exists(index_path):
                issues.append(
                    ArtifactLintIssue(
                        "error",
                        "artifacts.index.missing",
                        "index.json is missing.",
                        path=str(index_path),
                    )
                )
            elif self._fs.exists(artifacts_dir) and self._fs.is_dir(artifacts_dir):
                index_payload = self._load_index(index_path, issues)
                if index_payload is not None:
                    self._validate_index(
                        index_payload,
                        artifacts_dir,
                        issues,
                        strict=strict,
                    )
        except Exception as exc:
            logger.exception("Artifact lint failed: %s", artifacts_dir)
            issues.append(
                ArtifactLintIssue(
                    "error",
                    "artifacts.lint.exception",
                    f"Unexpected error: {exc}",
                )
            )

        finished_at = datetime.now(UTC)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        status = _resolve_status(issues)
        logger.info("Artifact lint finished: %s (%s)", artifacts_dir, status)
        return ArtifactLintSummary(
            status=status,
            issues=issues,
            artifacts_dir=artifacts_dir,
            index_path=index_path,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            strict=strict,
        )

    def _validate_dir(self, artifacts_dir: Path, issues: list[ArtifactLintIssue]) -> None:
        if not self._fs.exists(artifacts_dir):
            issues.append(
                ArtifactLintIssue(
                    "error",
                    "artifacts.dir.missing",
                    "Artifacts directory is missing.",
                    path=str(artifacts_dir),
                )
            )
            return
        if not self._fs.is_dir(artifacts_dir):
            issues.append(
                ArtifactLintIssue(
                    "error",
                    "artifacts.dir.not_directory",
                    "Artifacts path is not a directory.",
                    path=str(artifacts_dir),
                )
            )

    def _load_index(
        self,
        index_path: Path,
        issues: list[ArtifactLintIssue],
    ) -> dict[str, object] | None:
        try:
            payload = json.loads(self._fs.read_text(index_path))
        except json.JSONDecodeError as exc:
            issues.append(
                ArtifactLintIssue(
                    "error",
                    "artifacts.index.invalid_json",
                    f"index.json parse failed: {exc}",
                    path=str(index_path),
                )
            )
            return None
        except OSError as exc:
            issues.append(
                ArtifactLintIssue(
                    "error",
                    "artifacts.index.read_failed",
                    f"index.json read failed: {exc}",
                    path=str(index_path),
                )
            )
            return None

        if not isinstance(payload, dict):
            issues.append(
                ArtifactLintIssue(
                    "error",
                    "artifacts.index.invalid_schema",
                    "index.json root must be an object.",
                    path=str(index_path),
                )
            )
            return None
        return payload

    def _validate_index(
        self,
        payload: dict[str, object],
        artifacts_dir: Path,
        issues: list[ArtifactLintIssue],
        *,
        strict: bool,
    ) -> None:
        pipeline_id = payload.get("pipeline_id")
        if not isinstance(pipeline_id, str) or not pipeline_id.strip():
            issues.append(
                ArtifactLintIssue(
                    "error",
                    "artifacts.index.pipeline_id.missing",
                    "pipeline_id is missing.",
                )
            )

        nodes = payload.get("nodes")
        if not isinstance(nodes, list):
            issues.append(
                ArtifactLintIssue(
                    "error",
                    "artifacts.index.nodes.invalid",
                    "nodes list is missing or invalid.",
                )
            )
            return

        for idx, node in enumerate(nodes, start=1):
            if not isinstance(node, dict):
                issues.append(
                    ArtifactLintIssue(
                        "error",
                        "artifacts.index.node.invalid",
                        f"nodes[{idx}] entry must be an object.",
                    )
                )
                continue
            node_id = node.get("node_id")
            if not isinstance(node_id, str) or not node_id.strip():
                issues.append(
                    ArtifactLintIssue(
                        "error",
                        "artifacts.index.node_id.missing",
                        f"nodes[{idx}] node_id is missing.",
                    )
                )
            path_value = node.get("path")
            self._validate_path(
                path_value,
                artifacts_dir,
                issues,
                strict=strict,
                code="artifacts.index.node.path.missing",
                message=f"nodes[{idx}] path is missing.",
            )

        final_output = payload.get("final_output_path")
        if final_output:
            self._validate_path(
                final_output,
                artifacts_dir,
                issues,
                strict=strict,
                code="artifacts.index.final_output.missing",
                message="final_output_path is missing.",
            )

    def _validate_path(
        self,
        path_value: object,
        artifacts_dir: Path,
        issues: list[ArtifactLintIssue],
        *,
        strict: bool,
        code: str,
        message: str,
    ) -> None:
        if not isinstance(path_value, str) or not path_value.strip():
            issues.append(
                ArtifactLintIssue(
                    "error",
                    code,
                    message,
                )
            )
            return

        resolved = _resolve_artifact_path(artifacts_dir, Path(path_value))
        if self._fs.exists(resolved):
            return
        issues.append(
            ArtifactLintIssue(
                "error" if strict else "warning",
                code,
                "Artifact file is missing.",
                path=str(resolved),
            )
        )


def _resolve_artifact_path(base_dir: Path, candidate: Path) -> Path:
    if candidate.is_absolute():
        return candidate
    return base_dir / candidate


def _resolve_status(issues: list[ArtifactLintIssue]) -> LintStatus:
    if any(issue.level == "error" for issue in issues):
        return "error"
    if any(issue.level == "warning" for issue in issues):
        return "warning"
    return "ok"
