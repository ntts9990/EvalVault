from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from evalvault.config.settings import Settings
from evalvault.domain.entities import EvaluationRun
from evalvault.domain.services.ops_snapshot_service import (
    OpsSnapshotRequest,
    OpsSnapshotService,
)
from evalvault.ports.outbound.ops_snapshot_port import OpsSnapshotWriterPort
from evalvault.ports.outbound.storage_port import StoragePort


def test_collect_ops_snapshot_redacts_env(tmp_path) -> None:
    run = EvaluationRun(
        run_id="run-1",
        dataset_name="demo",
        dataset_version="1.0.0",
        model_name="model-x",
    )
    storage = MagicMock(spec=StoragePort)
    storage.get_run.return_value = run
    writer = MagicMock(spec=OpsSnapshotWriterPort)
    settings = Settings(openai_api_key="secret")
    output_path = tmp_path / "snapshot.json"

    service = OpsSnapshotService(
        storage=storage,
        writer=writer,
        settings=settings,
        output_path=output_path,
    )
    request = OpsSnapshotRequest(
        run_id="run-1",
        profile=None,
        db_path=Path("data/db/evalvault.db"),
        include_model_config=False,
        include_env=True,
        redact_keys=("OPENAI_API_KEY",),
    )

    envelope = service.collect(request)

    assert envelope.command == "ops_snapshot"
    assert envelope.status == "ok"
    writer.write_snapshot.assert_called_once()
    written_path, payload = writer.write_snapshot.call_args[0]
    assert written_path == output_path
    assert payload["data"]["run"]["run_id"] == "run-1"
    assert payload["data"]["env"]["openai_api_key"] == "[redacted]"
