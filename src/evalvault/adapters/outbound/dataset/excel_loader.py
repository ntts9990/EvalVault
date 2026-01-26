"""Excel dataset loader implementation."""

from pathlib import Path

import pandas as pd

from evalvault.adapters.outbound.dataset.base import BaseDatasetLoader
from evalvault.adapters.outbound.dataset.thresholds import extract_thresholds_from_rows
from evalvault.domain.entities.dataset import Dataset, TestCase


class ExcelDatasetLoader(BaseDatasetLoader):
    """Loader for Excel format datasets (.xlsx, .xls).

    Cross-platform compatible:
    - .xlsx files: Uses openpyxl engine
    - .xls files: Uses xlrd engine (requires xlrd package)
    """

    def supports(self, file_path: str | Path) -> bool:
        """Check if file is an Excel file.

        Args:
            file_path: Path to check

        Returns:
            True if file has .xlsx or .xls extension
        """
        suffix = Path(file_path).suffix.lower()
        return suffix in [".xlsx", ".xls"]

    def _get_excel_engine(self, file_path: Path) -> str:
        """Determine the appropriate pandas engine for the Excel file.

        Args:
            file_path: Path to Excel file

        Returns:
            Engine name ('openpyxl' for .xlsx, 'xlrd' for .xls)
        """
        suffix = file_path.suffix.lower()
        if suffix == ".xls":
            return "xlrd"
        return "openpyxl"

    def load(self, file_path: str | Path) -> Dataset:
        """Load dataset from Excel file.

        Expected columns:
        - id: Test case identifier
        - question: Question text
        - answer: Answer text
        - contexts: Context strings (JSON array or pipe-separated)
        - ground_truth: Ground truth answer (optional)
        - threshold_*: Dataset-level metric thresholds (optional, first non-empty row wins)

        Args:
            file_path: Path to Excel file

        Returns:
            Dataset object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
        """
        path = self._validate_file_exists(file_path)
        engine = self._get_excel_engine(path)

        try:
            df = pd.read_excel(path, engine=engine)
        except ImportError as e:
            if engine == "xlrd":
                raise ValueError(
                    "xlrd package is required for .xls files. Install it with: pip install xlrd"
                ) from e
            raise
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {e}") from e

        # Validate required columns
        required_columns = ["id", "question", "answer", "contexts"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        thresholds = extract_thresholds_from_rows(df.head(50).to_dict(orient="records"))

        # Parse test cases
        test_cases = []
        for _, row in df.iterrows():
            contexts = self._parse_contexts(row["contexts"])
            ground_truth = (
                row["ground_truth"]
                if "ground_truth" in df.columns and pd.notna(row["ground_truth"])
                else None
            )

            metadata = {}
            if "metadata" in df.columns:
                try:
                    metadata = self._parse_metadata_cell(row["metadata"])
                except ValueError as exc:
                    raise ValueError(f"Test case {row['id']}: {exc}") from exc
            if "summary_tags" in df.columns:
                tags = self._parse_summary_tags_cell(row["summary_tags"])
                if tags:
                    metadata["summary_tags"] = tags
            if "summary_intent" in df.columns:
                intent = self._parse_summary_intent_cell(row["summary_intent"])
                if intent:
                    metadata["summary_intent"] = intent

            test_case = TestCase(
                id=str(row["id"]),
                question=str(row["question"]),
                answer=str(row["answer"]),
                contexts=contexts,
                ground_truth=ground_truth,
                metadata=metadata,
            )
            test_cases.append(test_case)

        # Create dataset
        dataset = Dataset(
            name=self._get_default_name(path),
            version=self._get_default_version(),
            test_cases=test_cases,
            source_file=str(path),
            thresholds=thresholds,
        )

        return dataset
