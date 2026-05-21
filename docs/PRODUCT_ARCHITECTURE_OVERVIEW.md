# Product and Architecture Overview

## LLM Wiki MCP: a local-first knowledge substrate for humans and LLM agents

---

## Executive summary

LLM Wiki MCP is a local-first knowledge system that turns documents into a durable, searchable, graph-aware Markdown wiki. It exposes two complementary interfaces:

- a **CLI** for humans and operators;
- an **MCP tool layer** for LLM agents.

The goal is to move beyond disposable RAG chunks and build a maintained knowledge substrate that agents can search, read, inspect, extend, and reason over.

---

## The problem

Classic RAG is useful, but it often behaves like this:

```text
documents -> chunks -> retrieval -> prompt -> answer
```

This creates several problems:

- chunks are isolated;
- knowledge does not naturally compound;
- document provenance can be weak;
- answers may be hard to audit;
- agents have no durable model of what the system knows;
- repeated ingestion can waste time;
- maintenance is external to the retrieval system.

LLM Wiki MCP reframes the problem:

```text
documents -> maintained wiki -> graph + notes + provenance -> agentic tools -> grounded answers
```

---

## Core product idea

The product is a **living Markdown knowledge base** with an agent-accessible tool layer.

It is useful for:

- research projects;
- technical documentation;
- agent memory systems;
- AI-assisted knowledge management;
- local/private document intelligence;
- long-running engineering projects;
- GitHub-ready documentation and changelogs;
- provenance-aware ingestion workflows.

---

## Key user groups

### Human operator

Uses the CLI to:

- ingest files;
- inspect stats;
- run searches;
- ask questions;
- read pages;
- lint and repair the wiki;
- generate notes;
- view provenance;
- configure the local LLM.

### LLM agent

Uses the MCP to:

- search with notes;
- read full pages;
- retrieve article context;
- inspect capabilities;
- query tool catalogues;
- follow candidate links;
- reason over runtime state;
- build evidence-based answers.

---

## Architecture layers

```text
┌──────────────────────────────────────────────┐
│                  Human CLI                    │
│  ingest | search | ask | read | stats | lint  │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│                  MCP Tool Layer               │
│ search/read/retrieve/ask/notes/config/runtime │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│              Agentic Ask Pipeline             │
│ intent -> tools -> evidence -> synthesis      │
│ blank answer -> second pass -> fallback       │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│             Knowledge Substrate               │
│ Markdown wiki | notes | links | graph         │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│            Local Data and Runtime             │
│ SQLite FTS | provenance DB | history | config │
└──────────────────────────────────────────────┘
```

---

## Main components

### 1. Markdown wiki

Markdown is the source of truth. It is:

- human-readable;
- Git-friendly;
- diffable;
- editable by humans and agents;
- portable across tools.

### 2. SQLite search

SQLite FTS provides local search without requiring a remote vector database.

It supports:

- fast retrieval;
- page search;
- compact local state;
- rebuildable indexes.

### 3. Provenance database

The provenance database records:

- directory path;
- full source path;
- filename;
- file size;
- modification timestamp;
- SHA256 hash;
- linked wiki page;
- version events.

This allows repeated ingestion to skip unchanged files.

### 4. Notes system

AI sidecar notes provide reflective overlays:

- related concepts;
- candidate links;
- missing evidence;
- inferred connections;
- maintenance suggestions.

### 5. Agentic ask pipeline

The ask pipeline is designed to avoid one-shot brittle answers.

It can:

- identify intent;
- search;
- read pages;
- inspect notes;
- follow links;
- call an LLM;
- retry if blank;
- fall back to extractive answers.

### 6. Runtime self-access

The system can inspect:

- its capabilities;
- tool catalogue;
- command map;
- ask history;
- runtime journal;
- token metrics;
- provenance state.

This lets the system answer questions about itself.

---

## Why the CLI matters

The CLI is the human control panel.

It makes the system:

- inspectable;
- debuggable;
- testable;
- configurable;
- usable without a separate UI.

Example commands:

```text
/ingest ./docs
/ingest ./notes/idea.rtf
/ask what are you?
/stats
/provenance
/notes-all
/lint
```

The CLI should be quiet by default and verbose only when requested.

---

## Why the MCP matters

The MCP is the agent control surface.

It lets LLMs operate on structured tools instead of scraping terminal output.

This is crucial because agents need:

- predictable tool schemas;
- structured results;
- stable function names;
- safe read operations;
- controlled maintenance operations;
- runtime introspection.

---

## Answer strategy

The desired answer strategy is:

```text
basic question -> runtime/tool evidence answer
research question -> search + read pages + notes
blank LLM answer -> second-pass evidence expansion
still blank -> extractive fallback
```

The system should avoid:

- empty responses;
- generic pitch-style hallucinations;
- ignoring retrieved evidence;
- treating short follow-ups as isolated searches.

---

## GitHub-ready design choices

The current design moves toward public release by:

- using a stable package import: `llm_wiki_mcp`;
- avoiding versioned package names in code;
- removing stale SQLite indexes from the release;
- consolidating documentation;
- separating CLI docs from MCP/agent docs;
- keeping changelog history as sequential change sets;
- providing agent-facing instruction files.

---

## Product positioning

LLM Wiki MCP is best described as:

> A local-first, Markdown-native, MCP-accessible knowledge substrate for LLM agents and human operators.

It is not merely a chatbot, not merely a RAG pipeline, and not merely a wiki.

It is a bridge between:

- documents;
- memory;
- tools;
- agents;
- local LLMs;
- humans in the loop.

---

## Future opportunities

Potential future directions include:

- richer citation handling;
- better graph ranking;
- optional vector embeddings;
- web UI;
- Obsidian integration;
- MCP-native editing workflows;
- automated page refactoring;
- multi-agent note iteration;
- stronger test coverage;
- provenance-aware Git workflows.
