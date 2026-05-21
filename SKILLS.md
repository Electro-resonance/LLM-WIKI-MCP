# Skills / Operating Notes for Agents

When using this repository as an agent tool, prefer safe, inspectable actions:

1. Initialise a vault before ingestion: `llm-wiki --vault ./wiki_vault init`.
2. Ingest narrow folders first, then widen the scope once results look sensible.
3. Use `retrieve ... --show` or `ask ... --dry-run` before relying on generated answers.
4. Treat Markdown pages as the source of truth; SQLite indexes can be rebuilt.
5. Run `lint`, `repair`, and `reindex` after large ingestion batches.
6. Do not commit generated vault state, local histories, metrics, or indexes.
7. Keep examples generic: no private paths, local machine names, internal project names, or local IP addresses.
