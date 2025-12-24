"""Base class for prompt templates."""

from abc import ABC, abstractmethod


class PromptTemplate(ABC):
    """Abstract base class for language-specific prompt templates.

    Provides an interface for customizing evaluation prompts based on language.
    This allows Ragas metrics to be evaluated using language-appropriate instructions.
    """

    @abstractmethod
    def get_faithfulness_prompt(self) -> str:
        """Get the prompt template for faithfulness evaluation.

        Returns:
            Prompt template string for evaluating answer faithfulness to context
        """
        pass

    @abstractmethod
    def get_answer_relevancy_prompt(self) -> str:
        """Get the prompt template for answer relevancy evaluation.

        Returns:
            Prompt template string for evaluating answer relevancy to question
        """
        pass

    @abstractmethod
    def get_context_precision_prompt(self) -> str:
        """Get the prompt template for context precision evaluation.

        Returns:
            Prompt template string for evaluating context precision
        """
        pass

    @abstractmethod
    def get_context_recall_prompt(self) -> str:
        """Get the prompt template for context recall evaluation.

        Returns:
            Prompt template string for evaluating context recall
        """
        pass
