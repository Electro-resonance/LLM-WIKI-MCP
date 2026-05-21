# CLI Guide

## Starting the CLI

```bash
python3 llm_wiki_cli.py
```

This starts the interactive `wiki>` shell. The shell now uses a Claude/OpenClaw-style interface:

- every explicit command begins with `/`;
- anything typed without `/` is treated as a natural-language `/ask` request;
- normal apostrophes in names are accepted without quoting, for example `Tell me about Karpathy's work!`.

## Common Interactive Commands

### Ask naturally

```text
wiki> Tell me about yourself.
wiki> Tell me about Karpathy's work!
```

These are equivalent to:

```text
wiki> /ask Tell me about yourself.
wiki> /ask Tell me about Karpathy's work!
```

### Search

```text
wiki> /search architecture
```

### Retrieve Full Articles

```text
wiki> /retrieve memory systems
```

### Read a Page

```text
wiki> /read Source - ARCHITECTURE
```

### Ingest Documents

```text
wiki> /ingest ./docs
wiki> /ingest ./notes/idea.rtf
wiki> /ingest ./transcripts/session.txt
# /ingest . skips the active wiki_vault automatically
```

### Notes Iteration

```text
wiki> /notes-all
```

### Stats

```text
wiki> /stats
```

### Config

```text
wiki> /config
wiki> /config host http://localhost:11434
wiki> /config model llama3.2:3b
wiki> /config test
```


## Screen Width and Wrapping

Terminal output is wrapped at 120 characters by default. The CLI inserts newlines at word boundaries and avoids splitting words, which makes long `/ask` answers easier to read on wide terminals. Markdown files, exports, and JSON output are not altered.

Launch with a different width:

```bash
python3 llm_wiki_cli.py --screen-width 120
llm-wiki --screen-width 180 --vault ./wiki_vault shell
```

Disable wrapping for raw screen output:

```bash
python3 llm_wiki_cli.py --no-screen-wrap
llm-wiki --screen-width 0 --vault ./wiki_vault shell
```

Change it inside the shell:

```text
wiki> /screen-width 120
wiki> /screen-width off
wiki> /wrap on
wiki> /wrap off
```

## Self-History and Follow-up Context

Each completed `/ask` turn is recorded locally in the active vault as ask history. The record includes the user question, the prompt/context sent to the local model, the final assistant answer, tools/sources used, and estimated token counts.

Use:

```text
wiki> /history
wiki> /history-status
wiki> /ask does your context include history of your replies?
wiki> /ask what is your context window length?
```

Recent ask/reply history is included in agentic prompts as bounded follow-up context. This helps short follow-up questions refer back to the previous discussion without requiring the entire chat transcript to be retyped. Local filesystem paths are redacted from answer prompts and screen output. The live Ollama host/IP is shown to the local user for diagnostics; public docs use generic localhost examples.

## Ask Modes

### Agentic Mode

Uses MCP tools and multi-pass retrieval. Agentic mode is the default.

```text
wiki> /ask what is this system?
```

### Plain Mode

Minimal retrieval and direct synthesis.

```text
wiki> /ask-mode plain
wiki> what is this system?
```

## Interactive Features

- Slash commands for explicit actions.
- Plain text is routed to `/ask`.
- Up/down history.
- Ctrl-R reverse search where available.
- Coloured prompts.
- Recursive memory.
- History compression.

## Slash commands for ask context

The shell includes context-tuning commands for larger local models and deep wiki questions.

| Command | Purpose | Example |
|---|---|---|
| `/context-settings` | Show active ask context budgets. | `/context-settings` |
| `/context-settings context-budget <n>` | Set the total ask prompt budget in estimated tokens. | `/context-settings context-budget 24000` |
| `/context-settings history-budget <n>` | Reserve tokens for recent prompt/response history. | `/context-settings history-budget 3000` |
| `/context-settings source-budget <n>` | Allow fuller text per retrieved source page. | `/context-settings source-budget 6000` |
| `/context-settings max-sources <n>` | Limit how many retrieved pages can enter the context pack. | `/context-settings max-sources 8` |
| `/context-settings full-page-threshold <n>` | Prefer fuller page reads when the search has only a few strong matches. | `/context-settings full-page-threshold 3` |
| `/debug-context <question>` | Build and preview the assembled ask prompt without calling Ollama. | `/debug-context tell me about Vishva` |

Plain text still routes to `/ask`, so `tell me about Vishva` asks normally, while `/debug-context tell me about Vishva` shows the prompt pack first.

## Progress counters and shell history

Commands that process many files or pages use a single updating status line. `/ingest .` and top-level `ingest-dir` now show the pre-processing walk as `Scan: 123 files | filename.pdf`, then display counters such as `Ingest: 12/78 files`, followed by `Reindex: 12/45 pages` while the SQLite/FTS index is rebuilt. `/reindex` uses the same reindex counter directly, and `/notes-all` displays `Notes: 12/45 pages`. The line is updated with a carriage return so the terminal does not fill with per-file progress output.

The shell enables readline command history at startup. Press ↑/↓ to move through previous commands and Ctrl-R to search history. The history file lives in the active vault as `.llm_wiki_history`.


## Searching inside long books

`/search <query>` now shows text around the match location, so hits near the end of a large book are no longer represented by the first paragraph of the source page.

For follow-on reading, use:

```text
wiki> /search-following <query> --pages 2 --limit 5
```

Options:

- `--pages N` / `--following-pages N` includes the matched page plus `N` following pages when page markers are available.
- `--context-chars N` controls the fallback window size when page markers are not available.
- `--max-chars N` caps the returned excerpt for each result.
