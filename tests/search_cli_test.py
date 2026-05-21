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

from llm_wiki_mcp.context_api import LLMWikiContextEngine

vault = Path(tempfile.mkdtemp(prefix='wiki_search_test_'))
engine = LLMWikiContextEngine(vault)
engine.store.create_page('Article Notes', '# Article Notes\n\nOne article about context engines.', tags=['test'], source='test', overwrite=True)
engine.store.reindex()

lower = engine.search('article')
upper = engine.search('ARTICLE')
plural = engine.search('articles')
diag = engine.store.search_diagnostics('articles')

assert lower['count'] >= 1
assert upper['count'] >= 1
assert plural['count'] >= 1
assert diag['diagnostics']['case_sensitive'] is False
assert 'article' in diag['diagnostics']['expanded_terms']
assert 'articles' in diag['diagnostics']['expanded_terms']

print('search_cli_test: PASS')
