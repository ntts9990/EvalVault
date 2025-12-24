"""Language detection utilities using langdetect."""

from collections import Counter

from langdetect import LangDetectException, detect, detect_langs


class LanguageDetector:
    """Language detection utility for RAG evaluation datasets.

    Uses langdetect library to identify the language of text content.
    Supports Korean, English, Japanese, and Chinese (Simplified/Traditional).
    """

    SUPPORTED_LANGUAGES = {"ko", "en", "ja", "zh-cn", "zh-tw"}

    @staticmethod
    def detect(text: str) -> str:
        """Detect the language of a given text.

        Args:
            text: Text to detect language from

        Returns:
            Language code (e.g., 'ko', 'en', 'ja', 'zh-cn', 'zh-tw')
            Returns 'unknown' if detection fails or text is empty
        """
        if not text or not text.strip():
            return "unknown"

        try:
            detected_lang = detect(text)
            # Normalize language codes
            if detected_lang == "zh":
                # langdetect returns 'zh' for Chinese, need to check if simplified or traditional
                # For now, default to zh-cn (simplified)
                # A more sophisticated approach would analyze character sets
                return "zh-cn"
            return detected_lang
        except LangDetectException:
            return "unknown"

    @staticmethod
    def detect_with_confidence(text: str) -> list[tuple[str, float]]:
        """Detect language with confidence scores.

        Args:
            text: Text to detect language from

        Returns:
            List of tuples (language_code, confidence_score) sorted by confidence
            Returns empty list if detection fails or text is empty
        """
        if not text or not text.strip():
            return []

        try:
            detected_langs = detect_langs(text)
            results = []
            for lang_prob in detected_langs:
                lang = lang_prob.lang
                prob = lang_prob.prob
                # Normalize language codes
                if lang == "zh":
                    lang = "zh-cn"  # Default to simplified Chinese
                results.append((lang, prob))
            return results
        except LangDetectException:
            return []

    @classmethod
    def detect_dataset_language(cls, texts: list[str]) -> str:
        """Detect the dominant language in a dataset.

        Analyzes multiple texts and determines the most common language.
        Useful for selecting appropriate prompts for evaluation.

        Args:
            texts: List of texts to analyze

        Returns:
            Dominant language code
            Returns 'unknown' if no clear language can be determined
        """
        if not texts:
            return "unknown"

        # Detect language for each text
        detected_languages = []
        for text in texts:
            lang = cls.detect(text)
            if lang != "unknown":
                detected_languages.append(lang)

        # Return 'unknown' if no valid detections
        if not detected_languages:
            return "unknown"

        # Count occurrences and return the most common
        language_counts = Counter(detected_languages)
        most_common_lang, _ = language_counts.most_common(1)[0]
        return most_common_lang
