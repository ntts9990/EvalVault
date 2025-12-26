"""Unit tests for prompt customization."""

from evalvault.domain.prompts.base import PromptTemplate
from evalvault.domain.prompts.english import EnglishPrompts
from evalvault.domain.prompts.korean import KoreanPrompts


class TestPromptTemplate:
    """Test PromptTemplate base class."""

    def test_prompt_template_has_required_methods(self):
        """Test that PromptTemplate has required methods."""
        # PromptTemplate is abstract, check it has the expected structure
        assert hasattr(PromptTemplate, "get_faithfulness_prompt")
        assert hasattr(PromptTemplate, "get_answer_relevancy_prompt")
        assert hasattr(PromptTemplate, "get_context_precision_prompt")
        assert hasattr(PromptTemplate, "get_context_recall_prompt")


class TestEnglishPrompts:
    """Test English prompt templates."""

    def test_english_prompts_instantiation(self):
        """Test that EnglishPrompts can be instantiated."""
        prompts = EnglishPrompts()
        assert prompts is not None

    def test_get_faithfulness_prompt_returns_string(self):
        """Test that faithfulness prompt returns a string."""
        prompts = EnglishPrompts()
        prompt = prompts.get_faithfulness_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_answer_relevancy_prompt_returns_string(self):
        """Test that answer_relevancy prompt returns a string."""
        prompts = EnglishPrompts()
        prompt = prompts.get_answer_relevancy_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_context_precision_prompt_returns_string(self):
        """Test that context_precision prompt returns a string."""
        prompts = EnglishPrompts()
        prompt = prompts.get_context_precision_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_context_recall_prompt_returns_string(self):
        """Test that context_recall prompt returns a string."""
        prompts = EnglishPrompts()
        prompt = prompts.get_context_recall_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_english_prompts_contain_english_keywords(self):
        """Test that English prompts contain English keywords."""
        prompts = EnglishPrompts()
        faithfulness = prompts.get_faithfulness_prompt()

        # Check for English keywords (case-insensitive)
        assert any(keyword in faithfulness.lower() for keyword in ["context", "answer", "evaluate"])


class TestKoreanPrompts:
    """Test Korean prompt templates."""

    def test_korean_prompts_instantiation(self):
        """Test that KoreanPrompts can be instantiated."""
        prompts = KoreanPrompts()
        assert prompts is not None

    def test_get_faithfulness_prompt_returns_string(self):
        """Test that faithfulness prompt returns a string."""
        prompts = KoreanPrompts()
        prompt = prompts.get_faithfulness_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_answer_relevancy_prompt_returns_string(self):
        """Test that answer_relevancy prompt returns a string."""
        prompts = KoreanPrompts()
        prompt = prompts.get_answer_relevancy_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_context_precision_prompt_returns_string(self):
        """Test that context_precision prompt returns a string."""
        prompts = KoreanPrompts()
        prompt = prompts.get_context_precision_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_context_recall_prompt_returns_string(self):
        """Test that context_recall prompt returns a string."""
        prompts = KoreanPrompts()
        prompt = prompts.get_context_recall_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_korean_prompts_contain_korean_text(self):
        """Test that Korean prompts contain Korean characters."""
        prompts = KoreanPrompts()
        faithfulness = prompts.get_faithfulness_prompt()

        # Check if the prompt contains Hangul characters (Korean)
        has_korean = any("\uac00" <= char <= "\ud7a3" for char in faithfulness)
        assert has_korean, "Korean prompts should contain Korean characters"

    def test_korean_prompts_contain_korean_keywords(self):
        """Test that Korean prompts contain expected Korean keywords."""
        prompts = KoreanPrompts()
        faithfulness = prompts.get_faithfulness_prompt()

        # Check for Korean keywords
        korean_keywords = ["컨텍스트", "답변", "평가", "문맥", "응답"]
        assert any(keyword in faithfulness for keyword in korean_keywords)


class TestJapanesePrompts:
    """Test Japanese prompt templates."""

    def test_japanese_prompts_instantiation(self):
        """Test that JapanesePrompts can be instantiated."""
        from evalvault.domain.prompts.japanese import JapanesePrompts

        prompts = JapanesePrompts()
        assert prompts is not None

    def test_get_faithfulness_prompt_returns_string(self):
        """Test that faithfulness prompt returns a string."""
        from evalvault.domain.prompts.japanese import JapanesePrompts

        prompts = JapanesePrompts()
        prompt = prompts.get_faithfulness_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_answer_relevancy_prompt_returns_string(self):
        """Test that answer_relevancy prompt returns a string."""
        from evalvault.domain.prompts.japanese import JapanesePrompts

        prompts = JapanesePrompts()
        prompt = prompts.get_answer_relevancy_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_context_precision_prompt_returns_string(self):
        """Test that context_precision prompt returns a string."""
        from evalvault.domain.prompts.japanese import JapanesePrompts

        prompts = JapanesePrompts()
        prompt = prompts.get_context_precision_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_context_recall_prompt_returns_string(self):
        """Test that context_recall prompt returns a string."""
        from evalvault.domain.prompts.japanese import JapanesePrompts

        prompts = JapanesePrompts()
        prompt = prompts.get_context_recall_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_japanese_prompts_contain_japanese_text(self):
        """Test that Japanese prompts contain Japanese characters."""
        from evalvault.domain.prompts.japanese import JapanesePrompts

        prompts = JapanesePrompts()
        faithfulness = prompts.get_faithfulness_prompt()

        # Check if the prompt contains Hiragana, Katakana, or Kanji characters
        has_japanese = any(
            "\u3040" <= char <= "\u309f"  # Hiragana
            or "\u30a0" <= char <= "\u30ff"  # Katakana
            or "\u4e00" <= char <= "\u9fff"  # Kanji
            for char in faithfulness
        )
        assert has_japanese, "Japanese prompts should contain Japanese characters"

    def test_japanese_prompts_contain_japanese_keywords(self):
        """Test that Japanese prompts contain expected Japanese keywords."""
        from evalvault.domain.prompts.japanese import JapanesePrompts

        prompts = JapanesePrompts()
        faithfulness = prompts.get_faithfulness_prompt()

        # Check for Japanese keywords (evaluation-related terms)
        japanese_keywords = ["評価", "コンテキスト", "回答", "質問"]
        assert any(keyword in faithfulness for keyword in japanese_keywords)


