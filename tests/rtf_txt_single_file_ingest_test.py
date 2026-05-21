#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression tests: TXT/RTF ingestion and single-file /ingest targets."""
from pathlib import Path
import tempfile

from llm_wiki_mcp.cli import ingest_path
from llm_wiki_mcp.context_api import release_ingest_directory_provenance
from llm_wiki_mcp.server import WikiConfig, WikiStore, set_vault


def test_provenance_ingest_accepts_single_txt_file() -> None:
    """Document the `test_provenance_ingest_accepts_single_txt_file` function used by the LLM Wiki MCP release."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = root / "wiki_vault"
        txt = root / "single-note.txt"
        txt.write_text("Single TXT ingest token AlphaNeedle123", encoding="utf-8")

        result = release_ingest_directory_provenance(str(vault), str(txt), recursive=True, apply=True)
        assert result["counts"]["processed"] == 1
        assert result["counts"]["total"] == 1

        set_vault(vault)
        store = WikiStore(WikiConfig(vault))
        hits = store.search("AlphaNeedle123", limit=5)["results"]
        assert hits, "single TXT file should be ingested and searchable"


def test_provenance_ingest_accepts_rtf_files() -> None:
    """Document the `test_provenance_ingest_accepts_rtf_files` function used by the LLM Wiki MCP release."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = root / "wiki_vault"
        docs = root / "docs"
        docs.mkdir()
        rtf = docs / "meeting-notes.rtf"
        rtf.write_text(r"{\rtf1\ansi Meeting notes\par Synth design token BetaNeedle456\par}", encoding="utf-8")

        result = release_ingest_directory_provenance(str(vault), str(docs), recursive=True, apply=True)
        assert result["counts"]["processed"] == 1

        set_vault(vault)
        store = WikiStore(WikiConfig(vault))
        hits = store.search("BetaNeedle456", limit=5)["results"]
        assert hits, "RTF text should be stripped and indexed for search"
        page = store.read_page(hits[0]["title"])
        assert "rtf1" not in page["body"].lower()


def test_top_level_ingest_path_accepts_single_rtf_file() -> None:
    """Document the `test_top_level_ingest_path_accepts_single_rtf_file` function used by the LLM Wiki MCP release."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = root / "wiki_vault"
        rtf = root / "brief.rtf"
        rtf.write_text(r"{\rtf1\ansi Single file RTF token GammaNeedle789\par}", encoding="utf-8")

        report = ingest_path(vault, rtf, patterns=["*.rtf"], recursive=True, limit=10, json_output=True)
        assert report["ingested_count"] == 1

        set_vault(vault)
        store = WikiStore(WikiConfig(vault))
        hits = store.search("GammaNeedle789", limit=5)["results"]
        assert hits, "top-level ingest-dir path should accept a single RTF file"


if __name__ == "__main__":
    test_provenance_ingest_accepts_single_txt_file()
    test_provenance_ingest_accepts_rtf_files()
    test_top_level_ingest_path_accepts_single_rtf_file()
    print("rtf_txt_single_file_ingest_test: ok")
