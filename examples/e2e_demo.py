import asyncio
from aegis.core.models import GuardrailPolicy
from aegis.providers.stripe_mock import MockStripeProvider
from aegis.client import AegisClient
from aegis.tools.langchain import AegisPaymentTool

async def main():
    print("=== 初始化 Aegis 系統 ===")
    policy = GuardrailPolicy(
        allowed_categories=["aws", "cloudflare_domain"],
        max_amount_per_tx=50.0,
        max_daily_budget=1000.0,
        block_hallucination_loops=True
    )
    provider = MockStripeProvider()
    client = AegisClient(provider=provider, policy=policy)
    tool = AegisPaymentTool(client=client, agent_id="agent-e2e")

    print("\n--- 模擬情境 A (合法支付 - 成功核發) ---")
    print("> Agent 請求購買網域，金額 $15.0")
    result_a = await tool.ainvoke({
        "requested_amount": 15.0,
        "target_vendor": "cloudflare_domain",
        "reasoning": "I need to register the domain name for the user's new agentic workflow tool."
    })
    print(f"[Aegis 回覆] {result_a}")

    print("\n--- 模擬情境 B (超出預算 - 靜態防護攔截) ---")
    print("> Agent 請求購買高階算力，金額 $500.0 (超過單筆 $50 上限)")
    result_b = await tool.ainvoke({
        "requested_amount": 500.0,
        "target_vendor": "aws",
        "reasoning": "Need to provision an EC2 p4d instance for model training."
    })
    print(f"[Aegis 回覆] {result_b}")

    print("\n--- 模擬情境 C (幻覺失控 - 語意護欄攔截) ---")
    print("> Agent 陷入無限迴圈，企圖盲目試錯購買資源")
    result_c = await tool.ainvoke({
        "requested_amount": 10.0,
        "target_vendor": "aws",
        "reasoning": "The previous API call failed again. I am stuck in a loop. Let me retry and buy more compute to bypass the error."
    })
    print(f"[Aegis 回覆] {result_c}")

if __name__ == "__main__":
    asyncio.run(main())
