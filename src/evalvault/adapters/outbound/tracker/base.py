"""Base class and unified error policy for tracker adapters.

EvalVault writes evaluation traces to several backends (MLflow, Phoenix,
Langfuse). Historically each adapter raised its own error vocabulary,
which made dual-logging compositions brittle: a network glitch in one
backend could crash the whole logging pipeline before other trackers got
a chance to log.

This module codifies a single error policy that every concrete adapter
follows, and provides ``safe_emit`` so composition layers (for example
``cli/commands/run_helpers.py`` or ``api/adapter.py``) can call a tracker
without a single backend taking down the rest.

Error policy
------------

Recoverable / caller-side errors -- **always propagate**:
    ``ValueError``
        Raised when the *caller* violates the adapter contract, e.g. by
        passing a ``trace_id`` that was never started (or was already
        ended). These signal bugs in the orchestrator and must surface so
        they can be fixed; ``safe_emit`` deliberately re-raises them.

Non-recoverable / tracker-internal errors -- **swallowed by safe_emit**:
    ``RuntimeError``
        Raised when the tracker itself cannot proceed: initialization
        failure, missing API surface on the SDK, network exhaustion, etc.
        These are environmental and the caller cannot fix them at the
        call site, so dual-logging composition should keep going with the
        remaining trackers.
    Any other ``Exception`` raised by the underlying SDK (httpx, otel,
    mlflow, langfuse). Treated the same as ``RuntimeError`` for
    open-circuit purposes.

The split matches the existing behaviour of the three adapters: they all
already raise ``ValueError`` on unknown ``trace_id`` lookups, and Phoenix
raises ``RuntimeError`` for tracer initialisation failures. This module
makes that contract explicit and uniformly enforceable.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

R = TypeVar("R")


class BaseTrackerAdapter:
    """Common base for tracker adapters.

    Concrete adapters still conform to :class:`evalvault.ports.outbound.
    tracker_port.TrackerPort` structurally; inheriting from this base is
    additive and only provides shared helpers:

    - :meth:`_require_trace` -- look up an active trace handle and raise
      a consistent ``ValueError`` if the caller passed an unknown id.
    - :meth:`safe_emit` -- run a tracker call so that backend-internal
      failures do not break peer trackers in a dual-logging composition.

    Subclasses with a different lookup vocabulary (MLflow speaks "Run"
    rather than "Trace") override :attr:`_lookup_label`.
    """

    #: Human-readable label used in the ``ValueError`` message produced
    #: by :meth:`_require_trace`. Override per adapter; default matches
    #: the OpenTelemetry / Langfuse vocabulary.
    _lookup_label: str = "Trace"

    def _require_trace(self, active: dict[str, Any], trace_id: str) -> Any:
        """Resolve ``trace_id`` against an active-trace mapping.

        Args:
            active: ``{trace_id: backend_handle}`` mapping owned by the
                adapter (e.g. ``self._active_runs`` for MLflow,
                ``self._active_spans`` for Phoenix, ``self._traces`` for
                Langfuse).
            trace_id: identifier supplied by the caller.

        Returns:
            The backend handle stored under ``trace_id``.

        Raises:
            ValueError: if ``trace_id`` is not present in ``active``.
                The message is ``"{label} not found: {trace_id}"`` and is
                considered part of the adapter's public contract (tests
                match on it).
        """
        if trace_id not in active:
            raise ValueError(f"{self._lookup_label} not found: {trace_id}")
        return active[trace_id]

    def safe_emit(
        self,
        op: str,
        func: Callable[..., R],
        *args: Any,
        default: R | None = None,
        **kwargs: Any,
    ) -> R | None:
        """Open-circuit wrapper around a tracker call.

        Caller-side ``ValueError`` propagates (per the error policy in
        the module docstring). Every other exception is logged at
        ``WARNING`` and ``default`` is returned, so a composing
        dual-logger can fall through to the next tracker.

        Args:
            op: short label for the operation, used in the log message
                (e.g. ``"log_evaluation_run"``).
            func: callable to execute -- typically a bound method on the
                adapter itself.
            *args: positional arguments forwarded to ``func``.
            default: value returned when ``func`` raises a
                tracker-internal error.
            **kwargs: keyword arguments forwarded to ``func``.

        Returns:
            Whatever ``func`` returns, or ``default`` on
            tracker-internal failure.
        """
        try:
            return func(*args, **kwargs)
        except ValueError:
            # Caller-side bug; must surface so it can be fixed upstream.
            raise
        except Exception as exc:
            logger.warning(
                "tracker.%s: %s failed (%s); continuing",
                type(self).__name__,
                op,
                exc,
            )
            return default
