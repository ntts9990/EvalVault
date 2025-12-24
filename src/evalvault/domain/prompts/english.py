"""English prompt templates for Ragas evaluation."""

from evalvault.domain.prompts.base import PromptTemplate


class EnglishPrompts(PromptTemplate):
    """English language prompts for Ragas evaluation metrics.

    These prompts are used by default when evaluating English datasets.
    They follow Ragas best practices for evaluation prompts.
    """

    def get_faithfulness_prompt(self) -> str:
        """Get faithfulness evaluation prompt in English.

        Faithfulness measures how well the answer is grounded in the provided context.
        """
        return """Given a context and an answer, evaluate whether the answer is faithful to the context.
An answer is faithful if all claims in the answer can be verified using the context.

Context: {context}
Answer: {answer}

Evaluate the faithfulness of the answer on a scale of 0.0 to 1.0, where:
- 0.0: The answer contains claims that are not supported by the context
- 1.0: All claims in the answer are fully supported by the context

Provide your evaluation and reasoning."""

    def get_answer_relevancy_prompt(self) -> str:
        """Get answer relevancy evaluation prompt in English.

        Answer relevancy measures how well the answer addresses the question.
        """
        return """Given a question and an answer, evaluate how relevant the answer is to the question.
A relevant answer directly addresses the question without unnecessary information.

Question: {question}
Answer: {answer}

Evaluate the relevancy of the answer on a scale of 0.0 to 1.0, where:
- 0.0: The answer is completely irrelevant to the question
- 1.0: The answer is perfectly relevant and directly addresses the question

Provide your evaluation and reasoning."""

    def get_context_precision_prompt(self) -> str:
        """Get context precision evaluation prompt in English.

        Context precision measures whether the retrieved contexts are relevant to the question.
        """
        return """Given a question and retrieved contexts, evaluate the precision of the contexts.
Precision measures whether the contexts contain relevant information for answering the question.

Question: {question}
Contexts: {contexts}

Evaluate the context precision on a scale of 0.0 to 1.0, where:
- 0.0: The contexts contain mostly irrelevant information
- 1.0: All contexts are highly relevant to the question

Provide your evaluation and reasoning."""

    def get_context_recall_prompt(self) -> str:
        """Get context recall evaluation prompt in English.

        Context recall measures whether all necessary information is present in the contexts.
        """
        return """Given a question, ground truth answer, and retrieved contexts, evaluate the recall of the contexts.
Recall measures whether the contexts contain all the information needed to answer the question correctly.

Question: {question}
Ground Truth: {ground_truth}
Contexts: {contexts}

Evaluate the context recall on a scale of 0.0 to 1.0, where:
- 0.0: The contexts are missing critical information needed to answer the question
- 1.0: The contexts contain all necessary information to produce the ground truth answer

Provide your evaluation and reasoning."""
