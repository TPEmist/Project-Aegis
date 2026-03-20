# Project Aegis (AgentPay)

**Status: MVP Completed**

## 專案概述
- **目標**：為 Agentic AI (如 LangChain/AutoGPT) 打造的「動態預算與權限管理協議」SDK。解決 AI 遇到付費牆時中斷的痛點，同時透過「硬性語意邊界」防止 AI 產生幻覺把信用卡刷爆。
- **技術棧**：Python 3.10+, uv, Pydantic, pytest, pytest-asyncio, langchain-core, 模擬 Stripe API。
- **核心架構**：
  1. The Vault (人類主帳戶)
  2. The Seal (虛擬單次支付憑證 VCC)
  3. Semantic Guardrails (語意與金額硬性邊界)

## 當前進度
- [x] Phase 0: 基礎設施建置 (專案初始化, 安裝依賴, 建立 skills 腳本與 MEMORY.md)
- [x] Phase 1: 核心領域模型 (建立 GuardrailPolicy, PaymentIntent, VirtualSeal 領域模型與單元測試通過)
- [x] Phase 2: 發卡模組實作 (建立 `VirtualCardProvider` 介面與 `MockStripeProvider` 實作，包含靜態金額防禦與非同步 pytest 驗證通過)
- [x] Phase 3: 語意護欄與決策引擎實作 (建立 `GuardrailEngine`，包含 Vendor 類別比對與幻覺迴圈關鍵字阻斷邏輯，單元測試通過)
- [x] Phase 4: SDK 核心協調層與 LangChain 工具整合 (建立 `AegisClient` 與 `AegisPaymentTool`，整合測試通過)
- [x] Phase 5: 端到端模擬腳本 (E2E Demo) 實作 (建立 `examples/e2e_demo.py`，完整展示合法發卡、金額超限攔截與幻覺防護三個情境)

## 如何執行 E2E Demo (MVP 成果)
使用以下指令即可看到完整的核心運行流程：
```bash
cd project-aegis
PYTHONPATH=. uv run python examples/e2e_demo.py
```

## 資料結構 (Schema) 與 API 介面約定
目前的 Pydantic 模型定義在 `aegis.core.models` 中：
- `GuardrailPolicy`: `allowed_categories`, `max_amount_per_tx`, `max_daily_budget`, `block_hallucination_loops`
- `PaymentIntent`: `agent_id`, `requested_amount`, `target_vendor`, `reasoning`
- `VirtualSeal`: `seal_id`, `card_number`, `cvv`, `expiration_date`, `authorized_amount`, `status`, `rejection_reason`

發卡模組介面定義在 `aegis.providers` 中：
- `VirtualCardProvider` (抽象基底類別)
- `MockStripeProvider` (實作類別，可根據金額上限制阻擋發卡，或發放模擬卡號)

語意護欄模組定義在 `aegis.engine.guardrails` 中：
- `GuardrailEngine`: 評估 `intent.target_vendor` 是否符合設定類別與 `intent.reasoning` 是否具幻覺或無窮迴圈特徵。

SDK 核心層與擴充模組：
- `AegisClient`: 將 `GuardrailEngine` 與 `VirtualCardProvider` 串連的處理入口。
- `AegisPaymentTool`: LangChain `BaseTool` 實作，供 Agent 進行非同步主動操作。

## 開發模式規範 (Development Protocol)
- **嚴格代理開發模式 (Strict CLI-Delegation)**：現場總監 (Tech Lead) 絕對禁止直接撰寫專案功能程式碼。
- **職責劃分**：
  - **Tech Lead (Agent)**: 負責維持大局觀與記憶 (`MEMORY.md`)、設計與撰寫測試 (`tests/`)、呼叫 CLI 腳本下達實作指令，並統籌驗證工作。
  - **gemini-cli** (透過 `skills/ask_cli.sh`): 負責所有功能程式碼的實體撰寫工作。所有 `aegis/` 內的改動必須強制透過指揮 CLI 腳本完成。

## 已知問題
- MVP 目前採用 heuristics 啟發式機制 (keyword-based) 檢查 Vendor 與推理，未來需替換為小型地端/雲端 LLM 的語意判定。
