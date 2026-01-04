"""Stage metric playbook loader."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class StageMetricPlaybookLoader:
    """Load stage metric action definitions from YAML."""

    DEFAULT_PATH = (
        Path(__file__).parent.parent.parent.parent / "config" / "stage_metric_playbook.yaml"
    )

    def __init__(self, playbook_path: Path | str | None = None):
        self._path = Path(playbook_path) if playbook_path else self.DEFAULT_PATH
        self._playbook: dict[str, dict[str, Any]] | None = None

    def load(self) -> dict[str, dict[str, Any]]:
        if self._playbook is not None:
            return self._playbook

        if not self._path.exists():
            logger.debug("StageMetric playbook not found: %s", self._path)
            self._playbook = {}
            return self._playbook

        with self._path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        metrics = data.get("metrics", {})
        if not isinstance(metrics, dict):
            logger.warning("Invalid StageMetric playbook format: metrics is not a dict")
            self._playbook = {}
            return self._playbook

        normalized: dict[str, dict[str, Any]] = {}
        for metric_name, payload in metrics.items():
            if not isinstance(payload, dict):
                continue
            action_payload = (
                payload.get("action") if isinstance(payload.get("action"), dict) else payload
            )
            normalized[str(metric_name)] = dict(action_payload)

        self._playbook = normalized
        return self._playbook
