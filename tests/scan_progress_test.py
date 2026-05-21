#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression tests for scan-phase progress on large ingest targets."""
from pathlib import Path

from llm_wiki_mcp.cli import ingest_path
from llm_wiki_mcp.context_api import release_ingest_directory_provenance


def test_provenance_ingest_reports_scan_before_ingest(tmp_path: Path):
    """Document the `test_provenance_ingest_reports_scan_before_ingest` function used by the LLM Wiki MCP release."""
    vault = tmp_path / "wiki_vault"
    source = tmp_path / "source"
    source.mkdir()
    for idx in range(3):
        (source / f"doc{idx}.txt").write_text(f"scan progress text {idx}", encoding="utf-8")

    events = []
    release_ingest_directory_provenance(
        str(vault),
        str(source),
        recursive=True,
        apply=True,
        progress_callback=lambda cur, total, item=None, action="": events.append((cur, total, Path(item).name if item else "", action)),
    )

    scan_events = [event for event in events if event[3] == "scan"]
    ingest_events = [event for event in events if event[3] not in {"scan", "reindex", "done"}]
    assert scan_events, events
    assert scan_events[0][1] == 0  # total is unknown while walking the tree
    assert ingest_events, events
    assert events.index(scan_events[0]) < events.index(ingest_events[0])


def test_legacy_ingest_path_reports_scan_before_processing(tmp_path: Path):
    """Document the `test_legacy_ingest_path_reports_scan_before_processing` function used by the LLM Wiki MCP release."""
    vault = tmp_path / "vault"
    source = tmp_path / "source"
    source.mkdir()
    (source / "alpha.txt").write_text("alpha searchable text", encoding="utf-8")
    (source / "beta.md").write_text("# beta\n\nmore searchable text", encoding="utf-8")

    events = []
    ingest_path(
        vault,
        source,
        ["*.md", "*.txt"],
        True,
        100,
        progress_callback=lambda cur, total, item=None, action="": events.append((cur, total, Path(item).name if item else "", action)),
    )

    scan_events = [event for event in events if event[3] == "scan"]
    ingest_events = [event for event in events if event[3] == "ingest"]
    assert scan_events, events
    assert ingest_events, events
    assert events.index(scan_events[0]) < events.index(ingest_events[0])
