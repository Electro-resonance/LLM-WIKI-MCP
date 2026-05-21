# MCP Functions Reference

This file lists the MCP tools exposed by the release server. It is written for AI clients and agent frameworks that need to decide which function to call, when to call it, and whether it changes state.

## Recommended AI usage pattern

1. Discover capabilities with `wiki_tool_catalog`, `wiki_capabilities`, or `wiki_agentic_tool_manifest`.
2. Gather evidence with `wiki_search`, `wiki_search_with_notes`, `wiki_retrieve_articles`, `wiki_read_page`, or `wiki_combined_page_context` before answering.
3. Use `wiki_ask`, `wiki_ask_agentic`, `wiki_ask_plain`, or `wiki_ask_ollama` for local-model synthesis.
4. Use lint, graph, notes, health, and reconcile tools to maintain the wiki as a structured knowledge graph.
5. Treat page writing, ingest, delete, rename, config, record, and repair/apply tools as state-changing. Prefer read-only inspection unless the user explicitly asks for changes.

Most tools accept an optional `vault_path`/`vault` style argument; if omitted, the MCP server uses its configured default `wiki_vault`.

## Complete tool list

| Tool | Group | Purpose |
| --- | --- | --- |
| `wiki_init` | Other MCP tools | Initialise the local Markdown wiki vault with seed pages and SQLite index. |
| `wiki_status` | Other MCP tools | Return vault paths, page counts, raw counts, estimated word count, and index status. |
| `wiki_create_page` | Wiki writing and ingestion tools | Create a wiki page with YAML-style front matter. |
| `wiki_read_page` | Search, retrieval, and ask tools | Read a wiki page by title, including metadata and outgoing wiki links. |
| `wiki_update_page` | Wiki writing and ingestion tools | Replace, append, or prepend content on an existing wiki page. |
| `wiki_append_section` | Wiki writing and ingestion tools | Append a headed section to a wiki page. |
| `wiki_search` | Search, retrieval, and ask tools | Search wiki pages using SQLite FTS with prefix, singular/plural expansion, and fallback token scoring. |
| `wiki_search_diagnostics` | Search, retrieval, and ask tools | Explain how a query is normalised and show suggestions when search results are surprising. |
| `wiki_retrieve_articles` | Search, retrieval, and ask tools | Given a prompt/query, search the wiki and retrieve the top-k full maintained articles plus an LLM-ready context block. |
| `wiki_ask_ollama` | Search, retrieval, and ask tools | Prompt -> retrieve wiki context -> ask a local Ollama model using configurable host/model. |
| `wiki_config` | Configuration tools | Create/read/update/test the llm_wiki_config.json file containing Ollama host/model defaults. |
| `wiki_reindex` | Maintenance and documentation tools | Rebuild the SQLite index from Markdown files. |
| `wiki_ingest_file` | Wiki writing and ingestion tools | Ingest a Markdown/text file into the wiki as a source page. |
| `wiki_ingest_directory` | Wiki writing and ingestion tools | Bulk ingest Markdown, TXT, RTF, PDF, DOCX, and legacy DOC stub content from a directory or one supported file. |
| `wiki_import_transcript` | Wiki writing and ingestion tools | Convert a transcript or long chat into a durable wiki page. |
| `wiki_build_context_pack` | Search, retrieval, and ask tools | Build a bounded context pack from the most relevant wiki pages. |
| `wiki_graph_links` | Graph and relationship tools | Return wiki nodes, outgoing edges, and backlinks from [[wiki-links]]. |
| `wiki_lint` | Maintenance and documentation tools | Check for broken links, orphan pages, and very short pages. |
| `wiki_repair_lint` | Maintenance and documentation tools | Plan or apply safe repairs for broken links, orphan pages, and short pages. Dry-run by default. |
| `wiki_export_llms_txt` | Other MCP tools | Export the wiki into an llms.txt style context file. |
| `wiki_log_decision` | Other MCP tools | Log an architectural or project decision into SQLite and the Decision Log page. |
| `wiki_list_pages` | Search, retrieval, and ask tools | List pages with metadata, optional tag/category filters. |
| `wiki_resolve` | Search, retrieval, and ask tools | Resolve loose document handles to canonical wiki titles with suggestions. |
| `wiki_backlinks` | Graph and relationship tools | Return incoming and outgoing links for a page. |
| `wiki_rename_page` | Wiki writing and ingestion tools | Rename a page and optionally update [[wiki-links]] across the vault. |
| `wiki_delete_page` | Wiki writing and ingestion tools | Delete a page with optional tombstone backup and report inbound links. |
| `wiki_categories` | Graph and relationship tools | List categories and tags in use. |
| `wiki_toc` | Maintenance and documentation tools | Generate/update a Table of Contents wiki page. |
| `wiki_schema` | Maintenance and documentation tools | Read or update the wiki schema/conventions document. |
| `wiki_dry_run_write` | Wiki writing and ingestion tools | Preview a create/update and lint it without writing. |
| `wiki_related` | Graph and relationship tools | Find related pages using shared terms and links. |
| `wiki_health_report` | Maintenance and documentation tools | Summarise index, lint, graph density, and operational pain points. |
| `wiki_mermaid_graph` | Graph and relationship tools | Render the wiki document-link graph as Mermaid flowchart text, optionally writing a Markdown file. |
| `wiki_mermaid_neighbourhood` | Graph and relationship tools | Render a Mermaid graph centred on a page and its nearby incoming/outgoing links. |
| `wiki_tool_self_question` | Agent self-access and capability tools | Ask the LLM Wiki tool about itself by building a self-describing context block from config, docs, and wiki files. |
| `wiki_usage_snapshot` | Agent self-access and capability tools | Estimate wiki size and token usage for the current vault. |
| `wiki_config_load` | Configuration tools | Load and persist active vault config defaults. |
| `wiki_config_set` | Configuration tools | Persistently set a dotted config key, e.g. ask.recursive_enabled. |
| `wiki_recursive_ask_preview` | Search, retrieval, and ask tools | Preview recursive ask context with rolling history compression. |
| `wiki_ask_history` | Runtime history, provenance, and logging tools | Read recent ask history records. |
| `wiki_record_ask_turn` | Runtime history, provenance, and logging tools | Record question, prompt, answer, sources and token estimates into ask history, compressing when needed. |
| `wiki_compress_history` | Runtime history, provenance, and logging tools | Compress ask history if the configured token budget is exceeded. |
| `wiki_recursive_context` | Search, retrieval, and ask tools | Build recursive context from compressed long-term memory, recent ask memory, retrieved wiki context, and the current question. |
| `wiki_llm_metrics` | Agent self-access and capability tools | Return recorded LLM token/s, latency and token usage metrics. |
| `wiki_self_access_snapshot` | Agent self-access and capability tools | Return config, usage, metrics, history and compression state for tool self-access. |
| `wiki_record_ask_turn_with_metrics` | Runtime history, provenance, and logging tools | Record question, prompt, answer, sources, elapsed seconds and token/s metrics. |
| `wiki_capabilities` | Agent self-access and capability tools | Return live runtime capabilities: LLM, retrieval, runtime self-access, maintenance, and relevant files. |
| `wiki_runtime_journal` | Runtime history, provenance, and logging tools | Return recent runtime execution journal events. |
| `wiki_record_runtime_event` | Runtime history, provenance, and logging tools | Record a runtime event with command, query, tools used, success, latency, and token metrics. |
| `wiki_command_tool_map` | Agent self-access and capability tools | Return the mapping from CLI commands to internal/MCP tools. |
| `wiki_reconcile_docs` | Maintenance and documentation tools | Compare docs, command surface and function list to identify missing or stale documentation. |
| `wiki_runtime_graph` | Graph and relationship tools | Return Mermaid graph of runtime execution flow. |
| `wiki_safe_self_dispatch` | Agent self-access and capability tools | Map a natural-language request such as 'run self-stats' to a safe read-only self-access tool and execute it. |
| `wiki_page_notes_iterate` | AI sidecar notes and link tools | Create/update AI sidecar notes for a page, including key terms and candidate links. |
| `wiki_notes_iterate_all` | AI sidecar notes and link tools | Iterate AI sidecar notes for all pages or a limited number. |
| `wiki_search_with_notes` | AI sidecar notes and link tools | Search combined source page text and AI sidecar notes. |
| `wiki_notes_status` | AI sidecar notes and link tools | Return AI notes coverage and missing notes. |
| `wiki_candidate_links` | AI sidecar notes and link tools | Find candidate links for a page using source text and AI notes. |
| `wiki_combined_page_context` | Search, retrieval, and ask tools | Return a page combined with its AI sidecar notes for retrieval/context. |
| `wiki_notes_graph` | AI sidecar notes and link tools | Render Mermaid graph from AI note candidate links. |
| `wiki_ask_agentic` | Search, retrieval, and ask tools | Bounded read-only agentic ask: plan, call local wiki tools, build evidence pack and LLM prompt. |
| `wiki_limitations_report` | Agent self-access and capability tools | Return fixed/reduced and remaining known limitations. |
| `wiki_agentic_tool_manifest` | Agent self-access and capability tools | Return the safe tool manifest used by bounded agentic ask. |
| `wiki_ask` | Search, retrieval, and ask tools | Ask the wiki using current ask mode, agentic by default. |
| `wiki_ask_plain` | Search, retrieval, and ask tools | Plain retrieve-and-synthesize ask without tool loop. |
| `wiki_set_ask_mode` | Configuration tools | Set default ask mode: agentic or plain. |
| `wiki_tool_catalog` | Agent self-access and capability tools | Return the full Release tool catalogue. |
| `wiki_planner_tools` | Agent self-access and capability tools | Return planner tool groups. |
| `wiki_config_test` | Configuration tools | Test configured Ollama connection. |
| `wiki_resolve_intent` | Search, retrieval, and ask tools | Resolve short/contextual user intent before planning tools. |
| `wiki_provenance_summary` | Runtime history, provenance, and logging tools | Return SQL ingest provenance summary. |
| `wiki_file_provenance_status` | Runtime history, provenance, and logging tools | Check whether a file is new, changed or unchanged based on mtime and SHA256. |
| `wiki_startup_commands` | Runtime history, provenance, and logging tools | Get startup command list from config. |
| `wiki_set_default_startup` | Runtime history, provenance, and logging tools | Set startup commands to /ingest ./docs and /notes-all. |
| `wiki_build_development_history` | Maintenance and documentation tools | Build GitHub-friendly DEVELOPMENT_HISTORY.md. |
| `wiki_ingest_directory_plan` | Wiki writing and ingestion tools | Plan a provenance-aware directory or single-file ingest without updating unchanged files. |
| `wiki_consolidate_docs` | Maintenance and documentation tools | Consolidate docs into fewer category files and archive scattered version docs. |

