"""NLP 분석 서비스 인터페이스."""

from typing import Protocol

from evalvault.domain.entities import EvaluationRun
from evalvault.domain.entities.analysis import (
    KeywordInfo,
    NLPAnalysis,
    QuestionTypeStats,
)


class NLPAnalysisPort(Protocol):
    """NLP 분석을 위한 포트 인터페이스.

    텍스트 통계, 질문 유형 분류, 키워드 추출 등의 NLP 분석 기능을 제공합니다.
    """

    def analyze_text_statistics(
        self,
        run: EvaluationRun,
    ) -> NLPAnalysis:
        """텍스트 기본 통계를 분석합니다.

        질문, 답변, 컨텍스트에 대한 기본 텍스트 통계를 계산합니다.
        - 문자 수, 단어 수, 문장 수
        - 평균 단어 길이
        - 어휘 다양성 (unique word ratio)

        Args:
            run: 분석할 평가 실행 결과

        Returns:
            텍스트 통계가 포함된 NLPAnalysis 객체
        """
        ...

    def classify_question_types(
        self,
        run: EvaluationRun,
    ) -> list[QuestionTypeStats]:
        """질문 유형을 분류합니다.

        규칙 기반으로 질문을 다음 유형으로 분류합니다:
        - FACTUAL: 사실형 (무엇, 언제, 어디, 누가 / what, when, where, who)
        - REASONING: 추론형 (왜, 어떻게 / why, how)
        - COMPARATIVE: 비교형 (비교, 차이 / compare, difference)
        - PROCEDURAL: 절차형 (방법, 단계 / how to, steps)
        - OPINION: 의견형 (생각, 의견 / opinion, think)

        Args:
            run: 분석할 평가 실행 결과

        Returns:
            질문 유형별 통계 리스트
        """
        ...

    def extract_keywords(
        self,
        run: EvaluationRun,
        *,
        top_k: int = 20,
    ) -> list[KeywordInfo]:
        """키워드를 추출합니다.

        TF-IDF 기반으로 중요 키워드를 추출하고,
        각 키워드가 포함된 테스트 케이스의 메트릭 평균 점수를 계산합니다.

        Args:
            run: 분석할 평가 실행 결과
            top_k: 추출할 키워드 수 (기본값: 20)

        Returns:
            키워드 정보 리스트 (TF-IDF 점수 내림차순)
        """
        ...

    def analyze(
        self,
        run: EvaluationRun,
        *,
        include_text_stats: bool = True,
        include_question_types: bool = True,
        include_keywords: bool = True,
        top_k_keywords: int = 20,
    ) -> NLPAnalysis:
        """통합 NLP 분석을 수행합니다.

        여러 NLP 분석을 한 번에 수행하여 NLPAnalysis 객체로 반환합니다.

        Args:
            run: 분석할 평가 실행 결과
            include_text_stats: 텍스트 통계 포함 여부
            include_question_types: 질문 유형 분석 포함 여부
            include_keywords: 키워드 분석 포함 여부
            top_k_keywords: 추출할 키워드 수

        Returns:
            NLPAnalysis 객체
        """
        ...
