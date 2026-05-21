# LLM Wiki MCP CLI Demo Tutorial

## A practical walkthrough of the local-first wiki, CLI, and agentic ask workflow

This tutorial is based on a captured CLI demonstration showing the LLM Wiki MCP running interactively, ingesting documents, and answering higher-level questions about itself, its architecture, Karpathy’s LLM Wiki pattern, and recursive agentic behaviour.

---

## 1. Starting the CLI

From the project directory, run:

```bash
python3 llm_wiki_cli.py
```

The CLI opens an interactive shell with the LLM Wiki banner and a prompt:

```text
wiki>
```

The interface is designed to be human-readable and operator-friendly. It exposes commands for search, retrieval, asking questions, reading pages, ingesting files, linting, graphing, and configuration.

Typical first commands:

```text
help
/stats
/config
```

---

## 2. Ingesting documents

The demo shows a document ingest run:

```text
wiki> /ingest .
```

The improved expected behaviour is compact by default:

```text
Ingest scan: <project-root>
Files read: 165
New: 55 | Updated: 0 | Already ingested: 110 | Errors: 0
110 files were already ingested and unchanged.
```

This tells the user what happened without flooding the terminal.

Use verbose mode when you need the full file list:

```text
/ingest ./docs --verbose
/ingest ./notes/idea.rtf
```

### Why this matters

The LLM Wiki MCP is designed for repeated ingestion. Once a file has already been ingested, it should not be reprocessed unless its timestamp or SHA256 hash changes.

This gives the system build-like behaviour:

```text
first ingest  -> new files processed
second ingest -> unchanged files skipped
changed file  -> updated and versioned
```

---

## 3. Asking the system what it is

The demo asks the system to write about itself:

```text
/ask write a medium style article on what you are and why you exist.
Ensure to mention Karpathy and his post.
```

The answer describes the LLM Wiki MCP as:

- a local-first Markdown knowledge engine;
- a durable alternative to disposable RAG chunks;
- an MCP-accessible substrate for LLM agents;
- a CLI-accessible tool for humans;
- inspired by Andrej Karpathy’s LLM Wiki idea.

The important pattern is:

```text
documents -> maintained wiki -> graph + notes + provenance -> agentic tools -> grounded answers
```

This is the central architectural distinction.

---

## 4. Understanding why MCP and CLI both matter

The demo then asks for a longer article on the importance of the MCP and CLI.

The answer distinguishes two interfaces:

| Interface | Primary user | Purpose |
|---|---|---|
| MCP | LLM agents | Structured tool access to the wiki |
| CLI | Humans/operators | Direct control, testing, maintenance and inspection |

The MCP gives agents structured operations such as search, read, ask, ingest, inspect, and maintain.

The CLI gives humans a transparent control surface for running the system, testing behaviour, managing configuration, and understanding what the agent is doing.

Together, they form a human-agent knowledge loop.

---

## 5. Recursive ask behaviour

The demo asks:

```text
/ask write an article on the recursive nature of the LLM within the CLI?
```

The answer highlights the recursive loop:

```text
LLM -> MCP tools -> Wiki + Graph + Notes -> LLM -> ...
```

In agentic mode, the system may:

1. interpret the user request;
2. search the wiki;
3. read relevant pages;
4. inspect notes;
5. follow links;
6. call the LLM;
7. retry with expanded context if the answer is blank;
8. record or compress history.

This makes the CLI more than a simple shell. It becomes an execution surface for recursive knowledge work.

---

## 6. Comparing the implementation to Karpathy’s LLM Wiki idea

The demo asks the agent to compare itself to Karpathy’s LLM Wiki notes.

A good comparison should emphasise:

| Shared principle | LLM Wiki MCP implementation |
|---|---|
| Markdown as durable knowledge | Markdown remains the source of truth |
| Local-first workflow | Runs locally with SQLite and Ollama support |
| Wiki as maintained context | Pages, notes, links and graph structure persist |
| Agentic knowledge work | MCP tools allow agents to search, read and maintain |
| Human review | CLI and Git-friendly docs keep the process inspectable |

The LLM Wiki MCP extends the general pattern with:

- MCP tools;
- provenance-aware ingestion;
- runtime introspection;
- sidecar notes;
- graph visualisation;
- multi-pass answer synthesis;
- compact CLI workflows;
- versionless Python package structure.

---

## 7. Recommended demo flow

For a clean live demo, use this sequence:

```text
python3 llm_wiki_cli.py
help
/stats
/ingest ./docs
/ingest ./notes/idea.rtf
/ask what are you?
/ask what can you do?
/ask what was the inspiration for this project?
/ask write a medium style article on what you are and why you exist. Ensure to mention Karpathy and his post.
/ask write a longer medium article so that the reader can understand the importance of your MCP and CLI.
/ask write an article on the recursive nature of the LLM within the CLI.
/ask compare yourself to Karpathy's LLM Wiki idea.
```

Optional maintenance:

```text
/lint
/notes-all
/mermaid
/provenance
```

---

## 8. What the demo proves

The demonstration shows that the system can:

- ingest and track documents;
- distinguish new and already-ingested files;
- answer architectural questions about itself;
- use the wiki as evidence;
- explain its own purpose;
- describe the relationship between CLI, MCP and LLM agents;
- compare itself to the Karpathy LLM Wiki pattern;
- produce article-style outputs from its maintained documentation.

---

## 9. What to improve next

The demo also suggests important improvements:

- keep answer synthesis grounded in retrieved pages;
- avoid generic startup-pitch answers;
- cite source pages more explicitly;
- distinguish evidence from inference;
- make compact ingest output the default;
- preserve verbose mode for debugging;
- ensure basic identity/config questions always answer from runtime evidence.

These improvements are already reflected in the current design direction.
