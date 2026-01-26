"""CSV dataset loader implementation."""

from pathlib import Path

import pandas as pd

from evalvault.adapters.outbound.dataset.base import BaseDatasetLoader
from evalvault.adapters.outbound.dataset.thresholds import extract_thresholds_from_rows
from evalvault.domain.entities.dataset import Dataset, TestCase

# Common encodings to try for cross-platform compatibility
# Order: UTF-8 with BOM -> UTF-8 -> CP949 (Korean Windows) -> EUC-KR -> Latin-1 (fallback)
ENCODING_FALLBACKS = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1"]


class CSVDatasetLoader(BaseDatasetLoader):
    """Loader for CSV format datasets.

    Cross-platform compatible:
    - Tries multiple encodings for Windows/macOS/Linux compatibility
    - Handles UTF-8 BOM (common in Windows-generated files)
    - Falls back to common Korean encodings (CP949, EUC-KR)
    """

    def supports(self, file_path: str | Path) -> bool:
        """Check if file is a CSV file.

        Args:
            file_path: Path to check

        Returns:
            True if file has .csv extension
        """
        return Path(file_path).suffix.lower() == ".csv"

    def _read_csv_with_encoding_fallback(self, path: Path) -> pd.DataFrame:
        """Read CSV file with automatic encoding detection.

        Tries multiple encodings in order until one succeeds.
        Optionally uses chardet for detection if available.

        Args:
            path: Path to CSV file

        Returns:
            DataFrame from CSV

        Raises:
            ValueError: If no encoding works
        """
        # Try chardet first if available
        try:
            import chardet

            with open(path, "rb") as f:
                raw_data = f.read()
                detected = chardet.detect(raw_data)
                if detected["encoding"] and detected["confidence"] > 0.7:
                    try:
                        return pd.read_csv(path, encoding=detected["encoding"])
                    except (UnicodeDecodeError, LookupError):
                        pass  # Fall through to manual attempts
        except ImportError:
            pass  # chardet not installed, use fallback list

        # Try each encoding in order
        errors = []
        for encoding in ENCODING_FALLBACKS:
            try:
                return pd.read_csv(path, encoding=encoding)
            except UnicodeDecodeError as e:
                errors.append(f"{encoding}: {e}")
            except LookupError:
                errors.append(f"{encoding}: unknown encoding")

        raise ValueError(
            f"Failed to read CSV file with any encoding. Tried: {', '.join(ENCODING_FALLBACKS)}"
        )

    def load(self, file_path: str | Path) -> Dataset:
        """Load dataset from CSV file.

        Expected columns:
        - id: Test case identifier
        - question: Question text
        - answer: Answer text
        - contexts: Context strings (JSON array or pipe-separated)
        - ground_truth: Ground truth answer (optional)
        - threshold_*: Dataset-level metric thresholds (optional, first non-empty row wins)

        Args:
            file_path: Path to CSV file

        Returns:
            Dataset object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
        """
        path = self._validate_file_exists(file_path)

        try:
            df = self._read_csv_with_encoding_fallback(path)
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}") from e

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
