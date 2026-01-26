"""Tests for dataset loaders."""

import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from evalvault.adapters.outbound.dataset.csv_loader import CSVDatasetLoader
from evalvault.adapters.outbound.dataset.excel_loader import ExcelDatasetLoader
from evalvault.adapters.outbound.dataset.json_loader import JSONDatasetLoader
from evalvault.adapters.outbound.dataset.loader_factory import get_loader
from evalvault.domain.entities.dataset import Dataset


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory path."""
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def csv_file(fixtures_dir):
    """Get CSV fixture file path."""
    return fixtures_dir / "sample_dataset.csv"


@pytest.fixture
def excel_file(fixtures_dir):
    """Get Excel fixture file path."""
    return fixtures_dir / "sample_dataset.xlsx"


@pytest.fixture
def json_file(fixtures_dir):
    """Get JSON fixture file path."""
    return fixtures_dir / "sample_dataset.json"


class TestCSVDatasetLoader:
    """Tests for CSV dataset loader."""

    def test_load_csv_with_json_contexts(self, csv_file):
        """Test loading CSV file with JSON array contexts."""
        loader = CSVDatasetLoader()
        dataset = loader.load(csv_file)

        assert isinstance(dataset, Dataset)
        assert len(dataset) == 4
        assert dataset.source_file == str(csv_file)

        # Check first test case (JSON contexts)
        tc = dataset.test_cases[0]
        assert tc.id == "test_001"
        assert tc.question == "What is Python?"
        assert tc.answer == "Python is a high-level programming language."
        assert len(tc.contexts) == 2
        assert tc.contexts[0] == "Python is a programming language"
        assert tc.ground_truth == "Python is a high-level interpreted programming language."

    def test_load_csv_with_pipe_separated_contexts(self, csv_file):
        """Test loading CSV file with pipe-separated contexts."""
        loader = CSVDatasetLoader()
        dataset = loader.load(csv_file)

        # Check last test case (pipe-separated contexts)
        tc = dataset.test_cases[3]
        assert tc.id == "test_004"
        assert len(tc.contexts) == 3
        assert tc.contexts[0] == "Test-Driven Development"
        assert tc.contexts[1] == "Write tests first"
        assert tc.contexts[2] == "Red-Green-Refactor cycle"

    def test_csv_loader_with_nonexistent_file(self):
        """Test CSV loader with non-existent file."""
        loader = CSVDatasetLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.csv")

    def test_csv_loader_creates_default_metadata(self, csv_file):
        """Test that CSV loader creates default name and version."""
        loader = CSVDatasetLoader()
        dataset = loader.load(csv_file)

        assert dataset.name == "sample_dataset"
        assert dataset.version == "1.0.0"

    def test_csv_loader_reads_thresholds(self, csv_file):
        """Test that CSV loader reads dataset-level thresholds."""
        loader = CSVDatasetLoader()
        dataset = loader.load(csv_file)

        assert dataset.thresholds["faithfulness"] == pytest.approx(0.7)
        assert dataset.thresholds["answer_relevancy"] == pytest.approx(0.7)

    def test_csv_loader_reads_metadata_columns(self, tmp_path):
        """Test CSV loader reads summary tags/intent and metadata JSON."""
        csv_path = tmp_path / "metadata_dataset.csv"
        with csv_path.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "id",
                    "question",
                    "answer",
                    "contexts",
                    "summary_tags",
                    "summary_intent",
                    "metadata",
                ]
            )
            writer.writerow(
                [
                    "tc-001",
                    "Question?",
                    "Answer",
                    json.dumps(["ctx"]),
                    "exclusion|limit",
                    "agent_notes",
                    json.dumps({"priority": "high"}),
                ]
            )

        loader = CSVDatasetLoader()
        dataset = loader.load(csv_path)

        metadata = dataset.test_cases[0].metadata
        assert metadata["summary_tags"] == ["exclusion", "limit"]
        assert metadata["summary_intent"] == "agent_notes"
        assert metadata["priority"] == "high"


class TestExcelDatasetLoader:
    """Tests for Excel dataset loader."""

    def test_load_excel_file(self, excel_file):
        """Test loading Excel file."""
        loader = ExcelDatasetLoader()
        dataset = loader.load(excel_file)

        assert isinstance(dataset, Dataset)
        assert len(dataset) == 4
        assert dataset.source_file == str(excel_file)

        # Verify data matches CSV loader
        tc = dataset.test_cases[0]
        assert tc.id == "test_001"
        assert tc.question == "What is Python?"
        assert len(tc.contexts) == 2

    def test_excel_loader_with_nonexistent_file(self):
        """Test Excel loader with non-existent file."""
        loader = ExcelDatasetLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.xlsx")

    def test_excel_loader_creates_default_metadata(self, excel_file):
        """Test that Excel loader creates default name and version."""
        loader = ExcelDatasetLoader()
        dataset = loader.load(excel_file)

        assert dataset.name == "sample_dataset"
        assert dataset.version == "1.0.0"

    def test_excel_loader_reads_thresholds(self, excel_file):
        """Test that Excel loader reads dataset-level thresholds."""
        loader = ExcelDatasetLoader()
        dataset = loader.load(excel_file)

        assert dataset.thresholds["faithfulness"] == pytest.approx(0.7)
        assert dataset.thresholds["answer_relevancy"] == pytest.approx(0.7)

    def test_excel_loader_reads_metadata_columns(self, tmp_path):
        """Test Excel loader reads summary tags/intent and metadata JSON."""
        df = pd.DataFrame(
            [
                {
                    "id": "tc-001",
                    "question": "Question?",
                    "answer": "Answer",
                    "contexts": '["ctx"]',
                    "summary_tags": "exclusion,limit",
                    "summary_intent": "agent_notes",
                    "metadata": '{"priority":"high"}',
                }
            ]
        )
        excel_path = tmp_path / "metadata_dataset.xlsx"
        df.to_excel(excel_path, index=False)

        loader = ExcelDatasetLoader()
        dataset = loader.load(excel_path)

        metadata = dataset.test_cases[0].metadata
        assert metadata["summary_tags"] == ["exclusion", "limit"]
        assert metadata["summary_intent"] == "agent_notes"
        assert metadata["priority"] == "high"


class TestJSONDatasetLoader:
    """Tests for JSON dataset loader."""

    def test_load_json_file(self, json_file):
        """Test loading JSON file."""
        loader = JSONDatasetLoader()
        dataset = loader.load(json_file)

        assert isinstance(dataset, Dataset)
        assert len(dataset) == 4
        assert dataset.name == "test_dataset"
        assert dataset.version == "1.0.0"
        assert dataset.source_file == str(json_file)

        # Check first test case
        tc = dataset.test_cases[0]
        assert tc.id == "test_001"
        assert tc.question == "What is Python?"
        assert tc.answer == "Python is a high-level programming language."
        assert len(tc.contexts) == 2
        assert tc.contexts[0] == "Python is a programming language"
        assert tc.ground_truth == "Python is a high-level interpreted programming language."

    def test_json_loader_with_nonexistent_file(self):
        """Test JSON loader with non-existent file."""
        loader = JSONDatasetLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent.json")

    def test_json_loader_with_invalid_format(self, tmp_path):
        """Test JSON loader with invalid JSON format."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json")

        loader = JSONDatasetLoader()
        with pytest.raises(ValueError, match="(Invalid JSON|Failed to read JSON)"):
            loader.load(invalid_file)

    def test_json_loader_with_missing_required_fields(self, tmp_path):
        """Test JSON loader with missing required fields."""
        invalid_file = tmp_path / "missing_fields.json"
        invalid_file.write_text(json.dumps({"name": "test"}))

        loader = JSONDatasetLoader()
        with pytest.raises(ValueError, match="Missing required field"):
            loader.load(invalid_file)


