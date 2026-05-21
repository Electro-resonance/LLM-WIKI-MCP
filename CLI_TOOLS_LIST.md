# CLI Tools Reference

This is the human-facing command reference for the LLM Wiki CLI. The installed command is `llm-wiki`; when running directly from a checkout you can also use `python llm_wiki_cli.py`.

The interactive `wiki>` shell follows a Claude/OpenClaw-style convention: explicit commands begin with `/`, and anything typed without `/` is treated as a natural-language `/ask` request.

## Typical first run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .[docs,mcp]
llm-wiki --vault ./wiki_vault init
llm-wiki --vault ./wiki_vault shell
```

Inside the shell:

```text
wiki> /ingest .
# The active wiki_vault directory is skipped automatically
wiki> /config host http://localhost:11434
wiki> /config model llama3.2:3b
wiki> /screen-width 120
wiki> /ask What does this project do?
```

Use `llama3.2:3b` or another small model on CPU/no-GPU machines. Use a larger model if your PC/GPU can run it comfortably.


### Single-file examples

```text
wiki> /ingest ./notes/idea.rtf
wiki> /ingest ./transcripts/session.txt
wiki> /ingest ./papers/design-note.pdf
```

`/ingest .` skips the active `wiki_vault/` directory automatically so generated wiki pages are not absorbed back into the source set.

The same target can be used from the top-level CLI:

```bash
llm-wiki --vault ./wiki_vault ingest-dir ./notes/idea.rtf
llm-wiki --vault ./wiki_vault ingest-dir ./transcripts/session.txt
```

RTF extraction is dependency-free and strips common RTF control words into plain searchable text. TXT files are read directly as UTF-8 with replacement for invalid characters.

## Commands

| Command | What it does | Example |
| --- | --- | --- |
| `init` | Initialise a wiki vault with seed pages and an index. | `llm-wiki --vault ./wiki_vault init` |
| `ingest-dir` | Top-level command for ingesting a directory or one supported file. Use patterns to control directory file types, including TXT/RTF/PDF/DOCX. | `llm-wiki --vault ./wiki_vault ingest-dir ./notes/idea.rtf` |
| `shell` | Open the interactive shell. This is the easiest place to use short commands such as `/ingest .` and `/ask ...`. | `llm-wiki --vault ./wiki_vault shell` |
| `/ingest` | Interactive-shell command that ingests a directory recursively or one explicit file. It absorbs Markdown, TXT, RTF, PDF, DOCX, and legacy DOC stubs, and skips the active `wiki_vault/` on directory scans. | `wiki> /ingest ./notes/idea.rtf` |
| `/search` / `/find` | Search page snippets from the wiki index. | `wiki> /search architecture` |
| `/why` | Explain search normalisation and suggestions when results look surprising. | `wiki> /why architectures` |
| `/retrieve` | Retrieve top matching full wiki articles and optionally show an LLM-ready context block. | `wiki> /retrieve agentic ask --top-k 3` |
| `/articles` | Print the LLM-ready article context directly. | `wiki> /articles local first architecture` |
| `/ask` | Retrieve wiki context and ask the configured local Ollama model. | `wiki> /ask What does this project do?` |
| `/ask-mode` | Show or set default ask mode: `agentic` or `plain`. | `wiki> /ask-mode agentic` |
| `/ask-agentic` | Run the tool-calling ask workflow with final Ollama synthesis. | `wiki> /ask-agentic How does ingestion work?` |
| `/ask-agentic-dry` | Build the agentic evidence pack without calling Ollama. | `wiki> /ask-agentic-dry How does ingestion work?` |
| `/ask-agentic-protocol` | Show protocol-mode tool planning for an agentic ask. | `wiki> /ask-agentic-protocol What are the capabilities?` |
| `/ask-plain` | Run a non-agentic retrieve-and-synthesize ask. | `wiki> /ask-plain What does the README say?` |
| `context` | Build a bounded LLM-ready context pack without asking the model. | `llm-wiki --vault ./wiki_vault context "architecture" --limit 6 --max-chars 8000` |
| `/read` | Read a wiki page by title. | `wiki> /read Overview` |
| `/edit` | Open a page in `$EDITOR`, or print the path if no editor is set. | `wiki> /edit Overview` |
| `/pages` | List wiki pages in a table. | `wiki> /pages` |
| `/stats` | Show status and health summary. | `wiki> /stats` |
| `/lint` | Show broken links, orphan pages, and short pages. | `wiki> /lint` |
| `repair` | Plan or apply safe wiki lint repairs. Use `--apply` only when you want changes. | `llm-wiki --vault ./wiki_vault repair --apply` |
| `/reindex` | Rebuild the SQLite index from Markdown pages with a same-line `Reindex: n/m pages` progress counter. | `wiki> /reindex` |
| `/graph` | Show graph summary. | `wiki> /graph` |
| `mermaid` | Render the full wiki graph as Mermaid Markdown. | `llm-wiki --vault ./wiki_vault mermaid --output docs/wiki_graph.md` |
| `map` | Render a page-centred Mermaid neighbourhood. | `llm-wiki --vault ./wiki_vault map Overview --output docs/overview_graph.md` |
| `/export` | Export an `llms.txt` style context file. | `wiki> /export` |
| `/config` | Show or update configuration. | `wiki> /config` |
| `/config host` | Set the Ollama host. Public docs use localhost; users can substitute their own reachable Ollama endpoint. | `wiki> /config host http://localhost:11434` |
| `/config model` | Set the default model. Smaller models are useful on CPU/no-GPU machines. | `wiki> /config model llama3.2:3b` |
| `/config set` | Set any nested config key. | `wiki> /config set ollama.timeout_seconds 120` |
| `/config test` | Test the configured Ollama connection. | `wiki> /config test` |
| `/config edit` | Open the JSON config in `$EDITOR` and reload it. | `wiki> /config edit` |
| `/config reset` | Reset config to defaults. | `wiki> /config reset` |
| `/self` | Ask the tool/wiki about itself and print self-context. | `wiki> /self What can you inspect about yourself?` |
| `/usage` | Show estimated wiki/query token usage. | `wiki> /usage` |
| `/tokens` | Show token/s and ask metrics summary. | `wiki> /tokens` |
| `/self-stats` | Show structured self-access status, usage, and metrics. | `wiki> /self-stats` |
| `/self-usage` | Show usage snapshot for the tool/wiki/history. | `wiki> /self-usage` |
| `/capabilities` | Show the live runtime capability surface. | `wiki> /capabilities` |
| `/runtime-journal` | Show recent runtime execution journal entries. | `wiki> /runtime-journal` |
| `/command-map` | Show command-to-tool mapping. | `wiki> /command-map` |
| `/runtime-graph` | Print the Mermaid runtime execution graph. | `wiki> /runtime-graph` |
| `/reconcile` | Check documentation versus CLI/MCP surfaces. | `wiki> /reconcile` |
| `/recursive` | Enable or disable recursive ask memory. | `wiki> /recursive on` |
| `/compress` | Enable or disable ask-history compression. | `wiki> /compress on` |
| `/history` | Show recent ask history, including question, answer preview, and token estimates. | `wiki> /history` |
| `/history-status` | Show recursive memory/compression status for the stored prompt/response history. | `wiki> /history-status` |
| `/askrec` | Preview recursive ask using saved history. | `wiki> /askrec What did we discuss last time?` |
| `/recursive-preview` | Preview recursive context for a query. | `wiki> /recursive-preview architecture` |
| `/notes` | Show or create AI sidecar notes for a page. | `wiki> /notes Overview` |
| `/notes-iterate` | Iterate/write AI notes and candidate links for a page. | `wiki> /notes-iterate Overview` |
| `/notes-all` | Iterate notes for all pages, optionally with a limit. | `wiki> /notes-all 20` |
| `/notes-search` | Search source pages plus AI notes. | `wiki> /notes-search agentic retrieval` |
| `/notes-links` | Show candidate links for a page. | `wiki> /notes-links Overview` |
| `/notes-status` | Show AI notes coverage. | `wiki> /notes-status` |
| `/notes-graph` | Render Mermaid graph from AI note links. | `wiki> /notes-graph` |
| `/tool-catalog` | Show the unified MCP-style tool catalogue. | `wiki> /tool-catalog` |
| `/tool-count` | Show the full catalogue count. | `wiki> /tool-count` |
| `/planner-tools` | Show planner tool groups. | `wiki> /planner-tools` |
| `/intent-dry` | Show resolved intent and planned tools without executing the full ask. | `wiki> /intent-dry How do I configure Ollama?` |
| `/limitations` | Show known, fixed, and remaining limitations. | `wiki> /limitations` |
| `/provenance` | Show ingest provenance summary. | `wiki> /provenance` |
| `/startup` | Show startup command list or configure startup commands. | `wiki> /startup` |
| `/docs-consolidate` | Consolidate docs into fewer category files. | `wiki> /docs-consolidate` |
| `/history-build` | Build GitHub-friendly development history documentation. | `wiki> /history-build` |
| `/scope` | Explain or change wider query scope modes. | `wiki> /scope normal` |
| `/screen-width` | Show, set, or disable terminal-only word wrapping. Use `0` or `off` to disable. | `wiki> /screen-width 120` |
| `/wrap` | Enable or disable terminal-only word wrapping without changing the saved width. | `wiki> /wrap off` |
| `/json` | Toggle raw JSON output inside shell mode. | `wiki> /json on` |

