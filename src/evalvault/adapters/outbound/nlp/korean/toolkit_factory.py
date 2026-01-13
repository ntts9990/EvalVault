from __future__ import annotations

import logging

from evalvault.ports.outbound.korean_nlp_port import KoreanNLPToolkitPort

logger = logging.getLogger(__name__)


def try_create_korean_toolkit() -> KoreanNLPToolkitPort | None:
    try:
        from evalvault.adapters.outbound.nlp.korean.toolkit import KoreanNLPToolkit
    except Exception as exc:
        logger.debug("Korean toolkit import failed: %s", exc)
        return None
    try:
        return KoreanNLPToolkit()
    except Exception as exc:
        logger.debug("Korean toolkit init failed: %s", exc)
        return None
