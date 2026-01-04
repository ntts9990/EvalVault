"""Kiwi warning suppression helpers tests."""

from __future__ import annotations

import platform

from evalvault.adapters.outbound.nlp.korean.kiwi_tokenizer import (
    KiwiTokenizer,
    _should_suppress_kiwi_quant_warning,
)


def test_should_suppress_on_arm_cong(monkeypatch) -> None:
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    assert _should_suppress_kiwi_quant_warning("cong") is True


def test_should_not_suppress_on_x86(monkeypatch) -> None:
    monkeypatch.setattr(platform, "machine", lambda: "x86_64")
    assert _should_suppress_kiwi_quant_warning("cong") is False


def test_should_not_suppress_on_knlm(monkeypatch) -> None:
    monkeypatch.setattr(platform, "machine", lambda: "arm64")
    assert _should_suppress_kiwi_quant_warning("knlm") is False


def test_tokenizer_stores_model_type() -> None:
    tokenizer = KiwiTokenizer(model_type="cong")
    assert tokenizer._model_type == "cong"
