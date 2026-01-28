#!/usr/bin/env python3
"""Validate Open RAG Trace payloads against the minimal spec.

Supported input:
- JSON list of spans
- JSON object with "spans"
- OTLP JSON with "resourceSpans" (subset parsing)
- JSONL where each line is any of the above
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_SPEC_VERSION = "0.1"

ALLOWED_MODULES = {
    "ingest",
    "chunk",
    "embed",
    "retrieve",
    "rerank",
    "prompt",
    "llm",
    "postprocess",
    "eval",
    "cache",
}


@dataclass
class ModuleStats:
    """Stats for rag.module attribute across spans."""

    missing_count: int = 0
    standard_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    nonstandard_counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def record(self, module: str | None) -> None:
        if not module:
            self.missing_count += 1
        elif module in ALLOWED_MODULES or str(module).startswith("custom."):
            self.standard_counts[module] += 1
        else:
            self.nonstandard_counts[module] += 1

    @property
    def total_standard(self) -> int:
        return sum(self.standard_counts.values())

    @property
    def total_nonstandard(self) -> int:
        return sum(self.nonstandard_counts.values())


def _coerce_otlp_value(value: dict[str, Any]) -> Any:
    if "stringValue" in value:
        return value["stringValue"]
    if "intValue" in value:
        return int(value["intValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    if "boolValue" in value:
        return bool(value["boolValue"])
    if "arrayValue" in value:
        values = value["arrayValue"].get("values", [])
        return [_coerce_otlp_value(item) for item in values]
    if "kvlistValue" in value:
        pairs = value["kvlistValue"].get("values", [])
        return {item.get("key"): _coerce_otlp_value(item.get("value", {})) for item in pairs}
    return value


def _parse_otlp_attributes(attrs: list[dict[str, Any]]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in attrs or []:
        key = item.get("key")
        if not key:
            continue
        parsed[key] = _coerce_otlp_value(item.get("value", {}))
    return parsed


def _extract_spans_from_otlp(payload: dict[str, Any]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    for resource_span in payload.get("resourceSpans", []) or []:
        for scope_span in resource_span.get("scopeSpans", []) or []:
            for span in scope_span.get("spans", []) or []:
                attributes = _parse_otlp_attributes(span.get("attributes", []))
                spans.append(
                    {
                        "trace_id": span.get("traceId") or span.get("trace_id"),
                        "span_id": span.get("spanId") or span.get("span_id"),
                        "parent_span_id": span.get("parentSpanId") or span.get("parent_span_id"),
                        "name": span.get("name"),
                        "start_time": span.get("startTimeUnixNano") or span.get("start_time"),
                        "end_time": span.get("endTimeUnixNano") or span.get("end_time"),
                        "attributes": attributes,
                    }
                )
    return spans


def _extract_spans(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        if "resourceSpans" in payload:
            return _extract_spans_from_otlp(payload)
        if "spans" in payload and isinstance(payload["spans"], list):
            return [item for item in payload["spans"] if isinstance(item, dict)]
        return [payload]
    return []


def _load_payload(path: Path) -> list[Any]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in raw.splitlines() if line.strip()]
    return [json.loads(raw)]


def _validate_span(span: dict[str, Any], require_spec_version: bool) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    warnings: list[str] = []
    attributes = span.get("attributes") or {}

    for key in ("trace_id", "span_id", "name", "start_time", "end_time"):
        if not span.get(key):
            missing.append(key)

    module = attributes.get("rag.module")
    if not module:
        missing.append("attributes.rag.module")
    elif not (module in ALLOWED_MODULES or str(module).startswith("custom.")):
        warnings.append(f"unknown rag.module '{module}'")

    spec_version = attributes.get("spec.version")
    if not spec_version:
        if require_spec_version:
            missing.append("attributes.spec.version")
        else:
            warnings.append("missing attributes.spec.version")

    return missing, warnings


def _summarize(
    issues: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    total: int,
    module_stats: ModuleStats | None = None,
    filled_spec_version: int = 0,
) -> str:
    lines = [
        f"총 span: {total}",
        f"필수 누락: {len(issues)}",
        f"경고: {len(warnings)}",
    ]
    if filled_spec_version > 0:
        lines.append(f"spec.version 자동 채움: {filled_spec_version}")
    if module_stats:
        lines.append("")
        lines.append("[rag.module 통계]")
        lines.append(f"  표준 모듈: {module_stats.total_standard}")
        lines.append(f"  비표준 모듈: {module_stats.total_nonstandard}")
        lines.append(f"  누락: {module_stats.missing_count}")
        if module_stats.nonstandard_counts:
            nonstandard_list = ", ".join(
                f"{k}({v})" for k, v in sorted(module_stats.nonstandard_counts.items())
            )
            lines.append(f"  비표준 상세: {nonstandard_list}")
            lines.append("  권장: 표준 모듈 사용 또는 custom.<name> 형식으로 정규화")
        if module_stats.missing_count:
            lines.append("  권장: attributes.rag.module 필수 입력")
    return "\n".join(lines)


def _fill_spec_version(spans: list[dict[str, Any]], version: str) -> int:
    filled_count = 0
    for span in spans:
        attributes = span.get("attributes")
        if attributes is None:
            span["attributes"] = {"spec.version": version}
            filled_count += 1
        elif not attributes.get("spec.version"):
            attributes["spec.version"] = version
            filled_count += 1
    return filled_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Open RAG Trace payloads.")
    parser.add_argument("--input", required=True, help="Path to JSON/JSONL file")
    parser.add_argument(
        "--require-spec-version",
        action="store_true",
        help="Fail if attributes.spec.version is missing",
    )
    parser.add_argument(
        "--fill-spec-version",
        nargs="?",
        const=DEFAULT_SPEC_VERSION,
        metavar="VERSION",
        help=f"Auto-fill missing spec.version before validation (default: {DEFAULT_SPEC_VERSION})",
    )
    parser.add_argument(
        "--max-report",
        type=int,
        default=20,
        help="Max issues to print per category",
    )
    parser.add_argument(
        "--module-stats",
        action="store_true",
        help="Report rag.module missing/nonstandard statistics",
    )
    args = parser.parse_args()

    payloads = _load_payload(Path(args.input))
    spans: list[dict[str, Any]] = []
    for payload in payloads:
        spans.extend(_extract_spans(payload))

    if not spans:
        print("유효한 span을 찾지 못했습니다.", file=sys.stderr)
        return 2

    filled_count = 0
    if args.fill_spec_version:
        filled_count = _fill_spec_version(spans, args.fill_spec_version)

    module_stats = ModuleStats() if args.module_stats else None
    missing_issues: list[dict[str, Any]] = []
    warning_issues: list[dict[str, Any]] = []
    for index, span in enumerate(spans):
        missing, warnings = _validate_span(span, args.require_spec_version)
        if missing:
            missing_issues.append({"index": index, "missing": missing, "name": span.get("name")})
        if warnings:
            warning_issues.append({"index": index, "warnings": warnings, "name": span.get("name")})
        if module_stats:
            attributes = span.get("attributes") or {}
            module_stats.record(attributes.get("rag.module"))

    print(
        _summarize(
            missing_issues,
            warning_issues,
            len(spans),
            module_stats=module_stats,
            filled_spec_version=filled_count,
        )
    )

    for issue in missing_issues[: args.max_report]:
        print(f"[누락] #{issue['index']} {issue.get('name')}: {', '.join(issue['missing'])}")

    for issue in warning_issues[: args.max_report]:
        print(f"[경고] #{issue['index']} {issue.get('name')}: {', '.join(issue['warnings'])}")

    return 1 if missing_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
