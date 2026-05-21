#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
from pathlib import Path
import tempfile

from llm_wiki_mcp.context_api import LLMWikiContextEngine, release_ingest_directory_provenance

project = Path(tempfile.mkdtemp(prefix='wiki_provenance_ingest_project_'))
vault = Path(tempfile.mkdtemp(prefix='wiki_provenance_ingest_vault_'))
(project / 'ARCHITECTURE.md').write_text('# Architecture\n\nThis release architecture page explains local-first retrieval and search indexing.\n', encoding='utf-8')
(project / 'README.md').write_text('# Readme\n\nThis project has command line search examples.\n', encoding='utf-8')

engine = LLMWikiContextEngine(vault)
result = release_ingest_directory_provenance(str(vault), str(project), recursive=True, apply=True)
assert result['counts']['processed'] >= 2

# Regression: provenance ingest writes Markdown directly, so it must reindex FTS.
search = engine.search('architecture')
assert search['count'] >= 1, search
assert any('ARCHITECTURE' in row['title'] or 'Architecture' in row['snippet'] for row in search['results']), search

print('provenance_ingest_search_test: PASS')
