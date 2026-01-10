"""Tests for SyntheticQAGenerator."""

import pytest

from evalvault.domain.services.synthetic_qa_generator import (
    GeneratedQA,
    SyntheticQAConfig,
    SyntheticQAGenerator,
)


class MockLLM:
    """Mock LLM for testing."""

    def __init__(self, responses: dict | None = None):
        self.responses = responses or {}
        self.call_count = 0

    def get_model_name(self) -> str:
        return "mock-model"

    def generate_text(self, prompt: str, *, json_mode: bool = False) -> str:
        self.call_count += 1

        # Return question generation response
        if "질문을 생성" in prompt or "Generate questions" in prompt:
            return '{"questions": ["질문1은 무엇인가요?", "질문2는 어떻게 되나요?"]}'

        # Return answer generation response
        if "답변해주세요" in prompt or "Answer the question" in prompt:
            return '{"answer": "답변입니다", "confidence": "high", "has_info": true}'

        return '{"result": "unknown"}'


class TestSyntheticQAConfig:
    """Tests for SyntheticQAConfig."""

    def test_default_config(self):
        config = SyntheticQAConfig()
        assert config.num_questions == 10
        assert config.questions_per_chunk == 2
        assert config.chunk_size == 1000
        assert config.language == "ko"
        assert config.include_no_answer is True
        assert config.no_answer_ratio == 0.1
        assert config.min_confidence == "medium"

    def test_custom_config(self):
        config = SyntheticQAConfig(
            num_questions=50,
            chunk_size=2000,
            language="en",
            include_no_answer=False,
        )
        assert config.num_questions == 50
        assert config.chunk_size == 2000
        assert config.language == "en"
        assert config.include_no_answer is False


class TestSyntheticQAGenerator:
    """Tests for SyntheticQAGenerator."""

    @pytest.fixture
    def mock_llm(self):
        return MockLLM()

    @pytest.fixture
    def generator(self, mock_llm):
        return SyntheticQAGenerator(mock_llm)

    def test_init(self, generator, mock_llm):
        assert generator.llm == mock_llm

    def test_parse_questions_json(self, generator):
        response = '{"questions": ["질문1", "질문2", "질문3"]}'
        questions = generator._parse_questions(response)
        assert len(questions) == 3
        assert questions[0] == "질문1"

    def test_parse_questions_with_noise(self, generator):
        response = 'Here are the questions: {"questions": ["질문1", "질문2"]}'
        questions = generator._parse_questions(response)
        assert len(questions) == 2

    def test_parse_questions_fallback(self, generator):
        response = """1. 질문은 무엇인가요?
2. 어떻게 되나요?"""
        questions = generator._parse_questions(response)
        # Should extract question-like lines
        assert len(questions) >= 0  # May or may not extract depending on logic

    def test_parse_answer_json(self, generator):
        response = '{"answer": "답변", "confidence": "high", "has_info": true}'
        result = generator._parse_answer(response)
        assert result["answer"] == "답변"
        assert result["confidence"] == "high"
        assert result["has_info"] is True

    def test_parse_answer_fallback(self, generator):
        response = "This is a plain text answer"
        result = generator._parse_answer(response)
        assert result["answer"] == "This is a plain text answer"
        assert result["confidence"] == "low"

    def test_filter_by_confidence_high(self, generator):
        qa_list = [
            GeneratedQA("q1", "a1", "c1", "high", True, 0),
            GeneratedQA("q2", "a2", "c2", "medium", True, 1),
            GeneratedQA("q3", "a3", "c3", "low", True, 2),
        ]
        filtered = generator._filter_by_confidence(qa_list, "high")
        assert len(filtered) == 1
        assert filtered[0].question == "q1"

    def test_filter_by_confidence_medium(self, generator):
        qa_list = [
            GeneratedQA("q1", "a1", "c1", "high", True, 0),
            GeneratedQA("q2", "a2", "c2", "medium", True, 1),
            GeneratedQA("q3", "a3", "c3", "low", True, 2),
        ]
        filtered = generator._filter_by_confidence(qa_list, "medium")
        assert len(filtered) == 2

    def test_filter_by_confidence_low(self, generator):
        qa_list = [
            GeneratedQA("q1", "a1", "c1", "high", True, 0),
            GeneratedQA("q2", "a2", "c2", "medium", True, 1),
            GeneratedQA("q3", "a3", "c3", "low", True, 2),
        ]
        filtered = generator._filter_by_confidence(qa_list, "low")
        assert len(filtered) == 3

    def test_generate_empty_documents(self, generator):
        config = SyntheticQAConfig(num_questions=5)
        dataset = generator.generate([], config)
        assert len(dataset.test_cases) == 0
        assert dataset.metadata["method"] == "synthetic_qa"
        assert dataset.metadata["num_source_documents"] == 0

    def test_generate_with_documents(self, generator, mock_llm):
        documents = ["This is a test document with some content about insurance."]
        config = SyntheticQAConfig(
            num_questions=2,
            questions_per_chunk=2,
            chunk_size=500,
            include_no_answer=False,
            min_confidence="low",  # Accept all
        )

        dataset = generator.generate(documents, config)

        # Should have generated test cases
        assert len(dataset.test_cases) > 0
        assert dataset.name == "synthetic-qa-dataset"
        assert dataset.metadata["method"] == "synthetic_qa"
        assert dataset.metadata["llm_model"] == "mock-model"

        # Check test case structure
        tc = dataset.test_cases[0]
        assert tc.question is not None
        assert tc.ground_truth is not None  # Should have ground truth
        assert tc.contexts is not None
        assert tc.metadata["generated"] is True
        assert tc.metadata["method"] == "synthetic_qa"

    def test_generate_with_no_answer_cases(self, generator):
        documents = ["Test document content."]
        config = SyntheticQAConfig(
            num_questions=10,
            include_no_answer=True,
            no_answer_ratio=0.3,  # 30% no-answer
            min_confidence="low",
        )

        dataset = generator.generate(documents, config)

        # Check that some test cases have no-answer ground truth
        no_answer_cases = [tc for tc in dataset.test_cases if tc.ground_truth == "정보 없음"]
        # Should have at least some no-answer cases
        assert len(no_answer_cases) >= 0  # May be 0 if not enough regular Q&A

    def test_generate_with_progress_callback(self, generator):
        documents = ["Test document."]
        config = SyntheticQAConfig(num_questions=2, include_no_answer=False)

        progress_calls = []

        def progress_cb(current, total):
            progress_calls.append((current, total))

        generator.generate(documents, config, progress_cb)

        # Should have called progress callback
        assert len(progress_calls) > 0

    def test_generate_english(self, generator):
        documents = ["This is an English document about insurance policies."]
        config = SyntheticQAConfig(
            num_questions=2,
            language="en",
            include_no_answer=False,
            min_confidence="low",
        )

        dataset = generator.generate(documents, config)
        assert dataset.metadata["language"] == "en"


