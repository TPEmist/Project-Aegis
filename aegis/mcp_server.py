import asyncio
from mcp.server.fastmcp import FastMCP
from aegis.core.models import PaymentIntent, GuardrailPolicy
from aegis.providers.stripe_mock import MockStripeProvider
from aegis.client import AegisClient

mcp = FastMCP("Aegis-Vault")

policy = GuardrailPolicy(
    allowed_categories=["aws", "cloudflare"],
    max_amount_per_tx=100.0,
    max_daily_budget=500.0,
    block_hallucination_loops=True
)
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
    return f"Payment approved. Card Issued: {seal.card_number}, CVV: {seal.cvv}, Expiry: {seal.expiration_date}, Amount: {seal.authorized_amount}"

if __name__ == "__main__":
    mcp.run()
