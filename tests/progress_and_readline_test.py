#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression tests for progress counters and interactive history setup."""
from pathlib import Path

from llm_wiki_mcp.cli import OneLineProgress, ingest_path, interactive_shell
from llm_wiki_mcp.context_api import release_ingest_directory_provenance, release_iterate_all_notes
from llm_wiki_mcp.server import WikiConfig, WikiStore


def test_one_line_progress_uses_carriage_return(capsys):
    """Document the `test_one_line_progress_uses_carriage_return` function used by the LLM Wiki MCP release."""
    progress = OneLineProgress("Ingest", "files", enabled=True)
    progress.update(1, 3, "alpha.md", "ingest")
    progress.update(2, 3, "beta.md", "ingest")
    progress.done()
    out = capsys.readouterr().out
    assert "\rIngest: 1/3 files" in out
    assert "\rIngest: 2/3 files" in out
    assert "\nIngest: 1/3" not in out


def test_provenance_ingest_reports_progress(tmp_path: Path):
    """Document the `test_provenance_ingest_reports_progress` function used by the LLM Wiki MCP release."""
    source = tmp_path / "src"
    source.mkdir()
    for name in ["a.md", "b.txt"]:
        (source / name).write_text(f"content for {name}", encoding="utf-8")
    vault = tmp_path / "vault"
    events = []
    result = release_ingest_directory_provenance(
        str(vault), str(source), recursive=True, apply=True,
        progress_callback=lambda current, total, item, action="": events.append((current, total, Path(item).name if item else "", action)),
    )
    assert result["counts"]["processed"] == 2
    assert any(event[0] == 1 and event[1] == 2 and event[2] == "a.md" for event in events)
    assert any(event[0] == 2 and event[1] == 2 and event[2] == "b.txt" for event in events)


def test_legacy_ingest_dir_reports_progress(tmp_path: Path):
    """Document the `test_legacy_ingest_dir_reports_progress` function used by the LLM Wiki MCP release."""
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.md").write_text("# Alpha", encoding="utf-8")
    (source / "b.txt").write_text("Beta", encoding="utf-8")
    vault = tmp_path / "vault"
    events = []
    ingest_path(vault, source, ["*.md", "*.txt"], True, 100, progress_callback=lambda *args: events.append(args))
    scan_events = [event for event in events if len(event) > 3 and event[3] == "scan"]
    ingest_events = [event for event in events if len(event) > 3 and event[3] == "ingest"]
    assert len(scan_events) == 2
    assert len(ingest_events) == 2
    assert scan_events[0][0:2] == (1, 0)
    assert ingest_events[0][0:2] == (1, 2)
    assert ingest_events[1][0:2] == (2, 2)


def test_notes_all_reports_progress(tmp_path: Path):
    """Document the `test_notes_all_reports_progress` function used by the LLM Wiki MCP release."""
    vault = tmp_path / "vault"
    store = WikiStore(WikiConfig(vault))
    store.init_seed()
    store.create_page("Extra", "# Extra\n\nAlpha beta gamma", overwrite=True)
    events = []
    payload = release_iterate_all_notes(str(vault), limit=2, progress_callback=lambda *args: events.append(args))
    assert payload["count"] == 2
    assert len([e for e in events if e[0]]) >= 2


def test_interactive_shell_initialises_readline(monkeypatch, tmp_path: Path):
    """Document the `test_interactive_shell_initialises_readline` function used by the LLM Wiki MCP release."""
    import llm_wiki_mcp.cli as cli
    called = []
    monkeypatch.setattr(cli, "setup_release_readline_history", lambda vault: called.append(Path(vault)) or "history")
    monkeypatch.setattr("builtins.input", lambda prompt="": (_ for _ in ()).throw(EOFError()))
    assert interactive_shell(tmp_path / "vault") == 0
    assert called
