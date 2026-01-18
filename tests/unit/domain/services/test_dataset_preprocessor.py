from evalvault.domain.entities import Dataset, TestCase
from evalvault.domain.services.dataset_preprocessor import (
    DatasetPreprocessConfig,
    DatasetPreprocessor,
)


def test_preprocess_expands_short_reference_from_answer():
    dataset = Dataset(
        name="sample",
        version="1",
        test_cases=[
            TestCase(
                id="tc-1",
                question="이 보험의 사망보험금은 얼마인가요?",
                answer="해당 보험의 사망보험금은 1억원입니다.",
                contexts=["본 보험계약의 사망보험금은 1억원이며 지급됩니다."],
                ground_truth="1억원",
            )
        ],
    )
    preprocessor = DatasetPreprocessor(DatasetPreprocessConfig(min_reference_chars=6))

    report = preprocessor.apply(dataset, metrics=["context_recall"])

    assert dataset.test_cases[0].ground_truth == dataset.test_cases[0].answer
    assert report.references_filled_from_answer == 1


def test_preprocess_fills_missing_reference_from_context():
    dataset = Dataset(
        name="sample",
        version="1",
        test_cases=[
            TestCase(
                id="tc-2",
                question="사망보험금은 얼마인가요?",
                answer="",
                contexts=["사망보험금은 1억원입니다."],
                ground_truth=None,
            )
        ],
    )
    preprocessor = DatasetPreprocessor(DatasetPreprocessConfig(min_reference_chars=6))

    report = preprocessor.apply(dataset, metrics=["context_recall"])

    assert dataset.test_cases[0].ground_truth == "사망보험금은 1억원입니다."
    assert report.references_filled_from_context == 1


def test_preprocess_dedupes_and_trims_contexts():
    dataset = Dataset(
        name="sample",
        version="1",
        test_cases=[
            TestCase(
                id="tc-3",
                question="질문",
                answer="답변",
                contexts=[" ", " 내용  ", "내용", "다른"],
                ground_truth="정답",
            )
        ],
    )
    preprocessor = DatasetPreprocessor(DatasetPreprocessConfig(min_reference_chars=2))

    report = preprocessor.apply(dataset, metrics=["faithfulness"])

    assert dataset.test_cases[0].contexts == ["내용", "다른"]
    assert report.contexts_removed == 1
    assert report.contexts_deduped == 1


def test_preprocess_prefers_same_language_reference():
    dataset = Dataset(
        name="sample",
        version="1",
        test_cases=[
            TestCase(
                id="tc-4",
                question="사망보험금은 얼마인가요?",
                answer="The death benefit is 100 million won.",
                contexts=["사망보험금은 1억원입니다."],
                ground_truth="1억원",
            )
        ],
    )
    preprocessor = DatasetPreprocessor(DatasetPreprocessConfig(min_reference_chars=6))

    report = preprocessor.apply(dataset, metrics=["context_recall"])

    assert dataset.test_cases[0].ground_truth == "사망보험금은 1억원입니다."
    assert report.references_filled_from_context == 1


def test_preprocess_drops_noise_contexts():
    dataset = Dataset(
        name="sample",
        version="1",
        test_cases=[
            TestCase(
                id="tc-5",
                question="질문",
                answer="답변",
                contexts=["---", "...", "내용"],
                ground_truth="정답",
            )
        ],
    )
    preprocessor = DatasetPreprocessor(DatasetPreprocessConfig(min_reference_chars=2))

    report = preprocessor.apply(dataset, metrics=["faithfulness"])

    assert dataset.test_cases[0].contexts == ["내용"]
    assert report.contexts_removed == 2


def test_preprocess_treats_placeholder_reference_as_missing():
    dataset = Dataset(
        name="sample",
        version="1",
        test_cases=[
            TestCase(
                id="tc-6",
                question="사망보험금은 얼마인가요?",
                answer="N/A",
                contexts=["사망보험금은 1억원입니다."],
                ground_truth="null",
            )
        ],
    )
    preprocessor = DatasetPreprocessor(DatasetPreprocessConfig(min_reference_chars=6))

    report = preprocessor.apply(dataset, metrics=["context_recall"])

    assert dataset.test_cases[0].ground_truth == "사망보험금은 1억원입니다."
    assert report.references_filled_from_context == 1
    assert report.references_missing == 1
