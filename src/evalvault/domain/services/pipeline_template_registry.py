"""Phase 14.2: Pipeline Template Registry.

의도별 분석 파이프라인 템플릿을 관리하는 레지스트리입니다.

D-S4 (refactor): 실제 템플릿 빌더는
:mod:`evalvault.domain.services.pipeline_templates` 패키지의 카테고리별
모듈(``verify_templates`` / ``compare_templates`` / ``analyze_templates`` /
``generate_templates`` / ``other_templates``)로 분리되었습니다. 각 모듈은
import 시점에 패키지 수준 :func:`register` 콜백으로 자신의 빌더를 등록하며,
:class:`PipelineTemplateRegistry` 는 생성 시 등록된 빌더 전체를 실체화합니다.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisIntent,
    AnalysisPipeline,
)
from evalvault.domain.services.pipeline_templates import (
    TemplateBuilder,
    all_builders,
)

# =============================================================================
# PipelineTemplateRegistry
# =============================================================================


@dataclass
class PipelineTemplateRegistry:
    """파이프라인 템플릿 레지스트리.

    각 분석 의도에 대한 기본 파이프라인 템플릿을 관리합니다.
    """

    _templates: dict[AnalysisIntent, AnalysisPipeline] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """등록된 모든 템플릿 빌더를 실행해 인스턴스를 구성합니다."""
        for intent, builder in all_builders().items():
            self._templates[intent] = builder()

    def register(
        self,
        intent: AnalysisIntent,
        builder: Callable[[], AnalysisPipeline] | TemplateBuilder,
    ) -> None:
        """런타임에 새 빌더를 즉시 호출해 템플릿을 (재)등록합니다."""
        self._templates[intent] = builder()

    def get(self, intent: AnalysisIntent) -> AnalysisPipeline | None:
        """``intent`` 에 대응하는 템플릿을 조회합니다 (alias)."""
        return self._templates.get(intent)

    def get_template(self, intent: AnalysisIntent) -> AnalysisPipeline | None:
        """의도에 대응하는 파이프라인 템플릿 조회."""
        return self._templates.get(intent)

    def list_all(self) -> list[tuple[AnalysisIntent, AnalysisPipeline]]:
        return list(self._templates.items())
