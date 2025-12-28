"""Integration tests for data loading flow.

These tests verify the complete data loading pipeline works correctly.
"""

from pathlib import Path

import pytest

from evalvault.adapters.outbound.dataset import (
    CSVDatasetLoader,
    ExcelDatasetLoader,
    JSONDatasetLoader,
    get_loader,
)
from evalvault.domain.entities import Dataset, TestCase


class TestDataLoadingFlow:
    """데이터 로딩 플로우 통합 테스트."""

    @pytest.fixture
    def fixtures_path(self):
        """테스트 픽스처 경로."""
        return Path(__file__).parent.parent / "fixtures"

    def test_csv_to_ragas_format(self, fixtures_path):
        """CSV 파일 로드 -> Ragas 형식 변환 테스트."""
        csv_file = fixtures_path / "sample_dataset.csv"

        # Load dataset
        loader = get_loader(csv_file)
        assert isinstance(loader, CSVDatasetLoader)

        dataset = loader.load(csv_file)
        assert isinstance(dataset, Dataset)
        assert len(dataset) > 0

        # Convert to Ragas format
        ragas_list = dataset.to_ragas_list()
        assert len(ragas_list) == len(dataset)

        # Verify Ragas format
        for item in ragas_list:
            assert "user_input" in item
            assert "response" in item
            assert "retrieved_contexts" in item

    def test_excel_to_ragas_format(self, fixtures_path):
        """Excel 파일 로드 -> Ragas 형식 변환 테스트."""
        excel_file = fixtures_path / "sample_dataset.xlsx"

        loader = get_loader(excel_file)
        assert isinstance(loader, ExcelDatasetLoader)

        dataset = loader.load(excel_file)
        assert isinstance(dataset, Dataset)

        ragas_list = dataset.to_ragas_list()
        assert len(ragas_list) > 0

    def test_json_to_ragas_format(self, fixtures_path):
        """JSON 파일 로드 -> Ragas 형식 변환 테스트."""
        json_file = fixtures_path / "sample_dataset.json"

        loader = get_loader(json_file)
        assert isinstance(loader, JSONDatasetLoader)

        dataset = loader.load(json_file)
        assert isinstance(dataset, Dataset)

        ragas_list = dataset.to_ragas_list()
        assert len(ragas_list) > 0

    def test_dataset_metadata_preserved(self, fixtures_path):
        """데이터셋 메타데이터가 보존되는지 테스트."""
        json_file = fixtures_path / "sample_dataset.json"

        loader = get_loader(json_file)
        dataset = loader.load(json_file)

        # JSON dataset should have name and version from file
        assert dataset.name
        assert dataset.version
        assert dataset.source_file == str(json_file)

    def test_multiple_formats_consistent(self, fixtures_path):
        """여러 형식의 데이터가 일관된 구조를 가지는지 테스트."""
        csv_dataset = get_loader(fixtures_path / "sample_dataset.csv").load(
            fixtures_path / "sample_dataset.csv"
        )
        excel_dataset = get_loader(fixtures_path / "sample_dataset.xlsx").load(
            fixtures_path / "sample_dataset.xlsx"
        )

        # Both should have same number of test cases
        assert len(csv_dataset) == len(excel_dataset)

        # Both should have same test case IDs
        csv_ids = {tc.id for tc in csv_dataset}
        excel_ids = {tc.id for tc in excel_dataset}
        assert csv_ids == excel_ids


class TestTestCaseValidation:
    """테스트 케이스 유효성 검증 통합 테스트."""

    def test_test_case_required_fields(self):
        """필수 필드가 있는 테스트 케이스 생성."""
        tc = TestCase(
            id="tc-001",
            question="What is the answer?",
            answer="This is the answer.",
            contexts=["Context 1", "Context 2"],
        )

        assert tc.id == "tc-001"
        assert tc.question
        assert tc.answer
        assert len(tc.contexts) == 2
        assert tc.ground_truth is None

    def test_test_case_with_ground_truth(self):
        """ground_truth가 있는 테스트 케이스."""
        tc = TestCase(
            id="tc-001",
            question="What is Python?",
            answer="Python is a language.",
            contexts=["Python is a programming language."],
            ground_truth="A programming language",
        )

        ragas_dict = tc.to_ragas_dict()
        assert "reference" in ragas_dict
        assert ragas_dict["reference"] == "A programming language"

    def test_test_case_ragas_mapping(self):
        """Ragas 필드 매핑이 올바른지 테스트."""
        tc = TestCase(
            id="tc-001",
            question="Question",
            answer="Answer",
            contexts=["Context"],
        )

        ragas_dict = tc.to_ragas_dict()

        # Verify Ragas field names
        assert ragas_dict["user_input"] == "Question"
        assert ragas_dict["response"] == "Answer"
        assert ragas_dict["retrieved_contexts"] == ["Context"]
