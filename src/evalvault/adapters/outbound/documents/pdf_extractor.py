from __future__ import annotations

from pathlib import Path


def extract_text_from_pdf(
    path: Path,
    *,
    enable_ocr: bool = False,
    ocr_backend: str = "paddleocr",
    ocr_lang: str = "korean",
    ocr_device: str = "auto",
    ocr_mode: str = "text",
    ocr_min_chars: int = 200,
) -> str:
    text = ""
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))

        parts: list[str] = []
        for page in reader.pages:
            extracted = (page.extract_text() or "").strip()
            if extracted:
                parts.append(extracted)

        text = "\n\n".join(parts).strip()
    except ImportError:
        text = ""
    except Exception:
        text = ""

    if text and len(text) >= max(0, ocr_min_chars):
        return text

    if not enable_ocr:
        return text

    if ocr_backend == "paddleocr":
        from evalvault.adapters.outbound.documents.ocr import paddleocr_backend

        return paddleocr_backend.extract_text_from_pdf(
            path,
            lang=ocr_lang,
            device=ocr_device,
            mode=ocr_mode,
        )

    raise ValueError(f"Unsupported OCR backend: {ocr_backend}")
