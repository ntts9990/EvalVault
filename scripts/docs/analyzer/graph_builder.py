"""Graph builder for type and dependency visualization.

타입 그래프와 의존성 그래프를 구축하고,
레이아웃 좌표를 미리 계산합니다.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict

from scripts.docs.models.schema import (
    ClassSymbol,
    FunctionSymbol,
    GraphEdge,
    GraphNode,
    ModuleInfo,
    TypeGraph,
)


class GraphBuilder:
    """그래프 빌더."""

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []

    def build_type_graph(self, modules: list[ModuleInfo]) -> TypeGraph:
        """모듈들에서 타입 그래프 구축.

        Args:
            modules: 분석된 모듈 목록

        Returns:
            타입 그래프
        """
        self._nodes = {}
        self._edges = []

        for module in modules:
            self._process_module(module)

        # 레이아웃 계산
        self._calculate_layout()

        return TypeGraph(
            nodes=list(self._nodes.values()),
            edges=self._edges,
        )

    def build_dependency_graph(self, modules: list[ModuleInfo]) -> TypeGraph:
        """모듈 간 의존성 그래프 구축.

        Args:
            modules: 분석된 모듈 목록

        Returns:
            의존성 그래프
        """
        self._nodes = {}
        self._edges = []

        # 모듈 노드 생성
        for module in modules:
            node_id = self._make_id(module.name)
            self._nodes[node_id] = GraphNode(
                id=node_id,
                label=module.name.split(".")[-1],
                kind="module",
                module_path=module.name,
                metadata={
                    "full_name": module.name,
                    "layer": module.layer,
                    "file_path": module.file_path,
                },
            )

        # 의존성 엣지 생성
        module_names = {m.name for m in modules}
        for module in modules:
            source_id = self._make_id(module.name)
            for imp in module.imports:
                # 프로젝트 내부 import만
                target_module = self._find_matching_module(imp, module_names)
                if target_module:
                    target_id = self._make_id(target_module)
                    if target_id in self._nodes and source_id != target_id:
                        self._edges.append(
                            GraphEdge(
                                source=source_id,
                                target=target_id,
                                relation="uses",
                                label="imports",
                            )
                        )

        # 레이아웃 계산
        self._calculate_layout()

        return TypeGraph(
            nodes=list(self._nodes.values()),
            edges=self._edges,
        )

    def _process_module(self, module: ModuleInfo) -> None:
        """모듈에서 타입 노드와 엣지 추출."""
        # 클래스 노드 생성
        for cls in module.classes:
            self._add_class_node(cls, module)

        # 함수에서 타입 참조 추출
        for func in module.functions:
            self._add_function_types(func, module)

    def _add_class_node(self, cls: ClassSymbol, module: ModuleInfo) -> None:
        """클래스 노드 추가."""
        node_id = self._make_id(cls.qualified_name)

        self._nodes[node_id] = GraphNode(
            id=node_id,
            label=cls.name,
            kind="class",
            module_path=module.name,
            metadata={
                "qualified_name": cls.qualified_name,
                "is_dataclass": cls.is_dataclass,
                "is_protocol": cls.is_protocol,
                "layer": cls.layer,
            },
        )

        # 상속 관계 엣지
        for base in cls.bases:
            if base not in ("object", "ABC", "Protocol"):
                base_id = self._make_id(base)
                self._add_type_node(base, module.name)
                self._edges.append(
                    GraphEdge(
                        source=node_id,
                        target=base_id,
                        relation="inherits",
                        label="extends",
                    )
                )

        # 필드 타입 엣지 (dataclass, class variables)
        for var_name, type_ref in {**cls.class_variables, **cls.instance_variables}.items():
            type_id = self._make_id(type_ref.base_type)
            self._add_type_node(type_ref.base_type, module.name)
            self._edges.append(
                GraphEdge(
                    source=node_id,
                    target=type_id,
                    relation="contains",
                    label=var_name,
                )
            )

        # 메서드의 입출력 타입
        for method in cls.methods:
            self._add_function_types(method, module, parent_id=node_id)

    def _add_function_types(
        self,
        func: FunctionSymbol,
        module: ModuleInfo,
        parent_id: str | None = None,
    ) -> None:
        """함수의 입출력 타입 노드/엣지 추가."""
        func_id = self._make_id(func.qualified_name)

        self._nodes[func_id] = GraphNode(
            id=func_id,
            label=func.name,
            kind="function",
            module_path=module.name,
            metadata={
                "qualified_name": func.qualified_name,
                "is_async": func.is_async,
                "layer": func.layer,
            },
        )

        # 입력 타입 엣지
        for param in func.io.inputs:
            if param.type_ref and param.type_ref.base_type:
                type_id = self._make_id(param.type_ref.base_type)
                self._add_type_node(param.type_ref.base_type, module.name)
                self._edges.append(
                    GraphEdge(
                        source=type_id,
                        target=func_id,
                        relation="input",
                        label=param.name,
                    )
                )

        # 출력 타입 엣지
        if func.io.output and func.io.output.base_type:
            type_id = self._make_id(func.io.output.base_type)
            self._add_type_node(func.io.output.base_type, module.name)
            self._edges.append(
                GraphEdge(
                    source=func_id,
                    target=type_id,
                    relation="output",
                    label="returns",
                )
            )

        # 예외 타입 엣지
        for exc in func.io.raises:
            exc_id = self._make_id(exc.exception_type)
            self._add_type_node(exc.exception_type, module.name)
            self._edges.append(
                GraphEdge(
                    source=func_id,
                    target=exc_id,
                    relation="raises",
                    label="raises",
                )
            )

    def _add_type_node(self, type_name: str, module_path: str) -> None:
        """타입 노드 추가 (없으면)."""
        type_id = self._make_id(type_name)
        if type_id not in self._nodes:
            self._nodes[type_id] = GraphNode(
                id=type_id,
                label=type_name,
                kind="type",
                module_path=module_path,
            )

    def _find_matching_module(self, import_path: str, module_names: set[str]) -> str | None:
        """import 경로에 매칭되는 모듈 찾기."""
        # 정확히 일치
        if import_path in module_names:
            return import_path

        # evalvault로 시작하는지 확인
        if import_path.startswith("evalvault."):
            # 부모 모듈 매칭
            parts = import_path.split(".")
            for i in range(len(parts), 0, -1):
                candidate = ".".join(parts[:i])
                if candidate in module_names:
                    return candidate

        return None

    def _make_id(self, name: str) -> str:
        """이름에서 고유 ID 생성."""
        # 짧은 해시로 변환
        hash_val = hashlib.md5(name.encode()).hexdigest()[:8]
        # 안전한 이름 부분 추출
        safe_name = name.split(".")[-1].replace("-", "_")[:20]
        return f"{safe_name}_{hash_val}"

    def _calculate_layout(self) -> None:
        """그래프 레이아웃 계산.

        간단한 force-directed 레이아웃 알고리즘 사용.
        복잡한 경우 networkx를 사용하는 것이 좋음.
        """
        if not self._nodes:
            return

        nodes = list(self._nodes.values())
        n = len(nodes)

        # 초기 위치: 원형 배치
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / n
            radius = 300 + (i % 3) * 100  # 약간의 변형
            node.x = 500 + radius * math.cos(angle)
            node.y = 400 + radius * math.sin(angle)

        # 레이어별 그룹핑
        layer_groups: dict[str, list[GraphNode]] = defaultdict(list)
        for node in nodes:
            layer = node.metadata.get("layer", "other")
            layer_groups[layer].append(node)

        # 레이어별 Y 좌표 조정
        layer_y = {
            "domain": 100,
            "ports": 300,
            "adapters": 500,
            "config": 700,
            "other": 900,
        }

        for layer, group_nodes in layer_groups.items():
            base_y = layer_y.get(layer, 500)
            for i, node in enumerate(group_nodes):
                node.y = base_y + (i % 5) * 50
                node.x = 100 + (i * 150) % 900

        # 간단한 Force-directed 반복 (선택적)
        self._apply_force_directed(nodes, iterations=50)

    def _apply_force_directed(self, nodes: list[GraphNode], iterations: int = 50) -> None:
        """간단한 force-directed 레이아웃 적용."""
        if len(nodes) < 2:
            return

        # 엣지를 인접 리스트로 변환
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in self._edges:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)

        node_map = {n.id: n for n in nodes}

        k = 100  # 이상적인 거리
        t = 100  # 온도 (점점 감소)

        for _ in range(iterations):
            # 각 노드에 대한 힘 계산
            forces: dict[str, tuple[float, float]] = {n.id: (0.0, 0.0) for n in nodes}

            for i, n1 in enumerate(nodes):
                for n2 in nodes[i + 1 :]:
                    dx = n1.x - n2.x
                    dy = n1.y - n2.y
                    dist = max(math.sqrt(dx * dx + dy * dy), 0.01)

                    # 반발력
                    repulsion = k * k / dist
                    fx = dx / dist * repulsion
                    fy = dy / dist * repulsion

                    forces[n1.id] = (forces[n1.id][0] + fx, forces[n1.id][1] + fy)
                    forces[n2.id] = (forces[n2.id][0] - fx, forces[n2.id][1] - fy)

            # 연결된 노드 간 인력
            for edge in self._edges:
                if edge.source in node_map and edge.target in node_map:
                    n1 = node_map[edge.source]
                    n2 = node_map[edge.target]
                    dx = n1.x - n2.x
                    dy = n1.y - n2.y
                    dist = max(math.sqrt(dx * dx + dy * dy), 0.01)

                    attraction = dist * dist / k
                    fx = dx / dist * attraction
                    fy = dy / dist * attraction

                    forces[n1.id] = (forces[n1.id][0] - fx * 0.1, forces[n1.id][1] - fy * 0.1)
                    forces[n2.id] = (forces[n2.id][0] + fx * 0.1, forces[n2.id][1] + fy * 0.1)

            # 위치 업데이트
            for node in nodes:
                fx, fy = forces[node.id]
                # 힘 제한
                mag = math.sqrt(fx * fx + fy * fy)
                if mag > t:
                    fx = fx / mag * t
                    fy = fy / mag * t

                node.x += fx
                node.y += fy

                # 경계 제한
                node.x = max(50, min(950, node.x))
                node.y = max(50, min(750, node.y))

            # 온도 감소
            t *= 0.95
