# The Self-Extending LLM Wiki

## Toward Reflective Agentic Systems That Identify and Repair Their Own Weaknesses

### Preface

This book introduces the LLM Wiki MCP as more than a retrieval tool. It is a small but meaningful experiment in reflective software: a system that stores its own documentation, exposes its own runtime state, asks questions about itself, identifies missing capabilities, and can be extended with new functions that reduce those gaps.

The idea developed through practical iteration. Each version of the tool revealed a weakness. A missing function became a new command. A vague answer became a prompt improvement. A lack of self-knowledge became a self-access surface. A retrieval miss became notes, links, and graph-aware search. A static ask pipeline became an agentic ask pipeline. A command-line frustration became history, completion, and Ctrl-R.

This is not AGI. It is not conscious. It is not autonomous in the grand science-fiction sense. But it points toward a design pattern that is important: agentic systems can become more useful when they are built to inspect their own limitations and propose concrete extensions to their own tool surface.

The phrase “self-improving system” should be used carefully. In this project, improvement does not mean unbounded autonomous mutation. It means a disciplined loop:

```text
observe behaviour
identify weakness
document the gap
design a bounded function
implement the function
test the function
record the change
make the new capability available to future reasoning
```

This is a practical and safe stepping stone toward more capable agentic systems.

---

## Chapter 1 — What the LLM Wiki MCP Is

The LLM Wiki MCP is a local knowledge-operating layer. Its central idea is simple: use Markdown as the durable source of truth, use a lightweight database for search, expose the system through CLI and MCP tools, and allow an LLM to reason over the maintained wiki.

Traditional retrieval-augmented generation often treats documents as disposable chunks. The LLM Wiki takes a different view. It treats knowledge as a maintained structure. Pages have names. Pages can link. Pages can be repaired. Pages can have sidecar notes. Pages can be indexed, linted, graphed, and re-used by agents.

At its core, the system contains:

- a Markdown wiki vault;
- a search/index layer;
- a command-line interface;
- an MCP tool surface;
- Ollama-backed local LLM synthesis;
- self-access tools for config, usage, history, tokens, and runtime state;
- AI notes that extend search and link discovery;
- agentic ask flows that can call tools before answering.

The tool is therefore not merely a “chat with documents” system. It is a working memory layer for an agent.

---

## Chapter 2 — Why Static RAG Is Not Enough

Classic RAG usually follows this pipeline:

```text
query -> chunks -> prompt -> answer
```

That is useful, but it has limits. Chunks do not understand themselves. They do not know when documentation is stale. They do not know that a command exists but is not documented. They do not maintain cross-links. They do not record runtime behaviour. They do not usually explain the tool that produced them.

The LLM Wiki MCP moves toward:

```text
query
 -> structured wiki search
 -> sidecar notes
 -> candidate links
 -> runtime state
 -> self-access snapshots
 -> tool traces
 -> LLM synthesis
 -> maintenance suggestions
```

This is important because agentic systems need operational grounding. A system that can inspect its runtime state is less likely to hallucinate its capabilities. A system that can reconcile its docs against its actual command surface is less likely to drift. A system that can record its own actions can debug itself later.

---

## Chapter 3 — The Self-Questioning Tool

A self-questioning tool can answer questions like:

- What are you?
- What can you do?
- What is your current configuration?
- Which commands exist?
- Which docs describe you?
- What is missing?
- Which functions are planned but not implemented?
- What failed recently?
- How large is your wiki?
- What model are you using?
- What runtime capabilities are enabled?

In this project, self-questioning began as a documentation idea and became a practical tool surface. Commands such as `self-stats`, `self-usage`, `tokens`, `capabilities`, `runtime-journal`, and `command-map` allow the system to expose its own state.

The deeper insight is that the tool itself becomes a first-class knowledge source.

A source is no longer only a PDF, a Markdown page, or a pasted document. A source can be:

