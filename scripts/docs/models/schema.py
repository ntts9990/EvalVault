"""Data models for code analysis and documentation.

전문가 관점을 통합한 데이터 모델:
- IT 전문가: 정확한 타입 정보, 의존성, 데이터 흐름
- 인지심리학자: 확신도(Confidence)로 불확실성 명시
- UX 전문가: 계층적 구조, 검색/필터 가능한 속성
- 교육학자: 일관된 템플릿, 맥락 정보
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class Confidence(Enum):
    """확신도 레벨.

    - HIGH: 타입힌트가 명시적으로 있음
    - MEDIUM: docstring이나 기본값에서 추론
    - LOW: 휴리스틱으로 추정
    - UNKNOWN: 정보 없음
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Visibility(Enum):
    """심볼 가시성."""

    PUBLIC = "public"
    INTERNAL = "internal"  # 단일 언더스코어 (_)
    PRIVATE = "private"  # 이중 언더스코어 (__)
    DUNDER = "dunder"  # __name__ 스타일


class SideEffectKind(Enum):
    """부작용 종류."""

    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    DATABASE = "database"
    HTTP_REQUEST = "http_request"
    ENVIRONMENT = "environment"
    LOGGING = "logging"
    SUBPROCESS = "subprocess"


@dataclass
class TypeRef:
    """타입 참조.

    Attributes:
        raw: 원본 타입 문자열 (예: "list[str]", "Optional[EvalRequest]")
        normalized: 정규화된 형태 (예: "list[str]", "EvalRequest | None")
        base_type: 기본 타입 (예: "list", "EvalRequest")
        type_args: 제네릭 인자들 (예: ["str"])
        is_optional: Optional 여부
        is_collection: 컬렉션 여부 (list, dict, set 등)
        module_path: 타입이 정의된 모듈 경로 (알 수 있는 경우)
        confidence: 타입 정보 확신도
    """

    raw: str
    normalized: str = ""
    base_type: str = ""
    type_args: list[str] = field(default_factory=list)
    is_optional: bool = False
    is_collection: bool = False
    module_path: str | None = None
    confidence: Confidence = Confidence.HIGH

    def __post_init__(self) -> None:
        if not self.normalized:
            self.normalized = self.raw
        if not self.base_type:
            self.base_type = self._extract_base_type()

    def _extract_base_type(self) -> str:
        """기본 타입 추출."""
        raw = self.raw.strip()
        if "[" in raw:
            return raw.split("[")[0]
        if "|" in raw:
            parts = [p.strip() for p in raw.split("|") if p.strip() != "None"]
            return parts[0] if parts else "None"
        return raw


@dataclass
class Parameter:
    """함수/메서드 파라미터.

    Attributes:
        name: 파라미터 이름
        type_ref: 타입 참조
        default: 기본값 (있는 경우)
        is_optional: 선택적 파라미터 여부
        kind: 파라미터 종류 (positional, keyword, *args, **kwargs)
        description: docstring에서 추출한 설명
    """

    name: str
    type_ref: TypeRef | None = None
    default: str | None = None
    is_optional: bool = False
    kind: Literal["positional", "keyword", "var_positional", "var_keyword"] = "positional"
    description: str = ""


@dataclass
class RaisedException:
    """발생 가능한 예외.

    Attributes:
        exception_type: 예외 타입 (예: "ValueError", "FileNotFoundError")
        condition: 발생 조건 (추출 가능한 경우)
        confidence: 확신도
    """

    exception_type: str
    condition: str = ""
    confidence: Confidence = Confidence.HIGH


@dataclass
class SideEffect:
    """부작용 정보.

    Attributes:
        kind: 부작용 종류
        evidence: 탐지 근거 (코드 패턴, 함수 호출 등)
        target: 대상 (파일 경로, URL, DB 테이블 등)
        confidence: 확신도
    """

    kind: SideEffectKind
    evidence: str
    target: str = ""
    confidence: Confidence = Confidence.MEDIUM


@dataclass
class IOSpec:
    """입출력 명세.

    Attributes:
        inputs: 입력 파라미터 목록
        output: 반환 타입
        raises: 발생 가능한 예외들
        side_effects: 부작용들
        overall_confidence: 전체 확신도
    """

    inputs: list[Parameter] = field(default_factory=list)
    output: TypeRef | None = None
    raises: list[RaisedException] = field(default_factory=list)
    side_effects: list[SideEffect] = field(default_factory=list)
    overall_confidence: Confidence = Confidence.UNKNOWN


