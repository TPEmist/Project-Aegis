#!/usr/bin/env bash
set -e

echo ">> Running pytest..."
set +e
PYTHONPATH=. uv run pytest > pytest_output.log 2>&1
TEST_EXIT_CODE=$?
set -e

if [ $TEST_EXIT_CODE -ne 0 ]; then
  echo ">> Tests failed. Sending error trace to gemini-cli for fix..."
  ERROR_TRACE=$(cat pytest_output.log)
  ./skills/ask_cli.sh "Tests failed with the following error:\n$ERROR_TRACE\n\nPlease provide a fix."
else
  echo ">> Tests passed."
fi
