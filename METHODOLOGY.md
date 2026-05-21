# Methodology

LLM Wiki MCP treats maintained Markdown as the durable knowledge substrate.

The method is:

1. Ingest local source material into stable wiki pages.
2. Preserve provenance so pages can be refreshed when source files change.
3. Search and retrieve from the wiki rather than repeatedly throwing raw fragments at a model.
4. Let local agents query the wiki through context packs, CLI commands, or MCP tools.
5. Use linting, repair, backlinks, notes, and graph views to keep the knowledge base navigable.
6. Keep runtime state local and out of version control.

This combines the practicality of a local CLI with an agent-readable MCP surface.
