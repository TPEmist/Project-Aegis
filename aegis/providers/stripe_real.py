import stripe
from aegis.providers.base import VirtualCardProvider
from aegis.core.models import PaymentIntent, GuardrailPolicy, VirtualSeal
import uuid

class StripeIssuingProvider(VirtualCardProvider):
    def __init__(self, api_key: str):
        stripe.api_key = api_key

    async def issue_card(self, intent: PaymentIntent, policy: GuardrailPolicy) -> VirtualSeal:
        if intent.requested_amount > policy.max_amount_per_tx:
            return VirtualSeal(
                seal_id=str(uuid.uuid4()),
                authorized_amount=0.0,
                status="Rejected",
                rejection_reason="Amount exceeds policy limit"
            )

        card = stripe.issuing.Card.create(
            type='virtual',
            currency='usd',
            spending_controls={
                'spending_limits': [
                    {
                        'amount': int(intent.requested_amount * 100),
                        'interval': 'all_time'
                    }
                ]
            }
        )
        
        return VirtualSeal(
            seal_id=str(uuid.uuid4()),
            card_number=f"****{card.last4}",
            cvv="***",
            expiration_date=f"{card.exp_month}/{card.exp_year}",
            authorized_amount=intent.requested_amount,
            status="Issued"
        )
