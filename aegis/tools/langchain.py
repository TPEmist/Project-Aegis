from typing import Type, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from aegis.core.models import PaymentIntent
from aegis.client import AegisClient

class AegisPaymentInput(BaseModel):
    requested_amount: float = Field(..., description="The amount of money to request.")
    target_vendor: str = Field(..., description="The vendor to pay.")
    reasoning: str = Field(..., description="Reasoning for this payment.")

class AegisPaymentTool(BaseTool):
    name: str = "aegis_payment_tool"
    description: str = "當你需要突破付費牆、購買 API 配額或支付任何線上服務時使用。請提供完整的購買理由與目標供應商。"
    args_schema: Type[BaseModel] = AegisPaymentInput
    
    client: Any = Field(description="The AegisClient instance")
    agent_id: str = Field(..., description="The ID of the Agent making the request")
    
    def __init__(self, client: AegisClient, agent_id: str, **kwargs):
        super().__init__(client=client, agent_id=agent_id, **kwargs)

    def _run(self, requested_amount: float, target_vendor: str, reasoning: str, run_manager=None) -> str:
        raise NotImplementedError("Use the async method _arun instead.")

    async def _arun(self, requested_amount: float, target_vendor: str, reasoning: str, run_manager=None) -> str:
        intent = PaymentIntent(
            agent_id=self.agent_id,
            requested_amount=requested_amount,
            target_vendor=target_vendor,
            reasoning=reasoning
        )
        
        seal = await self.client.process_payment(intent)
        
        if seal.status.lower() == "rejected":
            return f"Payment rejected by guardrails. Reason: {seal.rejection_reason}"
        else:
            return f"Payment approved. Card Issued: {seal.card_number}, CVV: {seal.cvv}, Expiry: {seal.expiration_date}, Authorized Amount: {seal.authorized_amount}"
