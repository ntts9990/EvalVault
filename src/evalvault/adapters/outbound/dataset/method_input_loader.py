"""Loader for base question datasets used by method plugins."""

from __future__ import annotations

import json
from pathlib import Path

from evalvault.domain.entities.method import MethodInput, MethodInputDataset


class MethodInputDatasetLoader:
    """Load question-first datasets for method execution."""

    def load(self, file_path: str | Path) -> MethodInputDataset:
        path = self._validate_file_exists(file_path)
        data = self._read_json_with_bom_handling(path)

        if "test_cases" not in data:
            raise ValueError("Missing required field: test_cases")

        test_cases: list[MethodInput] = []
        for idx, tc_data in enumerate(data["test_cases"]):
            if "id" not in tc_data or "question" not in tc_data:
                raise ValueError(f"Test case {idx}: missing required field 'id' or 'question'")

            contexts = tc_data.get("contexts")
            if isinstance(contexts, str):
                contexts = self._parse_contexts(contexts)
            if contexts is None:
                contexts = []

            test_cases.append(
                MethodInput(
                    id=str(tc_data["id"]),
                    question=str(tc_data["question"]),
                    ground_truth=tc_data.get("ground_truth"),
                    contexts=contexts,
                    metadata=tc_data.get("metadata", {}),
                )
            )

        thresholds: dict[str, float] = {}
        raw_thresholds = data.get("thresholds", {})
        for metric_name, threshold_value in raw_thresholds.items():
            if not isinstance(threshold_value, int | float):
                raise ValueError(f"Invalid threshold value for '{metric_name}': must be a number")
            if not 0.0 <= threshold_value <= 1.0:
                raise ValueError(
                    f"Invalid threshold value for '{metric_name}': must be between 0.0 and 1.0"
                )
            thresholds[metric_name] = float(threshold_value)

        return MethodInputDataset(
            name=data.get("name", path.stem),
            version=data.get("version", "1.0.0"),
            test_cases=test_cases,
            metadata=data.get("metadata", {}),
            thresholds=thresholds,
            source_file=str(path),
        )

    def _read_json_with_bom_handling(self, path: Path) -> dict:
        encodings = ["utf-8-sig", "utf-8"]
        for encoding in encodings:
            try:
                with open(path, encoding=encoding) as f:
                    return json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        raise ValueError(f"Failed to read JSON file with encodings: {encodings}")

    def _parse_contexts(self, contexts_str: str) -> list[str]:
        if not contexts_str:
            return []
        contexts_str = str(contexts_str).strip()
        if contexts_str.startswith("["):
            try:
                value = json.loads(contexts_str)
                if isinstance(value, list):
                    return [str(item) for item in value]
            except json.JSONDecodeError:
                pass
        return [ctx.strip() for ctx in contexts_str.split("|") if ctx.strip()]

    def _normalize_path(self, file_path: str | Path) -> Path:
        path = Path(file_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            return path.resolve()
        except OSError:
            return path.absolute()

    def _validate_file_exists(self, file_path: str | Path) -> Path:
        path = self._normalize_path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        return path
