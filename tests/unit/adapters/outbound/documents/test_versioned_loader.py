from __future__ import annotations

from datetime import date

import pytest

from evalvault.adapters.outbound.documents.versioned_loader import (
    load_versioned_chunks_from_pdf_dir,
)


def test_load_versioned_chunks_from_pdf_dir_builds_doc_ids(tmp_path, monkeypatch) -> None:
    (tmp_path / "terms_20240401.pdf").write_bytes(b"not a pdf")
    (tmp_path / "guide_250108_v2.pdf").write_bytes(b"not a pdf")

    def fake_extract_text_from_pdf(_path, **_kwargs):
        return "hello world"

    monkeypatch.setattr(
        "evalvault.adapters.outbound.documents.versioned_loader.extract_text_from_pdf",
        fake_extract_text_from_pdf,
    )

    chunks = load_versioned_chunks_from_pdf_dir(tmp_path, chunk_size=1000, overlap=0)

    assert len(chunks) == 2
    ids = sorted([c.doc_id for c in chunks])
    assert ids[0].startswith("guide:2025-01-08#")
    assert ids[1].startswith("terms:2024-04-01#")

    dates = {c.doc_key: c.effective_date for c in chunks}
    assert dates["terms"] == date(2024, 4, 1)
    assert dates["guide"] == date(2025, 1, 8)


def test_load_versioned_chunks_from_pdf_dir_raises_when_no_text(tmp_path, monkeypatch) -> None:
    (tmp_path / "terms_20240401.pdf").write_bytes(b"not a pdf")

    def empty_extract(_path, **_kwargs):
        return ""

    monkeypatch.setattr(
        "evalvault.adapters.outbound.documents.versioned_loader.extract_text_from_pdf",
        empty_extract,
    )

    with pytest.raises(ValueError):
        load_versioned_chunks_from_pdf_dir(tmp_path)
