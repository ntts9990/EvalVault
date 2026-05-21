"""Tracker adapters for logging evaluation traces.

All concrete adapters share the error policy and helpers defined in
:mod:`evalvault.adapters.outbound.tracker.base`. See that module for the
recoverable vs non-recoverable error contract.
"""

from evalvault.adapters.outbound.tracker.base import BaseTrackerAdapter
from evalvault.adapters.outbound.tracker.langfuse_adapter import LangfuseAdapter
from evalvault.adapters.outbound.tracker.mlflow_adapter import MLflowAdapter
from evalvault.adapters.outbound.tracker.multi_adapter import MultiTrackerAdapter
from evalvault.adapters.outbound.tracker.phoenix_adapter import PhoenixAdapter

__all__ = [
    "BaseTrackerAdapter",
    "LangfuseAdapter",
    "MLflowAdapter",
    "MultiTrackerAdapter",
    "PhoenixAdapter",
]
