"""Phase 14: Query-Based DAG Analysis Pipeline Entities.

사용자 쿼리를 분석하여 자동으로 DAG 스타일 분석 파이프라인을 구성하고
실행하는 시스템의 핵심 엔티티들을 정의합니다.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# =============================================================================
# Enums
# =============================================================================


class AnalysisIntent(str, Enum):
    """사용자 쿼리에서 파악되는 분석 의도.

    의도 분류기(Intent Classifier)가 사용자 쿼리를 분석하여
    적절한 분석 파이프라인을 구성하는 데 사용됩니다.
    """

    # 검증 (Verification)
    VERIFY_MORPHEME = "verify_morpheme"  # 형태소 분석 검증
    VERIFY_EMBEDDING = "verify_embedding"  # 임베딩 품질 검증
    VERIFY_RETRIEVAL = "verify_retrieval"  # 검색 품질 검증

    # 비교 (Comparison)
    COMPARE_SEARCH_METHODS = "compare_search"  # 검색 방식 비교 (RRF vs 다른 방식)
    COMPARE_MODELS = "compare_models"  # 모델 비교
    COMPARE_RUNS = "compare_runs"  # 실행 결과 비교

    # 분석 (Analysis)
    ANALYZE_LOW_METRICS = "analyze_low_metrics"
    ANALYZE_PATTERNS = "analyze_patterns"
    ANALYZE_TRENDS = "analyze_trends"
    ANALYZE_STATISTICAL = "analyze_statistical"
    ANALYZE_NLP = "analyze_nlp"
    ANALYZE_DATASET_FEATURES = "analyze_dataset_features"
    ANALYZE_CAUSAL = "analyze_causal"
    ANALYZE_NETWORK = "analyze_network"
    ANALYZE_PLAYBOOK = "analyze_playbook"

    DETECT_ANOMALIES = "detect_anomalies"
    FORECAST_PERFORMANCE = "forecast_performance"

    GENERATE_HYPOTHESES = "generate_hypotheses"

    # 벤치마크 (Benchmark)
    BENCHMARK_RETRIEVAL = "benchmark_retrieval"  # 검색 벤치마크

    # 보고서 (Report)
    GENERATE_SUMMARY = "generate_summary"  # 요약 보고서
    GENERATE_DETAILED = "generate_detailed"  # 상세 보고서
    GENERATE_COMPARISON = "generate_comparison"  # 비교 보고서


class AnalysisIntentCategory(str, Enum):
    """분석 의도 카테고리.

    의도를 상위 카테고리로 그룹화합니다.
    """

    VERIFICATION = "verification"  # 검증
    COMPARISON = "comparison"  # 비교
    ANALYSIS = "analysis"  # 분석
    REPORT = "report"  # 보고서


class NodeExecutionStatus(str, Enum):
    """노드 실행 상태."""

    PENDING = "pending"  # 대기 중
    RUNNING = "running"  # 실행 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실패
    SKIPPED = "skipped"  # 건너뜀


# =============================================================================
# AnalysisNode
# =============================================================================


@dataclass
class AnalysisNode:
    """분석 DAG의 개별 노드.

    파이프라인 내에서 특정 분석 모듈을 실행하는 단위입니다.

    Attributes:
        id: 노드 고유 식별자
        name: 노드 표시 이름
        module: 실행할 분석 모듈 ID
        params: 모듈 실행 파라미터
        depends_on: 이 노드가 의존하는 노드 ID 목록
    """

    id: str
    name: str
    module: str
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)

    @property
    def has_dependencies(self) -> bool:
        """의존성 존재 여부."""
        return len(self.depends_on) > 0

    @property
    def is_root(self) -> bool:
        """루트 노드 여부 (의존성 없음)."""
        return not self.has_dependencies


# =============================================================================
# AnalysisContext
# =============================================================================


@dataclass
class AnalysisContext:
    """분석 실행 컨텍스트.

    사용자 쿼리와 함께 분석에 필요한 추가 정보를 담습니다.

    Attributes:
        query: 사용자 분석 요청 쿼리
        run_id: 분석 대상 평가 실행 ID (선택)
        dataset: 분석 대상 데이터셋 (선택)
        additional_params: 추가 파라미터
    """

    query: str
    run_id: str | None = None
    dataset: Any | None = None
    additional_params: dict[str, Any] = field(default_factory=dict)

    @property
    def has_run_id(self) -> bool:
        """run_id 존재 여부."""
        return self.run_id is not None

    @property
    def has_dataset(self) -> bool:
        """dataset 존재 여부."""
        return self.dataset is not None


# =============================================================================
# AnalysisPipeline
# =============================================================================


@dataclass
class AnalysisPipeline:
    """분석 DAG 파이프라인.

    의도에 따라 구성된 분석 노드들의 방향성 비순환 그래프(DAG)입니다.

    Attributes:
        intent: 분석 의도
        nodes: 분석 노드 목록
        edges: 노드 간 엣지 (source, target) 튜플 목록
        pipeline_id: 파이프라인 고유 ID
        created_at: 생성 시간
    """

    intent: AnalysisIntent
    nodes: list[AnalysisNode] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)
    pipeline_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def get_node(self, node_id: str) -> AnalysisNode | None:
        """ID로 노드 조회.

        Args:
            node_id: 노드 ID

        Returns:
            노드 또는 None
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    @property
    def root_nodes(self) -> list[AnalysisNode]:
        """루트 노드 목록 (의존성 없는 노드)."""
        return [node for node in self.nodes if node.is_root]

    @property
    def leaf_nodes(self) -> list[AnalysisNode]:
        """리프 노드 목록 (다른 노드가 의존하지 않는 노드)."""
        # 다른 노드의 depends_on에 포함되지 않은 노드
        all_dependencies = set()
        for node in self.nodes:
            all_dependencies.update(node.depends_on)

        # 엣지의 source도 확인
        sources = {src for src, _ in self.edges}

        return [
            node
            for node in self.nodes
            if node.id not in all_dependencies and node.id not in sources
        ]

    @property
    def node_count(self) -> int:
        """노드 개수."""
        return len(self.nodes)

    def topological_order(self) -> list[str]:
        """위상 정렬된 노드 실행 순서.

        Kahn's algorithm을 사용하여 DAG를 위상 정렬합니다.

        Returns:
            노드 ID 목록 (실행 순서)
        """
        if not self.nodes:
            return []

        # 진입 차수 계산
        in_degree: dict[str, int] = {node.id: 0 for node in self.nodes}
        for node in self.nodes:
            for dep in node.depends_on:
                if dep in in_degree:
                    pass  # 의존 노드가 있다는 건 dep이 나를 가리킨다는 것이 아님
            in_degree[node.id] = len(node.depends_on)

        # 진입 차수 0인 노드로 시작
        queue: deque[str] = deque()
        for node_id, degree in in_degree.items():
            if degree == 0:
                queue.append(node_id)

        result: list[str] = []
        while queue:
            current = queue.popleft()
            result.append(current)

            # 현재 노드를 의존하는 노드들의 진입 차수 감소
            for node in self.nodes:
                if current in node.depends_on:
                    in_degree[node.id] -= 1
                    if in_degree[node.id] == 0:
                        queue.append(node.id)

        return result

    def validate(self) -> bool:
        """파이프라인 유효성 검증 (순환 의존성 검사).

        Returns:
            유효하면 True, 순환이 있으면 False
        """
        # 위상 정렬 결과와 노드 수가 같으면 순환 없음
        order = self.topological_order()
        return len(order) == len(self.nodes)

    def add_node(self, node: AnalysisNode) -> None:
        """노드 추가.

        Args:
            node: 추가할 노드
        """
        self.nodes.append(node)

    def add_edge(self, source: str, target: str) -> None:
        """엣지 추가.

        Args:
            source: 소스 노드 ID
            target: 타겟 노드 ID
        """
        self.edges.append((source, target))


