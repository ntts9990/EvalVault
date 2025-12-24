"""Korean prompt templates for Ragas evaluation."""

from evalvault.domain.prompts.base import PromptTemplate


class KoreanPrompts(PromptTemplate):
    """Korean language prompts for Ragas evaluation metrics.

    These prompts are optimized for evaluating Korean insurance documents
    and other Korean-language RAG systems.
    """

    def get_faithfulness_prompt(self) -> str:
        """Get faithfulness evaluation prompt in Korean.

        Faithfulness (충실도): 답변이 제공된 컨텍스트에 얼마나 충실한지 평가
        """
        return """주어진 컨텍스트와 답변을 바탕으로, 답변이 컨텍스트에 얼마나 충실한지 평가하세요.
답변이 충실하다는 것은 답변의 모든 주장이 컨텍스트를 통해 검증될 수 있다는 것을 의미합니다.

컨텍스트: {context}
답변: {answer}

답변의 충실도를 0.0에서 1.0 사이의 점수로 평가하세요:
- 0.0: 답변에 컨텍스트에서 지원되지 않는 주장이 포함되어 있음
- 1.0: 답변의 모든 주장이 컨텍스트에서 완전히 지원됨

평가 점수와 그 이유를 제시하세요."""

    def get_answer_relevancy_prompt(self) -> str:
        """Get answer relevancy evaluation prompt in Korean.

        Answer relevancy (답변 관련성): 답변이 질문과 얼마나 관련이 있는지 평가
        """
        return """주어진 질문과 답변을 바탕으로, 답변이 질문과 얼마나 관련이 있는지 평가하세요.
관련성 있는 답변은 불필요한 정보 없이 질문을 직접적으로 다룹니다.

질문: {question}
답변: {answer}

답변의 관련성을 0.0에서 1.0 사이의 점수로 평가하세요:
- 0.0: 답변이 질문과 완전히 무관함
- 1.0: 답변이 질문과 완벽하게 관련되어 있고 질문을 직접적으로 다룸

평가 점수와 그 이유를 제시하세요."""

    def get_context_precision_prompt(self) -> str:
        """Get context precision evaluation prompt in Korean.

        Context precision (컨텍스트 정밀도): 검색된 컨텍스트가 질문과 관련이 있는지 평가
        """
        return """주어진 질문과 검색된 컨텍스트를 바탕으로, 컨텍스트의 정밀도를 평가하세요.
정밀도는 컨텍스트가 질문에 답하는 데 필요한 관련 정보를 포함하는지를 측정합니다.

질문: {question}
컨텍스트: {contexts}

컨텍스트 정밀도를 0.0에서 1.0 사이의 점수로 평가하세요:
- 0.0: 컨텍스트에 대부분 관련 없는 정보가 포함되어 있음
- 1.0: 모든 컨텍스트가 질문과 매우 관련이 있음

평가 점수와 그 이유를 제시하세요."""

    def get_context_recall_prompt(self) -> str:
        """Get context recall evaluation prompt in Korean.

        Context recall (컨텍스트 재현율): 필요한 모든 정보가 컨텍스트에 있는지 평가
        """
        return """주어진 질문, 정답, 그리고 검색된 컨텍스트를 바탕으로, 컨텍스트의 재현율을 평가하세요.
재현율은 컨텍스트가 질문에 올바르게 답하는 데 필요한 모든 정보를 포함하는지를 측정합니다.

질문: {question}
정답: {ground_truth}
컨텍스트: {contexts}

컨텍스트 재현율을 0.0에서 1.0 사이의 점수로 평가하세요:
- 0.0: 컨텍스트에 질문에 답하는 데 필요한 중요한 정보가 누락되어 있음
- 1.0: 컨텍스트에 정답을 생성하는 데 필요한 모든 정보가 포함되어 있음

평가 점수와 그 이유를 제시하세요."""
