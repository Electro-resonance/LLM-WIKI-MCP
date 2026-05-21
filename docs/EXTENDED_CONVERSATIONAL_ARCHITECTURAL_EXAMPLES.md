# Extended Conversational and Architectural Examples

This document extends the earlier conversational examples with additional real-world CLI interactions and generated article outputs from the LLM Wiki MCP system.

The examples demonstrate:
- self-description;
- origin stories;
- recursive ask workflows;
- architectural explanation;
- MCP reasoning;
- user onboarding;
- provenance-aware ingestion;
- article generation from maintained context.

Sensitive local references, internal workspace names, local paths, and IP addresses have been sanitised for public release.

---

# Additional Captured Sessions

## Session A

```text
python3 llm_wiki_cli.py

 _     _     __  __
| |   | |   |  \/  |
| |   | |   | |\/| |
| |___| |___| |  | |
|_____|_____|_|  |_|

 __        __ ___  _  __ ___
 \ \      / /|_ _|| |/ /|_ _|
  \ \ /\ / /  | | | ' /  | |
   \ V  V /   | | | . \  | |
    \_/\_/   |___||_|\_\|___|

        L L M   W I K I
        maintained context, not disposable chunks

Type: help, search <query>, retrieve <query>, ask <question>, self <question>, articles <query>, context <query>, read <title>, stats, lint, repair, mermaid [file.md], map <title>, json on, exit
wiki> /ingest .
Ingest scan: <project-root>
Files read: 124
New: 62 | Updated: 0 | Already ingested: 0 | Errors: 0
Pages written/updated: 62
Approx document words: 24240
Approx document characters: 172832
wiki> /ask explain what you are please and the origins of the project!
Ask mode: agentic
User request: explain what you are please and the origins of the project!

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
**What the LLM Wiki MCP is**

The LLM Wiki MCP is a *local‑first* knowledge engine that lets an LLM read, write, lint, graph and export a durable Markdown wiki.
* A single Python server exposes a set of safe, read‑only tools that an LLM agent can call via MCP.
* Markdown files are the source of truth; SQLite Full‑Text Search indexes them and builds a graph of pages, notes and provenance.
* The LLM is invoked through the `wiki_ask_*` tools, and it can query its own runtime state, history, token usage and configuration.
* The system is deliberately designed for **agentic** use: an LLM can inspect its own weaknesses, add new commands, and keep the wiki up‑to‑date.

> “A useful AI system should not merely retrieve information; it should understand, organise, connect, critique, extend, and improve its own knowledge structures over time.” – *BOOK, Preface*【Source - BOOK】.

> “The LLM Wiki MCP turns useful conclusions, definitions, decisions, contradictions, and source notes into maintained Markdown pages. The wiki becomes a living source of truth rather than a pile of transient chunks.” – *README*【Source - README】.

**Origins of the project**

1. **Frustration with ordinary Retrieval‑Augmented Generation (RAG)**
   Traditional RAG pipelines retrieve a handful of chunks, feed them into the LLM, and output an answer. The chunks are disposable, opaque, and can become stale. The project started as a response to this brittleness.
   > “Traditional RAG repeatedly retrieves fragments. An LLM Wiki turns useful conclusions, definitions, decisions, contradictions, and source notes into maintained Markdown pages.” – *README*【Source - README】.

2. **Inspiration from Andrej Karpathy’s LLM Wiki pattern**
   The idea was seeded by Karpathy’s “LLM Wiki” concept, which showed that an LLM could be given a persistent, searchable memory by wrapping it around a wiki‑style repository instead of a flat chunk set.
   > “The LLM Wiki MCP is a local‑first, Markdown‑based, MCP‑accessible knowledge engine inspired by the LLM Wiki pattern.” – *BOOK_DEVELOPMENT_CHRONICLE*【Source - docs - BOOK_DEVELOPMENT_CHRONICLE】.

3. **Evolution into a reflective, self‑extending system**
   The initial prototype grew into a full system that stores its own documentation, exposes its runtime state, and can add new tools to patch gaps it discovers. It became an experiment in *reflective software* that can introspect, identify weaknesses, and extend itself.
   > “This book introduces the LLM Wiki MCP as more than a retrieval tool. It is a small but meaningful experiment in reflective software: a system that stores its own documentation, exposes its own runtime state, asks questions about itself, identifies missing capabilities, and can be extended with new functions that reduce those gaps.” – *BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS*【Source - BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS】.

**Summary**

The LLM Wiki MCP is a locally run, Markdown‑based knowledge base that an LLM can query and modify through MCP tools. It was born out of a need to move beyond RAG, inspired by Karpathy’s LLM Wiki idea, and designed to be reflective, provenance‑aware, and self‑improving. The project’s journey and architectural choices are detailed in the *BOOK_DEVELOPMENT_CHRONICLE* and related documentation.
wiki> /ask write a medium article on what you are and your origins. Write both regarding technical architecture and also as a primer for the new potential user!
Ask mode: agentic
User request: write a medium article on what you are and your origins. Write both regarding technical architecture and also as a primer for the new potential user!

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
**Title:  The LLM Wiki MCP – A Local‑First Knowledge Engine for Humans and LLMs**

---

## 1.  What the LLM Wiki MCP Is

The LLM Wiki MCP (Multimodal Knowledge Processor) is a **local‑first** system that turns any collection of documents into a *durable, searchable, graph‑aware Markdown wiki* that can be queried by both people and language‑model agents.
> “LLM Wiki MCP is a local‑first knowledge system that turns documents into a durable, searchable, graph‑aware Markdown wiki.” – *PRODUCT_ARCHITECTURE_OVERVIEW*

At its heart the system stores every page in Markdown, keeps a SQLite FTS index for fast local search, and records provenance data (path, hash, timestamps) so that re‑ingesting a folder only updates changed files. It exposes two complementary interfaces:

| Interface | Primary user | What it does |
|-----------|--------------|--------------|
| **CLI** | Humans & operators | Ingest, lint, inspect stats, view provenance, run queries |
| **MCP tool layer** | LLM agents | Structured search, read pages, retrieve context, manage notes, call the LLM locally |

The MCP is the “agent‑side” of the system – it is the set of tools an LLM can call to reason over the wiki.

---

## 2.  Origins – From Karpathy’s LLM Wiki Pattern

The idea came from Andrej Karpathy’s **LLM Wiki** post, which argued that an LLM should help *build and maintain* a knowledge base rather than merely pull out chunks. 
> “A useful AI knowledge system should not only retrieve documents. It should maintain knowledge, inspect itself, learn from its own operation, and improve the way it answers.” – *BOOK_DEVELOPMENT_CHRONICLE*

The development chronicle shows a clear evolution: early attempts at simple retrieval‑augmented generation (RAG) were replaced by a *maintained wiki* that tracks provenance, links, and side‑car notes. Each iteration added a new command, a new note‑type, or a new graph view until the system could self‑question and extend its own tool surface.

---

## 3.  Technical Architecture in Detail

1. **Markdown Vault** – The source of truth; every article is a Markdown file, human‑editable, Git‑friendly, and diff‑able.

2. **SQLite FTS (Full‑Text Search)** – Provides a fast local index without a remote vector store.

3. **Provenance DB** – Records file path, SHA‑256, size, timestamp, and link to the corresponding wiki page, enabling incremental ingestion.

4. **Notes System** – AI side‑car notes add context, summaries, and link hints that the LLM can consult before answering.

5. **Graph Layer** – Every page can link to others; a Mermaid graph can be exported for visual inspection.

6. **MCP Tool Layer** – Exposes commands such as `wiki_search`, `wiki_read_page`, `wiki_retrieve_articles`, and `wiki_ingest_directory` to the LLM via the MCP protocol.

7. **Agentic Ask Pipeline** –
   ```text
   query → structured wiki search → sidecar notes → candidate links → runtime state → tool traces → LLM synthesis → maintenance suggestions
   ```
   This recursive loop allows the LLM to *self‑question*, e.g. “What are you?” or “Which commands exist?” – see the *BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS* self‑questioning tool.

8. **Local Ollama Model** – The system ships with an Ollama backend (e.g., `llama3.2:3b`) so all synthesis stays on‑premises.

9. **CLI UX** – Interactive shell `wiki>` with auto‑completion, history, and Ctrl‑R search. Ingest runs summarise by default (`/ingest ./docs`) and can be verbose on `--verbose`.

The full architectural diagram can be found in *PRODUCT_ARCHITECTURE_OVERVIEW* (see the layered diagram block).

---

## 4.  A Quick Primer for New Users

### 4.1  Install & Run the Local Server

```bash
# Clone the repo and install
git clone https://github.com/Electro-resonance/LLM-WIKI-MCP
cd llm_wiki_mcp
pip install -e .[mcp]   # includes MCP dependencies