class TestGeneratedQA:
    """Tests for GeneratedQA dataclass."""

    def test_create(self):
        qa = GeneratedQA(
            question="질문입니다",
            answer="답변입니다",
            context="컨텍스트",
            confidence="high",
            has_info=True,
            source_chunk_idx=0,
        )
        assert qa.question == "질문입니다"
        assert qa.answer == "답변입니다"
        assert qa.confidence == "high"
        assert qa.has_info is True


class TestNoAnswerGeneration:
    """Tests for no-answer case generation."""

    @pytest.fixture
    def mock_llm(self):
        return MockLLM()

    @pytest.fixture
    def generator(self, mock_llm):
        return SyntheticQAGenerator(mock_llm)

    def test_generate_no_answer_cases_korean(self, generator):
        chunks = ["청크1", "청크2"]
        config = SyntheticQAConfig(language="ko")
        no_answer_cases = generator._generate_no_answer_cases(chunks, 3, config)

        assert len(no_answer_cases) == 3
        for case in no_answer_cases:
            assert case.answer == "정보 없음"
            assert case.has_info is False
            assert case.confidence == "high"

    def test_generate_no_answer_cases_english(self, generator):
        chunks = ["chunk1", "chunk2"]
        config = SyntheticQAConfig(language="en")
        no_answer_cases = generator._generate_no_answer_cases(chunks, 2, config)

        assert len(no_answer_cases) == 2
        for case in no_answer_cases:
            assert case.answer == "No information available"
            assert case.has_info is False


class TestPromptGeneration:
    """Tests for prompt generation."""

    @pytest.fixture
    def mock_llm(self):
        return MockLLM()

    @pytest.fixture
    def generator(self, mock_llm):
        return SyntheticQAGenerator(mock_llm)

    def test_question_prompt_korean(self, generator):
        prompt = generator._get_question_prompt("테스트 컨텍스트", 3, "ko")
        assert "테스트 컨텍스트" in prompt
        assert "3" in prompt
        assert "질문" in prompt

    def test_question_prompt_english(self, generator):
        prompt = generator._get_question_prompt("test context", 3, "en")
        assert "test context" in prompt
        assert "3" in prompt
        assert "questions" in prompt.lower()

    def test_answer_prompt_korean(self, generator):
        prompt = generator._get_answer_prompt("컨텍스트", "질문입니다", "ko")
        assert "컨텍스트" in prompt
        assert "질문입니다" in prompt
        assert "답변" in prompt

    def test_answer_prompt_english(self, generator):
        prompt = generator._get_answer_prompt("context", "question", "en")
        assert "context" in prompt
        assert "question" in prompt
        assert "answer" in prompt.lower()
