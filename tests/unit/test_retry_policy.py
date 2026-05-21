"""Tests for RetryPolicy and retry helpers in llm.base."""

from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from evalvault.adapters.outbound.llm.base import (
    BaseLLMAdapter,
    RetryPolicy,
    retry_async,
    retry_sync,
)


class TestRetryPolicy:
    """RetryPolicy defaults and validation."""

    def test_defaults(self):
        policy = RetryPolicy()
        assert policy.max_attempts == 3
        assert policy.backoff_seconds == 1.0
        assert policy.backoff_multiplier == 2.0
        assert policy.timeout_seconds == 120.0

    def test_frozen(self):
        policy = RetryPolicy()
        with pytest.raises(ValidationError):
            policy.max_attempts = 5

    def test_model_copy_update(self):
        policy = RetryPolicy()
        updated = policy.model_copy(update={"max_attempts": 5, "timeout_seconds": 30.0})
        assert updated.max_attempts == 5
        assert updated.timeout_seconds == 30.0
        assert policy.max_attempts == 3  # original unchanged

    @pytest.mark.parametrize(
        "invalid_field, invalid_value",
        [
            ("max_attempts", 0),
            ("backoff_seconds", -1.0),
            ("backoff_multiplier", 0.5),
            ("timeout_seconds", -1.0),
        ],
    )
    def test_field_validation(self, invalid_field, invalid_value):
        with pytest.raises(ValidationError):
            RetryPolicy(**{invalid_field: invalid_value})


class TestRetryAsync:
    """retry_async helper behavior."""

    def test_succeeds_on_first_attempt(self):
        calls: list[int] = []

        async def fn() -> str:
            calls.append(1)
            return "ok"

        result = asyncio.run(retry_async(fn, policy=RetryPolicy(max_attempts=3)))
        assert result == "ok"
        assert len(calls) == 1

    def test_retries_until_success(self):
        calls: list[int] = []

        async def fn() -> str:
            calls.append(1)
            if len(calls) < 2:
                raise RuntimeError("transient")
            return "ok"

        result = asyncio.run(
            retry_async(fn, policy=RetryPolicy(max_attempts=3, backoff_seconds=0.0))
        )
        assert result == "ok"
        assert len(calls) == 2

    def test_raises_after_max_attempts(self):
        calls: list[int] = []

        async def fn() -> str:
            calls.append(1)
            raise RuntimeError("always fails")

        with pytest.raises(RuntimeError, match="always fails"):
            asyncio.run(retry_async(fn, policy=RetryPolicy(max_attempts=2, backoff_seconds=0.0)))
        assert len(calls) == 2

    def test_timeout_per_attempt(self):
        async def slow_fn() -> str:
            await asyncio.sleep(1.0)
            return "ok"

        with pytest.raises((TimeoutError, asyncio.TimeoutError)):
            asyncio.run(
                retry_async(
                    slow_fn,
                    policy=RetryPolicy(max_attempts=1, backoff_seconds=0.0, timeout_seconds=0.05),
                )
            )

    def test_zero_timeout_disables(self):
        async def fn() -> str:
            return "ok"

        result = asyncio.run(
            retry_async(fn, policy=RetryPolicy(max_attempts=1, timeout_seconds=0.0))
        )
        assert result == "ok"


class TestRetrySync:
    """retry_sync helper behavior."""

    def test_succeeds_on_first_attempt(self):
        result = retry_sync(lambda: "ok", policy=RetryPolicy(max_attempts=3))
        assert result == "ok"

    def test_retries_until_success(self):
        attempts = {"n": 0}

        def fn() -> str:
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise RuntimeError("transient")
            return "ok"

        result = retry_sync(fn, policy=RetryPolicy(max_attempts=3, backoff_seconds=0.0))
        assert result == "ok"
        assert attempts["n"] == 2

    def test_raises_after_max_attempts(self):
        attempts = {"n": 0}

        def fn() -> str:
            attempts["n"] += 1
            raise RuntimeError("always fails")

        with pytest.raises(RuntimeError, match="always fails"):
            retry_sync(fn, policy=RetryPolicy(max_attempts=2, backoff_seconds=0.0))
        assert attempts["n"] == 2


class TestBaseLLMAdapterRetryPolicy:
    """BaseLLMAdapter retry_policy plumbing."""

    def test_default_policy(self):
        class _Adapter(BaseLLMAdapter):
            provider_name = "test"

            async def agenerate_text(self, prompt, *, options=None):  # pragma: no cover
                return ""

            def generate_text(self, prompt, *, json_mode=False, options=None):  # pragma: no cover
                return ""

        adapter = _Adapter(model_name="test-model")
        assert adapter.get_retry_policy() == BaseLLMAdapter.default_retry_policy

    def test_custom_policy_override(self):
        class _Adapter(BaseLLMAdapter):
            provider_name = "test"

            async def agenerate_text(self, prompt, *, options=None):  # pragma: no cover
                return ""

            def generate_text(self, prompt, *, json_mode=False, options=None):  # pragma: no cover
                return ""

        custom = RetryPolicy(max_attempts=7, timeout_seconds=10.0)
        adapter = _Adapter(model_name="test-model", retry_policy=custom)
        assert adapter.get_retry_policy() == custom
        assert adapter.get_retry_policy().max_attempts == 7