## AI sidecar notes and link tools

### `wiki_candidate_links`

**Purpose:** Find candidate links for a page using source text and AI notes.
**Common inputs:** `vault_path`, `title`, `page`, `limit`.
**Required:** `title`.
**How an AI should use it:** Use to understand wiki structure, page relationships, and possible cross-links.

### `wiki_notes_graph`

**Purpose:** Render Mermaid graph from AI note candidate links.
**Common inputs:** `vault_path`, `limit_pages`.
**Required:** none.
**How an AI should use it:** Use to understand wiki structure, page relationships, and possible cross-links.

### `wiki_notes_iterate_all`

**Purpose:** Iterate AI sidecar notes for all pages or a limited number.
**Common inputs:** `vault_path`, `limit`.
**Required:** none.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

### `wiki_notes_status`

**Purpose:** Return AI notes coverage and missing notes.
**Common inputs:** `vault_path`.
**Required:** none.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

### `wiki_page_notes_iterate`

**Purpose:** Create/update AI sidecar notes for a page, including key terms and candidate links.
**Common inputs:** `vault_path`, `title`, `page`, `mode`, `max_links`.
**Required:** `title`.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

### `wiki_search_with_notes`

**Purpose:** Search combined source page text and AI sidecar notes.
**Common inputs:** `vault_path`, `query`, `limit`.
**Required:** `query`.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

