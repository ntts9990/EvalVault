from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


class SummaryAccuracy:
    """Measure whether summary entities are supported by contexts."""

    name = "summary_accuracy"

    _PERCENT_RE = re.compile(r"(?P<number>\d+(?:[.,]\d+)?)\s*(?P<unit>%|퍼센트|percent)", re.I)
    _CURRENCY_RE = re.compile(
        r"(?P<number>\d+(?:[.,]\d+)?)\s*(?P<unit>원|만원|억원|달러|usd|krw|won)",
        re.I,
    )
    _CURRENCY_PREFIX_RE = re.compile(r"(?P<unit>[$₩])\s*(?P<number>\d+(?:[.,]\d+)?)")
    _DURATION_RE = re.compile(
        r"(?P<number>\d+(?:[.,]\d+)?)\s*(?P<unit>년|개월|월|일|years?|months?|days?)",
        re.I,
    )
    _DATE_RE = re.compile(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b")

    _CURRENCY_MULTIPLIERS = {"만원": Decimal("10000"), "억원": Decimal("100000000")}
    _KRW_UNITS = {"원", "krw", "won", "₩", "만원", "억원"}
    _USD_UNITS = {"달러", "usd", "$"}
    _DURATION_UNITS = {
        "년": "year",
        "year": "year",
        "years": "year",
        "개월": "month",
        "월": "month",
        "month": "month",
        "months": "month",
        "일": "day",
        "day": "day",
        "days": "day",
    }

    _KEYWORDS_KO = (
        "면책",
        "제외",
        "단서",
        "다만",
        "조건",
        "자기부담",
        "한도",
        "감액",
    )
    _KEYWORDS_EN = (
        "exclusion",
        "excluded",
        "exception",
        "except",
        "condition",
        "deductible",
        "limit",
        "cap",
        "waiting period",
        "co-pay",
        "copay",
        "co-insurance",
        "coinsurance",
    )

    def score(self, answer: str, contexts: list[str]) -> float:
        if not contexts:
            return 0.0

        context_text = " ".join([ctx for ctx in contexts if ctx])
        context_entities = self._extract_entities(context_text)
        summary_entities = self._extract_entities(answer or "")

        if not summary_entities:
            return 0.5 if context_entities else 0.0
        if not context_entities:
            return 0.0

        supported = summary_entities.intersection(context_entities)
        return len(supported) / len(summary_entities)

    def _extract_entities(self, text: str) -> set[str]:
        entities = set()
        entities.update(self._extract_numeric_entities(text))
        entities.update(self._extract_keyword_entities(text))
        return entities

    def _extract_numeric_entities(self, text: str) -> set[str]:
        entities: set[str] = set()

        for match in self._PERCENT_RE.finditer(text):
            number = self._normalize_number(match.group("number"))
            if number:
                entities.add(f"percent:{number}")

        for match in self._CURRENCY_RE.finditer(text):
            number = self._normalize_number(match.group("number"))
            unit = match.group("unit").lower()
            normalized = self._normalize_currency(number, unit)
            if normalized:
                entities.add(f"currency:{normalized}")

        for match in self._CURRENCY_PREFIX_RE.finditer(text):
            number = self._normalize_number(match.group("number"))
            unit = match.group("unit")
            normalized = self._normalize_currency(number, unit)
            if normalized:
                entities.add(f"currency:{normalized}")

        for match in self._DURATION_RE.finditer(text):
            number = self._normalize_number(match.group("number"))
            unit = match.group("unit").lower()
            normalized = self._normalize_duration(number, unit)
            if normalized:
                entities.add(f"duration:{normalized}")

        for match in self._DATE_RE.finditer(text):
            entities.add(f"date:{self._normalize_date(match.group(0))}")

        return entities

    def _extract_keyword_entities(self, text: str) -> set[str]:
        entities: set[str] = set()
        lower = text.lower()

        for keyword in self._KEYWORDS_KO:
            if keyword in text:
                entities.add(f"kw:{keyword}")

        for keyword in self._KEYWORDS_EN:
            if keyword in lower:
                entities.add(f"kw:{keyword}")

        return entities

    def _normalize_currency(self, number: str | None, unit: str) -> str | None:
        if number is None:
            return None
        try:
            value = Decimal(number)
        except InvalidOperation:
            return None

        unit_key = unit.lower()
        multiplier = self._CURRENCY_MULTIPLIERS.get(unit_key)
        if multiplier:
            value *= multiplier

        if unit_key in self._KRW_UNITS:
            currency = "krw"
        elif unit_key in self._USD_UNITS:
            currency = "usd"
        else:
            currency = unit_key

        return f"{currency}:{self._format_decimal(value)}"

    def _normalize_duration(self, number: str | None, unit: str) -> str | None:
        if number is None:
            return None
        try:
            value = Decimal(number)
        except InvalidOperation:
            return None
        base_unit = self._DURATION_UNITS.get(unit, unit)
        return f"{self._format_decimal(value)}{base_unit}"

    @staticmethod
    def _normalize_date(raw: str) -> str:
        return re.sub(r"[./-]", "", raw)

    @staticmethod
    def _normalize_number(raw: str | None) -> str | None:
        if raw is None:
            return None
        cleaned = raw.replace(",", "").strip()
        if not cleaned:
            return None
        try:
            value = Decimal(cleaned)
        except InvalidOperation:
            return None
        return SummaryAccuracy._format_decimal(value)

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        if value == value.to_integral_value():
            return str(value.to_integral_value())
        return format(value.normalize(), "f").rstrip("0").rstrip(".")
