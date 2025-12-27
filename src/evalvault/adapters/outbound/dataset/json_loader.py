"""JSON dataset loader implementation."""

import json
from pathlib import Path

from evalvault.adapters.outbound.dataset.base import BaseDatasetLoader
from evalvault.domain.entities.dataset import Dataset, TestCase


class JSONDatasetLoader(BaseDatasetLoader):
    """Loader for JSON format datasets.

    Cross-platform compatible:
    - Handles UTF-8 BOM (common in Windows-generated files)
    - Falls back to standard UTF-8 if BOM encoding fails
    """

    def supports(self, file_path: str | Path) -> bool:
        """Check if file is a JSON file.

        Args:
            file_path: Path to check

        Returns:
            True if file has .json extension
        """
        return Path(file_path).suffix.lower() == ".json"

    def _read_json_with_bom_handling(self, path: Path) -> dict:
        """Read JSON file with BOM handling for cross-platform compatibility.

        Args:
            path: Path to JSON file

        Returns:
            Parsed JSON data

        Raises:
            ValueError: If JSON parsing fails
        """
        # Try UTF-8 with BOM first (handles Windows-generated files)
        encodings = ["utf-8-sig", "utf-8"]

        for encoding in encodings:
            try:
                with open(path, encoding=encoding) as f:
                    return json.load(f)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

        # If all encodings fail, raise with the last error
        raise ValueError(f"Failed to read JSON file with encodings: {encodings}")

    def load(self, file_path: str | Path) -> Dataset:
        """Load dataset from JSON file.

        Expected format:
        {
            "name": "dataset_name",
            "version": "1.0.0",
            "thresholds": {
                "faithfulness": 0.8,
                "answer_relevancy": 0.7
            },
            "test_cases": [
                {
                    "id": "test_001",
                    "question": "Question text",
                    "answer": "Answer text",
                    "contexts": ["context1", "context2"],
                    "ground_truth": "Ground truth text (optional)"
                }
            ],
            "metadata": {} (optional)
        }

        Args:
            file_path: Path to JSON file

        Returns:
            Dataset object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON format is invalid or missing required fields
        """
        path = self._validate_file_exists(file_path)

        try:
            data = self._read_json_with_bom_handling(path)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to read JSON file: {e}") from e

        # Validate required fields
        required_fields = ["test_cases"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required field: {missing_fields[0]}")

        # Parse test cases
        test_cases = []
        for idx, tc_data in enumerate(data["test_cases"]):
            # Validate test case fields
            tc_required = ["id", "question", "answer", "contexts"]
            tc_missing = [field for field in tc_required if field not in tc_data]
            if tc_missing:
                raise ValueError(f"Test case {idx}: missing required field '{tc_missing[0]}'")

            test_case = TestCase(
                id=str(tc_data["id"]),
                question=str(tc_data["question"]),
                answer=str(tc_data["answer"]),
                contexts=tc_data["contexts"],
                ground_truth=tc_data.get("ground_truth"),
                metadata=tc_data.get("metadata", {}),
            )
            test_cases.append(test_case)

        # Parse thresholds (validate values are between 0.0 and 1.0)
        thresholds = {}
        raw_thresholds = data.get("thresholds", {})
        for metric_name, threshold_value in raw_thresholds.items():
            if not isinstance(threshold_value, int | float):
                raise ValueError(f"Invalid threshold value for '{metric_name}': must be a number")
            if not 0.0 <= threshold_value <= 1.0:
                raise ValueError(
                    f"Invalid threshold value for '{metric_name}': must be between 0.0 and 1.0"
                )
            thresholds[metric_name] = float(threshold_value)

        # Create dataset
        dataset = Dataset(
            name=data.get("name", self._get_default_name(path)),
            version=data.get("version", self._get_default_version()),
            test_cases=test_cases,
            metadata=data.get("metadata", {}),
            source_file=str(path),
            thresholds=thresholds,
        )

        return dataset