# =============================================================================
# NodeResult
# =============================================================================


@dataclass
class NodeResult:
    """노드 실행 결과.

    Attributes:
        node_id: 노드 ID
        status: 실행 상태
        output: 실행 결과 데이터
        error: 에러 메시지 (실패 시)
        duration_ms: 실행 시간 (밀리초)
    """

    node_id: str
    status: NodeExecutionStatus
    output: Any | None = None
    error: str | None = None
    duration_ms: int | None = None

    @property
    def is_success(self) -> bool:
        """성공 여부."""
        return self.status == NodeExecutionStatus.COMPLETED

    @property
    def is_failure(self) -> bool:
        """실패 여부."""
        return self.status == NodeExecutionStatus.FAILED


# =============================================================================
# PipelineResult
# =============================================================================


@dataclass
class PipelineResult:
    """파이프라인 실행 결과.

    Attributes:
        pipeline_id: 파이프라인 ID
        intent: 분석 의도
        node_results: 노드별 실행 결과
        final_output: 최종 출력 데이터
        total_duration_ms: 총 실행 시간
        started_at: 시작 시간
        finished_at: 종료 시간
    """

    pipeline_id: str
    intent: AnalysisIntent
    node_results: dict[str, NodeResult] = field(default_factory=dict)
    final_output: Any | None = None
    total_duration_ms: int | None = None
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None

    def add_node_result(self, result: NodeResult) -> None:
        """노드 결과 추가.

        Args:
            result: 노드 실행 결과
        """
        self.node_results[result.node_id] = result

    def get_node_result(self, node_id: str) -> NodeResult | None:
        """노드 결과 조회.

        Args:
            node_id: 노드 ID

        Returns:
            노드 결과 또는 None
        """
        return self.node_results.get(node_id)

    @property
    def is_complete(self) -> bool:
        """완료 여부."""
        return self.finished_at is not None

    @property
    def success_count(self) -> int:
        """성공한 노드 수."""
        return sum(1 for r in self.node_results.values() if r.is_success)

    @property
    def failure_count(self) -> int:
        """실패한 노드 수."""
        return sum(1 for r in self.node_results.values() if r.is_failure)

    @property
    def all_succeeded(self) -> bool:
        """모든 노드 성공 여부."""
        if not self.node_results:
            return True
        return all(r.is_success for r in self.node_results.values())

    def mark_complete(
        self,
        final_output: Any | None = None,
        total_duration_ms: int | None = None,
    ) -> None:
        """완료 표시.

        Args:
            final_output: 최종 출력
            total_duration_ms: 총 실행 시간
        """
        self.finished_at = datetime.now()
        self.final_output = final_output
        self.total_duration_ms = total_duration_ms