# Start the MCP server
python llm_wiki_mcp_server.py server --vault ./wiki_vault
```

### 4.2  Start the Interactive CLI

```bash
python llm_wiki_cli.py --vault ./wiki_vault
```

You’ll see the `wiki>` prompt. Try the following:

| Command | What it does |
|---------|--------------|
| `help` | Show available commands |
| `/ingest ./docs` | Scan a folder or single file, index new files, skip unchanged ones |
| `ask “What are you?”` | The LLM will read the wiki and answer |
| `stats` | View ingest stats and file counts |
| `lint` | Find broken links or orphan pages |
| `notes-all` | Show AI side‑car notes for all pages |

### 4.3  Import Documents

Use the `/ingest` command or the `llm-wiki ingest-dir` CLI wrapper; both accept either a directory or one supported file. The system will record provenance so re‑ingesting only updates changed files.

### 4.4  Query with the LLM

You can ask the system in natural language:

```text
wiki> /ask “Explain the architecture of the LLM Wiki MCP.”
```

The LLM will search the wiki, consult notes, and produce a grounded answer. If the answer is incomplete, the recursive pipeline will retry with more context.

### 4.5  Use the MCP Layer as an Agent

If you’re building an LLM agent, add the MCP server to your agent configuration (e.g., in a Claude Desktop config). The agent can call tools like `wiki_search` or `wiki_read_page` and then synthesize its own response.

---

## 5.  Why This Matters – The Benefits

| Benefit | Why It Matters |
|---------|----------------|
| **Durable Knowledge** | Markdown pages persist across reboots; they can be version‑controlled in Git. |
| **Local‑First & Secure** | All data stays on your machine; no external vector store or API keys. |
| **Self‑Improving** | The system can *self‑question* and add new commands when gaps are detected (*BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS*). |
| **Transparent** | Provenance logs, graph views, and linting make the knowledge base auditable. |
| **Agent‑Ready** | The MCP surface allows LLMs to treat the wiki like a structured API, enabling complex reasoning workflows. |

---

## 6.  Getting Started in a Few Minutes

1. **Clone & install** as shown above.
2. **Create a wiki vault** (`./wiki_vault`) and a `docs/` folder with some Markdown.
3. **Run `python llm_wiki_cli.py --vault ./wiki_vault`** and type `/ingest ./docs`.
4. **Ask “What is the LLM Wiki MCP?”** – you’ll get a concise, markdown‑ready explanation.
5. **Explore**: `wiki> /stats`, `wiki> /lint`, `wiki> /mermaid --output graph.md` to generate a Mermaid graph.

---

## 7.  Closing Thoughts

The LLM Wiki MCP is more than a RAG wrapper; it’s a *living knowledge substrate* that sits on top of plain Markdown and SQLite. Inspired by Karpathy’s vision and built in a local‑first, agent‑centric way, it offers a path toward truly maintainable, introspective, and collaborative AI systems.

Whether you’re a researcher wanting a private knowledge base, a devops engineer looking for a reproducible documentation pipeline, or an AI engineer building a self‑reflective agent, the LLM Wiki MCP gives you the tools to keep your knowledge *alive* and *under your control*.

*Happy querying!*

---

**Sources**
- *BOOK_DEVELOPMENT_CHRONICLE* – development narrative and core architecture.
- *CLI_DEMO_TUTORIAL* – interactive shell, ingest behaviour, and query examples.
- *PRODUCT_ARCHITECTURE_OVERVIEW* – executive summary, interface diagram, and technical layers.
- *RESEARCH_BLOG_ARTICLE_FROM_DEMO* – comparison to classic RAG and local‑first rationale.
- *README* – installation, CLI commands, and tool list.
- *BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS* – self‑questioning and self‑improving design.
wiki>
```

