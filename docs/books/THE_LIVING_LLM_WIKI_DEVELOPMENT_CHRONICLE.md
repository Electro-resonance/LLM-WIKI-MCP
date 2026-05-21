# The Living LLM Wiki Development Chronicle

## From LLM Wiki Pattern to Reflective, Provenance-Aware MCP Knowledge System

---

# Preface

This book records the practical development journey of the LLM Wiki MCP system: a local-first, Markdown-based, MCP-accessible knowledge engine inspired by the LLM Wiki pattern.

The source material for this book is the project dialogue and terminal transcript captured during development. It includes design decisions, failures, fixes, and the gradual shaping of the tool into a more reliable, agent-facing knowledge system.

The project’s central idea is simple but powerful:

> A useful AI knowledge system should not only retrieve documents. It should maintain knowledge, inspect itself, learn from its own operation, and improve the way it answers.

---

# Chapter 1 — Why This Project Exists

The project began from dissatisfaction with ordinary retrieval-augmented generation.

Traditional RAG often behaves like this:

```text
documents -> chunks -> retrieval -> prompt -> answer
```

The LLM Wiki MCP instead aims for:

```text
documents -> maintained wiki -> graph + notes + provenance -> agentic tools -> grounded answers
```

The difference is not cosmetic. A wiki is a durable knowledge artefact. It can be linted, linked, read, edited, versioned, searched, cited, and extended. That makes it a stronger substrate for long-lived agentic work.

The project is therefore not just an MCP server and not just a CLI. It is a living knowledge substrate for LLM agents.

---

# Chapter 2 — The Local-First Principle

The system is intentionally local-first.

It runs in a local project folder, uses Markdown files as its source of truth, uses SQLite for indexing and provenance, and can call a local Ollama model.

This matters for:

- data sovereignty;
- auditability;
- reproducibility;
- low-cost experimentation;
- local/private research;
- Git-friendly workflows;
- agent access to stable tools.

A recurring WSL/Ollama configuration is:

```text
/config host http://localhost:11434
```

This reflects the pattern where the CLI runs inside WSL and the Ollama service is reachable via the Windows host bridge.

---

# Chapter 3 — From Versioned Packages to Stable Imports

One of the most important engineering lessons was that the Python package should not include the release version in its import path.

Earlier packages used imports such as:

```python
from llm_wiki_mcp.cli import main
```

This caused repeated failures when the extracted folder, package directory, and launcher script drifted out of alignment.

The improved pattern is:

```python
from llm_wiki_mcp.cli import main
```

The release ZIP can still be versioned, but the Python import path should remain stable:

```text
src/llm_wiki_mcp/
```

This is the correct design for a reusable Python package.

---

# Chapter 4 — The CLI as an Operator Interface

The CLI is for human operation.

It should allow a user to:

- start the shell with `python3 llm_wiki_cli.py`;
- configure Ollama;
- ingest directories or single files;
- query the wiki;
- inspect stats;
- run lint and repair;
- generate notes;
- view provenance;
- consolidate documentation;
- test retrieval quality.

The CLI should be helpful without being noisy.

A key improvement requested during development was that ingest should not print a huge list of every file by default. The default should be a compact summary. Verbose output should only happen when explicitly requested.

The improved ingest behaviour is:

```text
/ingest ./docs
/ingest ./notes/idea.rtf
```

prints summary statistics only.

```text
/ingest ./docs --verbose
/ingest ./notes/idea.rtf
```

prints the detailed file list.

This keeps the CLI useful for daily operation.

---

# Chapter 5 — The MCP as an Agent Interface

The MCP is not the CLI.

The CLI is for humans. The MCP is for agents.

This distinction led to a rewrite of the agent-facing documents:

- `AGENTS.md`
- `CLAUDE.md`
- `SKILLS.md`

These files should teach LLM agents how to use the MCP as a tool substrate, not merely how to run shell commands.

Agent-facing guidance focuses on:

- retrieving before answering;
- reading full pages rather than relying on snippets;
- using notes and graph links;
- widening scope when evidence is weak;
- retrying synthesis when answers are blank;
- distinguishing grounded evidence from inference;
- using runtime introspection tools;
- avoiding generic hallucinated answers.

The CLI guide was moved into a separate human-facing `CLI_GUIDE.md`.

---

# Chapter 6 — The Ask Pipeline

The ask pipeline evolved through many iterations.

The desired behaviour is:

1. interpret the user’s intent;
2. gather runtime/tool evidence;
3. search the wiki;
4. read relevant full pages;
5. inspect notes and linked pages;
6. call the LLM;
7. if blank, expand evidence and call again;
8. if still blank, produce an extractive fallback;
9. never simply say “No answer produced”.

This led to the evidence-first and second-pass answer strategy.

If the LLM synthesis returns blank, the system should:

- keep the original question;
- inspect first-pass search hits;
- retrieve the next likely pages;
- include notes and candidate links;
- rebuild the evidence pack;
- call the LLM again;
- only then fall back.

The project therefore moved from single-pass retrieval toward iterative answer construction.

---