## Top-level versus shell commands

- Top-level commands use the installed executable, for example `llm-wiki --vault ./wiki_vault search "architecture"`.
- Shell commands are slash-prefixed after `llm-wiki --vault ./wiki_vault shell`, for example `/search architecture`, `/ingest .`, and `/ask ...`. Plain text without a slash is routed to `/ask`, so `Tell me about Karpathy's work!` is valid.
- The shell supports command history and JSON toggling with `/json on` / `/json off`.


## PDF and DOCX absorption

Install optional document dependencies first:

```bash
pip install -e .[docs,mcp]
```

Then either run the shell command:

```text
wiki> /ingest .
# The active wiki_vault directory is skipped automatically
```

or target PDFs explicitly from the top-level CLI:

```bash
llm-wiki --vault ./wiki_vault ingest-dir ./papers --pattern "*.pdf"
```

PDF extraction reads the embedded text layer. For scanned/image-only PDFs, run OCR first or convert the document to Markdown/text before ingesting.

At interactive-shell startup, the CLI checks whether `pypdf` and `python-docx` are importable and prints PDF/DOCX extraction status lines. If a PDF page was previously created as a missing-`pypdf` placeholder, rerunning `/ingest .` after installing `pypdf` automatically refreshes that wiki page from the original PDF, even when the PDF file itself has not changed.

