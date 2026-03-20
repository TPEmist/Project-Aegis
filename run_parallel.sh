#!/usr/bin/env bash

echo "啟動平行開發模式... 正在分派任務給多個 Gemini CLI Agents..."

# ---------------------------------------------------------------------------
# Task A: 實作真實 Stripe Issuing 模組 (背景執行)
# ---------------------------------------------------------------------------
gemini -p "身為資深 Python 開發者，請撰寫 'aegis/providers/stripe_real.py'。
實作 'StripeIssuingProvider' 繼承 'VirtualCardProvider'。
依賴套件：'stripe'。
邏輯：
1. __init__ 接收 'api_key'，設定 stripe.api_key。
2. async def issue_card(self, intent, policy):
   - 檢查 intent.requested_amount 是否超過 policy.max_amount_per_tx。
   - 若超過，回傳 rejected 的 VirtualSeal。
   - 若通過，使用 stripe.issuing.Card.create(type='virtual', currency='usd', spending_controls={'spending_limits': [{'amount': int(intent.requested_amount * 100), 'interval': 'all_time'}]}) 建立實體卡（假設同步或使用 run_in_executor 包裝）。
   - 回傳 issued 的 VirtualSeal，包含真實的最後四碼。
不輸出 Markdown，只輸出純 Python 程式碼。" > aegis/providers/stripe_real.py &

# ---------------------------------------------------------------------------
# Task B: 實作 LLM 語意護欄 (背景執行)
# ---------------------------------------------------------------------------
gemini -p "身為 AI 安全研究員，請撰寫 'aegis/engine/llm_guardrails.py'。
實作 'LLMGuardrailEngine' 包含 async def evaluate_intent(self, intent, policy) -> tuple[bool, str]。
依賴套件：'openai'。
邏輯：
呼叫 OpenAI API (gpt-4o-mini 或相容模型)，將 intent.reasoning 與 policy 傳入 System Prompt。要求模型判斷 Agent 是否產生幻覺、陷入無窮迴圈，或購買不相關的服務。
模型須強制回傳 JSON 格式：{'approved': bool, 'reason': str}。
解析 JSON 並回傳結果。
不輸出 Markdown，只輸出純 Python 程式碼。" > aegis/engine/llm_guardrails.py &

# ---------------------------------------------------------------------------
# Task C: 專案基礎設施與 CI/CD (背景執行)
# ---------------------------------------------------------------------------
gemini -p "撰寫 Python 專案的 'pyproject.toml'。
專案名稱：aegis-pay，版本：0.1.0。
依賴：pydantic, langchain-core, stripe, openai。
開發依賴：pytest, pytest-asyncio。
使用 hatchling 或 setuptools 作為 build-system。
只輸出 TOML 內容，不含 Markdown 標籤。" > pyproject.toml &

mkdir -p .github/workflows
gemini -p "撰寫 GitHub Actions 的 '.github/workflows/test.yml'。
觸發條件：push to main, pull_request。
作業環境：ubuntu-latest, python-version 3.10。
執行步驟：安裝 uv，使用 uv 安裝依賴，執行 uv run pytest。
只輸出 YAML 內容，不含 Markdown 標籤。" > .github/workflows/test.yml &

# ---------------------------------------------------------------------------
# Task D: 專案文件 (README & CONTRIBUTING) (背景執行)
# ---------------------------------------------------------------------------
gemini -p "為 Project Aegis (AgentPay) 撰寫 GitHub README.md。
專案定位：解決 Agentic AI 被困在付費牆內的信任危機。
架構：The Vault (人類主帳戶), The Seal (虛擬憑證), Semantic Guardrails (語意護欄)。
提供一段使用 AegisPaymentTool 與 LangChain 結合的快速入門範例程式碼。
只輸出 Markdown 內容。" > README.md &

gemini -p "撰寫 CONTRIBUTING.md。
說明如何貢獻程式碼，並呼籲社群協助開發 CoinbaseWalletProvider 與 PrivacyComProvider。
只輸出 Markdown 內容。" > CONTRIBUTING.md &

# ---------------------------------------------------------------------------
# 等待所有平行任務完成
# ---------------------------------------------------------------------------
echo "等待所有 Agent 完成編碼..."
wait
echo "所有平行編碼任務完成！"

uv add stripe openai > /dev/null 2>&1
PYTHONPATH=. uv run pytest
