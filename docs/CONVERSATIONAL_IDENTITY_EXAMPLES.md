# Conversational Identity and Positioning Examples

## Example agentic conversations from the LLM Wiki MCP CLI

This document captures real interactive examples of the system explaining:
- what it is;
- how it differs from ordinary RAG;
- the influence of Andrej Karpathy's LLM Wiki ideas;
- why the MCP + CLI architecture matters;
- reflective and recursive agentic workflows.

These examples are valuable because they demonstrate the system explaining itself using its own maintained knowledge substrate.

---

## Captured interactive examples

```text
wiki> /ask I want to tell my friend about what you are! Please provide a couple of paragraphs summary including about the Kaparthy origin and why you are better!
Ask mode: agentic
User request: I want to tell my friend about what you are! Please provide a couple of paragraphs summary including about the Kaparthy origin and why you are better!

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
**What I am – a quick rundown for your friend**

I’m the *Living LLM Wiki MCP*—a local‑first, Markdown‑based knowledge engine that blends an LLM with a version‑controlled wiki.  The idea was inspired by **Andrew Karpathy’s “LLM Wiki” pattern** (hence the “Kaparthy” reference in the book’s title).  Karpathy showed that you can give an LLM a persistent, searchable memory by wrapping it around a wiki‑style repository, rather than just feeding it a fresh chunk of text each time.  My architecture takes that core insight and adds a layer of self‑reflection, provenance tracking, and agent‑centric tooling.

**Why I’m a step ahead of plain RAG**

Traditional retrieval‑augmented generation (RAG) is a linear pipeline: *documents → chunks → retrieval → prompt → answer*.  In practice, that can feel brittle and opaque—once a chunk is retrieved, you have no guarantee it stays relevant or that the answer’s provenance is clear.  I reorganise that into a more robust workflow:

1. **Documents** are stored in a **markdown‑based wiki** that lives on disk.
2. The system builds a **graph of concepts, notes, and links** (thanks to SQLite indexing).
3. **Agentic tools** can interrogate that graph, follow provenance trails, and even edit the wiki on the fly.
4. When the LLM answers a question, it can ground its response in the *exact page, chunk, and note* that supplied the information—making the output traceable and editable.

Because the knowledge base is *local* and *version‑controlled*, you get data sovereignty, auditability, and the ability to roll back changes.  The built‑in linting, note‑generation, and repair tools let the system learn from its own mistakes, so over time it becomes more reliable and easier to maintain than a standard RAG setup.  In short: I’m not just a retrieval engine; I’m a living, self‑extending knowledge substrate that an LLM can introspect, edit, and grow with you.
wiki> /ask longer and more why you are different and what you consist of
Ask mode: agentic
User request: longer and more why you are different and what you consist of

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
**Why the LLM‑Wiki MCP is different**

| Feature | How it differs from ordinary RAG or chat‑with‑docs systems | Why it matters |
|---------|----------------------------------------------------------|----------------|
| **Reflective, agentic design** | It is built to *inspect* its own behaviour and discover missing capabilities. | Reduces hallucinations and “unknown‑to‑you” failures. |
| **Structured Markdown vault** | Knowledge lives in named pages that can link, be edited, linted, and graphed. | Treats documents as a living knowledge graph instead of disposable chunks. |
| **Side‑car notes & graph‑aware search** | Notes add extra context and help surface hidden links. | Improves retrieval quality and uncovers implicit relationships. |
| **Runtime state exposure** | The LLM can ask for its own config, usage, token counts, and history. | Gives the agent a working memory about *how* it operates, not just *what* it knows. |
| **Agentic ask flow** | The LLM can *choose* to call tools (search, read page, list links, etc.) before giving an answer. | Enables a disciplined “observe → identify weakness → add function” loop. |
| **Safe, bounded evolution** | New functions are added only after they are documented, tested, and recorded. | Prevents un‑controlled self‑mutation while still allowing continuous improvement. |

In short, it is **not** a “chat‑with‑documents” system; it is a *working memory layer* that an agent can interrogate, repair, and extend.

---

**What the LLM‑Wiki MCP consists of**

The core components (as listed in Chapter 1 of the source “Source – BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS”) are:

1. **Markdown wiki vault** – the durable source of truth; pages can be linked and edited.
2. **Search / index layer** – a lightweight SQLite FTS engine that powers full‑text and graph‑aware queries.
3. **Command‑line interface** – allows manual exploration and maintenance (list pages, read page, etc.).
4. **MCP (Model‑Command‑Pipe) tool surface** – a set of safe, read‑only tools that the LLM can invoke.
5. **Ollama‑backed local LLM synthesis** – the engine that generates responses.
6. **Self‑access tools** – expose config, usage metrics, token counts, runtime state, and history.
7. **AI side‑car notes** – augment search with AI‑generated context and link discovery.
8. **Agentic ask flow** – orchestrates tool calls before synthesis, supporting a reflective loop.

These parts together create a system that can *reflect* on its knowledge, *repair* itself, and *extend* its own capabilities in a controlled, documented manner.
```

---

## Key themes demonstrated

### 1. Local-first knowledge systems

The examples repeatedly emphasise:
- Markdown as source of truth;
- local Ollama-hosted models;
- SQLite indexing;
- provenance-aware ingestion;
- Git-friendly workflows.

This positions the project as a durable local knowledge system rather than a disposable cloud chat interface.

---

### 2. Beyond ordinary RAG

The conversations explain a core architectural shift:

```text
documents -> chunks -> retrieval -> prompt -> answer
```

becomes:

```text
documents -> maintained wiki -> graph + notes + provenance -> agentic tools -> grounded answers
```

This is one of the defining conceptual contributions of the project.

---

### 3. Agentic reflective workflows

The examples demonstrate:
- tool-calling ask flows;
- runtime introspection;
- recursive retrieval;
- note generation;
- graph-aware reasoning;
- self-description from runtime evidence.

The system acts less like a one-shot chatbot and more like a maintained reflective substrate.

---

### 4. Karpathy influence

The examples correctly position the project as:
- inspired by Andrej Karpathy’s LLM Wiki concept;
- extended into a full MCP and CLI ecosystem;
- expanded with provenance, runtime introspection, notes, graph traversal, and recursive ask behaviour.

---

## Why these examples matter

These examples are important because they demonstrate:
- that the CLI is usable interactively;
- that the system can answer architectural questions about itself;
- that the MCP can expose structured reasoning workflows;
- that the wiki can function as maintained context rather than transient retrieval.

They also serve as excellent:
- README material;
- GitHub examples;
- research examples;
- onboarding demonstrations;
- blog excerpts;
- conference/demo material.

---

## Suggested future improvements

The examples also highlight future opportunities:

- stronger citations in final answers;
- more explicit provenance reporting;
- better answer retry strategies;
- richer graph traversal;
- configurable synthesis depth;
- improved runtime diagnostics;
- optional structured answer schemas;
- automatic source quoting.

These improvements align naturally with the reflective design philosophy of the LLM Wiki MCP.
