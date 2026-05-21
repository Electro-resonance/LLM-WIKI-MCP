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
    release_docx_extraction_status,
    release_ingest_directory_provenance,
    release_reindex_with_progress,
)
from llm_wiki_mcp.server import WikiConfig, WikiStore


def test_reindex_reports_per_page_progress(tmp_path: Path):
    """Document the `test_reindex_reports_per_page_progress` function used by the LLM Wiki MCP release."""
    vault = tmp_path / "wiki_vault"
    store = WikiStore(WikiConfig(vault))
    store.init_seed()
    store.create_page("Alpha", "# Alpha\n\nalpha content", tags=["test"], overwrite=True)
    events = []
    result = release_reindex_with_progress(vault, progress_callback=lambda cur, total, item=None, action="": events.append((cur, total, item, action)))
    assert result["indexed_pages"] >= 1
    assert events
    assert any(event[3] == "reindex" for event in events)
    assert events[-1][3] == "done"


def test_ingest_dot_skips_active_wiki_vault(tmp_path: Path):
    """Document the `test_ingest_dot_skips_active_wiki_vault` function used by the LLM Wiki MCP release."""
    project = tmp_path / "project"
    project.mkdir()
    vault = project / "wiki_vault"
    store = WikiStore(WikiConfig(vault))
    store.init_seed()
    (project / "outside.txt").write_text("outside searchable phrase", encoding="utf-8")
    generated = vault / "wiki" / "Generated.md"
    generated.write_text("# Generated\n\nthis should not be reingested", encoding="utf-8")

    result = release_ingest_directory_provenance(vault, project, recursive=True, apply=True)
    processed_names = {Path(row["path"]).name for row in result.get("processed", [])}
    assert "outside.txt" in processed_names
    assert "Generated.md" not in processed_names
    assert all("wiki_vault" not in str(row.get("path", "")) for row in result.get("processed", []))


def test_docx_status_shape():
    """Document the `test_docx_status_shape` function used by the LLM Wiki MCP release."""
    status = release_docx_extraction_status()
    assert status["module"] == "python-docx"
    assert isinstance(status["available"], bool)
    assert "DOCX text extraction" in status["message"]