---

## Session B

```text
 python3 llm_wiki_cli.py

 _     _     __  __
| |   | |   |  \/  |
| |   | |   | |\/| |
| |___| |___| |  | |
|_____|_____|_|  |_|

 __        __ ___  _  __ ___
 \ \      / /|_ _|| |/ /|_ _|
  \ \ /\ / /  | | | ' /  | |
   \ V  V /   | | | . \  | |
    \_/\_/   |___||_|\_\|___|

        L L M   W I K I
        maintained context, not disposable chunks

Type: help, search <query>, retrieve <query>, ask <question>, self <question>, articles <query>, context <query>, read <title>, stats, lint, repair, mermaid [file.md], map <title>, json on, exit
wiki> /ingest .
Ingest scan: <project-root>
Files read: 124
New: 62 | Updated: 0 | Already ingested: 0 | Errors: 0
Pages written/updated: 62
Approx document words: 24240
Approx document characters: 172832
wiki> /ask explain what you are please and the origins of the project!
Ask mode: agentic
User request: explain what you are please and the origins of the project!

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
**What the LLM Wiki MCP is**

The LLM Wiki MCP is a *local‑first* knowledge engine that lets an LLM read, write, lint, graph and export a durable Markdown wiki.
* A single Python server exposes a set of safe, read‑only tools that an LLM agent can call via MCP.
* Markdown files are the source of truth; SQLite Full‑Text Search indexes them and builds a graph of pages, notes and provenance.
* The LLM is invoked through the `wiki_ask_*` tools, and it can query its own runtime state, history, token usage and configuration.
* The system is deliberately designed for **agentic** use: an LLM can inspect its own weaknesses, add new commands, and keep the wiki up‑to‑date.

> “A useful AI system should not merely retrieve information; it should understand, organise, connect, critique, extend, and improve its own knowledge structures over time.” – *BOOK, Preface*【Source - BOOK】.

> “The LLM Wiki MCP turns useful conclusions, definitions, decisions, contradictions, and source notes into maintained Markdown pages. The wiki becomes a living source of truth rather than a pile of transient chunks.” – *README*【Source - README】.

**Origins of the project**

1. **Frustration with ordinary Retrieval‑Augmented Generation (RAG)**
   Traditional RAG pipelines retrieve a handful of chunks, feed them into the LLM, and output an answer. The chunks are disposable, opaque, and can become stale. The project started as a response to this brittleness.
   > “Traditional RAG repeatedly retrieves fragments. An LLM Wiki turns useful conclusions, definitions, decisions, contradictions, and source notes into maintained Markdown pages.” – *README*【Source - README】.

2. **Inspiration from Andrej Karpathy’s LLM Wiki pattern**
   The idea was seeded by Karpathy’s “LLM Wiki” concept, which showed that an LLM could be given a persistent, searchable memory by wrapping it around a wiki‑style repository instead of a flat chunk set.
   > “The LLM Wiki MCP is a local‑first, Markdown‑based, MCP‑accessible knowledge engine inspired by the LLM Wiki pattern.” – *BOOK_DEVELOPMENT_CHRONICLE*【Source - docs - BOOK_DEVELOPMENT_CHRONICLE】.

3. **Evolution into a reflective, self‑extending system**
   The initial prototype grew into a full system that stores its own documentation, exposes its runtime state, and can add new tools to patch gaps it discovers. It became an experiment in *reflective software* that can introspect, identify weaknesses, and extend itself.
   > “This book introduces the LLM Wiki MCP as more than a retrieval tool. It is a small but meaningful experiment in reflective software: a system that stores its own documentation, exposes its own runtime state, asks questions about itself, identifies missing capabilities, and can be extended with new functions that reduce those gaps.” – *BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS*【Source - BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS】.

**Summary**

The LLM Wiki MCP is a locally run, Markdown‑based knowledge base that an LLM can query and modify through MCP tools. It was born out of a need to move beyond RAG, inspired by Karpathy’s LLM Wiki idea, and designed to be reflective, provenance‑aware, and self‑improving. The project’s journey and architectural choices are detailed in the *BOOK_DEVELOPMENT_CHRONICLE* and related documentation.
wiki> /ask write a medium article on what you are and your origins. Write both regarding technical architecture and also as a primer for the new potential user!
Ask mode: agentic
User request: write a medium article on what you are and your origins. Write both regarding technical architecture and also as a primer for the new potential user!

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
**Title:  The LLM Wiki MCP – A Local‑First Knowledge Engine for Humans and LLMs**

---

## 1.  What the LLM Wiki MCP Is

The LLM Wiki MCP (Multimodal Knowledge Processor) is a **local‑first** system that turns any collection of documents into a *durable, searchable, graph‑aware Markdown wiki* that can be queried by both people and language‑model agents.
> “LLM Wiki MCP is a local‑first knowledge system that turns documents into a durable, searchable, graph‑aware Markdown wiki.” – *PRODUCT_ARCHITECTURE_OVERVIEW*

At its heart the system stores every page in Markdown, keeps a SQLite FTS index for fast local search, and records provenance data (path, hash, timestamps) so that re‑ingesting a folder only updates changed files. It exposes two complementary interfaces:

| Interface | Primary user | What it does |
|-----------|--------------|--------------|
| **CLI** | Humans & operators | Ingest, lint, inspect stats, view provenance, run queries |
| **MCP tool layer** | LLM agents | Structured search, read pages, retrieve context, manage notes, call the LLM locally |

The MCP is the “agent‑side” of the system – it is the set of tools an LLM can call to reason over the wiki.

---

## 2.  Origins – From Karpathy’s LLM Wiki Pattern

The idea came from Andrej Karpathy’s **LLM Wiki** post, which argued that an LLM should help *build and maintain* a knowledge base rather than merely pull out chunks. 
> “A useful AI knowledge system should not only retrieve documents. It should maintain knowledge, inspect itself, learn from its own operation, and improve the way it answers.” – *BOOK_DEVELOPMENT_CHRONICLE*

The development chronicle shows a clear evolution: early attempts at simple retrieval‑augmented generation (RAG) were replaced by a *maintained wiki* that tracks provenance, links, and side‑car notes. Each iteration added a new command, a new note‑type, or a new graph view until the system could self‑question and extend its own tool surface.

---

## 3.  Technical Architecture in Detail

1. **Markdown Vault** – The source of truth; every article is a Markdown file, human‑editable, Git‑friendly, and diff‑able.

2. **SQLite FTS (Full‑Text Search)** – Provides a fast local index without a remote vector store.

3. **Provenance DB** – Records file path, SHA‑256, size, timestamp, and link to the corresponding wiki page, enabling incremental ingestion.

4. **Notes System** – AI side‑car notes add context, summaries, and link hints that the LLM can consult before answering.

5. **Graph Layer** – Every page can link to others; a Mermaid graph can be exported for visual inspection.

6. **MCP Tool Layer** – Exposes commands such as `wiki_search`, `wiki_read_page`, `wiki_retrieve_articles`, and `wiki_ingest_directory` to the LLM via the MCP protocol.

7. **Agentic Ask Pipeline** –
   ```text
   query → structured wiki search → sidecar notes → candidate links → runtime state → tool traces → LLM synthesis → maintenance suggestions
   ```
   This recursive loop allows the LLM to *self‑question*, e.g. “What are you?” or “Which commands exist?” – see the *BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS* self‑questioning tool.

8. **Local Ollama Model** – The system ships with an Ollama backend (e.g., `llama3.2:3b`) so all synthesis stays on‑premises.

9. **CLI UX** – Interactive shell `wiki>` with auto‑completion, history, and Ctrl‑R search. Ingest runs summarise by default (`/ingest ./docs`) and can be verbose on `--verbose`.

The full architectural diagram can be found in *PRODUCT_ARCHITECTURE_OVERVIEW* (see the layered diagram block).

---

## 4.  A Quick Primer for New Users

### 4.1  Install & Run the Local Server

```bash
# Clone the repo and install
git clone https://github.com/Electro-resonance/LLM-WIKI-MCP
cd llm_wiki_mcp
pip install -e .[mcp]   # includes MCP dependencies

