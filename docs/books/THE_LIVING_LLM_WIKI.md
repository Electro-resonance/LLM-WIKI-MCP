# The Living LLM Wiki

## A Concise Book on Local-First Agentic Knowledge Systems

### Chapter 1 — From Retrieval to Memory

Retrieval augmented generation made LLMs more useful by allowing them to consult external material. Yet normal RAG has a weakness: it often treats knowledge as fragments. Each run retrieves pieces, answers the question, and then forgets the synthesis.

An LLM Wiki changes the centre of gravity. The answer is not merely produced. The answer is distilled into a maintained knowledge base. A page becomes better each time it is touched. The system gradually learns the structure of the work, not because the model has permanent internal memory, but because the project has an external memory that humans and agents can both read.

### Chapter 2 — Markdown as the Truth Layer

Markdown is boring in the best possible way. It is portable, readable, diffable, and usable by humans without special tooling. A Markdown wiki can outlive any particular model, vendor, framework, or database. The index may change. The agent may change. The interface may change. The pages remain.

The wiki should contain definitions, source summaries, open questions, contradictions, architectural decisions, and practical recipes. It should not become a dumping ground for raw output. The art is compression: turning a noisy conversation into a useful page.

### Chapter 3 — The MCP Layer

The Model Context Protocol turns the wiki into an active tool surface. An agent can search it, read pages, create new notes, append sections, import transcripts, lint links, and build context packs.

This is more powerful than asking an LLM to remember. It gives the agent a place to put durable knowledge and a disciplined way to retrieve it.

### Chapter 4 — The Vault

The vault has three main parts.

The `wiki/` directory stores the durable pages. The `raw/` directory stores copied source material. The SQLite index accelerates search but remains rebuildable. This keeps the system robust. If the database is deleted, the wiki survives.

### Chapter 5 — Context Packs

A context pack is a bounded bundle of relevant pages. It is designed for the reality of context windows. Instead of stuffing an entire vault into a prompt, the system searches for relevant pages and assembles a compact evidence pack.

This gives an agent enough memory to act coherently without drowning it in irrelevant material.

### Chapter 6 — Decisions and Contradictions

A mature knowledge system records not only facts, but choices. The decision log explains why the system took a particular direction. The contradictions page records places where sources, assumptions, or interpretations disagree.

This matters because long-running projects often fail not from lack of data, but from loss of reasoning history.

### Chapter 7 — Agentic Maintenance

An LLM Wiki should be maintained like a garden. Search finds pages. Editing improves pages. Linting finds weak structure. Links reveal the shape of knowledge. Orphans show isolated ideas. Broken links show concepts that want pages.

The agent should be encouraged to improve the wiki while answering questions, but with restraint. Durable pages should not be overwritten carelessly. Append, cite, clarify, and log decisions.

### Chapter 8 — Why release is Single-File

This version follows a single-file MCP style because it is easy to inspect and easy to adapt. The attached EML MCP server demonstrated a useful pattern: keep handlers explicit, tool definitions visible, MCP transport lazy, and tests runnable without the MCP package.

That structure makes the implementation approachable. You can paste the file into another project, run examples immediately, and then package it when needed.

### Chapter 9 — Future Extensions

Useful future additions include semantic embeddings, source citation spans, git-backed history, conflict resolution workflows, better transcript summarisation, page templates, automatic glossary extraction, and multi-vault federation.

The core principle should remain unchanged: Markdown is the truth layer; indexes and models are helpers.

### Chapter 10 — The Practical Philosophy

The system is not trying to make an LLM conscious or permanently self-aware. It gives human-led projects a durable external memory. The intelligence emerges from the loop: human intention, model synthesis, wiki preservation, and later reuse.

That loop is modest, practical, and powerful.

## Release.2 user CLI UX update

The user CLI now defaults to human-readable output instead of JSON. Use `--json` on normal commands or `/json on` inside the interactive shell when structured output is needed for scripting. See `docs/CLI_USER_EXPERIENCE.md` for examples.
