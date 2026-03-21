import pytest
from aegis.client import AegisClient
from aegis.engine.guardrails import GuardrailEngine
from aegis.engine.llm_guardrails import LLMGuardrailEngine
from aegis.core.models import GuardrailPolicy, PaymentIntent
from aegis.providers.stripe_mock import MockStripeProvider

@pytest.mark.asyncio
async def test_client_engine_injection():
    policy = GuardrailPolicy(allowed_categories=["test"], max_amount_per_tx=10, max_daily_budget=100)
    provider = MockStripeProvider()
    
    # Test default engine
    client_default = AegisClient(provider, policy, db_path=":memory:")
    assert isinstance(client_default.engine, GuardrailEngine)
    
    # Test injected engine
    custom_engine = GuardrailEngine()
    client_custom = AegisClient(provider, policy, engine=custom_engine, db_path=":memory:")
    assert client_custom.engine is custom_engine

@pytest.mark.asyncio
async def test_llm_engine_config():
    # Test with custom config
    engine = LLMGuardrailEngine(
        api_key="sk-test",
        base_url="https://api.ollama.com/v1",
        model="llama3",
        use_json_mode=False
    )
    
    assert engine.client.api_key == "sk-test"
    assert str(engine.client.base_url) == "https://api.ollama.com/v1/"
    assert engine.model == "llama3"
    assert engine.use_json_mode is False

@pytest.mark.asyncio
async def test_mcp_server_env_logic(monkeypatch):
    import os
    import json
    
    monkeypatch.setenv("AEGIS_ALLOWED_CATEGORIES", '["openai", "anthropic"]')
    monkeypatch.setenv("AEGIS_MAX_PER_TX", "250.0")
    
    # We re-import or reload to check env vars
    import importlib
    import aegis.mcp_server
    importlib.reload(aegis.mcp_server)
    
    assert aegis.mcp_server.policy.allowed_categories == ["openai", "anthropic"]
    assert aegis.mcp_server.policy.max_amount_per_tx == 250.0