- the current config;
- the runtime journal;
- the command map;
- the metrics log;
- the ask history;
- the notes graph;
- the list of exposed MCP tools.

This is one of the foundations of reflective agentic architecture.

---

## Chapter 4 — A System That Finds Its Own Weaknesses

The development history of the LLM Wiki MCP shows a repeated pattern:

1. A user tries something.
2. The output reveals a limitation.
3. The limitation is described in the wiki or chat.
4. A new function is added.
5. A smoke test proves the behaviour.
6. The new function becomes part of the next version.

Examples include:

- search not handling singular/plural well;
- CLI output being too JSON-heavy;
- config changes not persisting;
- agentic ask only printing evidence instead of synthesising;
- `ask run self-stats` describing a command instead of executing it;
- missing token/s metrics;
- missing runtime journal;
- missing full-page reads after search;
- lack of command history and Ctrl-R in the shell;
- AI notes not being searched alongside canonical pages.

Each problem became part of the system’s growth. The tool did not magically rewrite itself. Human intent and agentic implementation worked together. This is the key safety distinction: the system assists its own improvement, but changes are still bounded, inspectable, packaged, and tested.

---

## Chapter 5 — Weakness Identification as a Step Toward AGI-Like Behaviour

A future form of AGI may not begin as a single monolithic mind. It may emerge from agentic systems that can:

1. inspect their own behaviour;
2. identify mismatches between intended and actual capability;
3. propose new tools;
4. implement or request implementation of those tools;
5. test them;
6. incorporate them into future reasoning.

The LLM Wiki MCP is a small prototype of this loop.

It has several properties that point in this direction:

- it maintains a model of its own commands;
- it can expose its own config and metrics;
- it can record runtime traces;
- it can compare documentation with actual tools;
- it can identify missing docs and stale claims;
- it can add AI sidecar notes;
- it can search those notes later;
- it can use an agentic ask pipeline to call tools before answering.

This is not general intelligence. But it is a tool-based form of reflective capability. It gives the agent a memory of its own operation and a pathway to ask: “What am I missing?”

That question matters.

---

## Chapter 6 — The Self-Extending Wiki Loop

Release introduced AI sidecar notes. This was a significant shift. Instead of altering canonical pages directly, the AI can write notes beside each page:

```text
wiki/
  ARCHITECTURE.md

/notes/
  ARCHITECTURE.md
```

The sidecar note can include:

- a working summary;
- key terms;
- candidate links;
- suggested next actions;
- relationships to other pages.

This creates a loop:

```text
page -> notes -> candidate links -> improved search -> better context -> better notes
```

The notes are deliberately not the canonical source. They are the AI’s evolving interpretation layer. This allows the system to connect dots without corrupting the original record.

In knowledge systems, this is powerful. Human documents often contain implicit relationships. The sidecar note layer makes those relationships explicit and searchable.

---

## Chapter 7 — Agentic Ask and Tool Calling

Early versions of `ask` were essentially single-shot retrieval:

```text
question -> retrieve top pages -> ask Ollama
```

Later versions added `ask-agentic`, which can:

1. repair common query typos;
2. select safe read-only tools;
3. call those tools;
4. build an evidence pack;
5. read relevant full pages;
6. call Ollama for synthesis;
7. record the trace.

The important change is that the LLM no longer receives only raw search snippets. It receives an explicit system prompt explaining what it can access, what tools were called, and what evidence was gathered.

This reduces a major failure mode: the model saying “I could call X next” when the tool output is already present. Release added behaviour rules to prevent that.

The agent is therefore moving from:

```text
answer from retrieved text
```

toward:

```text
inspect, retrieve, read, synthesize, record
```

That is a more capable pattern.

---

## Chapter 8 — Runtime Memory and Operational Truth

The runtime journal is a crucial concept. Documentation says what should be true. Runtime logs show what actually happened.

A reflective system needs both.

The LLM Wiki MCP records or exposes:

