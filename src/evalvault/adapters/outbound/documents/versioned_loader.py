from __future__ import annotations

import hashlib
import json
import os
from datetime import date
from pathlib import Path

from evalvault.adapters.outbound.documents.pdf_extractor import extract_text_from_pdf
from evalvault.domain.services.document_chunker import DocumentChunker
from evalvault.domain.services.document_versioning import (
    VersionedChunk,
    normalize_doc_key,
    parse_effective_date_from_filename,
    pick_effective_date,
)


def _build_cache_key(
    *,
    directory: Path,
    pdf_paths: list[Path],
    chunk_size: int,
    overlap: int,
    enable_ocr: bool,
    ocr_backend: str,
    ocr_lang: str,
    ocr_device: str,
    ocr_mode: str,
    ocr_min_chars: int,
    contract_dates: list[date | None] | None,
    max_chunks: int | None,
) -> str:
    parts: list[str] = [
        str(directory.resolve()),
        f"chunk_size={chunk_size}",
        f"overlap={overlap}",
        f"enable_ocr={enable_ocr}",
        f"ocr_backend={ocr_backend}",
        f"ocr_lang={ocr_lang}",
        f"ocr_device={ocr_device}",
        f"ocr_mode={ocr_mode}",
        f"ocr_min_chars={ocr_min_chars}",
        f"max_chunks={max_chunks}",
    ]

    if contract_dates is not None:
        normalized_contracts: list[str] = []
        for value in contract_dates:
            if isinstance(value, date):
                normalized_contracts.append(value.isoformat())
            else:
                normalized_contracts.append("none")
        parts.append("contract_dates=" + ",".join(sorted(set(normalized_contracts))))

    for path in pdf_paths:
        try:
            stat = path.stat()
            parts.append(f"pdf={path.name}:{stat.st_mtime_ns}:{stat.st_size}")
        except OSError:
            parts.append(f"pdf={path.name}:missing")

    return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()


def _load_cache(path: Path) -> list[VersionedChunk] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(payload, list):
        return None

    chunks: list[VersionedChunk] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            effective_raw = item.get("effective_date")
            effective = date.fromisoformat(str(effective_raw))
            chunks.append(
                VersionedChunk(
                    doc_key=str(item.get("doc_key", "")),
                    effective_date=effective,
                    doc_id=str(item.get("doc_id", "")),
                    content=str(item.get("content", "")),
                    source=str(item.get("source")) if item.get("source") is not None else None,
                )
            )
        except Exception:
            continue

    return chunks or None


def _save_cache(path: Path, chunks: list[VersionedChunk]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "doc_key": chunk.doc_key,
                "effective_date": chunk.effective_date.isoformat(),
                "doc_id": chunk.doc_id,
                "content": chunk.content,
                "source": chunk.source,
            }
            for chunk in chunks
        ]
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        return


def load_versioned_chunks_from_pdf_dir(
    directory: Path,
    *,
    chunk_size: int = 1200,
    overlap: int = 120,
    enable_ocr: bool = False,
    ocr_backend: str = "paddleocr",
    ocr_lang: str = "korean",
    ocr_device: str = "auto",
    ocr_mode: str = "text",
    ocr_min_chars: int = 200,
    contract_dates: list[date | None] | None = None,
    cache_dir: Path | None = None,
    max_chunks: int | None = None,
) -> list[VersionedChunk]:
    chunker = DocumentChunker(chunk_size=chunk_size, overlap=overlap)

    all_pdf_paths = sorted(directory.glob("*.pdf"))
    skipped_pdfs: list[str] = []

    pdf_paths = all_pdf_paths
    if contract_dates is not None:
        seen_contracts: set[date] = set()
        sorted_contracts: list[date] = []
        for value in contract_dates:
            if isinstance(value, date) and value not in seen_contracts:
                seen_contracts.add(value)
                sorted_contracts.append(value)
        sorted_contracts = sorted(sorted_contracts)
        include_latest = not sorted_contracts

        candidates: dict[str, dict[date, Path]] = {}
        for path in all_pdf_paths:
            stem = path.stem
            doc_key = normalize_doc_key(stem)
            effective = parse_effective_date_from_filename(stem) or date.min
            candidates.setdefault(doc_key, {})[effective] = path

        selected_paths: list[Path] = []
        for version_map in candidates.values():
            dates = sorted(version_map)
            for contract in sorted_contracts:
                chosen = pick_effective_date(dates, contract)
                resolved = version_map.get(chosen)
                if resolved is not None:
                    selected_paths.append(resolved)

            if include_latest:
                chosen = pick_effective_date(dates, None)
                resolved = version_map.get(chosen)
                if resolved is not None:
                    selected_paths.append(resolved)

        pdf_paths = sorted(set(selected_paths))

    effective_cache_dir = cache_dir or Path("data/cache/versioned_pdf")
    cache_key = _build_cache_key(
        directory=directory,
        pdf_paths=pdf_paths,
        chunk_size=chunk_size,
        overlap=overlap,
        enable_ocr=enable_ocr,
        ocr_backend=ocr_backend,
        ocr_lang=ocr_lang,
        ocr_device=ocr_device,
        ocr_mode=ocr_mode,
        ocr_min_chars=ocr_min_chars,
        contract_dates=contract_dates,
        max_chunks=max_chunks,
    )
    cache_path = effective_cache_dir / f"{cache_key}.json"
    if cache_path.exists():
        cached = _load_cache(cache_path)
        if cached is not None:
            return cached

    chunks: list[VersionedChunk] = []
    reached_cap = False
    for path in pdf_paths:
        stem = path.stem
        doc_key = normalize_doc_key(stem)
        effective = parse_effective_date_from_filename(stem) or date.min

        text = extract_text_from_pdf(
            path,
            enable_ocr=enable_ocr,
            ocr_backend=ocr_backend,
            ocr_lang=ocr_lang,
            ocr_device=ocr_device,
            ocr_mode=ocr_mode,
            ocr_min_chars=ocr_min_chars,
        )
        if not text:
            skipped_pdfs.append(path.name)
            continue

        for idx, chunk in enumerate(chunker.chunk(text), start=1):
            if max_chunks is not None and len(chunks) >= max_chunks:
                reached_cap = True
                break
            chunk_id = f"{doc_key}:{effective.isoformat()}#{idx}"
            chunks.append(
                VersionedChunk(
                    doc_key=doc_key,
                    effective_date=effective,
                    doc_id=chunk_id,
                    content=_compact_text(chunk),
                    source=os.fspath(path),
                )
            )

        if reached_cap:
            break

    if not chunks:
        message = (
            f"No text extracted from PDFs under: {directory} "
            f"(pdfs_total={len(all_pdf_paths)}, pdfs_loaded={len(pdf_paths)}, skipped={len(skipped_pdfs)})"
        )
        if skipped_pdfs:
            preview = ", ".join(skipped_pdfs[:5])
            message += f". Examples: {preview}"
        raise ValueError(message)

    _save_cache(cache_path, chunks)
    return chunks


def _compact_text(text: str) -> str:
    return " ".join(text.split())
