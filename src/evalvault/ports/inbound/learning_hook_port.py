"""Domain Learning Hook port interface.

Hook that gets called after evaluation to form domain memories.
Implements the Formation dynamics from the Memory Survey framework.
"""

from typing import Protocol

from evalvault.domain.entities.memory import (
    BehaviorEntry,
    FactualFact,
    LearningMemory,
)
from evalvault.domain.entities.result import EvaluationRun


class DomainLearningHookPort(Protocol):
    """도메인 학습 훅 인터페이스.

    평가 완료 후 호출되어 도메인 메모리를 형성합니다.

    사용 예시:
        settings = Settings()
        llm_factory = SettingsLLMFactory(settings)
        korean_toolkit = try_create_korean_toolkit()
        evaluator = RagasEvaluator(korean_toolkit=korean_toolkit, llm_factory=llm_factory)
        hook = InsuranceDomainLearningHook(memory_adapter)

        # 평가 실행
        run = await evaluator.evaluate(dataset, metrics, llm)

        # 메모리 형성
        await hook.on_evaluation_complete(run, domain="insurance")
    """

    async def on_evaluation_complete(
        self,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
        auto_save: bool = True,
    ) -> dict[str, list]:
        """평가 완료 후 호출됩니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인 (예: 'insurance', 'medical')
            language: 언어 코드
            auto_save: 추출된 메모리를 자동 저장할지 여부

        Returns:
            추출된 메모리 정보:
            {
                "facts": list[FactualFact],
                "learning": LearningMemory,
                "behaviors": list[BehaviorEntry]
            }
        """
        ...

    def extract_and_save_facts(
        self,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
        min_confidence: float = 0.7,
    ) -> list[FactualFact]:
        """평가 결과에서 사실을 추출하고 저장합니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인
            language: 언어 코드
            min_confidence: 최소 faithfulness 점수

        Returns:
            추출된 FactualFact 리스트
        """
        ...

    def extract_and_save_patterns(
        self,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
    ) -> LearningMemory:
        """평가 결과에서 학습 패턴을 추출하고 저장합니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인
            language: 언어 코드

        Returns:
            추출된 LearningMemory
        """
        ...

    def extract_and_save_behaviors(
        self,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
        min_success_rate: float = 0.8,
    ) -> list[BehaviorEntry]:
        """평가 결과에서 행동을 추출하고 저장합니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인
            language: 언어 코드
            min_success_rate: 최소 성공률

        Returns:
            추출된 BehaviorEntry 리스트
        """
        ...
