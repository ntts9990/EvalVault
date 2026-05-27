"""Phase 14.2 D-S4: 의도별 파이프라인 템플릿 빌더 모듈.

각 카테고리 모듈은 자기 자신을 import 시점에 ``register()`` 콜백을 통해
모듈 수준 빌더 레지스트리에 등록합니다. :class:`PipelineTemplateRegistry`
인스턴스는 생성 시 :func:`all_builders` 로 등록된 빌더 사전을 읽어
:class:`evalvault.domain.entities.analysis_pipeline.AnalysisPipeline` 인스턴스를
초기화합니다.

분류 기준은 메소드 이름 접두어(``verify_*`` / ``compare_*`` / ``analyze_*`` /
``generate_*``)이며, 위 네 접두어에 부합하지 않는 빌더는
:mod:`other_templates` 에 모았습니다.
"""

from __future__ import annotations

from collections.abc import Callable

from evalvault.domain.entities.analysis_pipeline import (
    AnalysisIntent,
    AnalysisPipeline,
)

TemplateBuilder = Callable[[], AnalysisPipeline]

_BUILDERS: dict[AnalysisIntent, TemplateBuilder] = {}


def register(intent: AnalysisIntent, builder: TemplateBuilder) -> None:
    """모듈 수준 빌더 사전에 ``intent`` → ``builder`` 매핑을 등록합니다."""
    _BUILDERS[intent] = builder


def all_builders() -> dict[AnalysisIntent, TemplateBuilder]:
    """현재까지 등록된 빌더 사전의 사본을 반환합니다."""
    return dict(_BUILDERS)


# Side-effect import: 각 모듈이 import 시점에 register() 를 호출하여
# 자신의 빌더를 _BUILDERS 에 등록합니다.
from evalvault.domain.services.pipeline_templates import (  # noqa: E402, F401
    analyze_templates,
    compare_templates,
    generate_templates,
    other_templates,
    verify_templates,
)

__all__ = ["TemplateBuilder", "all_builders", "register"]
