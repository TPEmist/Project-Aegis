import uuid
from aegis.core.models import PaymentIntent, GuardrailPolicy, VirtualSeal
from aegis.providers.base import VirtualCardProvider
from aegis.engine.guardrails import GuardrailEngine

class AegisClient:
    def __init__(self, provider: VirtualCardProvider, policy: GuardrailPolicy):
        self.provider = provider
        self.policy = policy
        self.engine = GuardrailEngine()
        
    async def process_payment(self, intent: PaymentIntent) -> VirtualSeal:
        approved, reason = await self.engine.evaluate_intent(intent, self.policy)
        if not approved:
            return VirtualSeal(
                seal_id=str(uuid.uuid4()),
                authorized_amount=0.0,
                status="Rejected",
                rejection_reason=reason
            )
            
        return await self.provider.issue_card(intent, self.policy)
