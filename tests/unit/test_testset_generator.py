"""Unit tests for testset generator."""

import pytest

from evalvault.domain.entities import Dataset
from evalvault.domain.services.document_chunker import DocumentChunker
from evalvault.domain.services.testset_generator import (
    BasicTestsetGenerator,
    GenerationConfig,
)


class TestDocumentChunker:
    """Test suite for DocumentChunker."""

    def test_chunk_by_sentences(self):
        """Test chunking document by sentences."""
        chunker = DocumentChunker(chunk_size=100, overlap=0)
        document = (
            "이것은 첫 번째 문장입니다. 이것은 두 번째 문장입니다. 이것은 세 번째 문장입니다."
        )

        chunks = chunker.chunk(document)
        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)

    def test_chunk_with_overlap(self):
        """Test chunking with overlap between chunks."""
        chunker = DocumentChunker(chunk_size=30, overlap=10)
        document = "첫 번째 문장입니다. 두 번째 문장입니다. 세 번째 문장입니다. 네 번째 문장입니다."

        chunks = chunker.chunk(document)
        assert len(chunks) >= 2

    def test_chunk_short_document(self):
        """Test chunking document shorter than chunk size."""
        chunker = DocumentChunker(chunk_size=1000, overlap=0)
        document = "짧은 문서입니다."

        chunks = chunker.chunk(document)
        assert len(chunks) == 1
        assert chunks[0] == document

    def test_chunk_empty_document(self):
        """Test chunking empty document."""
        chunker = DocumentChunker(chunk_size=100, overlap=0)
        chunks = chunker.chunk("")
        assert chunks == []

    def test_chunk_preserves_content(self):
        """Test that chunking preserves all document content."""
        chunker = DocumentChunker(chunk_size=20, overlap=0)
        document = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        chunks = chunker.chunk(document)
        combined = "".join(chunks)
        assert document in combined or len(combined) >= len(document)


class TestGenerationConfig:
    """Test suite for GenerationConfig."""

    def test_default_config(self):
        """Test default generation configuration."""
        config = GenerationConfig()
        assert config.num_questions > 0
        assert config.chunk_size > 0
        assert config.chunk_overlap >= 0

    def test_custom_config(self):
        """Test custom generation configuration."""
        config = GenerationConfig(
            num_questions=20,
            chunk_size=500,
            chunk_overlap=50,
        )
        assert config.num_questions == 20
        assert config.chunk_size == 500
        assert config.chunk_overlap == 50


class TestBasicTestsetGenerator:
    """Test suite for BasicTestsetGenerator."""

    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return [
            "보험 상품의 보장 내용은 다음과 같습니다. 사망 시 1억원을 지급합니다.",
            "월 보험료는 50,000원이며, 보험 기간은 10년입니다.",
            "암 진단 시 3천만원의 진단비를 지급합니다.",
        ]

    def test_initialization(self):
        """Test generator initialization."""
        generator = BasicTestsetGenerator()
        assert generator is not None

    def test_chunk_documents(self, sample_documents):
        """Test document chunking."""
        generator = BasicTestsetGenerator()
        config = GenerationConfig(chunk_size=50, chunk_overlap=10)

        chunks = generator._chunk_documents(sample_documents, config)
        assert len(chunks) > 0
        assert all(isinstance(c, str) for c in chunks)

    def test_generate_creates_dataset(self, sample_documents):
        """Test that generate creates a Dataset object."""
        generator = BasicTestsetGenerator()
        config = GenerationConfig(num_questions=2)

        dataset = generator.generate(sample_documents, config)
        assert isinstance(dataset, Dataset)
        assert dataset.name == "generated-testset"

    def test_generate_creates_test_cases(self, sample_documents):
        """Test that generate creates test cases."""
        generator = BasicTestsetGenerator()
        config = GenerationConfig(num_questions=3)

        dataset = generator.generate(sample_documents, config)
        assert len(dataset.test_cases) > 0
        assert len(dataset.test_cases) <= config.num_questions

    def test_generate_test_case_structure(self, sample_documents):
        """Test that generated test cases have correct structure."""
        generator = BasicTestsetGenerator()
        config = GenerationConfig(num_questions=1)

        dataset = generator.generate(sample_documents, config)
        tc = dataset.test_cases[0]

        assert tc.id is not None
        assert tc.question is not None and len(tc.question) > 0
        assert tc.answer is not None  # May be empty for generation-only
        assert tc.contexts is not None and len(tc.contexts) > 0

    def test_generate_with_empty_documents(self):
        """Test generation with empty document list."""
        generator = BasicTestsetGenerator()
        config = GenerationConfig(num_questions=5)

        dataset = generator.generate([], config)
        assert len(dataset.test_cases) == 0

    def test_generate_extracts_contexts_from_chunks(self, sample_documents):
        """Test that contexts are extracted from document chunks."""
        generator = BasicTestsetGenerator()
        config = GenerationConfig(num_questions=2, chunk_size=100)

        dataset = generator.generate(sample_documents, config)
        for tc in dataset.test_cases:
            assert len(tc.contexts) > 0
            # Context should come from original documents
            assert any(
                any(word in context for word in doc.split()[:3])
                for doc in sample_documents
                for context in tc.contexts
            )

    def test_generate_creates_diverse_questions(self, sample_documents):
        """Test that generated questions are diverse."""
        generator = BasicTestsetGenerator()
        config = GenerationConfig(num_questions=3)

        dataset = generator.generate(sample_documents, config)
        questions = [tc.question for tc in dataset.test_cases]

        # Questions should not all be identical
        assert len(set(questions)) > 1 or len(questions) == 1

    def test_generate_with_custom_name(self, sample_documents):
        """Test generation with custom dataset name."""
        generator = BasicTestsetGenerator()
        config = GenerationConfig(num_questions=2, dataset_name="my-testset")

        dataset = generator.generate(sample_documents, config)
        assert dataset.name == "my-testset"

    def test_generate_sets_metadata(self, sample_documents):
        """Test that generated dataset has metadata."""
        generator = BasicTestsetGenerator()
        config = GenerationConfig(num_questions=2)

        dataset = generator.generate(sample_documents, config)
        assert dataset.metadata is not None
        assert "generated_at" in dataset.metadata
        assert "num_source_documents" in dataset.metadata
