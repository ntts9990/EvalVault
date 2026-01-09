"""Side effect detection for Python code.

파일 I/O, 데이터베이스, HTTP 요청, 환경변수, 로깅 등의
부작용을 정적 분석으로 탐지합니다.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field

from scripts.docs.models.schema import Confidence, SideEffect, SideEffectKind


@dataclass
class SideEffectPatterns:
    """부작용 탐지 패턴."""

    # 파일 읽기 패턴
    file_read_funcs: set[str] = field(
        default_factory=lambda: {
            "open",
            "read",
            "read_text",
            "read_bytes",
            "readlines",
            "readline",
            "load",
            "loads",  # json.load, pickle.load 등
        }
    )

    file_read_methods: set[str] = field(
        default_factory=lambda: {
            "read",
            "read_text",
            "read_bytes",
            "readlines",
            "readline",
        }
    )

    # 파일 쓰기 패턴
    file_write_funcs: set[str] = field(
        default_factory=lambda: {
            "write",
            "write_text",
            "write_bytes",
            "writelines",
            "dump",
            "dumps",
        }
    )

    file_write_methods: set[str] = field(
        default_factory=lambda: {
            "write",
            "write_text",
            "write_bytes",
            "writelines",
            "mkdir",
            "makedirs",
            "touch",
            "unlink",
            "remove",
            "rmdir",
        }
    )

    # 데이터베이스 패턴
    db_funcs: set[str] = field(
        default_factory=lambda: {
            "execute",
            "executemany",
            "commit",
            "rollback",
            "cursor",
            "connect",
            "create_engine",
        }
    )

    db_methods: set[str] = field(
        default_factory=lambda: {
            "execute",
            "executemany",
            "commit",
            "rollback",
            "fetchone",
            "fetchall",
            "fetchmany",
            "insert",
            "update",
            "delete",
            "query",
        }
    )

    # HTTP 요청 패턴
    http_funcs: set[str] = field(
        default_factory=lambda: {
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
            "request",
            "urlopen",
            "urlretrieve",
        }
    )

    http_methods: set[str] = field(
        default_factory=lambda: {
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
            "request",
            "send",
        }
    )

    http_modules: set[str] = field(
        default_factory=lambda: {
            "requests",
            "httpx",
            "aiohttp",
            "urllib",
            "http.client",
        }
    )

    # 환경변수 패턴
    env_funcs: set[str] = field(
        default_factory=lambda: {
            "getenv",
            "environ",
        }
    )

    # 로깅 패턴
    logging_funcs: set[str] = field(
        default_factory=lambda: {
            "debug",
            "info",
            "warning",
            "error",
            "critical",
            "exception",
            "log",
        }
    )

    # 서브프로세스 패턴
    subprocess_funcs: set[str] = field(
        default_factory=lambda: {
            "run",
            "call",
            "check_call",
            "check_output",
            "Popen",
            "system",
            "popen",
            "spawn",
        }
    )


class SideEffectDetector:
    """부작용 탐지기."""

    def __init__(self, patterns: SideEffectPatterns | None = None) -> None:
        self.patterns = patterns or SideEffectPatterns()

    def detect_in_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[SideEffect]:
        """함수 내 부작용 탐지.

        Args:
            node: 분석할 함수 AST 노드

        Returns:
            탐지된 부작용 목록
        """
        side_effects: list[SideEffect] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                effects = self._analyze_call(child)
                side_effects.extend(effects)
            elif isinstance(child, ast.With | ast.AsyncWith):
                effects = self._analyze_with(child)
                side_effects.extend(effects)

        # 중복 제거
        return self._deduplicate(side_effects)

    def detect_in_source(self, source: str) -> list[SideEffect]:
        """소스 코드 전체에서 부작용 탐지.

        Args:
            source: Python 소스 코드

        Returns:
            탐지된 부작용 목록
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []

        side_effects: list[SideEffect] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                effects = self._analyze_call(node)
                side_effects.extend(effects)

        return self._deduplicate(side_effects)

    def _analyze_call(self, node: ast.Call) -> list[SideEffect]:
        """함수 호출 분석."""
        effects: list[SideEffect] = []
        func_name = self._get_call_name(node)

        if not func_name:
            return effects

        # 파일 읽기
        if func_name in self.patterns.file_read_funcs:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.FILE_READ,
                    evidence=f"Call to {func_name}()",
                    confidence=Confidence.MEDIUM,
                )
            )

        # 파일 쓰기
        if func_name in self.patterns.file_write_funcs:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.FILE_WRITE,
                    evidence=f"Call to {func_name}()",
                    confidence=Confidence.MEDIUM,
                )
            )

        # 데이터베이스
        if func_name in self.patterns.db_funcs:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.DATABASE,
                    evidence=f"Call to {func_name}()",
                    confidence=Confidence.MEDIUM,
                )
            )

        # HTTP 요청
        if func_name in self.patterns.http_funcs:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.HTTP_REQUEST,
                    evidence=f"Call to {func_name}()",
                    confidence=Confidence.MEDIUM,
                )
            )

        # 환경변수
        if func_name in self.patterns.env_funcs:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.ENVIRONMENT,
                    evidence=f"Call to {func_name}()",
                    confidence=Confidence.HIGH,
                )
            )

        # 로깅
        if func_name in self.patterns.logging_funcs:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.LOGGING,
                    evidence=f"Call to {func_name}()",
                    confidence=Confidence.HIGH,
                )
            )

        # 서브프로세스
        if func_name in self.patterns.subprocess_funcs:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.SUBPROCESS,
                    evidence=f"Call to {func_name}()",
                    confidence=Confidence.HIGH,
                )
            )

        # 메서드 호출 분석
        if isinstance(node.func, ast.Attribute):
            method_effects = self._analyze_method_call(node)
            effects.extend(method_effects)

        return effects

    def _analyze_method_call(self, node: ast.Call) -> list[SideEffect]:
        """메서드 호출 분석."""
        effects: list[SideEffect] = []

        if not isinstance(node.func, ast.Attribute):
            return effects

        method_name = node.func.attr

        # 파일 읽기 메서드
        if method_name in self.patterns.file_read_methods:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.FILE_READ,
                    evidence=f"Method call .{method_name}()",
                    confidence=Confidence.MEDIUM,
                )
            )

        # 파일 쓰기 메서드
        if method_name in self.patterns.file_write_methods:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.FILE_WRITE,
                    evidence=f"Method call .{method_name}()",
                    confidence=Confidence.MEDIUM,
                )
            )

        # DB 메서드
        if method_name in self.patterns.db_methods:
            effects.append(
                SideEffect(
                    kind=SideEffectKind.DATABASE,
                    evidence=f"Method call .{method_name}()",
                    confidence=Confidence.MEDIUM,
                )
            )

        # HTTP 메서드
        if method_name in self.patterns.http_methods:
            # requests.get(), httpx.post() 등 확인
            receiver = self._get_receiver_name(node.func)
            if receiver in self.patterns.http_modules or method_name in {
                "get",
                "post",
                "put",
                "delete",
                "patch",
            }:
                effects.append(
                    SideEffect(
                        kind=SideEffectKind.HTTP_REQUEST,
                        evidence=f"Method call .{method_name}()",
                        confidence=Confidence.MEDIUM,
                    )
                )

        return effects

    def _analyze_with(self, node: ast.With | ast.AsyncWith) -> list[SideEffect]:
        """with 문 분석."""
        effects: list[SideEffect] = []

        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                call = item.context_expr
                func_name = self._get_call_name(call)

                if func_name == "open":
                    # open() 모드 분석
                    mode = self._get_open_mode(call)
                    if "r" in mode or mode == "":
                        effects.append(
                            SideEffect(
                                kind=SideEffectKind.FILE_READ,
                                evidence=f"open() with mode '{mode or 'r'}'",
                                confidence=Confidence.HIGH,
                            )
                        )
                    if "w" in mode or "a" in mode or "x" in mode:
                        effects.append(
                            SideEffect(
                                kind=SideEffectKind.FILE_WRITE,
                                evidence=f"open() with mode '{mode}'",
                                confidence=Confidence.HIGH,
                            )
                        )

        return effects

    def _get_call_name(self, node: ast.Call) -> str | None:
        """호출 함수 이름 추출."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _get_receiver_name(self, node: ast.Attribute) -> str | None:
        """메서드 수신자 이름 추출."""
        if isinstance(node.value, ast.Name):
            return node.value.id
        elif isinstance(node.value, ast.Attribute):
            return node.value.attr
        return None

    def _get_open_mode(self, call: ast.Call) -> str:
        """open() 호출에서 모드 추출."""
        # 위치 인자
        if len(call.args) >= 2:
            mode_arg = call.args[1]
            if isinstance(mode_arg, ast.Constant) and isinstance(mode_arg.value, str):
                return mode_arg.value

        # 키워드 인자
        for kw in call.keywords:
            if (
                kw.arg == "mode"
                and isinstance(kw.value, ast.Constant)
                and isinstance(kw.value.value, str)
            ):
                return kw.value.value

        return ""

    def _deduplicate(self, effects: list[SideEffect]) -> list[SideEffect]:
        """중복 제거."""
        seen: set[tuple[SideEffectKind, str]] = set()
        unique: list[SideEffect] = []

        for effect in effects:
            key = (effect.kind, effect.evidence)
            if key not in seen:
                seen.add(key)
                unique.append(effect)

        return unique
