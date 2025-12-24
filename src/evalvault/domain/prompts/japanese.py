"""Japanese prompt templates for Ragas evaluation."""

from evalvault.domain.prompts.base import PromptTemplate


class JapanesePrompts(PromptTemplate):
    """Japanese language prompts for Ragas evaluation metrics.

    These prompts are optimized for evaluating Japanese documents
    and Japanese-language RAG systems.
    """

    def get_faithfulness_prompt(self) -> str:
        """Get faithfulness evaluation prompt in Japanese.

        Faithfulness (忠実度): 回答が提供されたコンテキストにどれだけ忠実かを評価
        """
        return """与えられたコンテキストと回答に基づいて、回答がコンテキストに忠実であるかを評価してください。
回答が忠実であるとは、回答のすべての主張がコンテキストを通じて検証できることを意味します。

コンテキスト: {context}
回答: {answer}

回答の忠実度を0.0から1.0のスケールで評価してください:
- 0.0: 回答にコンテキストでサポートされていない主張が含まれている
- 1.0: 回答のすべての主張がコンテキストで完全にサポートされている

評価スコアとその理由を提示してください。"""

    def get_answer_relevancy_prompt(self) -> str:
        """Get answer relevancy evaluation prompt in Japanese.

        Answer relevancy (回答関連性): 回答が質問にどれだけ関連しているかを評価
        """
        return """与えられた質問と回答に基づいて、回答が質問にどれだけ関連しているかを評価してください。
関連性のある回答は、不要な情報なしに質問に直接対処します。

質問: {question}
回答: {answer}

回答の関連性を0.0から1.0のスケールで評価してください:
- 0.0: 回答が質問と完全に無関係である
- 1.0: 回答が完全に関連しており、質問に直接対処している

評価スコアとその理由を提示してください。"""

    def get_context_precision_prompt(self) -> str:
        """Get context precision evaluation prompt in Japanese.

        Context precision (コンテキスト精度): 検索されたコンテキストが質問に関連しているかを評価
        """
        return """与えられた質問と検索されたコンテキストに基づいて、コンテキストの精度を評価してください。
精度は、コンテキストが質問に答えるために必要な関連情報を含んでいるかどうかを測定します。

質問: {question}
コンテキスト: {contexts}

コンテキスト精度を0.0から1.0のスケールで評価してください:
- 0.0: コンテキストにほとんど無関係な情報が含まれている
- 1.0: すべてのコンテキストが質問に非常に関連している

評価スコアとその理由を提示してください。"""

    def get_context_recall_prompt(self) -> str:
        """Get context recall evaluation prompt in Japanese.

        Context recall (コンテキスト再現率): 必要なすべての情報がコンテキストにあるかを評価
        """
        return """与えられた質問、正解、そして検索されたコンテキストに基づいて、コンテキストの再現率を評価してください。
再現率は、コンテキストが質問に正しく答えるために必要なすべての情報を含んでいるかどうかを測定します。

質問: {question}
正解: {ground_truth}
コンテキスト: {contexts}

コンテキスト再現率を0.0から1.0のスケールで評価してください:
- 0.0: コンテキストに質問に答えるために必要な重要な情報が欠けている
- 1.0: コンテキストに正解を生成するために必要なすべての情報が含まれている

評価スコアとその理由を提示してください。"""