## Agent self-access and capability tools

### `wiki_agentic_tool_manifest`

**Purpose:** Return the safe tool manifest used by bounded agentic ask.
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_capabilities`

**Purpose:** Return live runtime capabilities: LLM, retrieval, runtime self-access, maintenance, and relevant files.
**Common inputs:** `vault_path`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_command_tool_map`

**Purpose:** Return the mapping from CLI commands to internal/MCP tools.
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

### `wiki_limitations_report`

**Purpose:** Return fixed/reduced and remaining known limitations.
**Common inputs:** `vault_path`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_llm_metrics`

**Purpose:** Return recorded LLM token/s, latency and token usage metrics.
**Common inputs:** `vault_path`, `limit`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_planner_tools`

**Purpose:** Return planner tool groups.
**Common inputs:** `vault_path`, `question`, `query`, `title`, `mode`, `limit`, `dry_run`, `apply`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_safe_self_dispatch`

**Purpose:** Map a natural-language request such as 'run self-stats' to a safe read-only self-access tool and execute it.
**Common inputs:** `vault_path`, `query`, `question`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_self_access_snapshot`

**Purpose:** Return config, usage, metrics, history and compression state for tool self-access.
**Common inputs:** `vault_path`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_tool_catalog`

**Purpose:** Return the full Release tool catalogue.
**Common inputs:** `vault_path`, `question`, `query`, `title`, `mode`, `limit`, `dry_run`, `apply`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_tool_self_question`