@dataclass
class BaseSymbol:
    """심볼 기본 정보.

    Attributes:
        name: 심볼 이름
        qualified_name: 전체 경로 (예: "evalvault.domain.services.evaluator.Evaluator.run")
        file_path: 파일 경로
        line_start: 시작 줄 번호
        line_end: 끝 줄 번호
        docstring: 문서화 문자열
        docstring_summary: docstring 첫 줄 요약
        visibility: 가시성
        decorators: 데코레이터 목록
        layer: 레이어 태그 (domain, ports, adapters)
    """

    name: str
    qualified_name: str
    file_path: str
    line_start: int
    line_end: int
    docstring: str = ""
    docstring_summary: str = ""
    visibility: Visibility = Visibility.PUBLIC
    decorators: list[str] = field(default_factory=list)
    layer: str = ""


@dataclass
class FunctionSymbol(BaseSymbol):
    """함수 심볼.

    Attributes:
        io: 입출력 명세
        is_async: 비동기 함수 여부
        is_generator: 제너레이터 여부
    """

    io: IOSpec = field(default_factory=IOSpec)
    is_async: bool = False
    is_generator: bool = False


@dataclass
class MethodSymbol(FunctionSymbol):
    """메서드 심볼.

    Attributes:
        is_classmethod: 클래스 메서드 여부
        is_staticmethod: 정적 메서드 여부
        is_property: 프로퍼티 여부
        is_abstractmethod: 추상 메서드 여부
        owner_class: 소유 클래스 이름
    """

    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    is_abstractmethod: bool = False
    owner_class: str = ""


@dataclass
class ClassSymbol(BaseSymbol):
    """클래스 심볼.

    Attributes:
        bases: 상속받는 클래스들
        methods: 메서드 목록
        class_variables: 클래스 변수들 (타입과 함께)
        instance_variables: 인스턴스 변수들 (타입과 함께)
        is_dataclass: dataclass 여부
        is_protocol: Protocol 여부
        is_abstract: ABC 여부
    """

    bases: list[str] = field(default_factory=list)
    methods: list[MethodSymbol] = field(default_factory=list)
    class_variables: dict[str, TypeRef] = field(default_factory=dict)
    instance_variables: dict[str, TypeRef] = field(default_factory=dict)
    is_dataclass: bool = False
    is_protocol: bool = False
    is_abstract: bool = False


@dataclass
class ModuleInfo:
    """모듈 정보.

    Attributes:
        name: 모듈 이름
        file_path: 파일 경로
        docstring: 모듈 docstring
        imports: import 문 목록
        functions: 함수 목록
        classes: 클래스 목록
        layer: 레이어 (domain, ports, adapters)
    """

    name: str
    file_path: str
    docstring: str = ""
    imports: list[str] = field(default_factory=list)
    functions: list[FunctionSymbol] = field(default_factory=list)
    classes: list[ClassSymbol] = field(default_factory=list)
    layer: str = ""


@dataclass
class GraphNode:
    """그래프 노드.

    Attributes:
        id: 노드 ID
        label: 표시 라벨
        kind: 노드 종류 (type, class, function, module)
        module_path: 모듈 경로
        x: X 좌표 (레이아웃 계산 후)
        y: Y 좌표 (레이아웃 계산 후)
        metadata: 추가 메타데이터
    """

    id: str
    label: str
    kind: Literal["type", "class", "function", "module"]
    module_path: str = ""
    x: float = 0.0
    y: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class GraphEdge:
    """그래프 엣지.

    Attributes:
        source: 소스 노드 ID
        target: 타겟 노드 ID
        relation: 관계 종류
        label: 표시 라벨
    """

    source: str
    target: str
    relation: Literal["input", "output", "contains", "inherits", "uses", "raises"]
    label: str = ""


@dataclass
class TypeGraph:
    """타입 그래프.

    Attributes:
        nodes: 노드 목록
        edges: 엣지 목록
    """

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


@dataclass
class ProjectAnalysis:
    """프로젝트 분석 결과.

    Attributes:
        project_name: 프로젝트 이름
        analyzed_at: 분석 시각
        version: 분석기 버전
        modules: 모듈 목록
        type_graph: 타입 그래프
        statistics: 통계 정보
    """

    project_name: str
    analyzed_at: str
    version: str = "1.0.0"
    modules: list[ModuleInfo] = field(default_factory=list)
    type_graph: TypeGraph = field(default_factory=TypeGraph)
    statistics: dict = field(default_factory=dict)
