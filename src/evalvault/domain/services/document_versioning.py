from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class VersionedChunk:
    doc_key: str
    effective_date: date
    doc_id: str
    content: str
    source: str | None = None


_DATE_YYYYMMDD = re.compile(r"(?P<ymd>\d{8})")
_DATE_YYMMDD = re.compile(r"(?P<ymd>\d{6})")
_DATE_DOTTED = re.compile(r"(?P<y>\d{4})\.(?P<m>\d{2})\.(?P<d>\d{2})")


def parse_contract_date(value: object) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None

    raw = value.strip()
    if not raw:
        return None

    dotted = _DATE_DOTTED.search(raw)
    if dotted:
        return date(int(dotted.group("y")), int(dotted.group("m")), int(dotted.group("d")))

    compact = re.sub(r"[^0-9]", "", raw)
    if len(compact) == 8:
        return date(int(compact[:4]), int(compact[4:6]), int(compact[6:8]))
    if len(compact) == 6:
        year = 2000 + int(compact[:2])
        return date(year, int(compact[2:4]), int(compact[4:6]))

    return None


def parse_effective_date_from_filename(stem: str) -> date | None:
    dotted = list(_DATE_DOTTED.finditer(stem))
    if dotted:
        m = dotted[-1]
        return date(int(m.group("y")), int(m.group("m")), int(m.group("d")))

    ymd8 = list(_DATE_YYYYMMDD.finditer(stem))
    if ymd8:
        ymd = ymd8[-1].group("ymd")
        return date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:8]))

    ymd6 = list(_DATE_YYMMDD.finditer(stem))
    if ymd6:
        ymd = ymd6[-1].group("ymd")
        year = 2000 + int(ymd[:2])
        return date(year, int(ymd[2:4]), int(ymd[4:6]))

    return None


def normalize_doc_key(stem: str) -> str:
    key = stem

    dotted = list(_DATE_DOTTED.finditer(key))
    if dotted:
        start, end = dotted[-1].span()
        key = (key[:start] + key[end:]).strip()

    ymd8 = list(_DATE_YYYYMMDD.finditer(key))
    if ymd8:
        start, end = ymd8[-1].span()
        key = (key[:start] + key[end:]).strip()

    ymd6 = list(_DATE_YYMMDD.finditer(key))
    if ymd6:
        start, end = ymd6[-1].span()
        key = (key[:start] + key[end:]).strip()

    key = re.sub(r"(?:^|[_\-])v\d+(?:$|[_\-])", "_", key, flags=re.IGNORECASE)
    key = re.sub(r"[_\-]{2,}", "_", key)
    key = key.strip(" _-")
    return key or stem


def pick_effective_date(available: list[date], contract: date | None) -> date:
    if not available:
        raise ValueError("no effective dates")
    available_sorted = sorted(set(available))
    if contract is None:
        return available_sorted[-1]

    eligible = [d for d in available_sorted if d <= contract]
    if eligible:
        return eligible[-1]

    return available_sorted[0]


def select_chunks_for_contract_date(
    chunks: list[VersionedChunk], contract: date | None
) -> list[VersionedChunk]:
    by_key: dict[str, list[VersionedChunk]] = {}
    for chunk in chunks:
        by_key.setdefault(chunk.doc_key, []).append(chunk)

    selected: list[VersionedChunk] = []
    for _doc_key, group in by_key.items():
        dates = [c.effective_date for c in group]
        chosen = pick_effective_date(dates, contract)
        selected.extend([c for c in group if c.effective_date == chosen])

    return selected