**Purpose:** Ask the LLM Wiki tool about itself by building a self-describing context block from config, docs, and wiki files.
**Common inputs:** `vault_path`, `question`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_usage_snapshot`

**Purpose:** Estimate wiki size and token usage for the current vault.
**Common inputs:** `vault_path`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

## Configuration tools

### `wiki_config`

**Purpose:** Create/read/update/test the llm_wiki_config.json file containing Ollama host/model defaults.
**Common inputs:** `action`, `key`, `value`.
**Required:** none.
**How an AI should use it:** Use to inspect or change local configuration such as Ollama host, model, or ask mode.

### `wiki_config_load`

**Purpose:** Load and persist active vault config defaults.
**Common inputs:** `vault_path`.
**Required:** none.
**How an AI should use it:** Use to inspect or change local configuration such as Ollama host, model, or ask mode.

### `wiki_config_set`

**Purpose:** Persistently set a dotted config key, e.g. ask.recursive_enabled.
**Common inputs:** `vault_path`, `key`, `value`.
**Required:** `key`, `value`.
**How an AI should use it:** Use to inspect or change local configuration such as Ollama host, model, or ask mode.

### `wiki_config_test`

**Purpose:** Test configured Ollama connection.
**Common inputs:** `vault_path`, `question`, `query`, `title`, `mode`, `limit`, `dry_run`, `apply`.
**Required:** none.
**How an AI should use it:** Use to inspect or change local configuration such as Ollama host, model, or ask mode.

### `wiki_set_ask_mode`

**Purpose:** Set default ask mode: agentic or plain.
**Common inputs:** `vault_path`, `question`, `query`, `title`, `mode`, `limit`, `dry_run`, `apply`.
**Required:** none.
**How an AI should use it:** Use to inspect or change local configuration such as Ollama host, model, or ask mode.

## Graph and relationship tools

### `wiki_backlinks`

**Purpose:** Return incoming and outgoing links for a page.
**Common inputs:** `title`.
**Required:** `title`.
**How an AI should use it:** Use to understand wiki structure, page relationships, and possible cross-links.

### `wiki_categories`

**Purpose:** List categories and tags in use.
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

### `wiki_graph_links`

**Purpose:** Return wiki nodes, outgoing edges, and backlinks from [[wiki-links]].
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use to understand wiki structure, page relationships, and possible cross-links.

### `wiki_mermaid_graph`

**Purpose:** Render the wiki document-link graph as Mermaid flowchart text, optionally writing a Markdown file.
**Common inputs:** `direction`, `include_orphans`, `max_edges`, `output_path`.
**Required:** none.
**How an AI should use it:** Use to understand wiki structure, page relationships, and possible cross-links.

### `wiki_mermaid_neighbourhood`

**Purpose:** Render a Mermaid graph centred on a page and its nearby incoming/outgoing links.
**Common inputs:** `title`, `depth`, `direction`, `output_path`.
**Required:** `title`.
**How an AI should use it:** Use to understand wiki structure, page relationships, and possible cross-links.

### `wiki_related`

**Purpose:** Find related pages using shared terms and links.
**Common inputs:** `title`, `limit`.
**Required:** `title`.
**How an AI should use it:** Use to understand wiki structure, page relationships, and possible cross-links.

### `wiki_runtime_graph`

**Purpose:** Return Mermaid graph of runtime execution flow.
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use to understand wiki structure, page relationships, and possible cross-links.

## Maintenance and documentation tools

### `wiki_build_development_history`

**Purpose:** Build GitHub-friendly DEVELOPMENT_HISTORY.md.
**Common inputs:** `vault_path`, `path`, `file_path`, `project_root`, `limit`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_consolidate_docs`