# Chapter 7 — Basic Questions Must Always Work

A repeated issue was that the system sometimes failed to answer basic questions such as:

```text
/ask what are you
/ask tell me what you are
/ask what can you do
```

These questions should not depend on a perfect wiki hit or even a successful LLM call.

They can be answered from runtime evidence:

- capabilities;
- tool catalogue;
- command map;
- ask history;
- configuration;
- provenance status.

This led to the direct runtime-answer fallback.

For example, the system can now answer that it is:

- a local Markdown wiki agent;
- an MCP-accessible knowledge tool;
- a CLI-accessible operator tool;
- backed by SQLite FTS;
- able to use Ollama;
- able to inspect its own runtime and tool catalogue;
- able to ingest documents and track provenance.

---

# Chapter 8 — Ingest Provenance

Document ingestion became a major reliability focus.

The system now records provenance information such as:

- full file path;
- directory path;
- filename;
- SHA256 hash;
- modification timestamp;
- linked wiki page;
- version events.

This supports correct repeated ingestion:

```text
first ingest -> new files processed
second ingest -> unchanged files skipped
changed file -> updated file listed
same filename in different directory -> tracked separately
```

The user specifically requested that a second ingest should not reprocess everything, and should instead say how many files were already ingested.

The improved behaviour is:

```text
New files: 0 | Updated files: 0 | Already ingested: 47 | Errors: 0
47 files were already ingested and unchanged.
```

---

# Chapter 9 — Compact Ingest Output

The transcript showed that ingesting a directory printed a very long list of files.

That is useful for debugging but poor as a default user experience.

The improved behaviour is:

## Default

```text
Ingest scan: ./docs
Files read: 47
New: 47 | Updated: 0 | Already ingested: 0 | Errors: 0
Pages written: 47
Estimated words: ...
Estimated characters: ...
```

## Verbose

```text
/ingest ./docs --verbose
```

prints each file, hash, source path, and wiki title.

This is a cleaner operator experience.

---

# Chapter 10 — Documentation Consolidation

The docs folder grew too large during rapid development.

Many small files were useful while developing but became overwhelming for users.

The project therefore moved toward fewer category files:

- overview and architecture;
- user guide;
- functions and tools;
- agentic ask and memory;
- notes, graphs, and maintenance;
- references and research;
- development history;
- answer quality.

The important principle is:

> Preserve the content, but reduce navigational friction.

For public GitHub readiness, documentation should be clear, consolidated, and easy to browse.

---

# Chapter 11 — Agent Answer Quality

The transcript showed several answer-quality problems:

- blank LLM synthesis;
- generic startup-like pitch answers;
- answers that ignored retrieved evidence;
- answers that failed to distinguish evidence from inference;
- answers that did not use recent discussion context.

The improved guidance is that answers should clearly separate:

- grounded evidence;
- inferred interpretation;
- speculative extrapolation;
- missing information.

When evidence exists, the system should use it. When evidence is partial, the system should still answer carefully. When evidence is missing, it should say what is missing and use runtime context where appropriate.

---

# Chapter 12 — Writing to Karpathy

One important use case was writing a post to Andrej Karpathy or to a GitHub discussion about the project.

The first generated answer had a problem: it hallucinated a release version and test status.

The correct behaviour should be:

- credit Karpathy’s original LLM Wiki gist;
- accurately describe what this implementation does;
- avoid invented claims such as “21/21 tests passed” unless verified;
- say that the system is local-first, Python-based, MCP-accessible, and Markdown/SQLite-backed;
- mention provenance, notes, graph tools, and self-questioning;
- explain that it evolved through practical iteration.

A good external post should be modest, accurate, and appreciative.

---

# Chapter 13 — Self-Questioning and Runtime Introspection

The project’s most distinctive idea is that tools can become visible to themselves.

The system can inspect:

- its configuration;
- its capabilities;
- its tools;
- its runtime journal;
- token usage;
- ask history;
- provenance;
- notes coverage;
- documentation consistency.

This allows the LLM Wiki MCP to answer questions about itself from evidence rather than from vague self-description.

Self-questioning turns operational state into knowledge.

---

# Chapter 14 — The System as a Proto Self-Extending Knowledge Ecology

The LLM Wiki MCP is not AGI.

But it points toward an architectural pattern where systems can:

- identify missing capabilities;
- document gaps;
- propose tool extensions;
- update documentation;
- improve retrieval;
- refine prompts;
- reflect on failures;
- track provenance;
- preserve memory.

This is a step toward self-extending agentic systems, where the intelligence is not only in the LLM but in the loop between:

```text
model + tools + memory + notes + graph + provenance + human steering
```

---

# Chapter 15 — Lessons Learned

The development journey suggests several practical lessons:

1. Stable package names matter.
2. CLI and MCP documentation should be separated.
3. Ingest should be quiet by default.
4. Verbose output should be opt-in.
5. SQLite indexes should be rebuilt locally, not shipped as brittle state.
6. Basic questions should answer from runtime evidence.
7. Search snippets are not enough; full page reads matter.
8. Blank LLM output should trigger a second retrieval/synthesis pass.
9. Docs should consolidate as the project matures.
10. Agent-facing files should teach MCP usage, not human CLI operation.

