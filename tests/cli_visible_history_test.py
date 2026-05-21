#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression tests: visible CLI asks appear in `/history`."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_history_shows_visible_ask_turn(tmp_path: Path):
    """Document the `test_cli_history_shows_visible_ask_turn` function used by the LLM Wiki MCP release."""
    repo = Path(__file__).resolve().parents[1]
    vault = tmp_path / "vault"
    proc = subprocess.run(
        [sys.executable, "llm_wiki_cli.py", "--vault", str(vault), "shell"],
        input="what are you\n/history\n/exit\n",
        cwd=repo,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "Recent ask history" in out
    assert "No ask history yet" not in out
    assert "User: what are you" in out
    assert "Assistant:" in out
    assert (vault / "ask_history.jsonl").exists()


def test_identity_answer_shows_runtime_localhost_url(tmp_path: Path):
    """Document the `test_identity_answer_shows_runtime_localhost_url` function used by the LLM Wiki MCP release."""
    repo = Path(__file__).resolve().parents[1]
    vault = tmp_path / "vault"
    proc = subprocess.run(
        [sys.executable, "llm_wiki_cli.py", "--vault", str(vault), "shell"],
        input="what are you\n/exit\n",
        cwd=repo,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "http://localhost:11434" in out
    assert "[local service redacted]" not in out
    assert "htt[local path redacted]" not in out
