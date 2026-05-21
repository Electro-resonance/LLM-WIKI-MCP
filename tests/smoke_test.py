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
import subprocess, sys, tempfile

root = Path(__file__).resolve().parents[1]
server = root / "llm_wiki_mcp_server.py"
with tempfile.TemporaryDirectory() as td:
    proc = subprocess.run([sys.executable, str(server), "local-test", "--vault", td], text=True, capture_output=True, timeout=30)
    print(proc.stdout)
    print(proc.stderr)
    assert proc.returncode == 0