class TestLoaderFactory:
    """Tests for loader factory."""

    def test_get_csv_loader(self):
        """Test factory returns CSV loader for .csv files."""
        loader = get_loader("data.csv")
        assert isinstance(loader, CSVDatasetLoader)

    def test_get_excel_loader_xlsx(self):
        """Test factory returns Excel loader for .xlsx files."""
        loader = get_loader("data.xlsx")
        assert isinstance(loader, ExcelDatasetLoader)

    def test_get_excel_loader_xls(self):
        """Test factory returns Excel loader for .xls files."""
        loader = get_loader("data.xls")
        assert isinstance(loader, ExcelDatasetLoader)

    def test_get_json_loader(self):
        """Test factory returns JSON loader for .json files."""
        loader = get_loader("data.json")
        assert isinstance(loader, JSONDatasetLoader)

    def test_get_loader_with_path_object(self):
        """Test factory works with Path objects."""
        loader = get_loader(Path("data.csv"))
        assert isinstance(loader, CSVDatasetLoader)

    def test_get_loader_with_unsupported_extension(self):
        """Test factory raises error for unsupported file types."""
        with pytest.raises(ValueError, match="Unsupported file format"):
            get_loader("data.txt")

    def test_factory_end_to_end_csv(self, csv_file):
        """Test factory with actual CSV file."""
        loader = get_loader(csv_file)
        dataset = loader.load(csv_file)
        assert len(dataset) == 4

    def test_factory_end_to_end_excel(self, excel_file):
        """Test factory with actual Excel file."""
        loader = get_loader(excel_file)
        dataset = loader.load(excel_file)
        assert len(dataset) == 4

    def test_factory_end_to_end_json(self, json_file):
        """Test factory with actual JSON file."""
        loader = get_loader(json_file)
        dataset = loader.load(json_file)
        assert len(dataset) == 4


class TestDatasetConversion:
    """Test dataset conversion to Ragas format."""

    def test_dataset_to_ragas_list(self, json_file):
        """Test converting dataset to Ragas format."""
        loader = JSONDatasetLoader()
        dataset = loader.load(json_file)

        ragas_list = dataset.to_ragas_list()
        assert len(ragas_list) == 4

        # Check first item
        item = ragas_list[0]
        assert item["user_input"] == "What is Python?"
        assert item["response"] == "Python is a high-level programming language."
        assert item["retrieved_contexts"] == [
            "Python is a programming language",
            "Python was created by Guido van Rossum",
        ]
        assert item["reference"] == "Python is a high-level interpreted programming language."
