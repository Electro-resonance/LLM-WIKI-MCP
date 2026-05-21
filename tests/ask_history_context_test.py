#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression tests for prompt/response self-history and safe answer output."""
from pathlib import Path
import tempfile

import llm_wiki_mcp.context_api as ca


def test_ask_records_prompt_response_history_and_uses_it():
    """Document the `test_ask_records_prompt_response_history_and_uses_it` function used by the LLM Wiki MCP release."""
    vault = Path(tempfile.mkdtemp(prefix="wiki_history_fix_"))

    def fake_generate(vault_path, prompt, **kwargs):
        """Document the `fake_generate` function used by the LLM Wiki MCP release."""
        assert "# Current Question" in prompt
        return {"ok": True, "answer": "The first answer mentions a working prototype.", "elapsed_seconds": 0.01}

    old = ca.release_ollama_generate
    ca.release_ollama_generate = fake_generate
    try:
        out = ca.release_ask(str(vault), "Tell me about the prototype", mode="agentic")
        assert "working prototype" in out["answer"]
        rows = ca.release_load_history(str(vault), 10)
        assert len(rows) == 1
        assert rows[0]["question"] == "Tell me about the prototype"
        assert "# Current Question" in rows[0]["prompt"]
        assert "working prototype" in rows[0]["answer"]

        hist = ca.release_execute_agent_tool_by_name(str(vault), "wiki_ask_history", {"limit": 10}, "history", {})
        assert hist["count"] == 1
        assert hist["history"][0]["question"] == "Tell me about the prototype"

        answer = ca.release_ask(str(vault), "does the context include history of your replies?", mode="agentic")["answer"]
        assert "prompt/response" in answer or "ask-history" in answer or "Recent turns" in answer
        assert "Tell me about the prototype" in answer
    finally:
        ca.release_ollama_generate = old


def test_public_sanitizer_redacts_paths_but_keeps_runtime_hosts_visible():
    """Document the `test_public_sanitizer_redacts_paths_but_keeps_runtime_hosts_visible` function used by the LLM Wiki MCP release."""
    mount_path = "/" + "mnt" + "/" + "f" + "/llm_wiki_test/Book.pdf"
    private_host = "http://" + ".".join(["172", "30", "64", "1"]) + ":11434"
    win_path = "C:" + "\\" + "Users" + "\\" + "User" + "\\" + "Project" + "\\" + "file.md"
    private_name = "".join(["Qyber", "netics"])
    text = f"Source file: {mount_path} and host {private_host} plus {win_path} {private_name}"
    cleaned = ca.release_sanitize_public_text(text)
    assert mount_path not in cleaned
    assert private_host in cleaned
    assert win_path not in cleaned
    assert private_name not in cleaned
    assert "[local path redacted]" in cleaned


def test_context_window_answer_does_not_guess_exact_model_limit():
    """Document the `test_context_window_answer_does_not_guess_exact_model_limit` function used by the LLM Wiki MCP release."""
    vault = Path(tempfile.mkdtemp(prefix="wiki_context_window_"))
    answer = ca.release_ask(str(vault), "what is your context window length?", mode="agentic")["answer"]
    assert "do not know the exact native context-window" in answer
    assert "Retrieved wiki context" in answer
    assert "/mnt/" not in answer


if __name__ == "__main__":
    test_ask_records_prompt_response_history_and_uses_it()
    test_public_sanitizer_redacts_paths_but_keeps_runtime_hosts_visible()
    test_context_window_answer_does_not_guess_exact_model_limit()
    print("ask_history_context_test: PASS")