**Purpose:** Consolidate docs into fewer category files and archive scattered version docs.
**Common inputs:** `project_root`, `archive`.
**Required:** none.
**How an AI should use it:** Use for diagnostics or maintenance. Report findings first, and only apply repairs when requested.

### `wiki_health_report`

**Purpose:** Summarise index, lint, graph density, and operational pain points.
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use for diagnostics or maintenance. Report findings first, and only apply repairs when requested.

### `wiki_lint`

**Purpose:** Check for broken links, orphan pages, and very short pages.
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use for diagnostics or maintenance. Report findings first, and only apply repairs when requested.

### `wiki_reconcile_docs`

**Purpose:** Compare docs, command surface and function list to identify missing or stale documentation.
**Common inputs:** `vault_path`, `project_root`.
**Required:** none.
**How an AI should use it:** Use for diagnostics or maintenance. Report findings first, and only apply repairs when requested.

### `wiki_reindex`

**Purpose:** Rebuild the SQLite index from Markdown files.
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use for diagnostics or maintenance. Report findings first, and only apply repairs when requested.

### `wiki_repair_lint`

**Purpose:** Plan or apply safe repairs for broken links, orphan pages, and short pages. Dry-run by default.
**Common inputs:** `apply`, `fix_broken`, `link_orphans`, `expand_short`, `create_missing`, `index_page`.
**Required:** none.
**How an AI should use it:** Use for diagnostics or maintenance. Report findings first, and only apply repairs when requested.

### `wiki_schema`

**Purpose:** Read or update the wiki schema/conventions document.
**Common inputs:** `update`, `body`.
**Required:** none.
**How an AI should use it:** Use for diagnostics or maintenance. Report findings first, and only apply repairs when requested.

### `wiki_toc`

**Purpose:** Generate/update a Table of Contents wiki page.
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use for diagnostics or maintenance. Report findings first, and only apply repairs when requested.

## Other MCP tools

### `wiki_export_llms_txt`

