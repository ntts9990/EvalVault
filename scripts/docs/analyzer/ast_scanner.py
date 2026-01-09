"""AST-based Python source code scanner.

Python AST를 사용하여 소스 코드에서 클래스, 함수, 메서드의
시그니처와 타입 정보를 추출합니다.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from scripts.docs.models.schema import (
    ClassSymbol,
    Confidence,
    FunctionSymbol,
    IOSpec,
    MethodSymbol,
    ModuleInfo,
    Parameter,
    RaisedException,
    TypeRef,
    Visibility,
)


@dataclass
class ScanConfig:
    """스캔 설정.

    Attributes:
        include_private: private 심볼 포함 여부
        include_dunder: dunder 메서드 포함 여부
        extract_docstrings: docstring 추출 여부
        extract_raises: raise 문 추출 여부
    """

    include_private: bool = True
    include_dunder: bool = False
    extract_docstrings: bool = True
    extract_raises: bool = True


class ASTScanner:
    """AST 기반 소스 코드 스캐너."""

    def __init__(self, config: ScanConfig | None = None) -> None:
        self.config = config or ScanConfig()

    def scan_file(self, file_path: Path) -> ModuleInfo | None:
        """단일 파일 스캔.

        Args:
            file_path: 스캔할 Python 파일 경로

        Returns:
            ModuleInfo 또는 파싱 실패 시 None
        """
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
            return None

        module_name = self._get_module_name(file_path)
        layer = self._detect_layer(file_path)

        module = ModuleInfo(
            name=module_name,
            file_path=str(file_path),
            docstring=ast.get_docstring(tree) or "",
            imports=self._extract_imports(tree),
            layer=layer,
        )

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                func = self._parse_function(node, module_name, str(file_path), layer)
                if func and self._should_include(func.name):
                    module.functions.append(func)
            elif isinstance(node, ast.ClassDef):
                cls = self._parse_class(node, module_name, str(file_path), layer, source)
                if cls and self._should_include(cls.name):
                    module.classes.append(cls)

        return module

    def scan_directory(
        self, dir_path: Path, exclude_patterns: list[str] | None = None
    ) -> list[ModuleInfo]:
        """디렉토리 재귀 스캔.

        Args:
            dir_path: 스캔할 디렉토리 경로
            exclude_patterns: 제외할 패턴들 (예: ["test_*", "*_test.py"])

        Returns:
            ModuleInfo 목록
        """
        exclude_patterns = exclude_patterns or []
        modules: list[ModuleInfo] = []

        for py_file in dir_path.rglob("*.py"):
            # 제외 패턴 체크
            if any(py_file.match(pattern) for pattern in exclude_patterns):
                continue

            # __pycache__ 제외
            if "__pycache__" in str(py_file):
                continue

            module = self.scan_file(py_file)
            if module:
                modules.append(module)

        return modules

    def _get_module_name(self, file_path: Path) -> str:
        """파일 경로에서 모듈 이름 추출."""
        parts = file_path.with_suffix("").parts

        # src/evalvault/... 패턴 찾기
        try:
            src_idx = parts.index("src")
            return ".".join(parts[src_idx + 1 :])
        except ValueError:
            pass

        # scripts/... 패턴
        try:
            scripts_idx = parts.index("scripts")
            return ".".join(parts[scripts_idx:])
        except ValueError:
            pass

        return ".".join(parts[-3:])  # 기본: 마지막 3 부분

    def _detect_layer(self, file_path: Path) -> str:
        """파일 경로에서 레이어 감지."""
        path_str = str(file_path)
        if "/domain/" in path_str:
            return "domain"
        elif "/ports/" in path_str:
            return "ports"
        elif "/adapters/" in path_str:
            return "adapters"
        elif "/config/" in path_str:
            return "config"
        return "other"

    def _extract_imports(self, tree: ast.Module) -> list[str]:
        """import 문 추출."""
        imports: list[str] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports

    def _parse_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module_name: str,
        file_path: str,
        layer: str,
    ) -> FunctionSymbol:
        """함수 노드 파싱."""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        docstring = ast.get_docstring(node) or ""

        func = FunctionSymbol(
            name=node.name,
            qualified_name=f"{module_name}.{node.name}",
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=docstring,
            docstring_summary=self._get_docstring_summary(docstring),
            visibility=self._get_visibility(node.name),
            decorators=self._extract_decorators(node),
            layer=layer,
            is_async=is_async,
            is_generator=self._is_generator(node),
            io=self._extract_io(node, docstring),
        )

        return func

    def _parse_class(
        self,
        node: ast.ClassDef,
        module_name: str,
        file_path: str,
        layer: str,
        source: str,
    ) -> ClassSymbol:
        """클래스 노드 파싱."""
        docstring = ast.get_docstring(node) or ""
        decorators = self._extract_decorators(node)

        cls = ClassSymbol(
            name=node.name,
            qualified_name=f"{module_name}.{node.name}",
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=docstring,
            docstring_summary=self._get_docstring_summary(docstring),
            visibility=self._get_visibility(node.name),
            decorators=decorators,
            layer=layer,
            bases=self._extract_bases(node),
            is_dataclass="dataclass" in decorators,
            is_protocol=self._is_protocol(node),
            is_abstract=self._is_abstract(node),
        )

        # 메서드 파싱
        for child in node.body:
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                method = self._parse_method(child, cls.qualified_name, file_path, layer, node.name)
                if method and self._should_include_method(method.name):
                    cls.methods.append(method)
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                # 클래스 변수 (타입 어노테이션 있는 경우)
                var_name = child.target.id
                type_ref = self._annotation_to_type_ref(child.annotation)
                if type_ref:
                    cls.class_variables[var_name] = type_ref

        # dataclass 필드 추출
        if cls.is_dataclass:
            cls.instance_variables = self._extract_dataclass_fields(node)

        return cls

    def _parse_method(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_qualified_name: str,
        file_path: str,
        layer: str,
        owner_class: str,
    ) -> MethodSymbol:
        """메서드 노드 파싱."""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        docstring = ast.get_docstring(node) or ""
        decorators = self._extract_decorators(node)

        method = MethodSymbol(
            name=node.name,
            qualified_name=f"{class_qualified_name}.{node.name}",
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=docstring,
            docstring_summary=self._get_docstring_summary(docstring),
            visibility=self._get_visibility(node.name),
            decorators=decorators,
            layer=layer,
            is_async=is_async,
            is_generator=self._is_generator(node),
            io=self._extract_io(node, docstring),
            is_classmethod="classmethod" in decorators,
            is_staticmethod="staticmethod" in decorators,
            is_property="property" in decorators,
            is_abstractmethod="abstractmethod" in decorators,
            owner_class=owner_class,
        )

        return method

    def _extract_io(self, node: ast.FunctionDef | ast.AsyncFunctionDef, docstring: str) -> IOSpec:
        """함수의 입출력 명세 추출."""
        io = IOSpec()

        # 파라미터 추출
        io.inputs = self._extract_parameters(node)

        # 반환 타입 추출
        if node.returns:
            io.output = self._annotation_to_type_ref(node.returns)
        else:
            # docstring에서 추출 시도
            return_type = self._extract_return_from_docstring(docstring)
            if return_type:
                io.output = TypeRef(raw=return_type, confidence=Confidence.MEDIUM)

        # raise 문 추출
        if self.config.extract_raises:
            io.raises = self._extract_raises(node)
            io.raises.extend(self._extract_raises_from_docstring(docstring))

        # 전체 확신도 계산
        io.overall_confidence = self._calculate_io_confidence(io)

        return io

    def _extract_parameters(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[Parameter]:
        """파라미터 추출."""
        params: list[Parameter] = []
        args = node.args

        # 기본값 매핑 (뒤에서부터)
        defaults = [None] * (len(args.args) - len(args.defaults)) + list(args.defaults)

        for i, arg in enumerate(args.args):
            # self, cls 건너뛰기
            if arg.arg in ("self", "cls"):
                continue

            type_ref = None
            if arg.annotation:
                type_ref = self._annotation_to_type_ref(arg.annotation)

            default_value = None
            if defaults[i] is not None:
                default_value = self._ast_to_string(defaults[i])

            params.append(
                Parameter(
                    name=arg.arg,
                    type_ref=type_ref,
                    default=default_value,
                    is_optional=default_value is not None,
                    kind="positional",
                )
            )

        # *args
        if args.vararg:
            type_ref = None
            if args.vararg.annotation:
                type_ref = self._annotation_to_type_ref(args.vararg.annotation)
            params.append(
                Parameter(
                    name=args.vararg.arg,
                    type_ref=type_ref,
                    kind="var_positional",
                )
            )

        # keyword-only args
        kw_defaults = args.kw_defaults
        for i, arg in enumerate(args.kwonlyargs):
            type_ref = None
            if arg.annotation:
                type_ref = self._annotation_to_type_ref(arg.annotation)

            default_value = None
            if kw_defaults[i] is not None:
                default_value = self._ast_to_string(kw_defaults[i])

            params.append(
                Parameter(
                    name=arg.arg,
                    type_ref=type_ref,
                    default=default_value,
                    is_optional=default_value is not None,
                    kind="keyword",
                )
            )

        # **kwargs
        if args.kwarg:
            type_ref = None
            if args.kwarg.annotation:
                type_ref = self._annotation_to_type_ref(args.kwarg.annotation)
            params.append(
                Parameter(
                    name=args.kwarg.arg,
                    type_ref=type_ref,
                    kind="var_keyword",
                )
            )

        return params

    def _annotation_to_type_ref(self, annotation: ast.expr) -> TypeRef:
        """AST 어노테이션을 TypeRef로 변환."""
        raw = self._ast_to_string(annotation)

        type_ref = TypeRef(raw=raw, confidence=Confidence.HIGH)

        # Optional 감지
        if "Optional" in raw or "| None" in raw or "None |" in raw:
            type_ref.is_optional = True

        # Collection 감지
        collection_types = {
            "list",
            "List",
            "dict",
            "Dict",
            "set",
            "Set",
            "tuple",
            "Tuple",
            "Sequence",
            "Iterable",
        }
        if any(ct in raw for ct in collection_types):
            type_ref.is_collection = True

        # 타입 인자 추출
        if "[" in raw:
            match = re.search(r"\[(.*)\]", raw)
            if match:
                args_str = match.group(1)
                # 간단한 파싱 (중첩된 제네릭은 정확하지 않을 수 있음)
                type_ref.type_args = [a.strip() for a in args_str.split(",")]

        return type_ref

    def _extract_raises(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[RaisedException]:
        """함수 내 raise 문 추출."""
        raises: list[RaisedException] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Raise) and child.exc:
                exc_type = self._get_exception_type(child.exc)
                if exc_type:
                    raises.append(
                        RaisedException(
                            exception_type=exc_type,
                            confidence=Confidence.HIGH,
                        )
                    )

        return raises

    def _get_exception_type(self, exc_node: ast.expr) -> str | None:
        """예외 타입 추출."""
        if isinstance(exc_node, ast.Call):
            if isinstance(exc_node.func, ast.Name):
                return exc_node.func.id
            elif isinstance(exc_node.func, ast.Attribute):
                return exc_node.func.attr
        elif isinstance(exc_node, ast.Name):
            return exc_node.id
        return None

    def _extract_raises_from_docstring(self, docstring: str) -> list[RaisedException]:
        """docstring에서 Raises 섹션 추출."""
        raises: list[RaisedException] = []
        if not docstring:
            return raises

        # Raises: 또는 Raises 섹션 찾기
        raises_pattern = r"(?:Raises?:?\s*\n)((?:\s+\w+.*\n?)+)"
        match = re.search(raises_pattern, docstring, re.MULTILINE)
        if match:
            raises_section = match.group(1)
            # 각 예외 항목 파싱
            exc_pattern = r"(\w+(?:Error|Exception|Warning)?)\s*[:.]?\s*(.*)"
            for exc_match in re.finditer(exc_pattern, raises_section):
                exc_type = exc_match.group(1)
                condition = exc_match.group(2).strip()
                raises.append(
                    RaisedException(
                        exception_type=exc_type,
                        condition=condition,
                        confidence=Confidence.MEDIUM,
                    )
                )

        return raises

    def _extract_return_from_docstring(self, docstring: str) -> str | None:
        """docstring에서 반환 타입 추출."""
        if not docstring:
            return None

        # Returns: 섹션 찾기
        patterns = [
            r"Returns?:\s*\n\s+(\w+(?:\[.*?\])?)",  # Returns:\n    TypeName
            r"Returns?\s+(\w+(?:\[.*?\])?)\s*:",  # Returns TypeName:
        ]

        for pattern in patterns:
            match = re.search(pattern, docstring)
            if match:
                return match.group(1)

        return None

    def _extract_decorators(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    ) -> list[str]:
        """데코레이터 추출."""
        decorators: list[str] = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    decorators.append(dec.func.attr)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
        return decorators

    def _extract_bases(self, node: ast.ClassDef) -> list[str]:
        """상속 클래스 추출."""
        bases: list[str] = []
        for base in node.bases:
            bases.append(self._ast_to_string(base))
        return bases

    def _extract_dataclass_fields(self, node: ast.ClassDef) -> dict[str, TypeRef]:
        """dataclass 필드 추출."""
        fields: dict[str, TypeRef] = {}
        for child in node.body:
            if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                var_name = child.target.id
                type_ref = self._annotation_to_type_ref(child.annotation)
                fields[var_name] = type_ref
        return fields

    def _is_generator(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """제너레이터 여부 확인."""
        return any(isinstance(child, ast.Yield | ast.YieldFrom) for child in ast.walk(node))

    def _is_protocol(self, node: ast.ClassDef) -> bool:
        """Protocol 여부 확인."""
        for base in node.bases:
            base_str = self._ast_to_string(base)
            if "Protocol" in base_str:
                return True
        return False

    def _is_abstract(self, node: ast.ClassDef) -> bool:
        """ABC 여부 확인."""
        for base in node.bases:
            base_str = self._ast_to_string(base)
            if "ABC" in base_str or "ABCMeta" in base_str:
                return True
        # 또는 abstractmethod 데코레이터가 있는 메서드가 있는지
        for child in node.body:
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                for dec in child.decorator_list:
                    if isinstance(dec, ast.Name) and dec.id == "abstractmethod":
                        return True
        return False

    def _get_visibility(self, name: str) -> Visibility:
        """이름에서 가시성 결정."""
        if name.startswith("__") and name.endswith("__"):
            return Visibility.DUNDER
        elif name.startswith("__"):
            return Visibility.PRIVATE
        elif name.startswith("_"):
            return Visibility.INTERNAL
        return Visibility.PUBLIC

    def _should_include(self, name: str) -> bool:
        """심볼 포함 여부 결정."""
        visibility = self._get_visibility(name)
        if visibility == Visibility.DUNDER:
            return self.config.include_dunder
        if visibility in (Visibility.PRIVATE, Visibility.INTERNAL):
            return self.config.include_private
        return True

    def _should_include_method(self, name: str) -> bool:
        """메서드 포함 여부 결정."""
        visibility = self._get_visibility(name)
        if visibility == Visibility.DUNDER:
            # __init__, __call__ 등은 항상 포함
            if name in ("__init__", "__call__", "__enter__", "__exit__", "__iter__", "__next__"):
                return True
            return self.config.include_dunder
        return self._should_include(name)

    def _get_docstring_summary(self, docstring: str) -> str:
        """docstring 첫 줄 요약 추출."""
        if not docstring:
            return ""
        lines = docstring.strip().split("\n")
        return lines[0].strip() if lines else ""

    def _calculate_io_confidence(self, io: IOSpec) -> Confidence:
        """IO 전체 확신도 계산."""
        confidences: list[Confidence] = []

        for param in io.inputs:
            if param.type_ref:
                confidences.append(param.type_ref.confidence)
            else:
                confidences.append(Confidence.UNKNOWN)

        if io.output:
            confidences.append(io.output.confidence)
        else:
            confidences.append(Confidence.UNKNOWN)

        if not confidences:
            return Confidence.UNKNOWN

        # 가장 낮은 확신도 반환
        priority = {
            Confidence.UNKNOWN: 0,
            Confidence.LOW: 1,
            Confidence.MEDIUM: 2,
            Confidence.HIGH: 3,
        }

        min_conf = min(confidences, key=lambda c: priority[c])
        return min_conf

    def _ast_to_string(self, node: ast.expr | None) -> str:
        """AST 노드를 문자열로 변환."""
        if node is None:
            return ""
        try:
            return ast.unparse(node)
        except Exception:
            return "<unparseable>"
