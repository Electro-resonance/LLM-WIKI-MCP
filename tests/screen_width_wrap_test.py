#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression test: terminal output wraps at word boundaries and can be disabled."""
from llm_wiki_mcp.cli import configure_screen_output, wrap_screen_text


def test_wrap_screen_text_preserves_words():
    """Document the `test_wrap_screen_text_preserves_words` function used by the LLM Wiki MCP release."""
    configure_screen_output(width=24, enabled=True)
    text = "alpha beta gamma delta epsilon zeta"
    wrapped = wrap_screen_text(text)
    lines = wrapped.splitlines()
    assert len(lines) > 1
    assert all(len(line) <= 24 for line in lines)
    assert "eps\n" not in wrapped
    assert wrapped.replace("\n", " ") == text


def test_wrap_screen_text_can_be_disabled():
    """Document the `test_wrap_screen_text_can_be_disabled` function used by the LLM Wiki MCP release."""
    text = "alpha beta gamma delta epsilon zeta"
    wrapped = wrap_screen_text(text, width=12, enabled=False)
    assert wrapped == text


def test_wrap_screen_text_preserves_code_fences():
    """Document the `test_wrap_screen_text_preserves_code_fences` function used by the LLM Wiki MCP release."""
    text = "before " + ("word " * 8).strip() + "\n```\n" + ("x" * 80) + "\n```"
    wrapped = wrap_screen_text(text, width=30, enabled=True)
    assert "x" * 80 in wrapped


def test_wrap_screen_text_wraps_block_quotes():
    """Ensure quoted prose is wrapped rather than left as one very long line."""
    text = "> alpha beta gamma delta epsilon zeta eta theta"
    wrapped = wrap_screen_text(text, width=20, enabled=True)
    lines = wrapped.splitlines()
    assert len(lines) > 1
    assert all(line.startswith("> ") for line in lines)
    assert all(len(line) <= 20 for line in lines)