**Purpose:** Export the wiki into an llms.txt style context file.
**Common inputs:** `output_path`, `max_chars`.
**Required:** none.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

### `wiki_init`

**Purpose:** Initialise the local Markdown wiki vault with seed pages and SQLite index.
**Common inputs:** `vault`.
**Required:** none.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

### `wiki_log_decision`

**Purpose:** Log an architectural or project decision into SQLite and the Decision Log page.
**Common inputs:** `title`, `decision`, `rationale`, `links`.
**Required:** `title`, `decision`.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

### `wiki_status`

**Purpose:** Return vault paths, page counts, raw counts, estimated word count, and index status.
**Common inputs:** none.
**Required:** none.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

## Runtime history, provenance, and logging tools

### `wiki_ask_history`

**Purpose:** Read recent ask history records.
**Common inputs:** `vault_path`, `limit`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_compress_history`

**Purpose:** Compress ask history if the configured token budget is exceeded.
**Common inputs:** `vault_path`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_file_provenance_status`

**Purpose:** Check whether a file is new, changed or unchanged based on mtime and SHA256.
**Common inputs:** `vault_path`, `path`, `file_path`, `project_root`, `limit`.
**Required:** none.
**How an AI should use it:** Use to inspect or record operational history/provenance when the workflow requires it.

### `wiki_provenance_summary`

**Purpose:** Return SQL ingest provenance summary.
**Common inputs:** `vault_path`, `path`, `file_path`, `project_root`, `limit`.
**Required:** none.
**How an AI should use it:** Use to inspect or record operational history/provenance when the workflow requires it.

### `wiki_record_ask_turn`

**Purpose:** Record question, prompt, answer, sources and token estimates into ask history, compressing when needed.
**Common inputs:** `vault_path`, `question`, `prompt`, `answer`, `sources`, `metadata`.
**Required:** `question`, `answer`.
**How an AI should use it:** Use to inspect or record operational history/provenance when the workflow requires it.

### `wiki_record_ask_turn_with_metrics`

**Purpose:** Record question, prompt, answer, sources, elapsed seconds and token/s metrics.
**Common inputs:** `vault_path`, `question`, `prompt`, `answer`, `sources`, `elapsed_seconds`, `metadata`.
**Required:** `question`, `answer`.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_record_runtime_event`

**Purpose:** Record a runtime event with command, query, tools used, success, latency, and token metrics.
**Common inputs:** `vault_path`, `command`, `query`, `tools_used`, `success`, `latency_seconds`, `token_metrics`, `metadata`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_runtime_journal`

**Purpose:** Return recent runtime execution journal events.
**Common inputs:** `vault_path`, `limit`.
**Required:** none.
**How an AI should use it:** Use when the AI needs self-awareness about capabilities, usage, limits, runtime state, or available tools.

### `wiki_set_default_startup`

**Purpose:** Set startup commands to /ingest ./docs and /notes-all.
**Common inputs:** `vault_path`, `path`, `file_path`, `project_root`, `limit`.
**Required:** none.
**How an AI should use it:** Use to inspect or record operational history/provenance when the workflow requires it.

### `wiki_startup_commands`

**Purpose:** Get startup command list from config.
**Common inputs:** `vault_path`, `path`, `file_path`, `project_root`, `limit`.
**Required:** none.
**How an AI should use it:** Use to inspect or record operational history/provenance when the workflow requires it.

## Search, retrieval, and ask tools

### `wiki_ask`

**Purpose:** Ask the wiki using current ask mode, agentic by default.
**Common inputs:** `vault_path`, `question`, `query`, `title`, `mode`, `limit`, `dry_run`, `apply`.
**Required:** none.
**How an AI should use it:** Use when the user wants an answer synthesized from wiki evidence by the configured local LLM.

### `wiki_ask_agentic`

