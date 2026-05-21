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
from llm_wiki_mcp.context_api import LLMWikiContextEngine
from llm_wiki_mcp.cli import ingest_path

import tempfile
vault = Path(tempfile.mkdtemp(prefix='llm_wiki_cli_test_'))
source = Path(__file__).resolve().parents[1] / 'examples' / 'raw'
engine = LLMWikiContextEngine(vault)
report = ingest_path(vault, source, ['*.md'], recursive=True, limit=10, json_output=False)
assert report['ingested_count'] >= 1
pack = engine.context_pack('durable Markdown memory', max_chars=2000)
assert pack['chars'] > 0
assert pack['sources']
print('cli_and_context_api_test: PASS')
