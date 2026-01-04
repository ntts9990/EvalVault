"""평가 실행 인터페이스."""

from collections.abc import Sequence
from typing import Protocol

from evalvault.domain.entities import Dataset, EvaluationRun
from evalvault.ports.outbound.korean_nlp_port import RetrieverPort


class EvaluatorPort(Protocol):
    """평가 실행을 위한 포트 인터페이스.

    데이터셋과 메트릭을 사용하여 모델 평가를 실행합니다.
    """

    def evaluate(
        self,
        dataset: Dataset,
        metrics: list[str],
        model: str,
        retriever: RetrieverPort | None = None,
        retriever_top_k: int = 5,
        retriever_doc_ids: Sequence[str] | None = None,
    ) -> EvaluationRun:
        """데이터셋에 대해 평가를 실행합니다.

        Args:
            dataset: 평가할 데이터셋
            metrics: 사용할 메트릭 목록 (예: ["faithfulness", "answer_relevancy"])
            model: 평가에 사용할 모델 이름
            retriever: 빈 컨텍스트 보강용 retriever (없으면 생략)
            retriever_top_k: retriever 결과 상위 k개 컨텍스트 사용
            retriever_doc_ids: retriever 결과 doc_id 인덱스를 해석할 때 사용할
                문서 ID 목록

        Returns:
            EvaluationRun 객체 (평가 결과 포함)
        """
        ...
