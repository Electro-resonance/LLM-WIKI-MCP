#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression test: blank LLM fallback answers first, then cites evidence."""
from llm_wiki_mcp.context_api import release_evidence_extract_answer


def test_fallback_answer_is_not_reference_dump_for_release_readiness():
    """Document the `test_fallback_answer_is_not_reference_dump_for_release_readiness` function used by the LLM Wiki MCP release."""
    evidence = [
        {
            "tool": "wiki_read_page",
            "result": {
                "ok": True,
                "title": "Source - README",
                "text": "# README\nLLM Wiki MCP is a local-first Markdown wiki for humans and LLM agents.\nIt includes GitHub-ready documentation, installation guidance, and release notes.",
            },
        },
        {
            "tool": "wiki_read_page",
            "result": {
                "ok": True,
                "title": "Source - INSTALL",
                "text": "# INSTALL\nInstall the package, configure Ollama, run /ingest ., then ask questions at the wiki prompt.",
            },
        },
        {
            "tool": "wiki_capabilities",
            "result": {
                "llm": {"provider": "ollama", "model": "llama3.2:3b"},
                "retrieval": {"sqlite_fts": True, "markdown_source_of_truth": True},
            },
        },
    ]
    trace = [{"tool": "wiki_search_with_notes"}, {"tool": "wiki_read_page"}]
    answer = release_evidence_extract_answer(
        "do you feel ready for github release?",
        trace=trace,
        evidence=evidence,
        llm_error="empty LLM response after second pass",
    )
    assert answer.startswith("## Direct answer")
    assert "Yes" in answer
    assert "GitHub release" in answer
    assert answer.index("## Direct answer") < answer.index("## Evidence used")
    assert "It is still an answer, not just a reference dump" in answer
