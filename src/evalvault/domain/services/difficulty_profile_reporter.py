"""Difficulty profile reporter.

D-S3b rewiring
--------------
The legacy :class:`DifficultyProfileReporter` (a thin pass-through over the
:class:`DifficultyProfileWriterPort`) stays the canonical write path. This
module additionally exposes :class:`DifficultyProfileBuilder` and
:class:`DifficultyProfileRenderer` conforming to the ``ReportBuilder`` /
``Renderer`` Protocols so domain consumers can opt into the new contract.
The legacy ``write`` method is byte-identical (it delegates to the writer
port unchanged).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evalvault.domain.services.reporting import (
    MetricTable,
    ReportData,
    ReportSection,
)
from evalvault.ports.outbound.difficulty_profile_port import DifficultyProfileWriterPort


class DifficultyProfileReporter:
    def __init__(self, writer: DifficultyProfileWriterPort) -> None:
        self._writer = writer

    def write(
        self,
        *,
        output_path: Path,
        artifacts_dir: Path,
        envelope: dict[str, object],
        artifacts: dict[str, object],
    ) -> dict[str, object]:
        return self._writer.write_profile(
            output_path=output_path,
            artifacts_dir=artifacts_dir,
            envelope=envelope,
            artifacts=artifacts,
        )


# ---------------------------------------------------------------------------
# D-S3b: Builder / Renderer adapters
# ---------------------------------------------------------------------------


def _difficulty_envelope_to_report_data(
    envelope: dict[str, object],
    artifacts: dict[str, object],
) -> ReportData:
    """Project a difficulty profile envelope onto :class:`ReportData`."""

    metadata: dict[str, Any] = {
        "envelope": dict(envelope),
        "artifacts": dict(artifacts),
    }

    sections: list[ReportSection] = []
    summary = envelope.get("summary")
    if isinstance(summary, dict):
        sections.append(
            ReportSection(
                title="Difficulty Summary",
                body=", ".join(f"{k}={v}" for k, v in summary.items()),
                section_type="summary",
                metadata=summary,
            )
        )

    bucket_rows: list[tuple[Any, ...]] = []
    buckets = envelope.get("buckets")
    if isinstance(buckets, list):
        for entry in buckets:
            if isinstance(entry, dict):
                bucket_rows.append(
                    (
                        entry.get("name"),
                        entry.get("count"),
                        entry.get("pass_rate"),
                    )
                )

    tables = (
        MetricTable(
            name="difficulty_buckets",
            columns=("bucket", "count", "pass_rate"),
            rows=tuple(bucket_rows),
        ),
    )

    return ReportData(
        report_id=str(envelope.get("run_id", "")) or str(envelope.get("id", "")),
        title="Difficulty Profile",
        sections=tuple(sections),
        tables=tables,
        metadata=metadata,
    )


class DifficultyProfileBuilder:
    """:class:`ReportBuilder` adapter for difficulty profiles.

    Note: difficulty profile *writing* (file artifacts) remains the
    responsibility of :class:`DifficultyProfileReporter` and its
    :class:`DifficultyProfileWriterPort`. The builder is a pure
    in-memory projection for downstream renderers.
    """

    def build(self, *args: Any, **kwargs: Any) -> ReportData:
        envelope = kwargs.pop("envelope", None)
        artifacts = kwargs.pop("artifacts", None)
        if envelope is None or artifacts is None:
            if len(args) != 2:
                raise ValueError(
                    "DifficultyProfileBuilder.build requires envelope and artifacts"
                )
            envelope, artifacts = args
        return _difficulty_envelope_to_report_data(envelope, artifacts)


class DifficultyProfileRenderer:
    """:class:`Renderer` Protocol adapter for difficulty profiles."""

    def render(self, data: ReportData) -> str:
        lines: list[str] = [f"# {data.title}", ""]
        for section in data.sections:
            lines.extend([f"## {section.title}", section.body, ""])
        buckets = next(
            (t for t in data.tables if t.name == "difficulty_buckets"), None
        )
        if buckets and buckets.rows:
            lines.append("## Buckets")
            for bucket, count, pass_rate in buckets.rows:
                lines.append(f"- {bucket}: count={count} pass_rate={pass_rate}")
        return "\n".join(lines).strip()


__all__ = [
    "DifficultyProfileBuilder",
    "DifficultyProfileRenderer",
    "DifficultyProfileReporter",
]
