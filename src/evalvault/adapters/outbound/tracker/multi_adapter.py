"""Composite tracker adapter that dispatches to several backends.

Historically the CLI (``run_helpers._log_to_trackers`` /
``_log_analysis_artifacts``) and the FastAPI inbound adapter
(``api.adapter._run_evaluation`` finalization block) each open-coded
their own "log to MLflow then to Phoenix (and maybe Langfuse)" loop. The
two open-coded loops drifted: only one of them captured per-provider
trace IDs cleanly, only one of them handled Phoenix-specific metadata,
and a single backend hiccup could leave the other backends without any
trace at all because the loop bubbled the exception out.

``MultiTrackerAdapter`` collapses both call sites onto one composition
primitive that:

* Holds an ordered ``[(provider_name, tracker_adapter)]`` list.
* Reuses :meth:`BaseTrackerAdapter.safe_emit` so a transient backend
  failure on one tracker does not block the remaining trackers.
* Maintains a ``parent trace_id -> {provider: per-tracker trace_id}``
  table so callers can drive ``start_trace`` / ``save_artifact`` /
  ``end_trace`` lifecycles through a single handle.
* Exposes :attr:`last_trace_ids` after :meth:`log_evaluation_run` so
  callers can fan provider-specific metadata (Phoenix trace URL,
  Langfuse trace ID, etc.) back into ``run.tracker_metadata`` without
  reaching for the underlying adapters.

Notes
-----

* The adapter is a *diagnostic* trace sink only (T0 authority). It does
  not infer verdicts, promote/rollback decisions, or any
  evaluation-gate semantics -- those belong to a separate decision
  surface (see ``project_decision_authority_t2`` memory).
* ``safe_emit`` propagates ``ValueError`` per the base error policy, so
  unknown ``trace_id`` lookups still surface as caller-side bugs.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from evalvault.adapters.outbound.tracker.base import BaseTrackerAdapter
from evalvault.domain.entities import EvaluationRun
from evalvault.ports.outbound.tracker_port import TrackerPort


class MultiTrackerAdapter(BaseTrackerAdapter, TrackerPort):
    """Fan a single TrackerPort call out to multiple backend adapters.

    Each backend is recorded as a ``(provider_name, tracker)`` pair so
    that:

    * Diagnostic log lines emitted by :meth:`BaseTrackerAdapter.safe_emit`
      include the provider, making "Phoenix is down, MLflow is fine"
      observable in the worker logs.
    * Callers can read :attr:`last_trace_ids` after a successful
      :meth:`log_evaluation_run` to obtain per-provider trace IDs and
      keep writing provider-specific metadata (e.g. Phoenix trace URL)
      into ``EvaluationRun.tracker_metadata``.

    Example::

        multi = MultiTrackerAdapter([
            ("mlflow", MLflowAdapter(...)),
            ("phoenix", PhoenixAdapter(...)),
        ])
        multi.log_evaluation_run(run)
        for provider, trace_id in multi.last_trace_ids.items():
            run.tracker_metadata.setdefault(provider, {})["trace_id"] = trace_id
    """

    # Human-readable label used in ValueError messages produced by
    # ``_require_trace``. Composition trace ids are minted locally and
    # do not map onto a single backend, so the label is generic.
    _lookup_label = "MultiTrace"

    def __init__(self, trackers: Sequence[tuple[str, Any]]):
        """Create a composite over ``trackers``.

        Args:
            trackers: ordered ``[(provider_name, tracker_adapter)]``
                pairs. The order is preserved when fanning out calls,
                which keeps logged events deterministic across runs.

        Raises:
            ValueError: when ``trackers`` is empty. A composite over
                zero trackers is almost certainly a wiring bug at the
                call site; surfacing it loudly is preferable to
                silently dropping evaluation traces.
        """
        if not trackers:
            raise ValueError("MultiTrackerAdapter requires at least one tracker")
        self._trackers: list[tuple[str, Any]] = list(trackers)
        # parent trace_id -> {provider name: per-tracker trace_id}
        self._active_traces: dict[str, dict[str, str]] = {}
        # Per-provider trace IDs from the most recent log_evaluation_run.
        # Callers read this to attach Phoenix URLs / Langfuse IDs back
        # into EvaluationRun.tracker_metadata.
        self.last_trace_ids: dict[str, str] = {}

    @property
    def trackers(self) -> list[tuple[str, Any]]:
        """Return a defensive copy of the wrapped ``(name, tracker)`` pairs."""
        return list(self._trackers)

    def get_tracker(self, name: str) -> Any | None:
        """Return the underlying adapter registered under ``name`` (or ``None``).

        Call sites that need to invoke a tracker-specific extension --
        e.g. Phoenix's ``log_rag_trace`` for per-test-case observability
        -- use this hook instead of pattern-matching on the public
        :attr:`trackers` list.
        """
        for provider, tracker in self._trackers:
            if provider == name:
                return tracker
        return None

    def per_tracker_trace_ids(self, trace_id: str) -> dict[str, str]:
        """Resolve ``trace_id`` to its per-backend child trace IDs.

        Useful for analysis-style flows that open a trace, write a few
        artifacts, then need to report each backend's trace ID
        individually to the console.

        Raises:
            ValueError: if ``trace_id`` is not currently open.
        """
        return dict(self._require_trace(self._active_traces, trace_id))

    def start_trace(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """Open a parent trace and fan it out to each tracker.

        Returns:
            A locally-minted parent trace ID. The mapping to per-tracker
            child IDs is kept internally and used by :meth:`add_span`,
            :meth:`log_score`, :meth:`save_artifact`, and
            :meth:`end_trace`.
        """
        parent_id = uuid.uuid4().hex
        per_tracker: dict[str, str] = {}
        for provider, tracker in self._trackers:
            child_id = self.safe_emit(
                f"start_trace[{provider}]",
                tracker.start_trace,
                name,
                metadata,
                default=None,
            )
            if child_id is not None:
                per_tracker[provider] = child_id
        self._active_traces[parent_id] = per_tracker
        return parent_id

    def add_span(
        self,
        trace_id: str,
        name: str,
        input_data: Any | None = None,
        output_data: Any | None = None,
    ) -> None:
        """Fan ``add_span`` out across every tracker that opened a child trace."""
        per_tracker = self._require_trace(self._active_traces, trace_id)
        for provider, tracker in self._trackers:
            child_id = per_tracker.get(provider)
            if child_id is None:
                continue
            self.safe_emit(
                f"add_span[{provider}]",
                tracker.add_span,
                child_id,
                name,
                input_data,
                output_data,
                default=None,
            )

    def log_score(
        self,
        trace_id: str,
        name: str,
        value: float,
        comment: str | None = None,
    ) -> None:
        """Fan ``log_score`` out across every tracker that opened a child trace."""
        per_tracker = self._require_trace(self._active_traces, trace_id)
        for provider, tracker in self._trackers:
            child_id = per_tracker.get(provider)
            if child_id is None:
                continue
            self.safe_emit(
                f"log_score[{provider}]",
                tracker.log_score,
                child_id,
                name,
                value,
                comment,
                default=None,
            )

    def save_artifact(
        self,
        trace_id: str,
        name: str,
        data: Any,
        artifact_type: str = "json",
    ) -> None:
        """Fan ``save_artifact`` out across every tracker with an open child trace."""
        per_tracker = self._require_trace(self._active_traces, trace_id)
        for provider, tracker in self._trackers:
            child_id = per_tracker.get(provider)
            if child_id is None:
                continue
            self.safe_emit(
                f"save_artifact[{provider}]",
                tracker.save_artifact,
                child_id,
                name,
                data,
                artifact_type,
                default=None,
            )

    def end_trace(self, trace_id: str) -> None:
        """Close every per-tracker child trace and drop the parent mapping."""
        per_tracker = self._require_trace(self._active_traces, trace_id)
        for provider, tracker in self._trackers:
            child_id = per_tracker.get(provider)
            if child_id is None:
                continue
            self.safe_emit(
                f"end_trace[{provider}]",
                tracker.end_trace,
                child_id,
                default=None,
            )
        del self._active_traces[trace_id]

    def log_evaluation_run(self, run: EvaluationRun) -> str:
        """Log a full evaluation run to every tracker.

        Each backend's call is wrapped with :meth:`safe_emit`, so a
        Phoenix outage no longer prevents MLflow from recording the run
        (or vice versa). Per-provider trace IDs are stashed in
        :attr:`last_trace_ids` for the caller.

        Returns:
            The first non-``None`` trace ID, mainly to keep the
            ``TrackerPort.log_evaluation_run`` contract. Callers should
            prefer :attr:`last_trace_ids` for routing metadata to the
            right provider key.
        """
        per_tracker: dict[str, str] = {}
        for provider, tracker in self._trackers:
            trace_id = self.safe_emit(
                f"log_evaluation_run[{provider}]",
                tracker.log_evaluation_run,
                run,
                default=None,
            )
            if trace_id is not None:
                per_tracker[provider] = trace_id
        self.last_trace_ids = per_tracker
        # TrackerPort.log_evaluation_run returns ``str``. Empty string
        # signals "every backend failed" to callers that only look at
        # the return value (keeping the contract; the detailed
        # per-provider view is on ``last_trace_ids``).
        return next(iter(per_tracker.values()), "")
