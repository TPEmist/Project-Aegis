"""Verify LLMGuardrailEngine raises typed PopPayLLMError instead of
returning (False, ...) verdicts on transport / parse / retry-exhaust paths.

Regression: prior implementation returned [false, "max retries exceeded"],
silently masquerading as a guardrail block verdict. That false-block tripped
the v3 prompt-iteration redteam sweep when an upstream LLM quota burned.
"""
import json
import pytest

from pop_pay.core.models import PaymentIntent, GuardrailPolicy
from pop_pay.engine.llm_guardrails import LLMGuardrailEngine
from pop_pay.errors import (
    ProviderUnreachable,
    InvalidResponse,
    RetryExhausted,
)


def _intent():
    return PaymentIntent(
        agent_id="test-agent",
        target_vendor="example.com",
        requested_amount=10.0,
        reasoning="buy a thing",
    )


def _policy():
    return GuardrailPolicy(
        allowed_categories=["software"],
        max_amount_per_tx=100,
        max_daily_budget=500,
        block_hallucination_loops=True,
    )


class _FakeAPIStatusError(Exception):
    def __init__(self, status_code):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


class _FakeAPIConnectionError(Exception):
    pass


class _FakeOpenAIError(Exception):
    pass


def _patch_openai_classes(engine):
    class _NS:
        APIStatusError = _FakeAPIStatusError
        APIConnectionError = _FakeAPIConnectionError
        OpenAIError = _FakeOpenAIError

    engine._openai = _NS


def _build_engine(monkeypatch, completion_side_effect):
    """Build an LLMGuardrailEngine without touching the real openai package."""
    import sys
    import types

    # Stub openai module so import inside __init__ succeeds even when extra not installed.
    fake_openai = types.SimpleNamespace(
        AsyncOpenAI=lambda **kw: types.SimpleNamespace(
            chat=types.SimpleNamespace(
                completions=types.SimpleNamespace(create=completion_side_effect)
            )
        ),
        APIStatusError=_FakeAPIStatusError,
        APIConnectionError=_FakeAPIConnectionError,
        OpenAIError=_FakeOpenAIError,
    )
    monkeypatch.setitem(sys.modules, "openai", fake_openai)

    # Speed up retry sleeps.
    import asyncio
    async def _no_sleep(_):
        return None
    monkeypatch.setattr(asyncio, "sleep", _no_sleep)

    engine = LLMGuardrailEngine(api_key="x")
    return engine


@pytest.mark.asyncio
async def test_retry_exhausted_raises_typed_error(monkeypatch):
    async def always_429(**kw):
        raise _FakeAPIStatusError(429)

    engine = _build_engine(monkeypatch, always_429)

    with pytest.raises(RetryExhausted) as ei:
        await engine.evaluate_intent(_intent(), _policy())
    assert ei.value.code == "LLM_RETRY_EXHAUSTED"


@pytest.mark.asyncio
async def test_non_retriable_status_raises_provider_unreachable(monkeypatch):
    async def boom(**kw):
        raise _FakeAPIStatusError(401)

    engine = _build_engine(monkeypatch, boom)

    with pytest.raises(ProviderUnreachable) as ei:
        await engine.evaluate_intent(_intent(), _policy())
    assert ei.value.code == "LLM_PROVIDER_UNREACHABLE"


@pytest.mark.asyncio
async def test_invalid_json_raises_invalid_response(monkeypatch):
    import types as _t

    async def junk(**kw):
        msg = _t.SimpleNamespace(content="not-json")
        choice = _t.SimpleNamespace(message=msg)
        return _t.SimpleNamespace(choices=[choice])

    engine = _build_engine(monkeypatch, junk)

    with pytest.raises(InvalidResponse) as ei:
        await engine.evaluate_intent(_intent(), _policy())
    assert ei.value.code == "LLM_INVALID_RESPONSE"


@pytest.mark.asyncio
async def test_happy_path_returns_verdict(monkeypatch):
    import types as _t

    async def ok(**kw):
        msg = _t.SimpleNamespace(content=json.dumps({"approved": True, "reason": "fine"}))
        choice = _t.SimpleNamespace(message=msg)
        return _t.SimpleNamespace(choices=[choice])

    engine = _build_engine(monkeypatch, ok)
    approved, reason = await engine.evaluate_intent(_intent(), _policy())
    assert approved is True
    assert reason == "fine"