---

# Appendix A — Extracted Development Transcript

The following transcript was used as source material for this book. Paths have been sanitised.

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
New files: 47 | Updated files: 0 | Already ingested: 0 | Errors: 0

New files:
- <project-root>/AGENTS.md (411311af064b)
- <project-root>/ARCHITECTURE.md (7ea67461fad8)
- <project-root>/BOOK.md (3d7e206112d1)
- <project-root>/CLAUDE.md (9bba4cfe9bbb)
- <project-root>/CLI_GUIDE.md (be1e8508f7a3)
- <project-root>/FUNCTION_LIST.md (53e57697004c)
- <project-root>/METHODOLOGY.md (bba370dd0c19)
- <project-root>/METHPOLOGY.md (bba370dd0c19)
- <project-root>/README.md (917c7bfb4f3c)
- <project-root>/SKILLS.md (070209278fab)
- <project-root>/docs/01_OVERVIEW_AND_ARCHITECTURE.md (4240f515672d)
- <project-root>/docs/02_USER_GUIDE.md (0ee23f416f7a)
- <project-root>/docs/03_FUNCTIONS_AND_TOOLS.md (f98ef1a6f65f)
- <project-root>/docs/04_AGENTIC_ANSWER_QUALITY.md (a1ae4e1452b4)
- <project-root>/docs/04_AGENTIC_ASK_AND_MEMORY.md (a0ebd29c18c9)
- <project-root>/docs/05_NOTES_GRAPHS_AND_MAINTENANCE.md (d5d0265a32d8)
- <project-root>/docs/06_REFERENCES_AND_RESEARCH.md (96ba1e5514f1)
- <project-root>/docs/07_DEVELOPMENT_HISTORY.md (cbbf1621f7c4)
- <project-root>/docs/BOOK.md (c2b26e7841e6)
- <project-root>/docs/BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS.md (a6c0aac76575)
- <project-root>/docs/FULL_FILENAME_REFERENCES.md (75501cdef549)
- <project-root>/docs/INDEX.md (012b5479ce38)
- <project-root>/docs/SKILLS.md (8d2a19f94ed2)
- <project-root>/docs/SQLITE_SELF_HEALING_INDEX.md (55d5562b2597)
- <project-root>/docs/TEST_REVIEW.md (d8716b5fa6fd)
- <project-root>/docs/TOOL_SELF_QUESTIONING.md (8f10014c5c72)
- <project-root>/docs/TOOL_SELF_QUESTIONING_LONG_CHAPTER.md (1c555ff4bd2e)
- <project-root>/docs/V42_LAUNCHER_PACKAGE_FIX.md (2085718af8ec)
- <project-root>/docs/VERSIONLESS_LAUNCHER_FIX.md (eed281fc781a)
- <project-root>/docs/VERSIONLESS_PACKAGE_IMPORTS.md (fd9cff281ec4)
- <project-root>/examples/raw/example_source.md (f1fbb5dbf1c1)
- <project-root>/tmp_ingest_test_docs/sample.md (1339156dc320)
- <project-root>/wiki_vault/deleted/Renamed Source.1779105069.md (ecf97e38afe2)
- <project-root>/wiki_vault/deleted/Renamed Source.1779106221.md (5fa3f16a8d17)
- <project-root>/wiki_vault/llms.txt (6c3c8da9acf6)
- <project-root>/wiki_vault/notes/Overview.md (886b0ce1b92c)
- <project-root>/wiki_vault/schema.md (f5c7a4f6fe2b)
- <project-root>/wiki_vault/wiki/Agent Memory.md (2b38350a5c12)
- <project-root>/wiki_vault/wiki/Contradictions.md (e7c327bf06fe)
- <project-root>/wiki_vault/wiki/Decision Log.md (1bbbffd3ff45)
- <project-root>/wiki_vault/wiki/Glossary.md (9143feb3d247)
- <project-root>/wiki_vault/wiki/Open Questions.md (bc1ebc4ec4d0)
- <project-root>/wiki_vault/wiki/Overview.md (f66ac6ef4ad5)
- <project-root>/wiki_vault/wiki/Source - BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS.md (a6c0aac76575)
- <project-root>/wiki_vault/wiki/Source - sample.md (2601eb4ea887)
- <project-root>/wiki_vault/wiki/Table of Contents.md (379bbb87e77a)
- <project-root>/wiki_vault/wiki/index.md (31fcb804075e)
wiki> /quit
$ python3 llm_wiki_cli.py

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
wiki> /ask tell me what you are!
Ask mode: agentic
User request: tell me what you are!

Tools called: wiki_capabilities, wiki_tool_catalog, wiki_command_tool_map, wiki_ask_history

Answer:
I am the **LLM Wiki MCP Agent** running over this local Markdown wiki vault.

In practical terms, I am a command-line and MCP-accessible knowledge tool that can:

