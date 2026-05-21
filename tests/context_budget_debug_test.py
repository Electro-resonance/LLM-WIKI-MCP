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

from llm_wiki_mcp.context_api import (
    release_context_settings,
    release_debug_context,
    release_set_config_value,
)
from llm_wiki_mcp.server import WikiConfig, WikiStore
from llm_wiki_mcp.cli import _parse_interactive_line


def test_context_budget_defaults_and_override(tmp_path: Path):
    """Document the `test_context_budget_defaults_and_override` function used by the LLM Wiki MCP release."""
    vault = tmp_path / "vault"
    store = WikiStore(WikiConfig(vault))
    store.init_seed()
    settings = release_context_settings(str(vault))
    assert settings["context_budget_tokens"] == 24000
    assert settings["history_budget_tokens"] == 3000
    assert settings["source_budget_tokens"] == 6000
    release_set_config_value(str(vault), "ask.context_budget_tokens", 16000)
    assert release_context_settings(str(vault))["context_budget_tokens"] == 16000


def test_debug_context_reads_fuller_matching_page(tmp_path: Path):
    """Document the `test_debug_context_reads_fuller_matching_page` function used by the LLM Wiki MCP release."""
    vault = tmp_path / "vault"
    store = WikiStore(WikiConfig(vault))
    store.init_seed()
    long_text = "Vishva Bindu bootstrap context. " * 500
    store.create_page("Source - Vishva", "# Source - Vishva\n\n" + long_text, tags=["source"], overwrite=True)
    store.reindex()
    payload = release_debug_context(str(vault), "tell me about Vishva")
    pack = payload["context_pack"]
    assert payload["dry_run"] is True
    assert "Source - Vishva" in pack["source_titles"]
    assert "Vishva Bindu bootstrap context" in pack["prompt"]
    assert pack["prompt_tokens_estimate"] <= pack["settings"]["context_budget_tokens"]


def test_debug_context_is_raw_text_command():
    """Document the `test_debug_context_is_raw_text_command` function used by the LLM Wiki MCP release."""
    cmd, args, raw, implicit = _parse_interactive_line("/debug-context Tell me about Karpathy's work")
    assert cmd == "debug-context"
    assert args == ["Tell me about Karpathy's work"]
    assert implicit is False
