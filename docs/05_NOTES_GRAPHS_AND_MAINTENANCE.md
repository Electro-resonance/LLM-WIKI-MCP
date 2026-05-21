# Notes, Graphs, and Maintenance

## AI sidecar notes

The wiki can maintain sidecar notes for pages so generated commentary does not have to overwrite canonical source pages. This keeps source-derived content and model-derived reflection separate.

## Graphs

Export a whole-wiki graph:

```bash
llm-wiki --vault ./wiki_vault mermaid --output docs/wiki_graph.md
```

Render a neighbourhood around one page:

```bash
llm-wiki --vault ./wiki_vault map "Overview" --output docs/overview_map.md
```

## Maintenance commands

- `stats` shows page and vault health.
- `lint` detects common wiki issues.
- `repair` proposes safe fixes.
- `repair --apply` applies selected safe repairs.
- `reindex` rebuilds the SQLite full-text index.
- `export` writes an `llms.txt` style export.

Run maintenance after large ingestion batches or structural edits.
