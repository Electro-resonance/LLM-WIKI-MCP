# Architecture

LLM Wiki MCP is intentionally local-first and simple to inspect.

```mermaid
flowchart LR
    A[Source folders] --> B[Ingest]
    B --> C[Markdown wiki pages]
    C --> D[SQLite FTS index]
    C --> E[AI sidecar notes]
    D --> F[Search and retrieve]
    E --> F
    F --> G[Context pack]
    G --> H[Local Ollama model]
    C --> I[MCP tools]
    D --> I
```

## Layers

1. **Markdown truth layer**: the wiki pages are normal files under the selected vault.
2. **Index/cache layer**: SQLite full-text search accelerates retrieval but is rebuildable.
3. **CLI layer**: `llm-wiki` gives human-facing commands and shell mode.
4. **Python layer**: `LLMWikiContextEngine` lets another application request context programmatically.
5. **MCP layer**: `llm-wiki-mcp` exposes wiki tools to an MCP client.
6. **Local LLM layer**: `ask` uses an Ollama-compatible endpoint to synthesise answers from retrieved context.

See `docs/01_OVERVIEW_AND_ARCHITECTURE.md` for the fuller overview.
