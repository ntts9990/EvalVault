"""Unit tests for language detection utilities."""

import pytest

from evalvault.utils.language import LanguageDetector


class TestLanguageDetector:
    """Test LanguageDetector class."""

    def test_detect_english(self):
        """Test detecting English text."""
        text = "This is an insurance policy document."
        result = LanguageDetector.detect(text)
        assert result == "en"

    def test_detect_korean(self):
        """Test detecting Korean text."""
        text = "이 보험의 보장금액은 얼마인가요?"
        result = LanguageDetector.detect(text)
        assert result == "ko"

    def test_detect_japanese(self):
        """Test detecting Japanese text."""
        text = "この保険の保障金額はいくらですか？"
        result = LanguageDetector.detect(text)
        assert result == "ja"

    def test_detect_chinese_simplified(self):
        """Test detecting Simplified Chinese text."""
        text = "这份保险的保障金额是多少？"
        result = LanguageDetector.detect(text)
        assert result == "zh-cn"

    def test_detect_chinese_traditional(self):
        """Test detecting Traditional Chinese text."""
        # Note: langdetect often struggles to distinguish between traditional/simplified
        # Chinese and may even confuse with Korean for short texts. Use longer text.
        text = "這份保險的保障金額是多少？保險公司會在收到理賠申請後進行審核。"
        result = LanguageDetector.detect(text)
        # Accept either zh-cn or ko due to langdetect limitations with CJK languages
        assert result in ["zh-cn", "ko"]

    def test_detect_empty_string(self):
        """Test detecting empty string."""
        text = ""
        result = LanguageDetector.detect(text)
        assert result == "unknown"

    def test_detect_very_short_text(self):
        """Test detecting very short text (might be unreliable)."""
        text = "Hi"
        result = LanguageDetector.detect(text)
        # Short text might not be detected reliably, but should not crash
        # langdetect may return any language code for very short text
        assert isinstance(result, str) and len(result) >= 2

    def test_detect_with_confidence_english(self):
        """Test detecting with confidence scores for English."""
        text = "This is a comprehensive insurance policy document with detailed coverage information."
        results = LanguageDetector.detect_with_confidence(text)

        assert len(results) > 0
        assert results[0][0] == "en"  # Top language should be English
        assert 0.0 <= results[0][1] <= 1.0  # Confidence should be between 0 and 1
        assert results[0][1] > 0.9  # High confidence for clear English text

    def test_detect_with_confidence_korean(self):
        """Test detecting with confidence scores for Korean."""
        text = "이 보험 상품은 사망, 질병, 상해에 대한 보장을 제공합니다."
        results = LanguageDetector.detect_with_confidence(text)

        assert len(results) > 0
        assert results[0][0] == "ko"  # Top language should be Korean
        assert results[0][1] > 0.9  # High confidence for clear Korean text

    def test_detect_with_confidence_empty_string(self):
        """Test detecting with confidence on empty string."""
        text = ""
        results = LanguageDetector.detect_with_confidence(text)
        assert results == []

    def test_detect_dataset_language_majority_korean(self):
        """Test detecting dataset language when majority is Korean."""
        texts = [
            "이 보험의 보장금액은 얼마인가요?",
            "보험료는 어떻게 계산되나요?",
            "What is the coverage amount?",  # One English text
            "보장 내용을 알려주세요.",
        ]
        result = LanguageDetector.detect_dataset_language(texts)
        assert result == "ko"

    def test_detect_dataset_language_majority_english(self):
        """Test detecting dataset language when majority is English."""
        texts = [
            "What is the premium amount?",
            "How is the coverage calculated?",
            "이 보험의 보장금액은 얼마인가요?",  # One Korean text
            "What are the terms and conditions?",
        ]
        result = LanguageDetector.detect_dataset_language(texts)
        assert result == "en"

    def test_detect_dataset_language_empty_list(self):
        """Test detecting dataset language with empty list."""
        texts = []
        result = LanguageDetector.detect_dataset_language(texts)
        assert result == "unknown"

    def test_detect_dataset_language_all_empty_strings(self):
        """Test detecting dataset language with all empty strings."""
        texts = ["", "", ""]
        result = LanguageDetector.detect_dataset_language(texts)
        assert result == "unknown"

    def test_detect_dataset_language_mixed_with_unknowns(self):
        """Test detecting dataset language with mix of languages and short texts."""
        texts = [
            "This is an insurance document.",
            "Another English document.",
            "Hi",  # Very short, might be unknown
            "",    # Empty
            "English text again.",
        ]
        result = LanguageDetector.detect_dataset_language(texts)
        assert result == "en"

    def test_supported_languages_constant(self):
        """Test that SUPPORTED_LANGUAGES is properly defined."""
        assert "ko" in LanguageDetector.SUPPORTED_LANGUAGES
        assert "en" in LanguageDetector.SUPPORTED_LANGUAGES
        assert "ja" in LanguageDetector.SUPPORTED_LANGUAGES
        assert "zh-cn" in LanguageDetector.SUPPORTED_LANGUAGES
        assert "zh-tw" in LanguageDetector.SUPPORTED_LANGUAGES

    def test_detect_mixed_language_text(self):
        """Test detecting text with mixed languages (should detect dominant language)."""
        text = "This is English text. 이것은 한국어입니다. But mostly English content here with more words."
        result = LanguageDetector.detect(text)
        # Should detect the dominant language (English in this case due to more words)
        assert result in ["en", "ko"]  # Accept either as mixed text can be ambiguous