## Terminal screen width

By default, terminal output is wrapped at 120 characters. The wrapper inserts newlines at word boundaries and avoids breaking words. It preserves fenced code blocks and does not alter JSON or exported Markdown files.

Top-level flags:

```bash
llm-wiki --screen-width 120 --vault ./wiki_vault shell
llm-wiki --no-screen-wrap --vault ./wiki_vault ask "What does this project do?"
llm-wiki --screen-width 0 --vault ./wiki_vault shell
```

Interactive commands:

```text
wiki> /screen-width 120
wiki> /screen-width off
wiki> /wrap on
wiki> /wrap off
```

## Ask context and debugging commands

| CLI command | How a user uses it | Notes |
|---|---|---|
| `/context-settings` | Inspect the current ask context budgets. | Shows total prompt, history, per-source, max-source and debug-preview limits. |
| `/context-settings context-budget 24000` | Save the total estimated-token budget for `/ask`. | Raise for larger models; lower for small CPU models. |
| `/context-settings history-budget 3000` | Save how much recent ask/reply history can be included. | Helps follow-up questions without flooding the model. |
| `/context-settings source-budget 6000` | Save how much text each full source page can contribute. | Useful for long PDFs/books. |
| `/context-settings max-sources 8` | Save the maximum number of source pages considered. | Prevents broad questions from pulling too many weak pages. |
| `/context-settings full-page-threshold 3` | Save when the system should favour fuller reads. | If only a few strong matches are found, the pages are loaded more deeply. |
| `/debug-context <question>` | Preview the assembled prompt pack without calling Ollama. | Use this when an answer looks shallow, confused, or overly extractive. |

## Progress and interactive history

- `/ingest .` and top-level `ingest-dir` use same-line progress counters for the scan and ingest phases, for example `Scan: 123 files | filename.pdf` followed by `Ingest: 12/78 files`.
- After ingesting new or updated files, reindexing shows `Reindex: 12/45 pages` on the same line.
- `/reindex` uses the same reindex counter directly.
- `/notes-all` uses a same-line progress counter while pages are processed, for example `Notes: 12/45 pages`.
- The counter uses carriage-return updates and clears itself before the final summary, keeping terminal output readable.
- Interactive shell history is enabled at startup; use ↑/↓ for previous/next commands and Ctrl-R for reverse search where supported.


## Long-book navigation commands

| Command | What it does | Example |
|---|---|---|
| `/search <query>` | Searches the wiki and shows snippets centred around the actual hit. | `/search recursive cognition` |
| `/search-following <query>` | Returns the matched page plus following pages or a larger hit-centred excerpt. | `/search-following recursive cognition --pages 3 --limit 2` |
