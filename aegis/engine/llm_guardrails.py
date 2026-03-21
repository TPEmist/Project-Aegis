import json
import openai
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from aegis.core.models import PaymentIntent, GuardrailPolicy

class LLMGuardrailEngine:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = 'gpt-4o-mini', use_json_mode: bool = True):
        self.client = openai.AsyncOpenAI(api_key=api_key or 'not-needed', base_url=base_url)
        self.model = model
        self.use_json_mode = use_json_mode

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError, openai.APITimeoutError))
    )
    async def evaluate_intent(self, intent: PaymentIntent, policy: GuardrailPolicy) -> tuple[bool, str]:
        prompt = f"""
Evaluate the following agent payment intent.
Reasoning: {intent.reasoning}
Policy allowed categories: {policy.allowed_categories}
Block hallucination/loops: {policy.block_hallucination_loops}

Determine if the agent is hallucinating, in an infinite loop, or buying unrelated services.
You must return only JSON: {{"approved": bool, "reason": str}}
"""
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a strict security module. IMPORTANT: Respond with ONLY valid JSON containing \"approved\" (bool) and \"reason\" (str), no other text."},
                {"role": "user", "content": prompt}
            ]
        }
        
        if self.use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        
        result_text = response.choices[0].message.content
        try:
            result = json.loads(result_text)
            return result.get("approved", False), result.get("reason", "Unknown")
        except (json.JSONDecodeError, KeyError, Exception) as e:
            return False, f"LLM Engine Error: {str(e)}"
