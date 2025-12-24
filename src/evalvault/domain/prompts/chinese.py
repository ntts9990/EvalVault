"""Chinese prompt templates for Ragas evaluation."""

from evalvault.domain.prompts.base import PromptTemplate


class ChinesePrompts(PromptTemplate):
    """Chinese language prompts for Ragas evaluation metrics.

    These prompts are optimized for evaluating Chinese documents
    and Chinese-language RAG systems. Uses Simplified Chinese.
    """

    def get_faithfulness_prompt(self) -> str:
        """Get faithfulness evaluation prompt in Chinese.

        Faithfulness (忠实度): 答案对提供的上下文的忠实程度
        """
        return """根据给定的上下文和答案，评估答案对上下文的忠实度。
答案忠实意味着答案中的所有声明都可以通过上下文进行验证。

上下文: {context}
答案: {answer}

请在0.0到1.0的范围内评估答案的忠实度：
- 0.0: 答案包含上下文不支持的声明
- 1.0: 答案中的所有声明都完全由上下文支持

请提供评估分数及其理由。"""

    def get_answer_relevancy_prompt(self) -> str:
        """Get answer relevancy evaluation prompt in Chinese.

        Answer relevancy (答案相关性): 答案与问题的相关程度
        """
        return """根据给定的问题和答案，评估答案与问题的相关程度。
相关的答案直接回答问题，不包含不必要的信息。

问题: {question}
答案: {answer}

请在0.0到1.0的范围内评估答案的相关性：
- 0.0: 答案与问题完全无关
- 1.0: 答案完全相关并直接回答问题

请提供评估分数及其理由。"""

    def get_context_precision_prompt(self) -> str:
        """Get context precision evaluation prompt in Chinese.

        Context precision (上下文精度): 检索的上下文与问题的相关性
        """
        return """根据给定的问题和检索到的上下文，评估上下文的精度。
精度衡量上下文是否包含回答问题所需的相关信息。

问题: {question}
上下文: {contexts}

请在0.0到1.0的范围内评估上下文精度：
- 0.0: 上下文包含大量无关信息
- 1.0: 所有上下文都与问题高度相关

请提供评估分数及其理由。"""

    def get_context_recall_prompt(self) -> str:
        """Get context recall evaluation prompt in Chinese.

        Context recall (上下文召回率): 上下文是否包含所有必要信息
        """
        return """根据给定的问题、标准答案和检索到的上下文，评估上下文的召回率。
召回率衡量上下文是否包含正确回答问题所需的所有信息。

问题: {question}
标准答案: {ground_truth}
上下文: {contexts}

请在0.0到1.0的范围内评估上下文召回率：
- 0.0: 上下文缺少回答问题所需的关键信息
- 1.0: 上下文包含生成标准答案所需的所有信息

请提供评估分数及其理由。"""
