import os
import json
import asyncio
from mcp.server.fastmcp import FastMCP
from aegis.core.models import PaymentIntent, GuardrailPolicy
from aegis.providers.stripe_mock import MockStripeProvider
from aegis.providers.stripe_real import StripeIssuingProvider
from aegis.client import AegisClient

mcp = FastMCP("Aegis-Vault")

# Load configuration from environment
allowed_categories = json.loads(os.getenv("AEGIS_ALLOWED_CATEGORIES", '["aws", "cloudflare"]'))
max_per_tx = float(os.getenv("AEGIS_MAX_PER_TX", "100.0"))
max_daily = float(os.getenv("AEGIS_MAX_DAILY", "500.0"))
block_loops = os.getenv("AEGIS_BLOCK_LOOPS", "true").lower() == "true"
stripe_key = os.getenv("AEGIS_STRIPE_KEY")
unmask_cards = os.getenv("AEGIS_UNMASK_CARDS", "false").lower() == "true"

policy = GuardrailPolicy(
    allowed_categories=allowed_categories,
    max_amount_per_tx=max_per_tx,
    max_daily_budget=max_daily,
    block_hallucination_loops=block_loops
)

if stripe_key:
    provider = StripeIssuingProvider(api_key=stripe_key)
else:
    provider = MockStripeProvider()

client = AegisClient(provider, policy)

@mcp.tool()
async def request_virtual_card(requested_amount: float, target_vendor: str, reasoning: str) -> str:
    """Request a virtual credit card for an automated purchase."""
    intent = PaymentIntent(
        agent_id="mcp-agent",
        requested_amount=requested_amount,
        target_vendor=target_vendor,
        reasoning=reasoning
    )
    seal = await client.process_payment(intent)
    if seal.status.lower() == "rejected":
        return f"Payment rejected by guardrails. Reason: {seal.rejection_reason}"
    
    if unmask_cards:
        return f"Payment approved. Card Issued: {seal.card_number}, CVV: {seal.cvv}, Expiry: {seal.expiration_date}, Amount: {seal.authorized_amount}"
    else:
        masked_card = f"****-****-****-{seal.card_number[-4:]}"
        return f"Payment approved. Card Issued: {masked_card}, Expiry: {seal.expiration_date}, Amount: {seal.authorized_amount}"

if __name__ == "__main__":
    mcp.run()