**Purpose:** Bounded read-only agentic ask: plan, call local wiki tools, build evidence pack and LLM prompt.
**Common inputs:** `vault_path`, `question`, `prompt`, `max_tool_calls`, `dry_run`.
**Required:** `question`.
**How an AI should use it:** Use when the user wants an answer synthesized from wiki evidence by the configured local LLM.

### `wiki_ask_ollama`

**Purpose:** Prompt -> retrieve wiki context -> ask a local Ollama model using configurable host/model.
**Common inputs:** `question`, `prompt`, `top_k`, `model`, `host`, `temperature`, `timeout_seconds`, `max_context_chars`, `max_chars_per_article`, `dry_run`.
**Required:** none.
**How an AI should use it:** Use when the user wants an answer synthesized from wiki evidence by the configured local LLM.

### `wiki_ask_plain`

**Purpose:** Plain retrieve-and-synthesize ask without tool loop.
**Common inputs:** `vault_path`, `question`, `query`, `title`, `mode`, `limit`, `dry_run`, `apply`.
**Required:** none.
**How an AI should use it:** Use when the user wants an answer synthesized from wiki evidence by the configured local LLM.

### `wiki_build_context_pack`

**Purpose:** Build a bounded context pack from the most relevant wiki pages.
**Common inputs:** `query`, `limit`, `max_chars`.
**Required:** `query`.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

### `wiki_combined_page_context`

**Purpose:** Return a page combined with its AI sidecar notes for retrieval/context.
**Common inputs:** `vault_path`, `title`, `page`.
**Required:** `title`.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

### `wiki_list_pages`

**Purpose:** List pages with metadata, optional tag/category filters.
**Common inputs:** `category`, `tag`, `limit`.
**Required:** none.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

### `wiki_read_page`

**Purpose:** Read a wiki page by title, including metadata and outgoing wiki links.
**Common inputs:** `title`.
**Required:** `title`.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

### `wiki_recursive_ask_preview`

**Purpose:** Preview recursive ask context with rolling history compression.
**Common inputs:** `vault_path`, `question`, `base_context`, `recursive`.
**Required:** `question`.
**How an AI should use it:** Use when the user request clearly matches the tool purpose.

### `wiki_recursive_context`

**Purpose:** Build recursive context from compressed long-term memory, recent ask memory, retrieved wiki context, and the current question.
**Common inputs:** `vault_path`, `question`, `base_context`.
**Required:** `question`.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

### `wiki_resolve`

**Purpose:** Resolve loose document handles to canonical wiki titles with suggestions.
**Common inputs:** `handle`, `limit`.
**Required:** `handle`.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

### `wiki_resolve_intent`

**Purpose:** Resolve short/contextual user intent before planning tools.
**Common inputs:** `vault_path`, `question`.
**Required:** `question`.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

### `wiki_retrieve_articles`

**Purpose:** Given a prompt/query, search the wiki and retrieve the top-k full maintained articles plus an LLM-ready context block.
**Common inputs:** `prompt`, `query`, `top_k`, `limit`, `max_chars_per_article`, `max_total_chars`, `include_metadata`.
**Required:** none.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

### `wiki_search`

**Purpose:** Search wiki pages using SQLite FTS with prefix, singular/plural expansion, and fallback token scoring.
**Common inputs:** `query`, `limit`.
**Required:** `query`.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

### `wiki_search_diagnostics`

**Purpose:** Explain how a query is normalised and show suggestions when search results are surprising.
**Common inputs:** `query`, `limit`.
**Required:** `query`.
**How an AI should use it:** Use to gather, disambiguate, or package evidence before answering.

## Wiki writing and ingestion tools

### `wiki_append_section`

**Purpose:** Append a headed section to a wiki page.
**Common inputs:** `title`, `heading`, `content`.
**Required:** `title`, `content`.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

### `wiki_create_page`

**Purpose:** Create a wiki page with YAML-style front matter.
**Common inputs:** `title`, `body`, `tags`, `source`, `overwrite`.
**Required:** `title`, `body`.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

