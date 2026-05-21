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

vault = Path(tempfile.mkdtemp(prefix='wiki_test_'))
engine = LLMWikiContextEngine(vault)
config = engine.config()
assert config['config']['ollama']['model'] == 'llama3.2:3b'
result = engine.ask_ollama('What is this wiki for?', dry_run=True)
assert result['ok'] is True
assert result['dry_run'] is True
assert 'Wiki context' in result['llm_prompt']
print('ollama_and_cli_test: PASS')
