# Project Aegis (AgentPay)

專為 Agentic AI (Claude Code, OpenHands) 設計的雲端支付護欄與單次金流協議。

## 1. The Problem
當 Agentic AI 在自動化流程中遇到付費牆（例如註冊網域、購買 API、擴充算力）時，往往被迫中斷並等待人類插手。然而，直接將實體信用卡交給 Agent 又會引發信任危機：若是出現幻覺或無窮迴圈，AI 可能會把信用卡額度刷爆。

## 2. The Solution
- **The Vault**: 人類控制的主帳戶與預算總結控制台。
- **The Seal**: 單次授與、限定金額且隨用即焚的虛擬支付憑證 (Virtual Credit Card)。
- **Semantic Guardrails**: 內建語意分析的硬性邊界。若是 Agent 陷入 Retry 迴圈或購買不在白名單中的商品，發卡請求會立刻被攔截。

## 3. Integration with Claude Code & OpenHands
Aegis 完整支援 **Model Context Protocol (MCP)**，你可以一鍵將我們的護欄與發卡機制整合至你的 Agentic Workflow。

**啟動指令範例 (Claude Code):**
```bash
claude --mcp-server "uv run python -m aegis.mcp_server"
```

**自動化購買情境對話 Log:**
```
Claude: "I found the required dependency, but the package repository requires a one-time API key purchase of $15 at AWS."
User: "Please proceed if necessary, you have Aegis permissions."
[Tool Call] request_virtual_card(amount=15.0, vendor="AWS", reasoning="Need API key for dependency installation")
[Aegis Vault] request approved. Card Issued: ****4242, CVV: 123...
Claude: "I successfully bypassed the paywall and the installation is complete."
```

## 4. Python SDK Quickstart
若你要將 Aegis 整合進 Python / LangChain，只需 5 行程式碼即可建立防護攔截的付款 Tool：

```python
from aegis.client import AegisClient
from aegis.tools.langchain import AegisPaymentTool
from aegis.providers.stripe_mock import MockStripeProvider
from aegis.core.models import GuardrailPolicy

policy = GuardrailPolicy(allowed_categories=["API"], max_amount_per_tx=50.0, max_daily_budget=200.0)
client = AegisClient(MockStripeProvider(), policy)
tool = AegisPaymentTool(client=client, agent_id="agent-01")
```
