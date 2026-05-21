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
    LLMWikiContextEngine,
    release_search_following_pages,
    release_search_with_notes,
)


def test_search_snippet_centres_on_late_book_match(tmp_path):
    """Document the `test_search_snippet_centres_on_late_book_match` function used by the LLM Wiki MCP release."""
    vault = tmp_path / "vault"
    engine = LLMWikiContextEngine(vault)
    body = "# Long Book\n\n" + ("opening material that should not dominate search.\n" * 400)
    body += "\n--- Page 42 of 50 ---\n\nThis late chapter contains the unique phrase ZENITH_NEEDLE and surrounding explanation.\n"
    body += "\n--- Page 43 of 50 ---\n\nContinuation after the match.\n"
    engine.store.create_page("Long Book", body, overwrite=True)
    engine.store.reindex()

    result = engine.search("ZENITH_NEEDLE", limit=1)
    assert result["results"]
    snippet = result["results"][0]["snippet"]
    assert "ZENITH_NEEDLE" in snippet
    assert "Page 42" in snippet
    assert result["results"][0]["truncated_before"] is True
    assert result["results"][0]["match_offset"] > 1000


def test_search_with_notes_returns_hit_centred_snippet(tmp_path):
    """Document the `test_search_with_notes_returns_hit_centred_snippet` function used by the LLM Wiki MCP release."""
    vault = tmp_path / "vault"
    engine = LLMWikiContextEngine(vault)
    body = "# Huge Source\n\n" + ("early filler text.\n" * 100)
    body += "\n--- Page 90 of 100 ---\n\nThe term ORBITAL_BINDU appears near the end of the book.\n"
    engine.store.create_page("Huge Source", body, overwrite=True)

    result = release_search_with_notes(str(vault), "ORBITAL_BINDU", limit=1, context_chars=500)
    assert result["results"]
    snippet = result["results"][0]["snippet"]
    assert "ORBITAL_BINDU" in snippet
    assert "Page 90" in snippet
    assert result["results"][0]["truncated_before"] is True


def test_search_following_pages_returns_current_and_following_pages(tmp_path):
    """Document the `test_search_following_pages_returns_current_and_following_pages` function used by the LLM Wiki MCP release."""
    vault = tmp_path / "vault"
    engine = LLMWikiContextEngine(vault)
    body = "# Book With Pages\n\n"
    for i in range(1, 8):
        phrase = " MATCH_ANCHOR" if i == 4 else ""
        body += f"\n--- Page {i} of 7 ---\n\nContent for page {i}.{phrase}\n"
    engine.store.create_page("Book With Pages", body, overwrite=True)

    result = release_search_following_pages(str(vault), "MATCH_ANCHOR", limit=1, following_pages=2, context_chars=1000)
    assert result["results"]
    row = result["results"][0]
    assert row["start_page"] == 4
    assert row["end_page"] == 6
    assert "Page 4" in row["excerpt"]
    assert "Page 5" in row["excerpt"]
    assert "Page 6" in row["excerpt"]
    assert "Page 7" not in row["excerpt"]
