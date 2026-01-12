from __future__ import annotations

from datetime import date

import pytest

from evalvault.domain.services.document_versioning import (
    VersionedChunk,
    normalize_doc_key,
    parse_contract_date,
    parse_effective_date_from_filename,
    pick_effective_date,
    select_chunks_for_contract_date,
)


def test_parse_contract_date_accepts_multiple_formats() -> None:
    assert parse_contract_date("2025.01.01") == date(2025, 1, 1)
    assert parse_contract_date("20250101") == date(2025, 1, 1)
    assert parse_contract_date("25-01-08") == date(2025, 1, 8)
    assert parse_contract_date(" ") is None
    assert parse_contract_date(None) is None
    assert parse_contract_date(123) is None


def test_parse_effective_date_from_filename_prefers_last_match() -> None:
    assert parse_effective_date_from_filename("terms_20240401") == date(2024, 4, 1)
    assert parse_effective_date_from_filename("(2025.01.01)") == date(2025, 1, 1)
    assert parse_effective_date_from_filename("terms_250108_v2") == date(2025, 1, 8)
    assert parse_effective_date_from_filename("x_20240401__20250623") == date(2025, 6, 23)
    assert parse_effective_date_from_filename("no_date_here") is None


def test_normalize_doc_key_removes_dates_and_versions() -> None:
    assert normalize_doc_key("보험약관_20240401_v2") == "보험약관"
    assert normalize_doc_key("foo-20240401-bar") == "foo_bar"
    assert normalize_doc_key("a__20240401__v10__b") == "a_b"


def test_pick_effective_date_selects_expected_version() -> None:
    available = [date(2024, 4, 1), date(2025, 1, 1)]
    assert pick_effective_date(available, None) == date(2025, 1, 1)
    assert pick_effective_date(available, date(2024, 12, 31)) == date(2024, 4, 1)
    assert pick_effective_date(available, date(2023, 12, 31)) == date(2024, 4, 1)

    with pytest.raises(ValueError):
        pick_effective_date([], date(2025, 1, 1))


def test_select_chunks_for_contract_date_filters_per_doc_key() -> None:
    chunks = [
        VersionedChunk(
            doc_key="A",
            effective_date=date(2024, 4, 1),
            doc_id="A:2024-04-01#1",
            content="a1",
        ),
        VersionedChunk(
            doc_key="A",
            effective_date=date(2025, 1, 1),
            doc_id="A:2025-01-01#1",
            content="a2",
        ),
        VersionedChunk(
            doc_key="B",
            effective_date=date(2023, 1, 1),
            doc_id="B:2023-01-01#1",
            content="b1",
        ),
    ]

    selected = select_chunks_for_contract_date(chunks, date(2024, 12, 31))

    assert sorted([c.doc_id for c in selected]) == ["A:2024-04-01#1", "B:2023-01-01#1"]
