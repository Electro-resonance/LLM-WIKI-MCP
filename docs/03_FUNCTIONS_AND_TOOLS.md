# Function List

## User CLI

- `init` — create the vault structure.
- `ingest-dir` — ingest a directory or one supported file into wiki pages.
- `search` / `why` — search and inspect query normalisation.
- `retrieve` — build an LLM-ready context pack from matching pages.
- `ask` — retrieve context and query the configured Ollama model.
- `config` — inspect or edit the local model/host/settings.
- `context` — build context text for another agent or script.
- `read` / `edit` — inspect or edit wiki pages.
- `stats` / `lint` / `repair` / `reindex` — maintain the wiki.
- `pages` — list wiki pages.
- `mermaid` / `map` — export graph views.
- `export` — write `llms.txt`.
- `shell` — open the interactive command shell.

## Python API

Use `LLMWikiContextEngine` from `llm_wiki_mcp.context_api` for embedding LLM Wiki into another local application.

## MCP API

Run `llm-wiki-mcp server --vault ./wiki_vault` to expose the wiki tools over stdio to an MCP client. The live tool list is defined in `src/llm_wiki_mcp/server.py`.


## MCP server mode

```bash
llm-wiki-mcp server --vault ./wiki_vault
```

The MCP layer is intentionally built from explicit tool definitions in `src/llm_wiki_mcp/server.py`, making the live tool surface auditable from source.
