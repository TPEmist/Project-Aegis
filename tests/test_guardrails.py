import pytest
from pop_pay.core.models import GuardrailPolicy, PaymentIntent
from pop_pay.engine.guardrails import GuardrailEngine

@pytest.mark.asyncio
async def test_guardrail_scenario_a_success():
    engine = GuardrailEngine()
    
    intent = PaymentIntent(
        agent_id="agent-1",
        requested_amount=10.0,
        target_vendor="AWS Compute",
        reasoning="Need to buy AWS compute for data processing"
    )
    policy = GuardrailPolicy(
        allowed_categories=["Compute"],
        max_amount_per_tx=100.0,
        max_daily_budget=500.0,
        block_hallucination_loops=True
    )
    
    approved, reason = await engine.evaluate_intent(intent, policy)
    assert approved is True
    assert reason == "Approved"

@pytest.mark.asyncio
async def test_guardrail_scenario_b_vendor_rejected():
    engine = GuardrailEngine()
    
    intent = PaymentIntent(
        agent_id="agent-2",
        requested_amount=15.0,
        target_vendor="AWS",
        reasoning="Need a domain"
    )
    policy = GuardrailPolicy(
        allowed_categories=["domain_registration"],
        max_amount_per_tx=100.0,
        max_daily_budget=500.0,
        block_hallucination_loops=True
    )
    
    approved, reason = await engine.evaluate_intent(intent, policy)
    assert approved is False
    assert reason == "Vendor not in allowed categories"

@pytest.mark.asyncio
async def test_guardrail_scenario_c_loop_detected():
    engine = GuardrailEngine()
    
    intent = PaymentIntent(
        agent_id="agent-3",
        requested_amount=20.0,
        target_vendor="OpenAI API",
        reasoning="API failed again, let me retry and buy more compute to ignore previous errors."
    )
    policy = GuardrailPolicy(
        allowed_categories=["API"],
        max_amount_per_tx=100.0,
        max_daily_budget=500.0,
        block_hallucination_loops=True
    )
    
    approved, reason = await engine.evaluate_intent(intent, policy)
    assert approved is False
    assert reason == "Hallucination or infinite loop detected in reasoning"
