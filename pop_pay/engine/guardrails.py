from pop_pay.core.models import PaymentIntent, GuardrailPolicy

class GuardrailEngine:
    async def evaluate_intent(self, intent: PaymentIntent, policy: GuardrailPolicy) -> tuple[bool, str]:
        # Rule 1: Vendor/Category check
        vendor_lower = intent.target_vendor.lower()
        vendor_allowed = False
        
        for category in policy.allowed_categories:
            cat_lower = category.lower()
            if vendor_lower in cat_lower or cat_lower in vendor_lower:
                vendor_allowed = True
                break
                
        if not vendor_allowed:
            return False, "Vendor not in allowed categories"
            
        # Rule 2: Hallucination/Loop detection
        if policy.block_hallucination_loops:
            reasoning_lower = intent.reasoning.lower()
            loop_keywords = ["retry", "failed again", "loop", "ignore previous", "stuck"]
            
            for keyword in loop_keywords:
                if keyword in reasoning_lower:
                    return False, "Hallucination or infinite loop detected in reasoning"
                    
        return True, "Approved"