class TestChinesePrompts:
    """Test Chinese prompt templates."""

    def test_chinese_prompts_instantiation(self):
        """Test that ChinesePrompts can be instantiated."""
        from evalvault.domain.prompts.chinese import ChinesePrompts

        prompts = ChinesePrompts()
        assert prompts is not None

    def test_get_faithfulness_prompt_returns_string(self):
        """Test that faithfulness prompt returns a string."""
        from evalvault.domain.prompts.chinese import ChinesePrompts

        prompts = ChinesePrompts()
        prompt = prompts.get_faithfulness_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_answer_relevancy_prompt_returns_string(self):
        """Test that answer_relevancy prompt returns a string."""
        from evalvault.domain.prompts.chinese import ChinesePrompts

        prompts = ChinesePrompts()
        prompt = prompts.get_answer_relevancy_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_context_precision_prompt_returns_string(self):
        """Test that context_precision prompt returns a string."""
        from evalvault.domain.prompts.chinese import ChinesePrompts

        prompts = ChinesePrompts()
        prompt = prompts.get_context_precision_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_get_context_recall_prompt_returns_string(self):
        """Test that context_recall prompt returns a string."""
        from evalvault.domain.prompts.chinese import ChinesePrompts

        prompts = ChinesePrompts()
        prompt = prompts.get_context_recall_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_chinese_prompts_contain_chinese_text(self):
        """Test that Chinese prompts contain Chinese characters."""
        from evalvault.domain.prompts.chinese import ChinesePrompts

        prompts = ChinesePrompts()
        faithfulness = prompts.get_faithfulness_prompt()

        # Check if the prompt contains Chinese characters (CJK Unified Ideographs)
        has_chinese = any("\u4e00" <= char <= "\u9fff" for char in faithfulness)
        assert has_chinese, "Chinese prompts should contain Chinese characters"

    def test_chinese_prompts_contain_chinese_keywords(self):
        """Test that Chinese prompts contain expected Chinese keywords."""
        from evalvault.domain.prompts.chinese import ChinesePrompts

        prompts = ChinesePrompts()
        faithfulness = prompts.get_faithfulness_prompt()

        # Check for Chinese keywords (evaluation-related terms)
        chinese_keywords = ["评估", "上下文", "答案", "问题", "忠实"]
        assert any(keyword in faithfulness for keyword in chinese_keywords)


class TestPromptFactory:
    """Test prompt factory functionality."""

    def test_get_prompts_for_language_english(self):
        """Test getting prompts for English language."""
        from evalvault.domain.prompts import get_prompts_for_language

        prompts = get_prompts_for_language("en")
        assert isinstance(prompts, EnglishPrompts)

    def test_get_prompts_for_language_korean(self):
        """Test getting prompts for Korean language."""
        from evalvault.domain.prompts import get_prompts_for_language

        prompts = get_prompts_for_language("ko")
        assert isinstance(prompts, KoreanPrompts)

    def test_get_prompts_for_language_unknown_defaults_to_english(self):
        """Test that unknown language defaults to English."""
        from evalvault.domain.prompts import get_prompts_for_language

        prompts = get_prompts_for_language("unknown")
        assert isinstance(prompts, EnglishPrompts)

    def test_get_prompts_for_language_japanese(self):
        """Test getting prompts for Japanese language."""
        from evalvault.domain.prompts import get_prompts_for_language
        from evalvault.domain.prompts.japanese import JapanesePrompts

        prompts = get_prompts_for_language("ja")
        assert isinstance(prompts, JapanesePrompts)

    def test_get_prompts_for_language_chinese(self):
        """Test getting prompts for Chinese language."""
        from evalvault.domain.prompts import get_prompts_for_language
        from evalvault.domain.prompts.chinese import ChinesePrompts

        prompts = get_prompts_for_language("zh-cn")
        assert isinstance(prompts, ChinesePrompts)

    def test_get_prompts_for_language_chinese_alias(self):
        """Test getting prompts for Chinese with 'zh' alias."""
        from evalvault.domain.prompts import get_prompts_for_language
        from evalvault.domain.prompts.chinese import ChinesePrompts

        prompts = get_prompts_for_language("zh")
        assert isinstance(prompts, ChinesePrompts)
