# The Tool That Asks Itself
## A Long Chapter on Recursive Self-Questioning and Runtime Introspection

In a living LLM Wiki, the tools that drive the agent are first-class citizens. They can read, write, search, repair, transform, summarise, index, validate, and interrogate the knowledge base. Yet in most systems those tools are still treated as black boxes: they accept external input, return a result, and disappear from the model’s field of view.

This chapter develops a different pattern. A tool should be able to become visible to itself. It should be possible to ask:

- What are you configured to do?
- What tools do you expose?
- What is your current state?
- What is missing from your documentation?
- What do your own logs, metrics, and health checks say?
- Which commands are most useful?
- Which wiki pages describe you?
- Which parts of your own design are stale, contradictory, or under-specified?

This is not merely a debugging trick. It is a way of turning operational software into a knowledge-bearing participant in the wiki. The tool becomes a source. The state of the tool becomes evidence. Its configuration, metrics, function list, schema, and health report can be placed into a context pack and reasoned about by an LLM.

The pattern is generic: any tool that exposes a callable interface can be wrapped with a small self-query helper. The helper asks the tool for structured information, formats that information as Markdown, and optionally stores the answer in the wiki.

> **Why this matters**
>
> A tool that can ask itself a question is a powerful debugging aid. It can expose hidden configuration, report its own metrics, reveal stale documentation, detect that an index needs rebuilding, or explain why a query failed. By recording the answer in the wiki, future agents can reuse that knowledge without re-running the introspection logic.

---

## 1. The Tool as a Knowledge Source

A normal source might be a PDF, Word document, Markdown file, transcript, source code file, or dataset. A self-questioning wiki adds another kind of source:

```text
the current operating state of the tool itself
```

That includes:

- config files;
- CLI help text;
- MCP tool schemas;
- currently registered function names;
- SQLite index state;
- wiki health reports;
- lint output;
- graph summaries;
- recent ask history;
- Ollama model and host settings;
- token and context estimates;
- error messages;
- command usage patterns;
- known limitations;
- repair suggestions.

In other words, the system can learn not only from documents but from its own operation.

This matters because long-running LLM systems drift. Tools gain new commands. Docs become stale. Config changes. A model changes. A host moves. Search behaviour improves. A feature becomes deprecated. Without introspection, the wiki may confidently explain an older version of the system.

Self-questioning gives the wiki a route back to the current truth.

---

## 2. Identify the Introspection Surface

Most tools expose one or more introspection surfaces. In the LLM Wiki context, the obvious ones are:

- `config` — current Ollama host, model, timeout, temperature, and ask settings;
- `help` — user-facing command list;
- `FUNCTION_LIST.md` — formal list of MCP tools and CLI commands;
- `stats` — page counts, word estimates, SQLite status, tags, and categories;
- `lint` — broken links, orphan pages, and short pages;
- `graph` — node and edge counts;
- `usage` — approximate wiki tokens and largest pages;
- `history` — recent ask history;
- `recursive-preview` — current recursive ask prompt assembly;
- `schema.md` — expected wiki conventions.

A tool does not need to reveal everything. The best introspection surfaces are:

1. small enough to fit into context;
2. structured enough to parse;
3. grounded in current runtime state;
4. safe to expose;
5. useful for maintenance decisions.

For example, the Ollama-facing part of the wiki should expose the configured host and model, but it should not reveal secret API keys. A self-query page should say:

```text
Ollama host: http://localhost:11434
Ollama model: gpt-oss:20b
Recursive ask: enabled
History compression: enabled
```

It should not expose credentials or private tokens.

---

## 3. Define a Self-Query Wrapper

A self-query wrapper is a small function that turns introspection into Markdown.

A simple version looks like this:

```python
from llm_wiki_mcp.context_api import v43_load_config
import json

def introspect_ollama_config(vault_path: str) -> str:
    /config = v43_load_config(vault_path)
    ollama = config.get("ollama", {})
    /ask = config.get("ask", {})

    return f"""# Tool: Ollama Configuration

## Ollama

```json
{json.dumps(ollama, indent=2)}
```

## Ask Settings

```json
{json.dumps(ask, indent=2)}
```
"""
```

That function does not need to call the LLM. It simply exposes tool state in a form the wiki can preserve.

A richer version can combine multiple surfaces:

