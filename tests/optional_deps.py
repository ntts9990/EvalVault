from __future__ import annotations

import importlib

_KIWI_STATE: tuple[bool, str] | None = None
_BM25_STATE: tuple[bool, str] | None = None
_SKLEARN_STATE: tuple[bool, str] | None = None


def _module_available(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
    except ImportError:
        return False
    return True


def kiwi_ready() -> tuple[bool, str]:
    """Check if KiwiTokenizer can initialize its model resources."""
    global _KIWI_STATE
    if _KIWI_STATE is not None:
        return _KIWI_STATE

    try:
        from evalvault.adapters.outbound.nlp.korean.kiwi_tokenizer import KiwiTokenizer

        tokenizer = KiwiTokenizer()
        _ = tokenizer.kiwi
    except Exception as exc:  # noqa: BLE001 - we only need readiness signal
        _KIWI_STATE = (False, f"kiwipiepy unavailable: {exc}")
    else:
        _KIWI_STATE = (True, "")

    return _KIWI_STATE


def rank_bm25_ready() -> tuple[bool, str]:
    """Check if rank_bm25 is installed."""
    global _BM25_STATE
    if _BM25_STATE is not None:
        return _BM25_STATE

    if _module_available("rank_bm25"):
        _BM25_STATE = (True, "")
    else:
        _BM25_STATE = (False, "rank_bm25 not installed")

    return _BM25_STATE


def sklearn_ready() -> tuple[bool, str]:
    """Check if scikit-learn is installed."""
    global _SKLEARN_STATE
    if _SKLEARN_STATE is not None:
        return _SKLEARN_STATE

    if _module_available("sklearn"):
        _SKLEARN_STATE = (True, "")
    else:
        _SKLEARN_STATE = (False, "scikit-learn not installed")

    return _SKLEARN_STATE
