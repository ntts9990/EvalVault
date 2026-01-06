"""Method plugin adapters."""

from evalvault.adapters.outbound.methods.external_command import ExternalCommandMethod
from evalvault.adapters.outbound.methods.registry import (
    ENTRYPOINT_GROUP,
    MethodRegistry,
    MethodSpec,
)

__all__ = [
    "ENTRYPOINT_GROUP",
    "ExternalCommandMethod",
    "MethodRegistry",
    "MethodSpec",
]
