# Agentic Ask and Memory

The `ask` workflow is designed to keep answers grounded in the local wiki.

## Ask pipeline

1. Normalise the user's question.
2. Search and retrieve relevant wiki pages.
3. Build a context pack containing source titles and excerpts.
4. Send the context pack and question to the configured Ollama model.
5. Store optional runtime history and metrics in the local vault.

## Recursive and agentic commands

The shell includes advanced commands for self-access, recursive history, token metrics, page notes, and agentic evidence packs. These commands are intended for experimentation and for giving a local agent awareness of the wiki's own state.

Useful shell commands include:

```text
wiki> /ask What is in the wiki?
wiki> /askrec What has changed recently?
wiki> /retrieve architecture --show
wiki> /history-status
wiki> /tokens
wiki> /capabilities
wiki> /notes-status
```

## Ask history records

The release records completed `/ask` turns in the local vault. Each history row can contain:

- the user question;
- the prompt/context assembled for the local LLM;
- the final assistant answer;
- tool/source names used for the answer;
- estimated prompt and answer token counts.

The `wiki_ask_history` MCP tool exposes recent turns to the agent. Agentic ask also injects a bounded recent ask/reply summary into the prompt so follow-up questions can use conversational context. This history is local runtime state, not a committed project file.

If a user asks about context-window length, the agent should not guess the native model limit. It should report the configured wiki context budget, recursive history budget, recent-turn count, and explain that the exact Ollama/model context length depends on the model/runtime configuration.

## Privacy note

Runtime history and metrics are local vault files. They are ignored by Git and should not be committed unless a user explicitly decides to publish a sanitized sample.

## Configurable context budgets

Agentic ask uses explicit budgets to prevent both under-contextualised answers and over-large prompts. The default settings are:

- `ask.context_budget_tokens`: 24000
- `ask.history_budget_tokens`: 3000
- `ask.source_budget_tokens`: 6000
- `ask.max_sources`: 8
- `ask.full_page_threshold`: 3

The CLI command `/context-settings` displays and edits these values. `/debug-context <question>` builds the context pack without calling Ollama, making it possible to audit whether the model is receiving enough evidence.
