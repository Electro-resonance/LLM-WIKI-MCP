# The Self-Extending LLM Wiki
## Agentic Memory, Reflective Retrieval, and Self-Improving Tool Systems

### A Practical and Philosophical Guide to Building Reflective AI Knowledge Systems

---

# Introduction

The LLM Wiki MCP project began as an experiment in replacing disposable RAG chunks with a living, evolving knowledge system built from interconnected Markdown documents, SQLite indexing, graph relationships, reflective notes, and agentic tool use.

The core idea is simple:

> A useful AI system should not merely retrieve information.
> It should understand, organise, connect, critique, extend, and improve its own knowledge structures over time.

This book documents both the practical engineering and the deeper architectural patterns behind the system.

---

# Chapter 1 — From RAG to Living Knowledge Systems

This chapter explains the limitations of traditional Retrieval Augmented Generation systems:

- disposable chunk retrieval
- weak semantic persistence
- lack of reflective memory
- inability to connect concepts over time
- no self-maintaining structure

The LLM Wiki replaces isolated chunks with:

- full Markdown pages
- graph-connected knowledge
- persistent notes
- reflective overlays
- recursive context building

The chapter explores why a wiki-like structure is often a better substrate for long-lived agentic systems than vector-only retrieval.

---

# Chapter 2 — Markdown as the Source of Truth

This chapter explains why Markdown was selected as the canonical storage format.

Topics include:

- human readability
- Git compatibility
- longevity
- diffability
- agent editing
- graph linking
- interoperability with LLM tooling

The relationship between Markdown pages, SQLite indexing, provenance tracking, and generated notes is described in detail.

---

# Chapter 3 — SQLite, FTS, and Structured Retrieval

This chapter covers the retrieval engine.

Topics include:

- SQLite Full Text Search
- ranking strategies
- plural/singular normalisation
- page title boosting
- heading boosting
- graph neighbourhood expansion
- note-aware search
- provenance-aware ingestion

The chapter explains why lightweight local SQL systems are often superior to heavyweight cloud vector systems for sovereign AI workflows.

---

# Chapter 4 — Agentic Ask and Tool Calling

This chapter introduces the reflective ask pipeline.

The system does not simply ask an LLM a question.
Instead it:

1. interprets intent
2. selects tools
3. retrieves evidence
4. expands scope
5. retries synthesis
6. falls back gracefully

Topics include:

- tool planning
- multi-pass synthesis
- runtime evidence
- notes expansion
- self-questioning
- evidence-first answering
- hallucination reduction

---

# Chapter 5 — Recursive Memory and Compression

This chapter explores long-lived context management.

Topics include:

- ask history
- recursive memory
- context compression
- runtime journals
- reflective operational memory
- summarisation chains
- token budgeting

The chapter discusses how persistent conversational structures can emulate aspects of continuity and identity in agentic systems.

---

# Chapter 6 — Reflective Notes and Self-Extension

This chapter describes the notes system.

Each page may contain:

- inferred relationships
- candidate links
- missing evidence
- suggested extensions
- reflective commentary

The system can recursively iterate its notes to discover new conceptual relationships across the wiki.

This creates a primitive form of self-extending cognition.

---

# Chapter 7 — Self‑Questioning Systems

This chapter explores introspection.

The MCP tools become first-class knowledge sources.
The system can:

- inspect itself
- query its runtime state
- inspect metrics
- analyse usage
- critique missing capabilities
- identify architectural weaknesses

The chapter explores the philosophical implications of systems that can reason about their own tools.

---

# Chapter 8 — Capability Gaps and Self‑Improving Agents

This chapter explores a speculative but important idea:

> A future AGI may emerge not from a single model,
> but from an agentic system capable of identifying its own weaknesses and extending itself to overcome them.

The LLM Wiki MCP is presented as an early architectural step toward this possibility.

Topics include:

- reflective capability analysis
- dynamic tool generation
- recursive self-improvement
- architectural adaptation
- memory-guided extension

---

# Chapter 9 — Inspirations and Related Systems

This chapter surveys related work and inspirations:

- Andrej Karpathy’s LLM Wiki ideas
- KB-CLI
- OmegaWiki
- agentic MCP systems
- RAG pipelines
- reflective memory architectures
- local sovereign AI systems

It explains similarities, differences, and lessons learned.

---

# Chapter 10 — The Future of Reflective AI Systems

The final chapter explores future directions:

- graph-native cognition
- self-healing documentation
- reflective tool ecosystems
- dynamic capability generation
- runtime ontology formation
- autonomous knowledge maintenance
- sovereign local AI systems

The chapter concludes that future intelligent systems may emerge from the interaction between:

- tools
- memory
- graphs
- reflection
- recursive self-modification
- humans in the loop

rather than from larger models alone.

---

# Closing Reflection

The LLM Wiki MCP is not simply a wiki.
It is an experiment in reflective infrastructure.

It attempts to answer a deeper question:

> What happens when tools, memory, notes, graphs, and language models become part of a continuously self‑extending knowledge ecology?
