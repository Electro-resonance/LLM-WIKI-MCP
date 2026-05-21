#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# retrieval, reflective notes, provenance-aware ingestion, and agentic context.
# =============================================================================

"""Command-line launcher for LLM Wiki MCP.

The source archive name can change, but the Python package import path remains stable for GitHub publishing.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm_wiki_mcp.cli import main

if __name__ == "__main__":
    main()