- search and read maintained wiki pages;
- retrieve context for questions;
- use an Ollama LLM to synthesize answers;
- inspect my own runtime/configuration/tool catalogue;
- maintain AI sidecar notes and graph links;
- lint, graph, ingest, and track source-file provenance.

Current LLM runtime: **ollama / gpt-oss:20b** at `http://localhost:11434`.
Retrieval: SQLite FTS=True, markdown source of truth=True.
Runtime: journaling=True, token metrics=True.
Maintenance: lint/repair/graph/reconcile tools are exposed via the CLI/MCP.

Recent discussion context: the last recorded question was `tell me about this tool please`.
wiki> /quit
$ python3 llm_wiki_cli.py

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
wiki> /ask write a chapter on what you are please!
Ask mode: agentic
User request: write a chapter on what you are please!

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
# Chapter — “Who Am I?”

In a living LLM‑Wiki, the agent that you are speaking to is more than a black‑box neural network. It is a *self‑aware* system built on top of the LLM‑Wiki MCP framework, and it can interrogate itself, report on its own health, and expose its tooling surface to the very LLM that powers it.
The chapter that follows explains the components, capabilities, and introspection patterns that define this agent, citing the source material that describes these concepts in detail.

## 1. The Agent as a Knowledge‑Bearing Tool

> *“In a living LLM Wiki, the tools that drive the agent are first‑class citizens. They can read, write, search, repair, transform, summarise, index, validate, and interrogate the knowledge base. … A tool should be able to become visible to itself.”* (Source – docs – TOOL_SELF_QUESTIONING_LONG_CHAPTER)

The agent is a wrapper around the *LLM‑Wiki MCP* server and its tool catalogue.
Its core responsibilities are:

| Responsibility | How it is achieved |
|----------------|--------------------|
| **Reading**    | `wiki_read_page` pulls Markdown content from `wiki_vault/wiki/`. |
| **Writing**    | `wiki_update_page`, `wiki_append_section` create or modify pages. |
| **Searching**  | `wiki_search_with_notes` and `wiki_retrieve_articles` perform FTS queries on the vault. |
| **Introspection** | `wiki_ask_history`, `wiki_llm_metrics`, `wiki_usage_snapshot` expose runtime data. |
| **Health & Maintenance** | `wiki_lint`, `wiki_reconcile_docs`, `wiki_health_report` detect and fix broken links, orphans, or stale docs. |
| **Runtime state** | The agent keeps an in‑memory snapshot of its configuration (`llm`, `retrieval`, `runtime`, `maintenance`, `files`) that is exposed to the LLM via the *self‑query helper* described in the source chapter. |

These building blocks allow the agent to act as a *first‑class knowledge source* – not just by ingesting documents, but also by exposing its own operational state.

## 2. The Introspection Surface

The agent’s introspection surface consists of a set of “safe read‑only” tools that return structured JSON, which the LLM then renders into human‑readable Markdown. The surface includes:

| Tool | What it returns |
|------|-----------------|
| `wiki_config_load` | Configuration JSON for LLM, retrieval, runtime, and maintenance. |
| `wiki_llm_metrics` | Token usage statistics and ask‑metrics. |
| `wiki_usage_snapshot` | Page and token usage, page counts, and largest pages. |
| `wiki_health_report` | Results of link‑checking, linting, and other health checks. |
| `wiki_ask_history` | Most recent ask prompts and responses. |
| `wiki_notes_status` | Coverage of AI sidecar notes. |
| `wiki_reconcile_docs` | Consistency checks between docs, notes, and tool surface. |

These tools are described explicitly in the chapter on *Enabling a Tool to Ask Itself a Question* (source file `TOOL_SELF_QUESTIONING_LONG_CHAPTER.md`). They allow the LLM to:

- **Ask**: “What are you configured to do?”
- **Understand**: “What tools do you expose?” and “What is your current state?”
- **Validate**: “What is missing from your documentation?” or “Which parts of your design are stale?”

## 3. Why Self‑Questioning Matters

The chapter emphasizes that self‑questioning is not merely a debugging aid, but a means of turning the operational software into a knowledge‑bearing participant in the wiki:

> *“By recording the answer in the wiki, future agents can reuse that knowledge without re‑running the introspection logic.”* (Source – docs – TOOL_SELF_QUESTIONING_LONG_CHAPTER)

Because the LLM‑Wiki is dynamic—tools are added, configurations change, and the underlying model may be upgraded—self‑questioning keeps the knowledge base honest. It prevents the LLM from speaking confidently about a stale version of the system.

## 4. The Agent’s Runtime Capabilities

The capabilities JSON available to the agent (queried via `wiki_capabilities`) provides a snapshot of what the agent can currently do:

```json
{
  "llm": { "provider": "ollama", "host": "...", "model": "gpt-oss:20b", ... },
  "retrieval": { "sqlite_fts": true, "markdown_source_of_truth": true, ... },
  "runtime": { "self_introspection": true, "runtime_journaling": true, ... },
  "maintenance": { "lint": true, "repair": true, "backlinks": true, ... },
  "files": { ... }
}
```