```python
def build_tool_self_context(vault_path: str, question: str) -> str:
    /config = v43_load_config(vault_path)
    /stats = wiki_usage_snapshot(vault_path)
    /history = v43_load_history(vault_path, max_records=10)

    return f"""# Tool Self-Question Context

Question: {question}

## Current Config

```json
{json.dumps(config, indent=2)}
```

## Usage Snapshot

```json
{json.dumps(stats, indent=2)}
```

## Recent Ask History

```json
{json.dumps(history, indent=2)}
```
"""
```

The wrapper creates a bridge between runtime state and durable knowledge.

---

## 4. Store the Introspection Result in the Wiki

There are two main strategies.

### Strategy A — Ephemeral Context

The tool builds self-context and passes it to the LLM, but does not write it to the wiki.

This is useful when:

- the result changes frequently;
- the user is debugging;
- the output is too noisy;
- the context might contain sensitive data;
- the answer is only needed once.

Example:

```text
wiki> /self what model are you configured to use?
```

The CLI prints a Markdown self-context block, which can be copied into an LLM prompt or inspected directly.

### Strategy B — Durable Page

The tool writes a page such as:

```text
Tool - Ollama Config.md
Tool - CLI Help.md
Tool - MCP Function List.md
Tool - Wiki Health Snapshot.md
```

This is useful when:

- the snapshot explains a decision;
- the configuration is important for reproducibility;
- the page can be cited later;
- the system needs an audit trail;
- the state forms part of project documentation.

A deterministic page title is important. Avoid vague titles such as `Tool Info`. Prefer:

```text
Tool - Ollama Config.md
Tool - Recursive Ask Settings.md
Tool - Query Usage Snapshot.md
```

---

## 5. Register the Wrapper as an MCP Tool

The MCP surface should expose introspection in a way an agent can call safely.

A specific tool might look like this:

```json
{
  "name": "wiki_introspect_ollama",
  "description": "Return the current Ollama configuration and ask settings for the active vault.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "vault_path": {
        "type": "string",
        "description": "Path to the wiki vault"
      },
      "write_page": {
        "type": "boolean",
        "description": "Whether to write the result into the wiki"
      }
    },
    "required": []
  }
}
```

A more generic tool might look like:

```json
{
  "name": "wiki_tool_self_question",
  "description": "Build self-question context from config, docs, function list, health reports, and recent usage.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "vault_path": {"type": "string"},
      "question": {"type": "string"},
      "include_history": {"type": "boolean"},
      "include_config": {"type": "boolean"},
      "include_health": {"type": "boolean"}
    },
    "required": ["question"]
  }
}
```

This is the more powerful pattern because it lets the LLM ask broad questions about the tool itself.

---

## 6. Ask the Tool About Its Own Behaviour

Once the self-query surface exists, the user can ask questions such as:

```text
wiki> /self what tools do you expose?
wiki> /self what is missing from your docs?
wiki> /self why might ask fail?
wiki> /self how many tokens are in the wiki?
wiki> /self what is the active Ollama model?
wiki> /self is recursive ask enabled?
```

The key is that the tool is not guessing from memory. It is reading its own files and current config.

For example, when asked:

```text
wiki> /self is recursive ask enabled?
```

the system can inspect:

```text
wiki_vault/llm_wiki_config.json
```

and answer from the actual `ask.recursive_enabled` setting.

---

## 7. Use the Introspection Result in a Context Pack

Once the introspection result exists as Markdown, it becomes a normal wiki source.

For example:

```python
pack = engine.retrieve_articles(
    "current recursive ask configuration and history compression",
    top_k=5
)
```

A good context pack might include:

- `Tool - Recursive Ask Settings.md`
- `V43_RECURSIVE_ASK.md`
- `V43_CONFIG_LOAD_SAVE.md`
- `QUERY_USAGE_AND_TOKEN_STATS.md`
- `TOOL_SELF_QUESTIONING.md`

The LLM can then answer configuration questions using maintained pages and runtime snapshots.

This is where the LLM Wiki becomes stronger than ordinary RAG. It can retrieve both documentary knowledge and operational knowledge.

---

## 8. Log the Decision

Per the wiki skill of logging important decisions, introspection events can be recorded.

Example:

```python
engine.wiki_log_decision(
    "Added self-questioning support so the tool can explain its own configuration and missing docs.",
    "Tool Self-Questioning"
)
```

Decision logs are valuable because they explain why the system has its current shape. A future maintainer can see not only what was changed, but why.

---

## 9. Lint and Maintain

After adding self-query pages, run:

