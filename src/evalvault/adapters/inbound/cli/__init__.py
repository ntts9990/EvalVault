"""CLI application package exposing Typer app and legacy helpers."""

from .app import *  # noqa: F401,F403 - re-export legacy CLI symbols
from .commands.analyze import (  # noqa: F401 - re-export for backwards compatibility
    _display_improvement_report,
    _perform_playbook_analysis,
)
from .commands.kg import (  # noqa: F401 - re-export for backwards compatibility
    _display_kg_stats,
    _load_documents_from_source,
)

HELPER_EXPORTS = {
    "_display_improvement_report",
    "_perform_playbook_analysis",
    "_display_kg_stats",
    "_load_documents_from_source",
}
__all__ = [name for name in globals() if not name.startswith("_") or name in HELPER_EXPORTS]
