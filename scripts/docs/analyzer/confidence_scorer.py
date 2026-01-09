"""Confidence scoring for type information.

타입 정보의 확신도를 계산합니다.
- HIGH: 명시적 타입힌트
- MEDIUM: docstring 또는 기본값에서 추론
- LOW: 휴리스틱 추정
- UNKNOWN: 정보 없음
"""

from __future__ import annotations

from scripts.docs.models.schema import (
    Confidence,
    FunctionSymbol,
    IOSpec,
    ModuleInfo,
)


class ConfidenceScorer:
    """확신도 계산기."""

    def score_module(self, module: ModuleInfo) -> dict[str, float]:
        """모듈 전체의 확신도 통계 계산.

        Args:
            module: 분석할 모듈

        Returns:
            확신도 통계 딕셔너리
        """
        all_confidences: list[Confidence] = []

        for func in module.functions:
            all_confidences.extend(self._collect_io_confidences(func.io))

        for cls in module.classes:
            for method in cls.methods:
                all_confidences.extend(self._collect_io_confidences(method.io))
            # 클래스 변수의 타입 확신도
            for type_ref in cls.class_variables.values():
                all_confidences.append(type_ref.confidence)
            for type_ref in cls.instance_variables.values():
                all_confidences.append(type_ref.confidence)

        return self._calculate_statistics(all_confidences)

    def score_function(self, func: FunctionSymbol) -> Confidence:
        """함수의 전체 확신도 계산.

        Args:
            func: 분석할 함수

        Returns:
            전체 확신도
        """
        return self._calculate_overall_confidence(func.io)

    def score_io(self, io: IOSpec) -> Confidence:
        """IO 명세의 전체 확신도 계산.

        Args:
            io: 분석할 IO 명세

        Returns:
            전체 확신도
        """
        return self._calculate_overall_confidence(io)

    def enhance_io_confidence(self, io: IOSpec, docstring: str = "") -> IOSpec:
        """IO 명세의 확신도 향상.

        docstring이나 다른 소스에서 추가 정보를 추출하여
        확신도를 향상시킵니다.

        Args:
            io: 향상시킬 IO 명세
            docstring: 참조할 docstring

        Returns:
            향상된 IO 명세
        """
        # docstring에서 타입 정보 추출
        if docstring:
            self._enhance_from_docstring(io, docstring)

        # 전체 확신도 재계산
        io.overall_confidence = self._calculate_overall_confidence(io)

        return io

    def _collect_io_confidences(self, io: IOSpec) -> list[Confidence]:
        """IO 명세에서 모든 확신도 수집."""
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

        return confidences

    def _calculate_overall_confidence(self, io: IOSpec) -> Confidence:
        """전체 확신도 계산.

        가장 낮은 확신도를 반환합니다.
        """
        confidences = self._collect_io_confidences(io)

        if not confidences:
            return Confidence.UNKNOWN

        priority = {
            Confidence.UNKNOWN: 0,
            Confidence.LOW: 1,
            Confidence.MEDIUM: 2,
            Confidence.HIGH: 3,
        }

        return min(confidences, key=lambda c: priority[c])

    def _calculate_statistics(self, confidences: list[Confidence]) -> dict[str, float]:
        """확신도 통계 계산."""
        if not confidences:
            return {
                "total": 0,
                "high_ratio": 0.0,
                "medium_ratio": 0.0,
                "low_ratio": 0.0,
                "unknown_ratio": 0.0,
            }

        total = len(confidences)
        counts = {
            Confidence.HIGH: 0,
            Confidence.MEDIUM: 0,
            Confidence.LOW: 0,
            Confidence.UNKNOWN: 0,
        }

        for c in confidences:
            counts[c] += 1

        return {
            "total": total,
            "high_ratio": counts[Confidence.HIGH] / total,
            "medium_ratio": counts[Confidence.MEDIUM] / total,
            "low_ratio": counts[Confidence.LOW] / total,
            "unknown_ratio": counts[Confidence.UNKNOWN] / total,
            "high_count": counts[Confidence.HIGH],
            "medium_count": counts[Confidence.MEDIUM],
            "low_count": counts[Confidence.LOW],
            "unknown_count": counts[Confidence.UNKNOWN],
        }

    def _enhance_from_docstring(self, io: IOSpec, docstring: str) -> None:
        """docstring에서 타입 정보 추출하여 확신도 향상."""
        import re

        # Args 섹션 파싱
        args_pattern = r"Args?:\s*\n((?:\s+\w+.*\n?)+)"
        args_match = re.search(args_pattern, docstring, re.MULTILINE)

        if args_match:
            args_section = args_match.group(1)
            # 각 인자 파싱: name (type): description 또는 name: description
            param_pattern = r"(\w+)\s*(?:\(([^)]+)\))?\s*:\s*(.*)"

            for param in io.inputs:
                for match in re.finditer(param_pattern, args_section):
                    if match.group(1) == param.name:
                        type_hint = match.group(2)
                        if (
                            type_hint
                            and param.type_ref
                            and param.type_ref.confidence == Confidence.UNKNOWN
                        ):
                            # docstring에서 타입 정보를 찾았으면 확신도 향상
                            param.type_ref.confidence = Confidence.MEDIUM
                        param.description = match.group(3).strip()
