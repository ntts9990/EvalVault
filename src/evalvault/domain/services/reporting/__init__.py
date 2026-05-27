"""Reporting interfaces (D-S3a slice).

This module defines the *interface* layer shared by domain report services.
D-S3a only introduces new code; existing report service files (benchmark,
debug, difficulty_profile, experiment, ops, prompt_suggestion, run_comparison,
stage_summary, unified) are NOT touched here. The follow-up slice D-S3b will
realign those services onto the ``Builder`` / ``Renderer`` / ``Composer`` shape
defined below.

Design summary
--------------
The nine existing services already converge on a small set of output concepts:

* an identity (``run_id`` / ``report_id``),
* a human-readable title with overview metadata,
* zero or more *sections* (title + markdown body + classification),
* one or more *metric tables* (subject/metric/rank scores),
* optional narrative markdown blocks (LLM analysis text),
* optional status / verdict (e.g. ``ok`` vs ``degraded`` in
  :class:`RunComparisonOutcome`),
* a timestamp and a free-form metadata bag.

:class:`ReportData` captures that lowest common denominator as a *frozen*
dataclass so renderers and tests can rely on immutability. Renderers and
builders are expressed as :class:`typing.Protocol` so adapters can conform
structurally without inheriting from a base class.

Authority discipline
--------------------
Per the project T2 commitment (memory: ``project_decision_authority_t2``),
the optional :attr:`ReportData.status` field carries **T1/T2 authority only**
(reporting / Evaluation Gate). Reports MUST NOT emit T3
``promote`` / ``rollback`` verdicts; those belong to the regression gate
layer and live outside the reporting interface.

LLM prompt scope
----------------
Per the LLM prompt discipline memory (``feedback_llm_prompt_discipline``),
prompt-bearing reporters (notably ``prompt_suggestion_reporter``) are out of
scope for D-S3a. Aligning them onto these interfaces is deferred to D-S3b
with an explicit prompt review pass; nothing here changes existing prompt
strings.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "MetricTable",
    "ReportBuilder",
    "ReportComposer",
    "ReportData",
    "ReportSection",
    "Renderer",
]


@dataclass(frozen=True)
class ReportSection:
    """A single titled block of a report.

    Sections are the unit of narrative composition shared by every report
    today (BenchmarkReportSection, UnifiedReportSection, debug bottleneck
    blocks, etc.). ``body`` is markdown text; ``section_type`` is a free-form
    classification (``analysis``, ``comparison``, ``trend``, ``correlation``,
    ``unified``, ``recommendation``, ``summary``, ...).
    """

    title: str
    body: str
    section_type: str = "analysis"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricTable:
    """A structured tabular block (metric scores, subject results, rankings).

    Rows are stored as a tuple of tuples to preserve frozen semantics. Each
    row must match the length of ``columns``; renderers are not required to
    validate this — builders should produce well-formed tables.
    """

    name: str
    columns: tuple[str, ...]
    rows: tuple[tuple[Any, ...], ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReportData:
    """Lowest common denominator across the nine domain report services.

    Attributes
    ----------
    report_id:
        Identifier of the underlying domain object (run id, report id,
        composite id like ``unified-<a>-<b>``, etc.).
    title:
        Human-readable header line. Renderers typically lift this into an
        H1 or a document title.
    sections:
        Ordered narrative blocks. May be empty for purely tabular reports
        (e.g. minimal stage summaries).
    tables:
        Structured tabular data. Defaults to ``()`` for reports that are
        prose-only.
    narratives:
        Named markdown blobs separate from ``sections``. Useful for
        decoupling LLM-generated analysis text from human-curated section
        layout, or for renderers that want to address specific bodies of
        text by key (e.g. ``executive_summary``, ``root_cause_analysis``).
    status:
        Optional verdict string. **T1/T2 authority only** — do not emit T3
        ``promote`` / ``rollback`` here. Typical values: ``ok``,
        ``degraded``, ``warning``, ``critical``.
    metadata:
        Free-form metadata bag (run ids, trace urls, dataset names, etc.).
    generated_at:
        UTC timestamp; defaults to the moment the dataclass is constructed.
    """

    report_id: str
    title: str
    sections: tuple[ReportSection, ...] = ()
    tables: tuple[MetricTable, ...] = ()
    narratives: Mapping[str, str] = field(default_factory=dict)
    # T1/T2 authority only. Reports must not emit T3 promote/rollback.
    status: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@runtime_checkable
class Renderer(Protocol):
    """Render a :class:`ReportData` to a target output format.

    Implementations are typically per-format (markdown, html, json sidecar,
    xlsx). Renderers must be pure functions of ``ReportData`` — any I/O
    (writing to disk, posting to a sink) is the caller's responsibility.
    """

    def render(self, data: ReportData) -> str:
        """Return the rendered representation as a string."""
        ...


@runtime_checkable
class ReportBuilder(Protocol):
    """Build a :class:`ReportData` from a domain input.

    Concrete builders take the inputs their corresponding service requires
    today (a run id and storages, a pair of runs, an experiment, ...) and
    return a fully-populated :class:`ReportData`. The :class:`ReportBuilder`
    contract is intentionally permissive about ``*args`` / ``**kwargs`` so
    that the nine existing services — which all take different shapes —
    can each conform without forcing a single signature.
    """

    def build(self, *args: Any, **kwargs: Any) -> ReportData:
        """Construct and return a :class:`ReportData`."""
        ...


@dataclass(frozen=True)
class ReportComposer:
    """Combine a :class:`ReportBuilder` with a :class:`Renderer`.

    A :class:`ReportComposer` is the single entry point for callers that
    just want "build the report and render it." It is what D-S3b will plug
    into ``UnifiedReport``-style consumers so each consumer can swap
    renderers (markdown / json / html) without re-wiring builders.
    """

    builder: ReportBuilder
    renderer: Renderer

    def compose(self, *args: Any, **kwargs: Any) -> str:
        """Build the report and return the rendered string.

        Positional and keyword arguments are forwarded verbatim to
        :meth:`ReportBuilder.build`.
        """
        data = self.builder.build(*args, **kwargs)
        return self.renderer.render(data)

    def emit(self, *args: Any, **kwargs: Any) -> tuple[ReportData, str]:
        """Build the report and return both the data and the rendered string.

        Useful when the caller needs to persist the structured
        :class:`ReportData` (e.g. to storage) *and* a rendered artifact
        (e.g. to disk) without invoking the builder twice.
        """
        data = self.builder.build(*args, **kwargs)
        return data, self.renderer.render(data)
