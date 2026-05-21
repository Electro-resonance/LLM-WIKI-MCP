# From Disposable RAG to Living Knowledge: What the LLM Wiki MCP Demo Shows

## A research/blog article based on the CLI demonstration

---

Most document chat systems still behave as if knowledge is temporary.

You ask a question. The system retrieves chunks. It stuffs them into a prompt. The model answers. Then the structure disappears until the next query.

That pattern works, but it has limits.

It does not naturally build a memory. It does not easily show what it knows. It does not maintain its own documentation. It does not track whether sources have changed. It does not create a durable knowledge artefact that humans and agents can improve together.

The LLM Wiki MCP demo points toward a different pattern.

Instead of treating documents as disposable chunks, it treats knowledge as a maintained local wiki.

---

## The inspiration: Karpathy’s LLM Wiki idea

Andrej Karpathy’s LLM Wiki idea helped crystallise a simple but important shift:

> use an LLM not only to answer questions, but to help build and maintain a durable knowledge base.

That idea changes the role of the model.

The LLM is no longer just a responder. It becomes a librarian, editor, linker, maintainer, and reflective assistant.

The LLM Wiki MCP takes that pattern and implements it as a local-first system with a command-line interface and an MCP tool layer.

---

## The key architectural shift

Classic RAG often looks like this:

```text
documents -> chunks -> retrieval -> prompt -> answer
```

The LLM Wiki MCP aims for this:

```text
documents -> maintained wiki -> graph + notes + provenance -> agentic tools -> grounded answers
```

This difference matters.

A chunk is temporary. A wiki page is durable.

A chunk is retrieved. A wiki page is maintained.

A chunk has limited context. A wiki page can link, cite, summarise, contradict, and evolve.

---

## What the demo shows

The CLI demo starts with the interactive shell and shows the system ingesting a project folder.

The ingest result reports new files, already-ingested files, and errors. This is a small detail with big implications. It means the system is not blindly reprocessing everything. It knows which files it has seen before.

That requires provenance.

The system tracks source files using metadata such as paths, timestamps and hashes. This gives ingestion a build-system quality: unchanged inputs can be skipped, changed inputs can be updated, and the wiki stays aligned with the source corpus.

---

## Why local-first matters

The LLM Wiki MCP is local-first.

It uses:

- Markdown as the source of truth;
- SQLite for local indexing;
- local runtime files for history and metrics;
- optional local Ollama models for synthesis;
- Git-friendly documentation.

This is valuable for research, engineering and private knowledge work. It keeps the user close to the data. It makes the system inspectable. It avoids the feeling that knowledge has disappeared into an opaque remote service.

Local-first is not nostalgia. It is an architectural choice for trust.

---

## The CLI and MCP split

The demo makes an important distinction clear.

The CLI is for humans.

The MCP is for agents.

The CLI lets a human operator run:

```text
/ingest ./docs
/ingest ./notes/idea.rtf
/ask what are you?
/stats
/lint
/notes-all
/provenance
```

The MCP gives an LLM agent structured tools for search, reading pages, retrieving context, inspecting capabilities, and reasoning over the wiki.

This separation is important. Humans need clarity and control. Agents need stable schemas and structured results.

The same knowledge base serves both.

---

## Recursive knowledge work

One of the strongest parts of the demo is the discussion of recursion.

In agentic mode, the LLM is not just called once. It can enter a loop:

```text
LLM -> tools -> wiki -> notes -> links -> LLM
```

The model can search, read, inspect, widen scope, and try again.

If the first synthesis returns blank, the system can retrieve more pages and notes, then call the LLM again. If that still fails, it can produce an extractive answer from the evidence.

This is a practical form of recursive knowledge work.

It does not require mystical claims about model consciousness. It simply recognises that better answers often come from iterative interaction between a model and its tools.

---

## A self-describing system

The demo asks the tool to explain what it is.

That is a deceptively important test.

A normal script might have no self-understanding. A normal chatbot might hallucinate an identity. A reflective tool system can answer from runtime evidence:

- what tools are available;
- what model is configured;
- where the wiki lives;
- what the index contains;
- what the provenance database knows;
- what the recent ask history contains.

This turns operational state into knowledge.

The system is not conscious, but it is inspectable. That is already useful.

---

## Why Markdown still matters

Markdown may seem humble, but it is central to the design.

Markdown is:

- readable;
- editable;
- portable;
- Git-compatible;
- easy for LLMs to write;
- easy for humans to review.

A maintained Markdown wiki gives the project a stable knowledge surface that both humans and agents can use.

This is one reason the LLM Wiki pattern is so attractive. It uses ordinary files as the substrate for extraordinary workflows.

---

## What this means for future agent systems

The demo suggests a broader direction for AI systems.

The intelligence of future systems may not come only from larger models. It may come from better loops:

```text
model + tools + memory + provenance + graph + human steering
```

A model with no memory is powerful but transient.

A model with a maintained knowledge substrate becomes more useful over time.

A model with tools can inspect, repair and extend that substrate.

A human in the loop can guide the process, catch errors, and decide what matters.

This is the deeper promise of the LLM Wiki MCP.

---

## The practical takeaway

The LLM Wiki MCP is not just another RAG wrapper.

It is a prototype of a local-first, reflective knowledge system where:

- documents become maintained pages;
- pages become graph-connected knowledge;
- knowledge becomes tool-accessible context;
- agents can reason over that context;
- humans can inspect and steer the process.

That is why the demo feels important.

It shows a path from document chat toward living knowledge infrastructure.

And that may be one of the most useful near-term directions for agentic AI.
