from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evalvault.config.model_config import get_model_config
from evalvault.config.settings import Settings, apply_profile
from evalvault.domain.entities import EvaluationRun
from evalvault.ports.outbound.ops_snapshot_port import OpsSnapshotWriterPort
from evalvault.ports.outbound.storage_port import StoragePort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpsSnapshotRequest:
    run_id: str
    profile: str | None
    db_path: Path | None
    include_model_config: bool
    include_env: bool
    redact_keys: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OpsSnapshotEnvelope:
    command: str
    version: int
    status: str
    started_at: str
    finished_at: str
    duration_ms: int
    artifacts: dict[str, Any]
    data: dict[str, Any]


class OpsSnapshotService:
    def __init__(
        self,
        *,
        storage: StoragePort,
        writer: OpsSnapshotWriterPort,
        settings: Settings,
        output_path: Path,
    ) -> None:
        self._storage = storage
        self._writer = writer
        self._settings = settings
        self._output_path = output_path

    def collect(self, request: OpsSnapshotRequest) -> OpsSnapshotEnvelope:
        started_at = datetime.now(UTC)
        logger.info("ops snapshot started", extra={"run_id": request.run_id})

        try:
            run = self._storage.get_run(request.run_id)
        except KeyError:
            logger.error("ops snapshot run missing", extra={"run_id": request.run_id})
            raise

        settings = self._settings
        if request.profile:
            settings = apply_profile(settings, request.profile)

        data = {
            "run": _build_run_snapshot(run),
            "profile": request.profile or settings.evalvault_profile,
            "db_path": str(request.db_path) if request.db_path else None,
        }

        if request.include_model_config:
            data["model_config"] = _build_model_config_snapshot(request.profile)

        if request.include_env:
            data["env"] = _build_env_snapshot(settings, request.redact_keys)

        finished_at = datetime.now(UTC)
        duration_ms = int((finished_at - started_at).total_seconds() * 1000)
        payload = OpsSnapshotEnvelope(
            command="ops_snapshot",
            version=1,
            status="ok",
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            duration_ms=duration_ms,
            artifacts={},
            data=data,
        )

        self._writer.write_snapshot(self._output_path, _serialize_envelope(payload))
        logger.info("ops snapshot finished", extra={"run_id": request.run_id})
        return payload


def _build_run_snapshot(run: EvaluationRun) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "dataset_name": run.dataset_name,
        "dataset_version": run.dataset_version,
        "model_name": run.model_name,
        "metrics_evaluated": list(run.metrics_evaluated),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "duration_seconds": run.duration_seconds,
        "total_test_cases": run.total_test_cases,
        "pass_rate": run.pass_rate,
        "metric_pass_rate": run.metric_pass_rate,
        "thresholds": run.thresholds,
        "tracker_metadata": run.tracker_metadata,
        "retrieval_metadata": run.retrieval_metadata,
    }


def _build_model_config_snapshot(profile: str | None) -> dict[str, Any] | None:
    try:
        config = get_model_config()
    except FileNotFoundError:
        return None

    if profile:
        try:
            profile_config = config.get_profile(profile)
        except KeyError:
            return {"available_profiles": sorted(config.profiles.keys())}
        return {
            "profile": profile,
            "description": profile_config.description,
            "llm": profile_config.llm.model_dump(),
            "embedding": profile_config.embedding.model_dump(),
        }

    return {
        "profiles": {name: entry.model_dump() for name, entry in config.profiles.items()},
    }


def _build_env_snapshot(settings: Settings, redact_keys: tuple[str, ...]) -> dict[str, Any]:
    data = settings.model_dump()
    normalized_redact = {key.upper() for key in redact_keys}
    for key in list(data.keys()):
        if key.upper() in normalized_redact:
            data[key] = "[redacted]"
    return data


def _serialize_envelope(envelope: OpsSnapshotEnvelope) -> dict[str, Any]:
    return {
        "command": envelope.command,
        "version": envelope.version,
        "status": envelope.status,
        "started_at": envelope.started_at,
        "finished_at": envelope.finished_at,
        "duration_ms": envelope.duration_ms,
        "artifacts": envelope.artifacts,
        "data": envelope.data,
    }
