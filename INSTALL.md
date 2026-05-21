# INSTALL.md

This guide sets up LLM Wiki MCP from a GitHub checkout, ingests the current directory, configures an Ollama connection, and asks questions against the local wiki using your own local agent.

## 1. Prerequisites

Install:

- Python 3.10 or newer.
- Git.
- Ollama, if you want to use the `/ask` command with a local model.

Confirm Python is available:

```bash
python --version
```

Confirm Ollama is available:

```bash
ollama --version
ollama list
```

## 2. Clone and install

```bash
git clone https://github.com/Electro-resonance/LLM-WIKI-MCP
cd LLM-WIKI-MCP
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[docs,mcp]
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

The editable install provides two console commands:

```bash
llm-wiki --help
llm-wiki-mcp --help
```

When running directly from a source checkout, these are equivalent:

```bash
python llm_wiki_cli.py --help
python llm_wiki_mcp_server.py --help
```

## 3. Initialise a vault

A vault is the local generated wiki store. It contains Markdown pages, the search index, config, runtime metrics, and optional notes.

```bash
llm-wiki --vault ./wiki_vault init
```

The repository ships only a placeholder `wiki_vault/.gitkeep`; runtime vault content is intentionally ignored by Git.

## 4. Ingest the current directory

To ingest the current project directory:

```bash
llm-wiki --vault ./wiki_vault ingest-dir . --pattern "*.md" --pattern "*.py" --pattern "*.txt" --pattern "*.rtf" --pattern "*.json"
```

Inside the interactive shell, the shorter form is:

```bash
llm-wiki --vault ./wiki_vault shell
wiki> /ingest .
wiki> /ingest ./notes/idea.rtf
wiki> /ingest ./transcripts/session.txt
```

The shell form scans supported document types recursively, including Markdown, `.txt`, `.rtf`, PDF, DOCX, and legacy DOC stubs. You can also point `/ingest` at one specific supported file instead of a directory. When you run `/ingest .`, the active `wiki_vault/` is skipped automatically so generated wiki pages are not re-ingested as source files. PDF and DOCX extraction require the optional document dependencies installed by `pip install -e .[docs,mcp]`. At shell startup, the CLI reports whether `pypdf` and `python-docx` are available. If a PDF was previously ingested while `pypdf` was missing, the next `/ingest .` run refreshes the old placeholder page automatically once `pypdf` is installed. PDF extraction reads the embedded text layer; scanned image-only PDFs should be OCR-converted before ingesting.

Useful variants:

```bash
llm-wiki --vault ./wiki_vault ingest-dir ./notes/idea.rtf
llm-wiki --vault ./wiki_vault ingest-dir ./transcripts/session.txt
llm-wiki --vault ./wiki_vault ingest-dir ./docs --pattern "*.md"
llm-wiki --vault ./wiki_vault ingest-dir ./notes --pattern "*.md" --pattern "*.txt" --pattern "*.rtf"
llm-wiki --vault ./wiki_vault ingest-dir ./papers --pattern "*.pdf"
llm-wiki --vault ./wiki_vault ingest-dir . --pattern "*.pdf" --pattern "*.docx"
llm-wiki --vault ./wiki_vault ingest-dir . --no-recursive --pattern "*.md"
```

## 5. Configure the Ollama connection

By default, use the standard local Ollama endpoint:

```bash
llm-wiki --vault ./wiki_vault config host http://localhost:11434
```

Choose the model used by `ask`:

```bash
llm-wiki --vault ./wiki_vault config model llama3.2:3b
```

Then test the connection:

```bash
llm-wiki --vault ./wiki_vault config test
```

Inside shell mode, use slash commands:

```text
wiki> /config host http://localhost:11434
wiki> /config model llama3.2:3b
wiki> /config test
```

## 6. Choose a default LLM for your PC

The default model is stored in `wiki_vault/llm_wiki_config.json`. You can change it at any time:

```bash
llm-wiki --vault ./wiki_vault config model <model-name>
```

Suggested starting points:

| Machine type | Example model choice | Notes |
| --- | --- | --- |
| CPU-only or small laptop | `llama3.2:1b` or `llama3.2:3b` | Fastest and easiest to run, but less capable on long synthesis. |
| Mid-range PC | `qwen2.5:7b`, `mistral:7b`, or similar | Better answers while remaining practical on many machines. |
| GPU workstation | A larger local model that fits VRAM | Better for long context, summarisation, and agentic ask workflows. |

Pull a model with Ollama before using it:

```bash
ollama pull llama3.2:3b
```

## 7. Ask the wiki

The top-level `ask` command retrieves relevant wiki pages, builds a prompt, and sends it to the configured Ollama model:

```bash
llm-wiki --vault ./wiki_vault ask "What does this project do?"
llm-wiki --vault ./wiki_vault ask "How do I use the ingest command?"
```

The shell version can be explicit with `/ask`, or conversational with no slash:

```text
wiki> /ask What does this project do?
wiki> How do I use the ingest command?
wiki> Tell me about Karpathy's work!
```

At the `wiki>` prompt, every explicit command begins with `/`. Text that does not begin with `/` is automatically treated as an `/ask` request.

To inspect the prompt and retrieval metadata without calling Ollama:

```bash
llm-wiki --vault ./wiki_vault ask "What does this project do?" --dry-run
```

To retrieve context without synthesis:

```bash
llm-wiki --vault ./wiki_vault retrieve "architecture" --top-k 5 --show
```


## 8. Adjust terminal screen width

The CLI wraps terminal text at 120 characters by default so long LLM answers do not rely on the terminal wrapping mid-word. This is only for screen output; JSON and exported Markdown are not reformatted.

Set the width when launching the CLI:

```bash
llm-wiki --screen-width 120 --vault ./wiki_vault shell
llm-wiki --screen-width 180 --vault ./wiki_vault ask "Summarise this wiki"
```

Disable terminal wrapping when you want raw Markdown-style output:

```bash
llm-wiki --no-screen-wrap --vault ./wiki_vault shell
llm-wiki --screen-width 0 --vault ./wiki_vault ask "Show the raw answer"
```

Inside the interactive shell you can change it at any time:

```text
wiki> /screen-width 120
wiki> /screen-width off
wiki> /wrap on
wiki> /wrap off
```

You can also set `LLM_WIKI_SCREEN_WIDTH` in the environment.

## 9. Maintain the wiki

After ingestion, useful maintenance commands are:

```bash
llm-wiki --vault ./wiki_vault stats
llm-wiki --vault ./wiki_vault lint
llm-wiki --vault ./wiki_vault repair
llm-wiki --vault ./wiki_vault repair --apply
llm-wiki --vault ./wiki_vault reindex
llm-wiki --vault ./wiki_vault export
```

Graph output:

```bash
llm-wiki --vault ./wiki_vault mermaid --output docs/wiki_graph.md
```

## 10. Run the MCP server

```bash
llm-wiki-mcp server --vault ./wiki_vault
```

Or from a checkout:

```bash
python llm_wiki_mcp_server.py server --vault ./wiki_vault
```

## 11. Troubleshooting

`config test` fails: confirm Ollama is running and that the configured host matches your machine setup.

`ask` is slow: select a smaller model with `/config model`, reduce `--top-k`, or reduce `--max-context-chars`.

Ingest misses files: add more `--pattern` options, check `--no-recursive`, and confirm optional document dependencies are installed for PDF/DOCX; TXT and RTF do not need extra packages. The active `wiki_vault/` is intentionally skipped during `/ingest .` to avoid absorbing generated wiki pages.

Search seems stale: run `llm-wiki --vault ./wiki_vault reindex`.

## Tuning ask context for your machine

After `/ingest .`, use `/context-settings` to inspect the active ask budgets. The default context budget is 24,000 estimated tokens, with 3,000 tokens reserved for recent ask/reply history and 6,000 tokens available per source page.

For smaller models or low-memory machines, reduce the budget:

```text
/context-settings context-budget 8000
/context-settings history-budget 1000
/context-settings source-budget 2000
/context-settings max-sources 4
```

For larger models, increase it:

```text
/context-settings context-budget 32000
/context-settings source-budget 8000
```

To inspect what would be sent to the model before running a real ask:

```text
/debug-context explain the main architecture
```

## Progress output and command history

During large ingests, the CLI shows same-line counters rather than a long stream of filenames. In the shell you will first see `Scan: 123 files | filename.pdf` while the directory tree is walked and the active `wiki_vault/` is skipped, then `Ingest: 12/78 files`, and finally `Reindex: 12/45 pages`. Each status updates in place and is cleared before the final summary. `/notes-all` uses the same pattern for pages.

The interactive shell also enables readline history. Use ↑/↓ to recall prior commands and Ctrl-R to reverse-search them. The history is saved in the selected vault as `.llm_wiki_history`.


## Searching large books after ingest

After ingesting a large PDF or book, use hit-centred search:

```text
wiki> /search key phrase
wiki> /search-following key phrase --pages 3
```

New PDF ingests include simple page markers where `pypdf` can read individual pages. These markers let `/search-following` return the matched page plus the following pages.

## Sample commented config

A commented sample config is included at `llm_wiki_config.sample.jsonc`. Copy it to `wiki_vault/llm_wiki_config.json`; the config loader accepts `//` and `#` comments.