# =============================================================================
# ModuleMetadata (분석 모듈 메타데이터)
# =============================================================================


@dataclass
class ModuleMetadata:
    """분석 모듈 메타데이터.

    의도 분류기가 적절한 모듈을 선택하는 데 사용됩니다.

    Attributes:
        module_id: 모듈 고유 ID
        name: 모듈 표시 이름
        description: 모듈 설명 (의도 분류 시 참조)
        input_types: 입력 타입 목록
        output_types: 출력 타입 목록
        requires: 필수 의존 모듈 ID 목록
        optional_requires: 선택적 의존 모듈 ID 목록
        tags: 태그 목록 (의도 분류 힌트)
    """

    module_id: str
    name: str
    description: str
    input_types: list[str]
    output_types: list[str]
    requires: list[str] = field(default_factory=list)
    optional_requires: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def matches_keywords(self, keywords: list[str]) -> bool:
        """키워드 매칭 여부.

        Args:
            keywords: 검색 키워드 목록

        Returns:
            하나라도 매칭되면 True
        """
        searchable = f"{self.name} {self.description} {' '.join(self.tags)}"
        searchable_lower = searchable.lower()

        return any(keyword.lower() in searchable_lower for keyword in keywords)

    def relevance_score(self, keywords: list[str]) -> int:
        """키워드 관련성 점수.

        Args:
            keywords: 검색 키워드 목록

        Returns:
            매칭된 키워드 수
        """
        searchable = f"{self.name} {self.description} {' '.join(self.tags)}"
        searchable_lower = searchable.lower()

        score = 0
        for keyword in keywords:
            if keyword.lower() in searchable_lower:
                score += 1
        return score


# =============================================================================
# ModuleCatalog (분석 모듈 카탈로그)
# =============================================================================


@dataclass
class ModuleCatalog:
    """분석 모듈 카탈로그.

    사용 가능한 분석 모듈들을 관리하는 레지스트리입니다.
    """

    _modules: dict[str, ModuleMetadata] = field(default_factory=dict)

    def register(self, metadata: ModuleMetadata) -> None:
        """모듈 등록.

        Args:
            metadata: 모듈 메타데이터
        """
        self._modules[metadata.module_id] = metadata

    def get(self, module_id: str) -> ModuleMetadata | None:
        """모듈 조회.

        Args:
            module_id: 모듈 ID

        Returns:
            모듈 메타데이터 또는 None
        """
        return self._modules.get(module_id)

    def list_all(self) -> list[ModuleMetadata]:
        """전체 모듈 목록.

        Returns:
            모듈 메타데이터 목록
        """
        return list(self._modules.values())

    def find_by_tag(self, tag: str) -> list[ModuleMetadata]:
        """태그로 모듈 검색.

        Args:
            tag: 검색 태그

        Returns:
            매칭된 모듈 목록
        """
        return [m for m in self._modules.values() if tag in m.tags]

    def find_by_keywords(self, keywords: list[str]) -> list[ModuleMetadata]:
        """키워드로 모듈 검색 (관련성 순 정렬).

        Args:
            keywords: 검색 키워드 목록

        Returns:
            매칭된 모듈 목록 (관련성 높은 순)
        """
        matches = []
        for module in self._modules.values():
            score = module.relevance_score(keywords)
            if score > 0:
                matches.append((score, module))

        # 점수 높은 순 정렬
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in matches]

    def get_dependencies(self, module_id: str) -> list[str]:
        """모듈의 모든 의존성 조회 (재귀).

        Args:
            module_id: 모듈 ID

        Returns:
            의존 모듈 ID 목록
        """
        deps: set[str] = set()
        self._collect_dependencies(module_id, deps)
        return list(deps)

    def _collect_dependencies(self, module_id: str, collected: set[str]) -> None:
        """의존성 재귀 수집.

        Args:
            module_id: 모듈 ID
            collected: 수집된 의존성 집합
        """
        module = self.get(module_id)
        if not module:
            return

        for dep_id in module.requires:
            if dep_id not in collected:
                collected.add(dep_id)
                self._collect_dependencies(dep_id, collected)