# Start the MCP server
python llm_wiki_mcp_server.py server --vault ./wiki_vault
```

### 4.2  Start the Interactive CLI

```bash
python llm_wiki_cli.py --vault ./wiki_vault
```

You’ll see the `wiki>` prompt. Try the following:

| Command | What it does |
|---------|--------------|
| `help` | Show available commands |
| `/ingest ./docs` | Scan a folder or single file, index new files, skip unchanged ones |
| `ask “What are you?”` | The LLM will read the wiki and answer |
| `stats` | View ingest stats and file counts |
| `lint` | Find broken links or orphan pages |
| `notes-all` | Show AI side‑car notes for all pages |

### 4.3  Import Documents

Use the `/ingest` command or the `llm-wiki ingest-dir` CLI wrapper; both accept either a directory or one supported file. The system will record provenance so re‑ingesting only updates changed files.

### 4.4  Query with the LLM

You can ask the system in natural language:

```text
wiki> /ask “Explain the architecture of the LLM Wiki MCP.”
```

The LLM will search the wiki, consult notes, and produce a grounded answer. If the answer is incomplete, the recursive pipeline will retry with more context.

### 4.5  Use the MCP Layer as an Agent

If you’re building an LLM agent, add the MCP server to your agent configuration (e.g., in a Claude Desktop config). The agent can call tools like `wiki_search` or `wiki_read_page` and then synthesize its own response.

---

## 5.  Why This Matters – The Benefits

| Benefit | Why It Matters |
|---------|----------------|
| **Durable Knowledge** | Markdown pages persist across reboots; they can be version‑controlled in Git. |
| **Local‑First & Secure** | All data stays on your machine; no external vector store or API keys. |
| **Self‑Improving** | The system can *self‑question* and add new commands when gaps are detected (*BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS*). |
| **Transparent** | Provenance logs, graph views, and linting make the knowledge base auditable. |
| **Agent‑Ready** | The MCP surface allows LLMs to treat the wiki like a structured API, enabling complex reasoning workflows. |

---

## 6.  Getting Started in a Few Minutes

1. **Clone & install** as shown above.
2. **Create a wiki vault** (`./wiki_vault`) and a `docs/` folder with some Markdown.
3. **Run `python llm_wiki_cli.py --vault ./wiki_vault`** and type `/ingest ./docs`.
4. **Ask “What is the LLM Wiki MCP?”** – you’ll get a concise, markdown‑ready explanation.
5. **Explore**: `wiki> /stats`, `wiki> /lint`, `wiki> /mermaid --output graph.md` to generate a Mermaid graph.

---

## 7.  Closing Thoughts

The LLM Wiki MCP is more than a RAG wrapper; it’s a *living knowledge substrate* that sits on top of plain Markdown and SQLite. Inspired by Karpathy’s vision and built in a local‑first, agent‑centric way, it offers a path toward truly maintainable, introspective, and collaborative AI systems.

Whether you’re a researcher wanting a private knowledge base, a devops engineer looking for a reproducible documentation pipeline, or an AI engineer building a self‑reflective agent, the LLM Wiki MCP gives you the tools to keep your knowledge *alive* and *under your control*.

*Happy querying!*

---

**Sources**
- *BOOK_DEVELOPMENT_CHRONICLE* – development narrative and core architecture.
- *CLI_DEMO_TUTORIAL* – interactive shell, ingest behaviour, and query examples.
- *PRODUCT_ARCHITECTURE_OVERVIEW* – executive summary, interface diagram, and technical layers.
- *RESEARCH_BLOG_ARTICLE_FROM_DEMO* – comparison to classic RAG and local‑first rationale.
- *README* – installation, CLI commands, and tool list.
- *BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS* – self‑questioning and self‑improving design.
wiki>
```

