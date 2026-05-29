"""Unit tests for the stable regress error taxonomy (Phase 1 real-adapter readiness).

`error_type` (Python class name) is kept for backward compatibility, but adapters
switch on the stable UPPER_SNAKE `error_code` / `error_category` instead.
"""

from __future__ import annotations

import re

from evalvault.adapters.inbound.cli.commands.regress import (
    ERROR_CATEGORY_INPUT,
    ERROR_CATEGORY_INTERNAL,
    ERROR_CATEGORY_PROVENANCE,
    ERROR_CODE_INCOMPLETE_PROVENANCE,
    ERROR_CODE_INTERNAL,
    ERROR_CODE_INVALID_INPUT,
    ERROR_CODE_RUN_NOT_FOUND,
    classify_regress_error,
)

T3_RELEASE_VOCABULARY = re.compile(r"promote|hold|rollback", re.IGNORECASE)


def test_key_error_maps_to_run_not_found() -> None:
    assert classify_regress_error(KeyError("run-x")) == (
        ERROR_CODE_RUN_NOT_FOUND,
        ERROR_CATEGORY_INPUT,
    )


def test_shared_metrics_maps_to_incomplete_provenance() -> None:
    exc = ValueError("No shared metrics available for regression gate.")
    assert classify_regress_error(exc) == (
        ERROR_CODE_INCOMPLETE_PROVENANCE,
        ERROR_CATEGORY_PROVENANCE,
    )


def test_comparable_metrics_maps_to_incomplete_provenance() -> None:
    exc = ValueError("No comparable metrics found for regression gate.")
    assert classify_regress_error(exc) == (
        ERROR_CODE_INCOMPLETE_PROVENANCE,
        ERROR_CATEGORY_PROVENANCE,
    )


def test_generic_value_error_maps_to_invalid_input() -> None:
    assert classify_regress_error(ValueError("unrecognized argument")) == (
        ERROR_CODE_INVALID_INPUT,
        ERROR_CATEGORY_INPUT,
    )


def test_unexpected_exception_maps_to_internal() -> None:
    assert classify_regress_error(RuntimeError("boom")) == (
        ERROR_CODE_INTERNAL,
        ERROR_CATEGORY_INTERNAL,
    )


def test_codes_are_upper_snake_and_never_t3_vocabulary() -> None:
    codes = (
        ERROR_CODE_INCOMPLETE_PROVENANCE,
        ERROR_CODE_RUN_NOT_FOUND,
        ERROR_CODE_INVALID_INPUT,
        ERROR_CODE_INTERNAL,
    )
    for code in codes:
        assert re.fullmatch(r"[A-Z][A-Z0-9_]+", code), code
        assert not T3_RELEASE_VOCABULARY.search(code), code
    for category in (ERROR_CATEGORY_PROVENANCE, ERROR_CATEGORY_INPUT, ERROR_CATEGORY_INTERNAL):
        assert not T3_RELEASE_VOCABULARY.search(category), category
