#!/usr/bin/env bash
set -e

# 將 MEMORY.md 作為上下文傳遞給 gemini (若存在)
MEMORY_FILE="$(dirname "$0")/../MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
  CONTEXT=$(cat "$MEMORY_FILE")
else
  CONTEXT=""
fi

PROMPT="$1"

if [ -z "$PROMPT" ]; then
  echo "Usage: ./ask_cli.sh \"<prompt>\""
  exit 1
fi

# 系統指令：禁止模型呼叫內部工具（防止 shell_command 錯誤）並確保可重試
SAFE_PROMPT="$PROMPT

[System Directive]:
1. 絕對禁止使用任何內部工具 (DO NOT use run_shell_command, read_file 等)。
2. 只限輸出純文字與程式碼，呼叫端會處理檔案寫入。
3. 若附帶 Context，請以此為背景知識：
$CONTEXT"

MAX_RETRIES=5
RETRY_DELAY=5

for ((i=1;i<=MAX_RETRIES;i++)); do
  # 將結果與錯誤一併擷取
  # 由於 stderr 通常包含 progress 或 rate limit 提示，可根據輸出判斷
  OUTPUT=$(gemini -p "$SAFE_PROMPT" 2>&1)
  
  if echo "$OUTPUT" | grep -qiE "exhausted your capacity|rate limit|quota|429"; then
    echo ">> [Rate Limit] 額度耗盡，等待 $RETRY_DELAY 秒後重試... ($i/$MAX_RETRIES)" >&2
    sleep $RETRY_DELAY
    RETRY_DELAY=$((RETRY_DELAY * 2))
  elif echo "$OUTPUT" | grep -qi "Error executing tool"; then
    echo ">> [Tool Error] 偵測到外部 CLI 工具執行錯誤，自動重試... ($i/$MAX_RETRIES)" >&2
    sleep $RETRY_DELAY
  else
    # 成功輸出
    echo "$OUTPUT"
    exit 0
  fi
done

echo ">> 經過 $MAX_RETRIES 次重試仍失敗，請稍後再試。" >&2
exit 1