These flags confirm that the agent can introspect itself (`self_introspection: true`), log its runtime (`runtime_journaling: true`), and perform maintenance tasks such as linting and repairing.

## 5. Putting It All Together

When you ask the agent a question, the workflow is:

1. **Input**: The LLM receives your prompt (“write a chapter on what you are please!”).
2. **Introspection**: It calls the introspection surface to gather its own state and configuration.
3. **Synthesis**: It stitches together the gathered evidence into a coherent Markdown chapter.
4. **Output**: The chapter is returned to you, optionally stored back in the wiki for future reference.

This loop ensures that every piece of information the agent provides about itself is verifiable, up‑to‑date, and documented.

---

**In summary:**
The agent you are interacting with is a *self‑aware* LLM‑Wiki MCP instance. It exposes a rich set of read‑only tools that let it introspect its configuration, performance, and health. By rendering that introspection into Markdown, the agent becomes a transparent, self‑documenting component of the wiki, continually aligning its knowledge with its actual runtime state.
wiki> /ask write a technical summary for a CTO
Ask mode: agentic
User request: write a technical summary for a CTO

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
**Technical Summary – LLM Wiki MCP release (for the CTO)**

| Feature | What it is | Why it matters |
|---------|------------|----------------|
| **Local‑first architecture** | A single Python server that lives in the same environment as the business data (the “wiki vault”). | No cloud dependency → full control of data, privacy, and auditability. |
| **Markdown‑based knowledge base** | All domain knowledge is stored as plain Markdown pages with optional side‑car notes. | Human‑readable, version‑controlled, and fully editable by any developer or knowledge worker. |
| **SQLite full‑text search (FTS)** | Fast, on‑disk search over all pages, powered by SQLite FTS5. | Near‑real‑time relevance ranking without external indexing services. |
| **Extensive tool surface** | 45+ core & page‑ops tools (`wiki_create_page`, `wiki_update_page`, `wiki_lint`, `wiki_graph_links`, `wiki_retrieve_articles`, `wiki_ask_ollama`, …). | Agents can manipulate, validate, and introspect the wiki programmatically. |
| **Self‑questioning / introspection** | `wiki_tool_self_question` builds a context pack that exposes config, health, metrics, and function list. | The system can “ask itself” what it can do, detect gaps, and auto‑populate new docs or code. |
| **Agentic ask workflow** | `wiki_ask_agentic` allows a local Ollama model to retrieve relevant pages, build context, and then call tools before answering. | Combines retrieval‑augmented generation with operational grounding, reducing hallucinations. |
| **Graph & linting** | Mermaid graph export (`wiki_mermaid_graph` / `wiki_mermaid_neighbourhood`) and linting (`wiki_lint`). | Visualises link structure, spot orphan/duplicate pages, and ensures link health. |
| **Runtime metrics & usage snapshot** | `wiki_llm_metrics`, `wiki_usage_snapshot`, `wiki_self_access_snapshot`. | Gives real‑time insight into token usage, page sizes, and overall system health. |
| **CLI & MCP server** | `llm-wiki` CLI for ingestion, export, graph, and history; MCP for tool‑based automation. | Developers can operate the wiki from the command line or integrate it into automated pipelines. |
| **Methodology** | Structured workflow: ingest → distil → link → audit → reuse. | Ensures knowledge remains up‑to‑date, traceable, and maintainable. |

### How it fits into the organization

1. **On‑premises, privacy‑first** – All data stays on your infrastructure, satisfying strict compliance regimes.
2. **Developer‑friendly** – Markdown + CLI + Python API means anyone can add, update, or review content without deep tooling expertise.
3. **Intelligent automation** – The self‑questioning tool surface allows the wiki to discover missing commands, update docs automatically, and surface health alerts to operators.
4. **Robust agent support** – Agents can call `wiki_ask_agentic` to get contextual knowledge, run maintenance tasks, or trigger self‑improvement loops (as described in *Book – Self‑Extending Agentic Systems*).
5. **Continuous evolution** – Each iteration adds new functions (e.g., `wiki_retrieve_articles`, `wiki_ask_ollama`), and the methodology ensures that each change is documented, tested, and linted before being published.

### Take‑away for the CTO

The LLM Wiki MCP release is a **self‑maintaining, introspective knowledge engine** that turns your Markdown vault into a living, queryable knowledge base. It gives your teams a single source of truth that can be accessed by both humans and LLM agents, while providing the tooling to keep that truth accurate, connected, and actionable. The result is a **more reliable, auditable, and autonomous** AI‑driven knowledge workflow.
wiki> /ask write a chapter that will astound readers related to your functionality!
Ask mode: agentic
User request: write a chapter that will astound readers related to your functionality!

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
# Chapter — The Self‑Reflective Agent: A Tool That Thinks for Itself

In a living LLM Wiki the tools that drive the agent are first‑class citizens, and this chapter shows how one of those tools can transcend its role as a mere “executor” and become an *autonomous knowledge source* of its own operation. By introspecting, a tool can ask itself the very questions that would otherwise require an external operator to read logs, inspect configuration files, or run diagnostic utilities.

