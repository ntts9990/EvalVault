from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PaddleOcrConfig:
    lang: str
    device: str
    mode: str


def _resolve_use_gpu(device: str) -> bool:
    if device == "gpu":
        return True
    if device == "cpu":
        return False
    try:
        import paddle

        return bool(paddle.device.is_compiled_with_cuda())
    except Exception:
        return False


def _pdf_to_images(pdf_path: Path) -> list[Any]:
    try:
        import numpy as np
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise RuntimeError(
            "PDF OCR requires `pypdfium2` and `numpy`. Install with `uv sync --extra ocr_paddle`"
        ) from exc

    pdf = pdfium.PdfDocument(str(pdf_path))
    images: list[Any] = []
    for page in pdf:
        bitmap = page.render(scale=2).to_numpy()
        if bitmap.ndim == 2:
            bitmap = np.stack([bitmap, bitmap, bitmap], axis=-1)
        if bitmap.shape[-1] == 4:
            bitmap = bitmap[:, :, :3]
        images.append(bitmap)
    return images


def extract_text_from_pdf(
    pdf_path: Path,
    *,
    lang: str,
    device: str,
    mode: str,
) -> str:
    try:
        from paddleocr import PaddleOCR, PPStructure
    except ImportError as exc:
        raise RuntimeError(
            "PaddleOCR is not installed. Install with `uv sync --extra ocr_paddle` and a paddlepaddle wheel"
        ) from exc

    use_gpu = _resolve_use_gpu(device)
    images = _pdf_to_images(pdf_path)

    parts: list[str] = []
    if mode == "structure":
        engine = PPStructure(
            ocr=True,
            table=True,
            show_log=False,
            lang=lang,
            use_gpu=use_gpu,
        )
        for image in images:
            items = engine(image)
            for item in items:
                item_type = str(item.get("type", ""))
                if item_type == "table":
                    res = item.get("res")
                    if isinstance(res, dict):
                        html = res.get("html")
                        if isinstance(html, str) and html.strip():
                            parts.append(html.strip())
                            continue
                res = item.get("res")
                if isinstance(res, str) and res.strip():
                    parts.append(res.strip())
                elif isinstance(res, list):
                    for cell in res:
                        if isinstance(cell, (list, tuple)) and len(cell) >= 2:
                            text = cell[1]
                            if isinstance(text, str) and text.strip():
                                parts.append(text.strip())
        return "\n".join(parts).strip()

    engine = PaddleOCR(
        lang=lang,
        use_gpu=use_gpu,
        use_angle_cls=True,
        show_log=False,
    )
    for image in images:
        result = engine.ocr(image, cls=True)
        for line in result or []:
            if isinstance(line, (list, tuple)) and len(line) >= 2:
                payload = line[1]
                if isinstance(payload, (list, tuple)) and payload:
                    text = payload[0]
                    if isinstance(text, str) and text.strip():
                        parts.append(text.strip())
    return "\n".join(parts).strip()
