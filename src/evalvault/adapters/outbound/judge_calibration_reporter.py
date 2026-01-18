from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from evalvault.domain.entities.judge_calibration import JudgeCalibrationResult


class JudgeCalibrationReporter:
    def render_json(self, result: JudgeCalibrationResult) -> dict[str, Any]:
        return {
            "summary": asdict(result.summary),
            "metrics": [asdict(metric) for metric in result.metrics],
            "case_results": {
                metric: [asdict(entry) for entry in entries]
                for metric, entries in result.case_results.items()
            },
            "warnings": list(result.warnings),
        }

    def write_artifacts(
        self,
        *,
        result: JudgeCalibrationResult,
        artifacts_dir: Path,
    ) -> dict[str, str]:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        index_path = artifacts_dir / "index.json"
        payload = {
            "run_id": result.summary.run_id,
            "metrics": [metric.metric for metric in result.metrics],
            "cases": {},
        }
        for metric, cases in result.case_results.items():
            case_path = artifacts_dir / f"{metric}.json"
            case_payload = [
                {
                    "test_case_id": case.test_case_id,
                    "raw_score": case.raw_score,
                    "calibrated_score": case.calibrated_score,
                    "label": case.label,
                    "label_source": case.label_source,
                }
                for case in cases
            ]
            case_path.write_text(
                json.dumps(case_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            payload["cases"][metric] = str(case_path)
        index_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"dir": str(artifacts_dir), "index": str(index_path)}
