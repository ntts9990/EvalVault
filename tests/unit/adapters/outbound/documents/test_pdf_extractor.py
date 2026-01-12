from __future__ import annotations

import pytest

from evalvault.adapters.outbound.documents import pdf_extractor


class _FakePage:
    def __init__(self, text: str):
        self._text = text

    def extract_text(self):
        return self._text


class _FakeReader:
    def __init__(self, _path: str):
        self.pages = [_FakePage("")]


def test_extract_text_from_pdf_uses_ocr_when_enabled(monkeypatch, tmp_path) -> None:
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"not a pdf")

    import pypdf

    monkeypatch.setattr(pypdf, "PdfReader", _FakeReader)
    monkeypatch.setattr(
        "evalvault.adapters.outbound.documents.ocr.paddleocr_backend.extract_text_from_pdf",
        lambda *_args, **_kwargs: "ocr text",
    )

    text = pdf_extractor.extract_text_from_pdf(pdf, enable_ocr=True, ocr_min_chars=1)

    assert text == "ocr text"


def test_extract_text_from_pdf_returns_text_layer_when_sufficient(monkeypatch, tmp_path) -> None:
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"not a pdf")

    class _Reader:
        def __init__(self, _path: str):
            self.pages = [_FakePage("hello")]

    import pypdf

    monkeypatch.setattr(pypdf, "PdfReader", _Reader)

    text = pdf_extractor.extract_text_from_pdf(pdf, enable_ocr=True, ocr_min_chars=1)

    assert text == "hello"


def test_extract_text_from_pdf_rejects_unknown_backend(tmp_path) -> None:
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"not a pdf")

    with pytest.raises(ValueError):
        pdf_extractor.extract_text_from_pdf(pdf, enable_ocr=True, ocr_backend="unknown")