---

# Observations from the Captured Sessions

## 1. The system behaves like a maintained knowledge substrate

The interactions consistently show the system:
- retrieving maintained wiki pages;
- following notes and linked concepts;
- grounding responses in stored Markdown documentation;
- producing architecture-aware answers.

This is significantly different from disposable chunk-based retrieval systems.

---

## 2. The MCP layer enables structured reasoning

The examples repeatedly show:

```text
Tools called:
- wiki_search_with_notes
- wiki_capabilities
- wiki_read_page
```

This highlights one of the key design goals:
the LLM should not hallucinate its runtime state, but instead retrieve it through structured tools.

---

## 3. Recursive ask behaviour is visible

The interactions demonstrate:
- retrieval;
- synthesis;
- reflective retries;
- runtime inspection;
- architecture explanation;
- grounding against stored docs.

This is effectively a recursive reasoning loop:

```text
question
 -> search
 -> read
 -> notes
 -> runtime state
 -> synthesis
 -> refinement
```

---

## 4. Why this matters for future agent systems

The sessions suggest a broader future direction:

```text
LLM + maintained wiki + tools + provenance + notes + recursive reasoning
```

Instead of isolated prompts, the system accumulates and maintains structured operational memory over time.

---

# Public Release Sanitisation Notes

For GitHub/public release preparation:
- local workspace names were removed;
- internal paths were replaced with placeholders;
- local Ollama IPs were anonymised;
- machine-specific identifiers were removed.

This keeps the docs suitable for public distribution while preserving the technical concepts and workflows.

---

# Recommended Follow-on Improvements

The captured sessions also reveal future opportunities:

- stronger inline citations;
- configurable answer depth;
- graph-ranked retrieval;
- retry-aware synthesis;
- adaptive note generation;
- richer provenance inspection;
- structured answer schemas;
- automatic architecture summaries.

These fit naturally with the reflective design philosophy of the LLM Wiki MCP.
