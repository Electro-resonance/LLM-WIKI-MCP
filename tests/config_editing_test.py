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
from llm_wiki_mcp.server import WikiStore, WikiConfig

vault = Path(tempfile.mkdtemp(prefix='wiki_config_test_'))
store = WikiStore(WikiConfig(vault=vault))
store.config_set('host', 'http://localhost:11434')
store.config_set('model', 'qwen2.5:7b')
store.config_set('ollama.timeout_seconds', '180')
config = store.config()['config']
assert config['ollama']['host'] == 'http://localhost:11434'
assert config['ollama']['model'] == 'qwen2.5:7b'
assert config['ollama']['timeout_seconds'] == 180
assert (vault / 'llm_wiki_config.json').exists()
print('config_editing_test: PASS')
