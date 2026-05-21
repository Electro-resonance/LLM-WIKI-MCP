# User Guide

## Initialise

```bash
llm-wiki --vault ./wiki_vault init
```

## Ingest

Ingest Markdown and source files from the current directory:

```bash
llm-wiki --vault ./wiki_vault ingest-dir . --pattern "*.md" --pattern "*.py" --pattern "*.txt" --pattern "*.rtf"
```

In shell mode:

```text
wiki> /ingest .
wiki> /ingest ./notes/idea.rtf
wiki> /ingest ./transcripts/session.txt
```

You can ingest one file directly, or point `/ingest` at a directory. Supported source types include Markdown, `.txt`, `.rtf`, `.pdf`, `.docx`, and legacy `.doc` placeholder stubs. When `/ingest .` scans a project tree, the active `wiki_vault/` is skipped automatically so generated wiki pages are not ingested back into themselves.

Inside the interactive `wiki>` prompt, explicit commands begin with `/`. Plain text is treated as an `/ask` question, so `Tell me about Karpathy's work!` is valid without quoting.

## Search and retrieve

```bash
llm-wiki --vault ./wiki_vault search "configuration"
llm-wiki --vault ./wiki_vault retrieve "configuration" --top-k 5 --show
```

## Configure local LLM

```bash
llm-wiki --vault ./wiki_vault config host http://localhost:11434
llm-wiki --vault ./wiki_vault config model llama3.2:3b
llm-wiki --vault ./wiki_vault config test
```

Use a smaller model for CPU-only machines and a larger model when you have enough GPU memory.

## Ask

```bash
llm-wiki --vault ./wiki_vault ask "What does this wiki say about installation?"
```

Dry-run first when you want to inspect the retrieved context:

```bash
llm-wiki --vault ./wiki_vault ask "What does this wiki say about installation?" --dry-run
```


## Screen width

Screen output is word-wrapped at 120 characters by default. Use this when launching the CLI:

```bash
llm-wiki --screen-width 120 --vault ./wiki_vault shell
llm-wiki --no-screen-wrap --vault ./wiki_vault shell
```

Inside the shell:

```text
wiki> /screen-width 120
wiki> /screen-width off
```

This affects terminal display only; Markdown exports and JSON are left unchanged.

## Maintain

```bash
llm-wiki --vault ./wiki_vault stats
llm-wiki --vault ./wiki_vault lint
llm-wiki --vault ./wiki_vault repair
llm-wiki --vault ./wiki_vault repair --apply
llm-wiki --vault ./wiki_vault reindex
```

## When answers feel too shallow

Use `/debug-context <question>` to see what context was assembled for the model. If only short snippets are present, increase the source or context budget:

```text
/context-settings source-budget 6000
/context-settings context-budget 24000
/debug-context your question here
```

For small models, reduce the same values instead.

## Large ingest feedback

When `/ingest .` processes many files, the CLI keeps compact one-line counters instead of printing every filename as a separate line. First it shows `Scan: 123 files | filename.pdf` while walking and filtering the directory tree, then `Ingest: 12/78 files` while absorbing files. When ingest finishes, the automatic index rebuild shows `Reindex: 12/45 pages`; `/reindex` shows the same counter when run manually. Top-level `ingest-dir` and `/notes-all` use the same one-line progress style.

The shell enables persistent command history, so ↑/↓ should recall previous commands rather than displaying raw escape characters. Ctrl-R performs reverse history search on readline-capable terminals.


## Long-book search

Use `/search` for ordinary hit-centred snippets. Use `/search-following <query> --pages N` to read onward from a match inside a large book. The MCP equivalent is `wiki_search_following_pages`.