- ask history;
- compressed ask history;
- token metrics;
- runtime events;
- command-to-tool mapping;
- capabilities;
- config state.

This creates operational truth. If a command failed, the system can see that it failed. If token/s is low, the system can see that. If a tool is declared in the manifest but missing from implementation, reconciliation can detect that.

For agentic systems, runtime truth is vital. Without it, the system reasons from stale claims.

---

## Chapter 9 — The Role of Human Governance

A system that identifies its own gaps and proposes new functions can be powerful. It can also become dangerous if changes are automatic, opaque, or unbounded.

The LLM Wiki MCP keeps several safety principles:

- mutating operations are not dispatched casually through natural language;
- self-access commands are read-only by default;
- AI notes are sidecars, not canonical overwrites;
- package changes are versioned;
- smoke tests are produced;
- docs are updated with each release;
- users remain in the loop.

This matters because self-extension should not mean uncontrolled self-modification. The safer model is human-guided recursive improvement.

---

## Chapter 10 — The Tool as a Mirror

There is a philosophical dimension here. The tool is not conscious, but it can become reflective in a cybernetic sense. It receives feedback about its behaviour, stores that feedback, and changes future behaviour based on that stored structure.

The human brings intention, judgement, and consciousness. The LLM provides synthesis, pattern recognition, and language. The tools provide action and state. The wiki provides memory.

Together they form a loop:

```text
human intention
 -> LLM interpretation
 -> tool action
 -> wiki memory
 -> runtime trace
 -> reflection
 -> improved tool
```

This is not a replacement for human intelligence. It is an amplifier of structured thinking.

---

## Chapter 11 — A New Kind of Software Development

The LLM Wiki MCP suggests a new development style:

- every feature is documented as it appears;
- every bug can become a chapter;
- every limitation can become a function;
- every function can become a tool;
- every tool can expose its own state;
- every state can become searchable knowledge.

This collapses the distance between code, docs, memory, and usage.

Instead of software documentation being an afterthought, documentation becomes the living interface through which the system understands itself.

---

## Chapter 12 — What This Means for AGI Research

If AGI is ever built as an agentic system rather than a single model, it will need more than intelligence inside a neural network. It will need:

- memory;
- tools;
- self-models;
- runtime awareness;
- error correction;
- goal management;
- safe action boundaries;
- mechanisms for improvement;
- mechanisms for refusing unsafe change;
- mechanisms for asking for help.

The LLM Wiki MCP is not AGI, but it is a concrete working metaphor for some of these requirements.

It demonstrates that an agent can become more useful when it can say:

```text
Here is what I know.
Here is what I can do.
Here is what failed.
Here is what is missing.
Here is the function that would close the gap.
Here is the test that proves it.
```

That is a small but meaningful step toward reflective agency.

---

## Chapter 13 — Practical Roadmap

The next steps for this tool are clear:

1. Improve the agentic planner so it can read multiple pages, not only one.
2. Add a review/apply workflow for promoting AI notes into canonical links.
3. Add an automatic docs reconciliation report.
4. Add exact Ollama token metrics when available.
5. Add model comparison reports.
6. Add richer graph visualisation.
7. Add tool ontology pages that distinguish CLI commands, MCP tools, and internal helpers.
8. Add safe code-generation proposals for missing functions.
9. Add a test generator that creates smoke tests from discovered gaps.
10. Add a release-note generator from runtime traces and git diffs.

The long-term vision is a tool that can help maintain itself while remaining safe, inspectable, and human-directed.

---

## Conclusion — The Step Toward Self-Extending Intelligence

The LLM Wiki MCP is a local knowledge tool. It is also an experiment in reflective architecture.

It asks a powerful question:

```text
What if a tool could understand enough about itself to help improve itself?
```

The answer is not AGI yet. But it is a path: a bounded, transparent, tool-based, human-guided path where limitations become knowledge, knowledge becomes functions, and functions become new capabilities.

That is the heart of the project.
