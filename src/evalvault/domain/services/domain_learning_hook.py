"""Domain Learning Hook service.

Implements the Formation dynamics by extracting and storing memories
from evaluation results. Coordinates between StoragePort and MemoryLifecyclePort.
"""

from evalvault.domain.entities.memory import (
    BehaviorEntry,
    FactualFact,
    LearningMemory,
)
from evalvault.domain.entities.result import EvaluationRun
from evalvault.ports.outbound.domain_memory_port import MemoryLifecyclePort


class DomainLearningHook:
    """도메인 학습 훅 서비스.

    평가 완료 후 호출되어 도메인 메모리를 형성합니다.
    Formation dynamics를 구현합니다.

    사용 예시:
        from evalvault.adapters.outbound.domain_memory import build_domain_memory_adapter
        memory_adapter = build_domain_memory_adapter()
        hook = DomainLearningHook(memory_adapter)

        # 평가 후 메모리 형성
        result = await hook.on_evaluation_complete(
            evaluation_run=run,
            domain="insurance",
            language="ko"
        )
        print(f"Extracted {len(result['facts'])} facts")
    """

    def __init__(self, memory_port: MemoryLifecyclePort):
        """Initialize the domain learning hook.

        Args:
            memory_port: Domain memory storage port
        """
        self.memory_port = memory_port

    async def on_evaluation_complete(
        self,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
        auto_save: bool = True,
    ) -> dict[str, list | LearningMemory]:
        """평가 완료 후 호출됩니다.

        모든 Formation dynamics를 실행하여 메모리를 형성합니다.

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
        # 1. 사실 추출
        facts = self.extract_and_save_facts(
            evaluation_run=evaluation_run,
            domain=domain,
            language=language,
            auto_save=auto_save,
        )

        # 2. 학습 패턴 추출
        learning = self.extract_and_save_patterns(
            evaluation_run=evaluation_run,
            domain=domain,
            language=language,
            auto_save=auto_save,
        )

        # 3. 행동 추출
        behaviors = self.extract_and_save_behaviors(
            evaluation_run=evaluation_run,
            domain=domain,
            language=language,
            auto_save=auto_save,
        )

        return {
            "facts": facts,
            "learning": learning,
            "behaviors": behaviors,
        }

    def extract_and_save_facts(
        self,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
        min_confidence: float = 0.7,
        auto_save: bool = True,
    ) -> list[FactualFact]:
        """평가 결과에서 사실을 추출하고 저장합니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인
            language: 언어 코드
            min_confidence: 최소 faithfulness 점수
            auto_save: 자동 저장 여부

        Returns:
            추출된 FactualFact 리스트
        """
        facts = self.memory_port.extract_facts_from_evaluation(
            evaluation_run=evaluation_run,
            domain=domain,
            language=language,
            min_confidence=min_confidence,
        )

        if auto_save:
            for fact in facts:
                # 중복 체크 후 저장
                existing = self.memory_port.find_fact_by_triple(
                    subject=fact.subject,
                    predicate=fact.predicate,
                    obj=fact.object,
                    domain=domain,
                )
                if existing:
                    # 기존 사실 업데이트
                    existing.verification_count += 1
                    existing.verification_score = (
                        existing.verification_score + fact.verification_score
                    ) / 2
                    self.memory_port.update_fact(existing)
                else:
                    self.memory_port.save_fact(fact)

        return facts

    def extract_and_save_patterns(
        self,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
        auto_save: bool = True,
    ) -> LearningMemory:
        """평가 결과에서 학습 패턴을 추출하고 저장합니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인
            language: 언어 코드
            auto_save: 자동 저장 여부

        Returns:
            추출된 LearningMemory
        """
        learning = self.memory_port.extract_patterns_from_evaluation(
            evaluation_run=evaluation_run,
            domain=domain,
            language=language,
        )

        if auto_save:
            self.memory_port.save_learning(learning)

        return learning

    def extract_and_save_behaviors(
        self,
        evaluation_run: EvaluationRun,
        domain: str,
        language: str = "ko",
        min_success_rate: float = 0.8,
        auto_save: bool = True,
    ) -> list[BehaviorEntry]:
        """평가 결과에서 행동을 추출하고 저장합니다.

        Args:
            evaluation_run: 평가 실행 결과
            domain: 도메인
            language: 언어 코드
            min_success_rate: 최소 성공률
            auto_save: 자동 저장 여부

        Returns:
            추출된 BehaviorEntry 리스트
        """
        behaviors = self.memory_port.extract_behaviors_from_evaluation(
            evaluation_run=evaluation_run,
            domain=domain,
            language=language,
            min_success_rate=min_success_rate,
        )

        if auto_save:
            for behavior in behaviors:
                self.memory_port.save_behavior(behavior)

        return behaviors

    def run_evolution(self, domain: str, language: str = "ko") -> dict[str, int]:
        """Evolution dynamics를 실행합니다.

        메모리 통합, 충돌 해결, 오래된 메모리 삭제를 수행합니다.

        Args:
            domain: 도메인
            language: 언어 코드

        Returns:
            Evolution 결과 통계:
            {
                "consolidated": int,
                "forgotten": int,
                "decayed": int
            }
        """
        # 1. 중복 사실 통합
        consolidated = self.memory_port.consolidate_facts(domain, language)

        # 2. 오래된 메모리 삭제
        forgotten = self.memory_port.forget_obsolete(domain)

        # 3. 검증 점수 감소
        decayed = self.memory_port.decay_verification_scores(domain)

        return {
            "consolidated": consolidated,
            "forgotten": forgotten,
            "decayed": decayed,
        }
