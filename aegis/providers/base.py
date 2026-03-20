from abc import ABC, abstractmethod
from aegis.core.models import PaymentIntent, GuardrailPolicy, VirtualSeal

class VirtualCardProvider(ABC):
    @abstractmethod
    async def issue_card(self, intent: PaymentIntent, policy: GuardrailPolicy) -> VirtualSeal:
        pass
