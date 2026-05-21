#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression tests for commented config, default wrapping, and shell exits."""
from pathlib import Path

from llm_wiki_mcp.cli import DEFAULT_SCREEN_WIDTH, _parse_interactive_line, wrap_screen_text
from llm_wiki_mcp.context_api import release_load_config
from llm_wiki_mcp.server import load_wiki_config


def test_default_screen_width_is_120():
    """Ensure the release default screen width matches the CLI documentation."""
    assert DEFAULT_SCREEN_WIDTH == 120


def test_bare_quit_exit_bye_are_not_implicit_ask():
    """Ensure bare shell exit words work without a slash."""
    for word in ("quit", "exit", "bye"):
        cmd, args, raw, implicit = _parse_interactive_line(word)
        assert cmd == word
        assert args == []
        assert implicit is False


def test_block_quotes_are_wrapped_for_screen_output():
    """Ensure quoted text is wrapped at word boundaries for terminal display."""
    wrapped = wrap_screen_text("> alpha beta gamma delta epsilon zeta", width=18, enabled=True)
    lines = wrapped.splitlines()
    assert len(lines) > 1
    assert all(line.startswith("> ") for line in lines)
    assert all(len(line) <= 18 for line in lines)


def test_config_loader_accepts_comments(tmp_path: Path):
    """Ensure both config loaders accept JSON with // and # comments."""
    vault = tmp_path / "wiki_vault"
    vault.mkdir()
    (vault / "llm_wiki_config.json").write_text(
        '{\n'
        '  // local Ollama model\n'
        '  "ollama": {\n'
        '    "host": "http://localhost:11434", # default local endpoint\n'
        '    "model": "llama3.2:3b"\n'
        '  }\n'
        '}\n',
        encoding="utf-8",
    )
    assert release_load_config(vault)["ollama"]["model"] == "llama3.2:3b"
    assert load_wiki_config(vault)["ollama"]["host"] == "http://localhost:11434"
