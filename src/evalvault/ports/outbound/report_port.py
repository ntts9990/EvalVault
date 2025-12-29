"""Report generation port interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from evalvault.domain.entities.analysis import AnalysisBundle


class ReportPort(Protocol):
    """보고서 생성 포트 인터페이스.

    다양한 형식의 분석 보고서를 생성합니다.
    """

    def generate_markdown(
        self,
        bundle: AnalysisBundle,
        *,
        include_nlp: bool = True,
        include_recommendations: bool = True,
    ) -> str:
        """Markdown 형식 보고서 생성.

        Args:
            bundle: 분석 결과 번들
            include_nlp: NLP 분석 포함 여부
            include_recommendations: 권장사항 포함 여부

        Returns:
            Markdown 형식의 보고서 문자열
        """
        ...

    def generate_html(
        self,
        bundle: AnalysisBundle,
        *,
        include_nlp: bool = True,
        include_recommendations: bool = True,
    ) -> str:
        """HTML 형식 보고서 생성.

        Args:
            bundle: 분석 결과 번들
            include_nlp: NLP 분석 포함 여부
            include_recommendations: 권장사항 포함 여부

        Returns:
            HTML 형식의 보고서 문자열
        """
        ...
