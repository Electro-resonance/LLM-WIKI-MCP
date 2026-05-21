# References and Research Context

LLM Wiki MCP is inspired by a practical pattern: keep important knowledge in a format that is simultaneously useful to humans, scripts, and LLM agents.

Related ideas include:

- Markdown-first personal or project knowledge bases.
- Retrieval-augmented generation, but with maintained source pages rather than transient chunks only.
- MCP tool interfaces for agent access to local capabilities.
- `llms.txt` style exports for making project context easy for models to consume.
- Local Ollama-compatible model serving for private or offline workflows.

The project is intentionally dependency-light. Markdown and SQLite provide the baseline; RTF/TXT ingestion is dependency-free; optional dependencies add PDF/DOCX extraction and MCP server integration.
