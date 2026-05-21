# Agent Notes

This repository contains a local-first Markdown wiki plus CLI, Python API, and MCP server.

For safe changes:

1. Keep source examples generic and free of private paths, hostnames, local IPs, or internal project names.
2. Do not commit generated vault state.
3. Run `python -m py_compile src/llm_wiki_mcp/*.py llm_wiki_cli.py llm_wiki_mcp_server.py` after code edits.
4. Prefer small, auditable changes to the explicit tool tables and CLI commands.
5. Update `README.md`, `INSTALL.md`, and `docs/INDEX.md` when user-facing behaviour changes.