---

## 1. Why Self‑Questioning Matters

A tool that can interrogate its own state is more than a debugging trick; it is a **knowledge‑bearing participant** in the wiki. When the tool answers questions such as “What are you configured to do?” or “Which metrics are you reporting?” it turns transient runtime data into a permanent record that can be queried by future agents. 

> *“A tool that can ask itself a question is a powerful debugging aid. It can expose hidden configuration, report its own metrics, reveal stale documentation, detect that an index needs rebuilding, or explain why a query failed. By recording the answer in the wiki, future agents can reuse that knowledge without re‑running the introspection logic.”* – (Source – docs – TOOL_SELF_QUESTIONING_LONG_CHAPTER)

---

## 2. The Introspection Surface

Every MCP tool exposes a variety of introspection hooks. The most useful for a self‑questioning pattern include:

| Surface | What it Reveals |
|---------|-----------------|
| `config` | Current Ollama host, model, timeouts, temperature, and ask settings |
| `help` | User‑facing command list |
| `FUNCTION_LIST.md` | Formal list of MCP tools and CLI commands |
| `stats` | Page counts, word estimates, SQLite status, tags, and categories |
| `lint` | Broken links, orphan pages, short pages |
| `graph` | Node and edge counts |
| `usage` | Approximate wiki tokens and largest pages |
| `history` | Recent ask history |

These surfaces collectively provide a **snapshot of the system’s living truth**. The chapter in the source documentation describes how the tool can systematically request each surface, format it as Markdown, and optionally store it in the wiki for future reference.

---

## 3. Building the Self‑Query Helper

A minimal helper wrapper follows a simple pattern:

1. **Invoke** the tool’s introspection endpoints in a deterministic order.
2. **Serialize** the results into a Markdown structure.
3. **Optionally persist** the structure as a wiki page (e.g., `Self‑State.md`).

The wrapper itself is a pure read‑only agentic tool; it never mutates the wiki unless explicitly instructed. Its job is to expose the tool’s internal state as an evidence source that the LLM can reason about.

---

## 4. The Self‑Reflective Workflow

1. **Agent Query**
   The agent asks the tool: *“Self‑state: please provide a current status report.”*

2. **Tool Introspection**
   The helper gathers data from the surfaces listed above and composes a Markdown document.

3. **Evidence Capture**
   The document is returned to the agent and may be written to the wiki as a *persistent* artifact.

4. **Reasoning Loop**
   The LLM can now *read* this artifact, compare it against older reports, detect drift, or even generate remediation suggestions.

---

## 5. Real‑World Impact

| Scenario | How Self‑Questioning Helps |
|----------|----------------------------|
| **Drift in Configuration** | Detects changes to the Ollama host or model without manual inspection. |
| **Stale Documentation** | Flags discrepancies between `FUNCTION_LIST.md` and actual CLI output. |
| **Index Corruption** | Reports SQLite state and triggers a rebuild if integrity checks fail. |
| **Usage Spike** | Alerts when token consumption exceeds historical averages. |
| **Error Analysis** | Records the last error message to aid debugging. |

These capabilities translate directly into **proactive maintenance** and **continuous learning** for the knowledge base, ensuring that the LLM never explains an obsolete system state.

---

## 6. Extending the Pattern

The self‑questioning paradigm is not limited to the MCP tools. Any tool exposing a callable interface—web services, database drivers, even external APIs—can be wrapped with a similar helper. The key requirements are:

* **Structured introspection endpoints** (e.g., health checks, metrics, config).
* **Serialization to a common format** (Markdown is preferred for human readability and wiki integration).
* **Non‑intrusive operation** to preserve system integrity.

By extending this pattern across all components, the entire ecosystem becomes a **living repository of its own operational truth**.

---

## 7. Closing Thoughts

Imagine an agent that, before answering a user’s query, consults the *Self‑State.md* page, learns that the underlying model has been upgraded, and tailors its response accordingly. Imagine a system that automatically flags outdated documentation the moment a new command is added. The self‑questioning tool is the cornerstone of such an adaptive, self‑aware knowledge base.

> *“The system can learn not only from documents but from its own operation.”* – (Source – docs – TOOL_SELF_QUESTIONING_LONG_CHAPTER)

This chapter showcases that **introspection is not a luxury—it is a necessity** for any living LLM Wiki that aims to stay truthful, reliable, and self‑correcting.
wiki> /ask write a chapter on what Karpathy would like about you and what would surprise him!
Ask mode: agentic
User request: write a chapter on what Karpathy would like about you and what would surprise him!

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
# Chapter X: What Karpathy Will Love…and What Will Surprise Him

*The following chapter is written from the perspective of an LLM‑Wiki MCP that has been carefully engineered to align with the principles that have guided Andre Karpathy’s career—from his early work on deep learning visual models to his later focus on long‑term system design.  It is a speculative look at the features that would resonate with him and the ones that might catch him off‑guard.*

---

## 1. What Karpathy Would Like About the System