### `wiki_delete_page`

**Purpose:** Delete a page with optional tombstone backup and report inbound links.
**Common inputs:** `title`, `tombstone`.
**Required:** `title`.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

### `wiki_dry_run_write`

**Purpose:** Preview a create/update and lint it without writing.
**Common inputs:** `title`, `body`, `mode`.
**Required:** `title`, `body`.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

### `wiki_import_transcript`

**Purpose:** Convert a transcript or long chat into a durable wiki page.
**Common inputs:** `transcript`, `title`, `speaker_prefixes`.
**Required:** `transcript`.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

### `wiki_ingest_directory`

**Purpose:** Bulk ingest Markdown, TXT, RTF, PDF, DOCX, and legacy DOC stub content from a directory or one supported file.
**Common inputs:** `directory`, `pattern`, `recursive`, `limit`.
**Required:** `directory`.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

### `wiki_ingest_directory_plan`

**Purpose:** Plan a provenance-aware directory or single-file ingest without updating unchanged files.
**Common inputs:** `vault_path`, `directory`, `path`, `recursive`, `dry_run`.
**Required:** none.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

### `wiki_ingest_file`

**Purpose:** Ingest a Markdown/text file into the wiki as a source page.
**Common inputs:** `path`, `title`, `copy_raw`.
**Required:** `path`.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

### `wiki_rename_page`

**Purpose:** Rename a page and optionally update [[wiki-links]] across the vault.
**Common inputs:** `old_title`, `new_title`, `update_links`.
**Required:** `old_title`, `new_title`.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

### `wiki_update_page`

**Purpose:** Replace, append, or prepend content on an existing wiki page.
**Common inputs:** `title`, `body`, `mode`.
**Required:** `title`, `body`.
**How an AI should use it:** Use only when the user asks to add, preview, or change wiki content; prefer dry-run before destructive/state-changing actions.

## Minimal MCP call examples

Search for evidence:

```json
{"name": "wiki_search_with_notes", "arguments": {"query": "architecture", "limit": 5}}
```

Read a known page:

```json
{"name": "wiki_read_page", "arguments": {"title": "Overview"}}
```

Ask using the configured local model:

```json
{"name": "wiki_ask", "arguments": {"question": "How does ingestion work?"}}
```

Inspect server capabilities:

```json
{"name": "wiki_capabilities", "arguments": {}}
```

## Ask-context behaviour for AI clients

The release ask pipeline now builds a bounded context pack before calling the local model. AI clients should prefer `wiki_ask_agentic` for normal question answering and use dry-run/protocol modes when they need to inspect evidence before synthesis. The context pack prioritises operational self-context for identity/runtime questions, recent ask/reply history for follow-ups, and fuller page reads when a search produces only a few strong source matches.

Recommended AI usage:

1. Use search tools to identify likely pages.
2. Read full pages when the source set is small and relevant.
3. Keep recent ask history for follow-ups, but do not treat it as immutable truth.
4. If an answer is uncertain, state uncertainty and still produce a supported synthesis.
5. Avoid returning raw references only; build an answer from the evidence.


## Long-document search tools

### `wiki_search_with_notes`

The generic MCP search now returns snippets centred around the match index instead of the beginning of the page. This is important for large books where the relevant passage may appear near the end of an ingested source page. Agents should use the `snippet`, `match_offset`, `truncated_before`, and `truncated_after` fields to decide whether further reading is needed.

Optional argument: `context_chars` controls the size of the hit-centred snippet.

### `wiki_search_following_pages`

Use this when a search hit is found inside a long book and the agent needs continuation context after the hit. It returns the matched page plus `following_pages` pages when page markers are present, or a larger hit-centred excerpt when page markers are unavailable.

Typical call:

```json
{
  "query": "recursive cognition",
  "following_pages": 3,
  "limit": 3,
  "context_chars": 4000,
  "max_chars": 16000
}
```
