from __future__ import annotations

from pathlib import Path

from evalvault.adapters.inbound.cli.utils.analysis_io import write_json
from evalvault.ports.outbound.difficulty_profile_port import DifficultyProfileWriterPort


class DifficultyProfileWriter(DifficultyProfileWriterPort):
    def write_profile(
        self,
        *,
        output_path: Path,
        artifacts_dir: Path,
        envelope: dict[str, object],
        artifacts: dict[str, object],
    ) -> dict[str, object]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        breakdown_path = artifacts_dir / "difficulty_breakdown.json"
        cases_path = artifacts_dir / "difficulty_cases.json"
        breakdown_payload = artifacts.get("breakdown")
        cases_payload = artifacts.get("cases")
        write_json(
            breakdown_path,
            breakdown_payload if isinstance(breakdown_payload, dict) else {},
        )
        write_json(
            cases_path,
            {"cases": cases_payload} if isinstance(cases_payload, list) else {"cases": []},
        )

        index_payload = {
            "files": {
                "breakdown": str(breakdown_path),
                "cases": str(cases_path),
            }
        }
        index_path = artifacts_dir / "index.json"
        write_json(index_path, index_payload)

        artifacts_index = {
            "dir": str(artifacts_dir),
            "index": str(index_path),
        }
        envelope["artifacts"] = artifacts_index
        write_json(output_path, envelope)

        return artifacts_index