```bash
python3 llm_wiki_cli.py --vault ./wiki_vault lint
```

Useful checks:

- Is the page orphaned?
- Does it link to the relevant docs?
- Are references full filenames?
- Does it expose secrets?
- Is the page too short to be useful?
- Does it duplicate another snapshot?
- Should old snapshots be archived?

Self-questioning can create noise if not controlled. The wiki should distinguish between:

- durable explanations;
- temporary runtime snapshots;
- logs;
- metrics;
- decisions;
- generated summaries.

A good convention is:

```text
Tool - Name.md             durable explanation
Snapshot - Name - Date.md  dated runtime state
Log - Name.md              append-only operational log
Decision Log.md            durable reasoning record
```

---

## 10. Safety and Privacy

A self-questioning tool can accidentally expose sensitive material. It should follow rules:

1. Never include API keys or secrets.
2. Redact tokens by default.
3. Prefer summaries over raw environment dumps.
4. Keep destructive tools out of self-query loops.
5. Require explicit confirmation before writing pages.
6. Keep a clear source list.
7. Use dry-run output before durable writes.
8. Bound recursive tool calls.
9. Avoid infinite self-inspection loops.
10. Make it obvious whether the answer came from docs, config, runtime state, or LLM inference.

This matters because the tool’s own configuration may contain operational details.

---

## 11. Recursive Self-Questioning

Release introduces recursive ask and history compression controls. This opens a deeper pattern:

```text
/ask -> answer -> record history -> compress history -> future ask uses prior compressed context
```

For self-questioning, this allows the tool to maintain a rolling understanding of its own evolution.

Example:

```text
wiki> /recursive on
wiki> /askrec what changed in this tool recently?
```

The answer can include prior ask history, compressed summaries, and current wiki state.

This must be bounded. A reflective tool should not recursively consume its entire history forever. The correct pattern is:

- keep recent turns verbatim;
- compress older turns;
- preserve decisions and citations;
- discard low-value chatter;
- store durable conclusions as pages;
- keep configuration explicit and editable.

Recursive self-questioning becomes a disciplined form of operational memory.

---

## 12. Tool Self-Questioning as a Design Pattern

The pattern generalises beyond LLM Wiki.

Any MCP tool can expose:

```text
tool_config
tool_status
tool_schema
tool_metrics
tool_recent_errors
tool_self_question
```

For a code-search tool, self-questioning might answer:

```text
Which repositories are indexed?
When was the index last updated?
Which filetypes are ignored?
```

For a database tool:

```text
Which schemas are available?
Which tables are largest?
Which queries failed recently?
```

For a document-generation tool:

```text
Which templates are available?
Which export formats are configured?
Which documents failed validation?
```

The broader idea is that tools should not only do work. They should explain their own state, limits, and assumptions.

---

## 13. Missing Evidence and Maintenance Actions

| Issue | Missing Evidence | Suggested Action |
|---|---|---|
| No durable tool-self page in many vaults | The wiki may only contain docs, not runtime state | Add `Tool Self-Questioning.md` and link it from `index.md` |
| No generic introspection MCP tool | Current tools may expose config but not broad self-questioning | Add `wiki_tool_self_question` |
| No snapshot policy | Runtime pages can become stale | Add `Snapshot - ...` naming conventions |
| No secret-redaction policy | Config may contain sensitive fields | Add redaction helper and docs |
| No recursive limit policy | Self-questioning can loop forever | Add max tool calls, max history tokens, and compression |
| No usage metrics | The tool cannot explain token/query behaviour | Add `wiki_usage_snapshot` and query logs |
| No source-type clarity | Answers may cite generated pages as if they were source docs | Preserve full filenames and source types |

---

## 14. Summary

A tool that can ask itself a question becomes inspectable. An inspectable tool becomes maintainable. A maintainable tool becomes part of the knowledge system it serves.

The pattern is:

1. Identify the introspection surface.
2. Wrap it in a self-query helper.
3. Format the result as Markdown.
4. Optionally store it as a wiki page.
5. Register it as an MCP tool.
6. Use it in context packs.
7. Log the decision.
8. Lint and maintain the resulting pages.
9. Redact secrets.
10. Bound recursion.
11. Preserve full source filenames.
12. Let the tool explain itself from evidence, not memory.

By following this pattern, any tool in the LLM Wiki ecosystem can become a first-class knowledge source, enabling agents to reason about their own tooling without external debugging sessions.
