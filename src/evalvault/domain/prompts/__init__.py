"""Prompt templates for different languages."""

from evalvault.domain.prompts.base import PromptTemplate
from evalvault.domain.prompts.chinese import ChinesePrompts
from evalvault.domain.prompts.english import EnglishPrompts
from evalvault.domain.prompts.japanese import JapanesePrompts
from evalvault.domain.prompts.korean import KoreanPrompts


def get_prompts_for_language(language: str) -> PromptTemplate:
    """Get appropriate prompts for the given language.

    Args:
        language: Language code (e.g., 'ko', 'en', 'ja', 'zh', 'zh-cn')

    Returns:
        PromptTemplate instance for the language (defaults to English for unsupported languages)
    """
    language_map = {
        "ko": KoreanPrompts(),
        "en": EnglishPrompts(),
        "ja": JapanesePrompts(),
        "zh": ChinesePrompts(),
        "zh-cn": ChinesePrompts(),
    }
    return language_map.get(language, EnglishPrompts())


__all__ = [
    "PromptTemplate",
    "EnglishPrompts",
    "KoreanPrompts",
    "JapanesePrompts",
    "ChinesePrompts",
    "get_prompts_for_language",
]