### 1.1 Explicit, Human‑Readable Source of Truth
Karpathy’s own journey has been driven by the belief that *data* and *code* should be **transparent**.  The wiki vault stores every page as Markdown, a format that is both machine‑parsing friendly and immediately understandable by a human engineer.  The README even notes the **local‑first** nature of the server, “A local‑first Python MCP server for maintaining an LLM Wiki” (Source – README).  This means the system keeps its knowledge on the developer’s own machine, avoiding the latency and trust issues that cloud‑based RAG systems introduce.  For someone who values reproducibility and auditability, that is a win.

### 1.2 A Tool‑First, Self‑Questioning Architecture
Karpathy has always appreciated systems that *expose* their own functionality.  The chapter “Enabling a Tool to Ask Itself a Question” (Source – docs – TOOL_SELF_QUESTIONING_LONG_CHAPTER) enumerates exactly the introspection questions the system can answer: *What are you configured to do? What tools do you expose? What is your current state?*  The ability for a tool to reveal its own command surface and runtime metrics turns what would normally be a black box into an **observable, queryable entity**—something that aligns with the “observable system” mindset Karpathy has championed.

### 1.3 A Self‑Improving, Feedback‑Loop‑Based Development Process
The book *The Self‑Extending LLM Wiki* (Source – BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS) describes a disciplined loop:
> “observe behaviour, identify weakness, document the gap, design a bounded function, implement the function, test the function, record the change, make the new capability available to future reasoning.”  This loop echoes the incremental experimentation that has guided Karpathy’s research.  It gives a clear, repeatable method to **close the loop** between observation, hypothesis, and validation—exactly what he has always praised in machine‑learning pipelines.

### 1.4 Built‑In Health & Diagnostics
From the self‑questioning tool, the system can answer *“What do your own logs, metrics, and health checks say?”*  That level of self‑diagnostics is crucial for long‑running agents.  Karpathy’s own research on deep learning systems emphasizes rigorous monitoring; a system that can automatically surface its own health report directly within the knowledge base is a natural fit.

### 1.5 Extensible via Declarative Sidecar Notes
The wiki’s note‑system, as described in *BOOK_SELF_EXTENDING_AGENTIC_SYSTEMS*, “stores inferred relationships, candidate links, missing evidence, and suggested extensions.”  It lets the system **autonomously suggest new content** based on gaps in the current knowledge graph.  This is an elegant form of meta‑learning that would resonate with Karpathy’s interest in *systems that learn to learn*.

---

## 2. What Will Surprise Karpathy

### 2.1 The Depth of Self‑Questioning
While Karpathy has praised introspection in machine‑learning systems, the self‑questioning tool goes further than a simple status report.  It can answer questions about **runtime state, command surface, wiki coverage, and even missing documentation**—all bundled into a single Markdown output.  For a developer used to *log files* and *debuggers*, seeing a **structured, self‑generated knowledge snapshot** that includes the entire tool surface and a list of missing pages is an unexpected, but powerful, surprise.

> “This is not merely a debugging trick. It is a way of turning operational software into a knowledge‑bearing participant in the wiki.” (Source – docs – TOOL_SELF_QUESTIONING_LONG_CHAPTER)

### 2.2 Automatic Extension of the Tool Surface
Karpathy often talks about “writing a few lines of code to get the system to do something new.”  What’s surprising is that the wiki’s **self‑improvement loop** is already baked in: when a missing capability is detected, the system can *propose* a bounded function, *implement* it (via a minimal patch), and *record* the change for future reasoning.  The system therefore *self‑generates* new tooling that was not in the original codebase—a step beyond the typical “write a function, run, observe” cycle.

### 2.3 Seamless Graph‑Based Reasoning
The wiki’s graph export (e.g., `wiki_mermaid_graph` from FUNCTION_LIST) turns Markdown into a **visual knowledge graph**.  Karpathy’s work on vision‑language models often uses graph representations to encode relationships.  The fact that a purely text‑based system can **output a Mermaid flowchart** that captures all linkages—and then use that graph for recursive context building—provides a bridge between his preference for structured data and the flexibility of a wiki.

> “The pattern is generic: any tool that exposes a callable interface can be wrapped with a small self‑query helper.” (Source – docs – TOOL_SELF_QUESTIONING_LONG_CHAPTER)

### 2.4 Local, Fully Reproducible RAG Without External APIs
Karpathy has expressed concerns about *data sovereignty* and *model drift* when relying on large cloud‑based APIs.  The wiki’s entire stack—SQLite FTS, Markdown, Ollama local models, and the self‑questioning tool—remains **completely local**.  The surprise here is how fully functional a *local‑only* RAG system can be, even when using a large 20B LLM, without compromising on the quality of context or the speed of inference.

> “A local-first Python MCP server for maintaining an LLM Wiki” (Source – README)

### 2.5 A Unified View of Metrics, History, and Tokens
Karpathy frequently stresses the importance of *token budgeting* and *usage analytics*.  The system’s `wiki_llm_metrics`, `wiki_usage_snapshot`, and `wiki_runtime_journal` tools give a **single, unified view** of token usage, ask history, and runtime events—all accessible via CLI and MCP commands.  Having this telemetry baked into the knowledge base, and automatically summarized in Markdown, is a subtle but powerful feature that would pleasantly surprise him.

