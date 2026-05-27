"""Unit tests for the D-S3a reporting interface module.

These tests cover the interface contracts only. The follow-up slice D-S3b
will rewire the nine concrete report services onto these interfaces and
add per-service tests; here we just lock down the shape of
``ReportData``, ``Renderer``, ``ReportBuilder``, and ``ReportComposer``.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime
from typing import Any

import pytest

from evalvault.domain.services.reporting import (
    MetricTable,
    Renderer,
    ReportBuilder,
    ReportComposer,
    ReportData,
    ReportSection,
)

# ---------------------------------------------------------------------------
# ReportData / ReportSection / MetricTable: immutability
# ---------------------------------------------------------------------------


def _make_report() -> ReportData:
    return ReportData(
        report_id="run-001",
        title="Sample report",
        sections=(ReportSection(title="Summary", body="hello", section_type="summary"),),
        tables=(
            MetricTable(
                name="metrics",
                columns=("metric", "score"),
                rows=(("faithfulness", 0.82),),
            ),
        ),
        narratives={"executive_summary": "all clear"},
        status="ok",
        metadata={"dataset": "demo"},
    )


def test_report_data_is_frozen_dataclass() -> None:
    assert is_dataclass(ReportData)
    report = _make_report()
    with pytest.raises(FrozenInstanceError):
        report.report_id = "tampered"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.title = "tampered"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "degraded"  # type: ignore[misc]


def test_report_section_and_metric_table_are_frozen() -> None:
    section = ReportSection(title="t", body="b")
    with pytest.raises(FrozenInstanceError):
        section.title = "x"  # type: ignore[misc]

    table = MetricTable(name="m", columns=("a",), rows=(("v",),))
    with pytest.raises(FrozenInstanceError):
        table.name = "n"  # type: ignore[misc]


def test_report_data_defaults_are_sane() -> None:
    report = ReportData(report_id="r1", title="T")
    assert report.sections == ()
    assert report.tables == ()
    assert report.narratives == {}
    assert report.status is None
    assert report.metadata == {}
    assert isinstance(report.generated_at, datetime)


def test_report_data_field_set_is_stable() -> None:
    # Guard against accidental schema drift in later slices: D-S3b should
    # not silently rename or drop one of these fields.
    expected = {
        "report_id",
        "title",
        "sections",
        "tables",
        "narratives",
        "status",
        "metadata",
        "generated_at",
    }
    assert {f.name for f in fields(ReportData)} == expected


# ---------------------------------------------------------------------------
# Renderer Protocol: structural conformance
# ---------------------------------------------------------------------------


class _GoodRenderer:
    def render(self, data: ReportData) -> str:
        return f"# {data.title}\n\nid={data.report_id}"


class _BadRenderer:
    def write(self, data: ReportData, path: str) -> None:  # wrong shape
        return None


def test_renderer_protocol_accepts_conforming_object() -> None:
    assert isinstance(_GoodRenderer(), Renderer)


def test_renderer_protocol_rejects_malformed_object() -> None:
    assert not isinstance(_BadRenderer(), Renderer)
    # A bare object with no render method must not pass either.
    assert not isinstance(object(), Renderer)


# ---------------------------------------------------------------------------
# ReportBuilder Protocol: structural conformance
# ---------------------------------------------------------------------------


class _GoodBuilder:
    def __init__(self, report: ReportData) -> None:
        self._report = report

    def build(self, *args: Any, **kwargs: Any) -> ReportData:
        return self._report


class _BadBuilder:
    def construct(self) -> ReportData:  # wrong method name
        raise NotImplementedError


def test_report_builder_protocol_accepts_conforming_object() -> None:
    builder = _GoodBuilder(_make_report())
    assert isinstance(builder, ReportBuilder)


def test_report_builder_protocol_rejects_malformed_object() -> None:
    assert not isinstance(_BadBuilder(), ReportBuilder)
    assert not isinstance(object(), ReportBuilder)


# ---------------------------------------------------------------------------
# ReportComposer: combines builder + renderer
# ---------------------------------------------------------------------------


class _RecordingBuilder:
    """Builder that records the args/kwargs it received."""

    def __init__(self, report: ReportData) -> None:
        self._report = report
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def build(self, *args: Any, **kwargs: Any) -> ReportData:
        self.calls.append((args, kwargs))
        return self._report


class _RecordingRenderer:
    """Renderer that records every ReportData passed to it."""

    def __init__(self) -> None:
        self.seen: list[ReportData] = []

    def render(self, data: ReportData) -> str:
        self.seen.append(data)
        return f"<rendered:{data.report_id}>"


def test_report_composer_compose_forwards_args_and_returns_rendered_string() -> None:
    report = _make_report()
    builder = _RecordingBuilder(report)
    renderer = _RecordingRenderer()
    composer = ReportComposer(builder=builder, renderer=renderer)

    output = composer.compose("run-001", metrics=("faithfulness",))

    assert output == "<rendered:run-001>"
    assert builder.calls == [(("run-001",), {"metrics": ("faithfulness",)})]
    assert renderer.seen == [report]


def test_report_composer_emit_returns_data_and_rendered_string() -> None:
    report = _make_report()
    builder = _RecordingBuilder(report)
    renderer = _RecordingRenderer()
    composer = ReportComposer(builder=builder, renderer=renderer)

    data, rendered = composer.emit()

    assert data is report
    assert rendered == "<rendered:run-001>"
    # emit must invoke the builder exactly once (no double-build).
    assert len(builder.calls) == 1
    assert renderer.seen == [report]


def test_report_composer_is_frozen() -> None:
    composer = ReportComposer(builder=_GoodBuilder(_make_report()), renderer=_GoodRenderer())
    with pytest.raises(FrozenInstanceError):
        composer.builder = _GoodBuilder(_make_report())  # type: ignore[misc]
