#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

today="$(date +%Y-%m-%d)"

echo "[context-refresh] Repository: $ROOT_DIR"
echo "[context-refresh] Date: $today"
echo

echo "[1/4] Required context files"
for file in AGENTS.md docs/agent-context.md docs/llm-playbook.md docs/roadmap.md; do
  if [ -f "$file" ]; then
    echo "  OK  $file"
  else
    echo "  MISSING  $file"
  fi
done
echo

echo "[2/4] Code/docs drift hints"
echo "  Recent protocol/event keywords in code:"
rg -n "MOVE_TOKEN|TOKEN_MOVED|PING|PONG|HELLO|ERROR|ROLL_DICE|DICE_ROLLED" \
  services/api/app/main.py apps/web/src/ui/App.tsx apps/web/src/ui/Board.tsx \
  --no-heading || true
echo

echo "[3/4] Working tree summary"
git status --short
echo

echo "[4/4] Manual update checklist"
echo "  - Update docs/agent-context.md:"
echo "    * Last updated: $today"
echo "    * Current Implementation Snapshot"
echo "    * Next Recommended Tasks"
echo "    * Open Decisions / Risks"
echo "  - If protocol/data model changed, update:"
echo "    * docs/protocol.md"
echo "    * docs/data-model.md"
echo "  - Keep AGENTS.md pointers accurate."