> “Tokens, history, usage, and runtime state can all be queried via the MCP surface.” (Source – FUNCTION_LIST)

---

## 3. Closing Thoughts

From **explicit Markdown** to **self‑questioning**, from **local RAG** to **graph‑based reasoning**, the LLM‑Wiki MCP embodies many of the design principles that have driven Karpathy’s work: *observability*, *modularity*, *reproducibility*, and *continuous self‑improvement*.  While he will undoubtedly appreciate the transparency and discipline built into the system, the most delightful surprises will come from the depth of introspection, the ability to automatically extend its own tool surface, and the seamless integration of graph‑based reasoning—all while staying strictly local and fully reproducible.

*If Karpathy were to peer into this wiki, he would likely see a faithful extension of the same values that have guided his career, coupled with the kind of elegant automation that turns the mundane act of debugging into a fully documented, self‑sustaining cycle.*
wiki> /ask write a post to send to Karpathy's github on our progress!
Error: No closing quotation
wiki> /ask write a post to send to Karpathys github page to report on our progress!
Ask mode: agentic
User request: write a post to send to Karpathys github page to report on our progress!

Tools called: wiki_search_with_notes, wiki_capabilities, wiki_read_page

Answer:
**Subject:** 🚀 LLM Wiki MCP release – 21/21 Tests Passed & New Self‑Questioning Tool 🚀

Hi @karpathy,

I’m excited to share our latest progress on the LLM Wiki MCP (see the repo for full code: <https://github.com/Electro-resonance/LLM-WIKI-MCP>). Below is a concise snapshot of what we’ve achieved in the release release and a brief overview of the key new capabilities.

---

### 1️⃣ What’s New in release?
- **Full‑stack local MCP**: A single‑file Python server that exposes a robust set of CLI & MCP tools for creating, reading, updating, linting, and graphing Markdown wiki pages. (Read more: [Source - README])
- **Lifecycle & maintenance tools** inspired by Karpathy’s schema‑first pattern – backlink resolution, rename/delete with link awareness, dry‑run writes, schema access, and health reports. (See [Source - FUNCTION_LIST] for the full tool list.)
- **Agentic Ask Pipeline**: The agent can now introspect its own runtime state and tools before answering, leading to more accurate and context‑aware responses. (See [Source - TOOL_SELF_QUESTIONING_LONG_CHAPTER] for the design.)
- **Self‑Questioning Tool**: A new helper that asks a tool about its own configuration, metrics, and health, and stores the answer as a wiki page for future agents to reuse. (More detail: [Source - TOOL_SELF_QUESTIONING_LONG_CHAPTER])

### 2️⃣ Regression Suite – 21/21 Tests Passed
Our automated test harness covers every core feature:
- Tool list completeness
- Vault initialization
- Page creation & reading
- Link extraction & SQLite FTS search
- Context pack generation
- Decision logging
- Graph & lint functions
- `llms.txt` export
- Dry‑run write validation
- Page listing & loose handle resolution
- Backlinks & related‑page discovery
- Table of contents generation
- Schema document creation/read
- Category/tag inventory
- Health reporting
- Rename/delete lifecycle operations
All tests are green in the sandbox local harness. (See [Source - TEST_REVIEW] for the full report.)

### 3️⃣ Self‑Questioning – Turning Operations Into Knowledge
By wrapping any MCP tool with a small introspection helper, we convert runtime state into a Markdown source. The wiki can now **explain its own configuration, expose hidden metrics, and flag stale documentation** automatically. This pattern makes the wiki a living truth layer rather than a static knowledge dump. (More on the concept: [Source - TOOL_SELF_QUESTIONING_LONG_CHAPTER])

### 4️⃣ Next Steps & Request
- **Public Release**: We’re preparing the release candidate for public distribution.
- **Community Feedback**: We’d love to hear your thoughts on the agentic ask pipeline and the self‑questioning approach.
- **Contribution**: If you see gaps or have ideas, we’re open to PRs.

Looking forward to your feedback!

Best,
[Your Name]
[Your Project/Org]

---

> *All source code and documentation can be found in the repo. The README outlines the core architecture, while FUNCTION_LIST details every exposed tool. The regression report confirms 100 % test coverage, and the Self‑Questioning chapter explains how tools become part of the knowledge base.*

(End of post)
wiki>
```

---

# Closing Reflection

The LLM Wiki MCP is best understood as a practical experiment in reflective AI infrastructure.

It is a wiki, but also a tool system.
It is a retrieval system, but also a memory substrate.
It is an MCP server, but also a self-describing operational layer.
It is local-first, but agent-ready.

Its deeper promise is that AI systems may become more useful not merely by increasing model size, but by improving the structures around the model:

- better memory;
- better tools;
- better provenance;
- better self-inspection;
- better documentation;
- better human steering.

That is the living LLM Wiki pattern.
