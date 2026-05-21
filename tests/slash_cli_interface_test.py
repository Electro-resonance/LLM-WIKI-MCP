#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression test: interactive shell uses slash commands and plain text asks."""
from llm_wiki_mcp.cli import _parse_interactive_line


def test_plain_text_routes_to_ask_and_preserves_apostrophes():
    """Document the `test_plain_text_routes_to_ask_and_preserves_apostrophes` function used by the LLM Wiki MCP release."""
    cmd, args, raw, implicit = _parse_interactive_line("Tell me about Karpathy's work!")
    assert cmd == "ask"
    assert implicit is True
    assert raw == "Tell me about Karpathy's work!"
    assert args == ["Tell me about Karpathy's work!"]


def test_slash_ask_preserves_apostrophes_without_quotes():
    """Document the `test_slash_ask_preserves_apostrophes_without_quotes` function used by the LLM Wiki MCP release."""
    cmd, args, raw, implicit = _parse_interactive_line("/ask Tell me about Karpathy's work!")
    assert cmd == "ask"
    assert implicit is False
    assert raw == "Tell me about Karpathy's work!"
    assert args == ["Tell me about Karpathy's work!"]


def test_slash_commands_parse_normally():
    """Document the `test_slash_commands_parse_normally` function used by the LLM Wiki MCP release."""
    cmd, args, raw, implicit = _parse_interactive_line("/config model llama3.2:3b")
    assert cmd == "config"
    assert args == ["model", "llama3.2:3b"]
    assert raw == "model llama3.2:3b"
    assert implicit is False


def test_slash_commands_keep_flag_parsing_after_apostrophe_fix():
    """Document the `test_slash_commands_keep_flag_parsing_after_apostrophe_fix` function used by the LLM Wiki MCP release."""
    cmd, args, raw, implicit = _parse_interactive_line("/retrieve architecture --top-k 2")
    assert cmd == "retrieve"
    assert args == ["architecture", "--top-k", "2"]
    assert raw == "architecture --top-k 2"
    assert implicit is False

    cmd, args, raw, implicit = _parse_interactive_line("/search Karpathy's work")
    assert cmd == "search"
    assert args == ["Karpathy's", "work"]
    assert raw == "Karpathy's work"


def test_bare_exit_words_are_shell_commands_not_asks():
    """Ensure bare quit/exit/bye leave the shell instead of routing to /ask."""
    for word in ("quit", "exit", "bye", "q"):
        cmd, args, raw, implicit = _parse_interactive_line(word)
        assert cmd == word
        assert args == []
        assert implicit is False
