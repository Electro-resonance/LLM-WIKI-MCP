#!/usr/bin/env bash
set -euo pipefail

VAULT="${1:-./wiki_vault}"

llm-wiki --vault "$VAULT" init
llm-wiki --vault "$VAULT" ingest-dir ./examples --pattern "*.md" --pattern "*.txt" --pattern "*.rtf"
llm-wiki --vault "$VAULT" search "example"
llm-wiki --vault "$VAULT" retrieve "example source" --top-k 3
llm-wiki --screen-width 120 --vault "$VAULT" ask "What is in the example source?" --dry-run

echo "Demo complete. Configure Ollama with: llm-wiki --vault $VAULT config host http://localhost:11434"

# Inspect and tune ask context
/context-settings
/context-settings context-budget 24000
/context-settings history-budget 3000
/context-settings source-budget 6000
/debug-context tell me about this wiki

# Large /ingest, /reindex, and /notes-all runs show a same-line progress counter.
# /ingest . skips the active wiki_vault automatically.
# In the interactive shell, use ↑/↓ to recall previous commands.

# Large ingests show: Scan: n files -> Ingest: n/N files -> Reindex: n/N pages
echo "/search-following recursive cognition --pages 2 --limit 2"
