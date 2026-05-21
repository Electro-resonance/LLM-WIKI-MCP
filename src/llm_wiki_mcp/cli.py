#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# retrieval, reflective notes, provenance-aware ingestion, and agentic context.
# =============================================================================

"""Core module for the LLM Wiki MCP package."""
from __future__ import annotations
from llm_wiki_mcp.context_api import *


def _compact_ingest_output_text(text: str, verbose: bool = False) -> str:
    """Suppress per-file ingest listings unless verbose is requested."""
    if verbose:
        return text
    lines = str(text or "").splitlines()
    out = []
    skip_section = False
    for line in lines:
        stripped = line.strip()
        if stripped in {"New files:", "Updated files:", "Already ingested:"}:
            skip_section = True
            continue
        if skip_section:
            if stripped.startswith("- "):
                continue
            if stripped == "":
                continue
            # resume when a non-list/non-blank line appears
            skip_section = False
        out.append(line)
    return "\n".join(out).strip()

def setup_release_readline_history(vault):
    """Enable ↑/↓ command history and Ctrl-R reverse search using readline."""
    try:
        import atexit
        import readline
        from pathlib import Path
        histfile = Path(vault) / ".llm_wiki_history"
        histfile.parent.mkdir(parents=True, exist_ok=True)
        try:
            readline.read_history_file(str(histfile))
        except FileNotFoundError:
            pass
        readline.set_history_length(2000)
        # Tab completion for slash command names when readline backend supports it.
        commands = SLASH_COMMANDS
        def completer(text, state):
            """Complete slash commands such as `/ask`, `/ingest`, and `/config`."""
            matches = [c for c in commands if c.startswith(text)]
            return matches[state] if state < len(matches) else None
        readline.set_completer(completer)
        try:
            readline.parse_and_bind("tab: complete")
            readline.parse_and_bind("\\C-r: reverse-search-history")
            # GNU readline uses quoted escape sequences for cursor keys; some
            # libedit builds accept the unquoted forms. Try both so ↑/↓ work
            # instead of echoing raw ^[[A/^[[B bytes.
            for binding in (
                '"\\e[A": previous-history',
                '"\\e[B": next-history',
                "\\e[A: previous-history",
                "\\e[B: next-history",
            ):
                try:
                    readline.parse_and_bind(binding)
                except Exception:
                    pass
        except Exception:
            pass
        atexit.register(lambda: readline.write_history_file(str(histfile)))
        return str(histfile)
    except Exception:
        return None




class OneLineProgress:
    """Same-line terminal counter for long-running CLI operations.

    The display uses carriage return (``\r``) rather than printing one line per
    file/page. It is enabled only for interactive terminal output unless forced,
    keeping scripted/test output clean.
    """

    def __init__(self, label: str = "Processing", unit: str = "files", enabled: Optional[bool] = None):
        """Document the `__init__` function used by the LLM Wiki MCP release."""
        self.label = label
        self.unit = unit
        self.enabled = sys.stdout.isatty() if enabled is None else bool(enabled)
        self._last_len = 0
        self._seen = False

    def update(self, current: int, total: int, item: Any = None, action: str = "") -> None:
        """Render ``current/total`` on one terminal line without mid-run spam."""
        if not self.enabled:
            return
        total = max(int(total or 0), 0)
        current = max(int(current or 0), 0)
        name = Path(str(item)).name if item else ""
        verb = str(action or "").strip()
        if verb == "reindex":
            display_label = "Reindex"
            display_unit = "pages"
        elif verb in {"scan", "scanning"}:
            display_label = "Scan"
            display_unit = "files"
        else:
            display_label = self.label
            display_unit = self.unit
        prefix = f"{display_label}: "
        counter = f"{current}/{total} {display_unit}" if total else f"{current} {display_unit}"
        details = f" | {verb}" if verb and verb not in {"done", "", "reindex", "scan", "scanning"} else ""
        suffix = f" | {name}" if name else ""
        msg = prefix + counter + details + suffix
        max_len = max(40, (SCREEN_WIDTH or DEFAULT_SCREEN_WIDTH) - 1)
        if len(msg) > max_len:
            msg = msg[: max_len - 1] + "…"
        pad = " " * max(0, self._last_len - len(msg))
        print("\r" + msg + pad, end="", flush=True)
        self._last_len = len(msg)
        self._seen = True

    def done(self, final_message: str | None = None) -> None:
        """Clear the progress line and optionally print one final message."""
        if not self.enabled:
            if final_message:
                print(final_message)
            return
        if self._seen:
            print("\r" + (" " * self._last_len) + "\r", end="", flush=True)
        if final_message:
            print(final_message)
        self._last_len = 0
        self._seen = False

def print_release_safe_self_result(payload):
    """Implement the print safe self result operation for the local LLM Wiki workflow."""
    command = payload.get("command")
    result = payload.get("result")
    print(f"Executed safe self-access command: {command}")
    if command == "self-stats":
        usage = result.get("usage", {}) if isinstance(result, dict) else {}
        cfg = result.get("config", {}) if isinstance(result, dict) else {}
        print(f"Recursive enabled: {cfg.get('ask', {}).get('recursive_enabled')}")
        print(f"Pages: {usage.get('pages')} | Wiki tokens: {usage.get('tokens_estimate')}")
        print(f"Ask turns: {usage.get('ask_history_turns')} | Ask history tokens: {usage.get('ask_history_tokens_estimate')}")
        print(f"Metric records: {result.get('metrics', {}).get('count') if isinstance(result, dict) else None}")
    elif command in {"self-usage", "usage", "stats"}:
        print(f"Vault: {result.get('vault')}")
        print(f"Pages: {result.get('pages')} | Words: {result.get('words')} | Wiki tokens: {result.get('tokens_estimate')}")
        print(f"Ask turns: {result.get('ask_history_turns')} | Ask history tokens: {result.get('ask_history_tokens_estimate')}")
        print("Largest pages:")
        for row in result.get("largest_pages", [])[:10]:
            print(f"  - {row.get('file')}: ~{row.get('tokens_estimate')} tokens")
    elif command == "tokens":
        print(f"Recorded asks: {result.get('count', 0)}")
        print(f"Total prompt tokens estimate: {result.get('total_prompt_tokens_estimate', 0)}")
        print(f"Total answer tokens estimate: {result.get('total_answer_tokens_estimate', 0)}")
        avg = result.get("avg_output_tokens_per_second")
        print(f"Average output tokens/s: {avg:.2f}" if avg is not None else "Average output tokens/s: n/a")
    elif command == "capabilities":
        print(f"LLM: host={result.get('llm', {}).get('host')} model={result.get('llm', {}).get('model')}")
        print(f"Runtime: {result.get('runtime', {})}")
        print(f"Maintenance: {result.get('maintenance', {})}")
    elif command == "command-map":
        for cmd, tools in result.items():
            print(f"  {cmd}: {', '.join(tools)}")
    elif command == "runtime-journal":
        events = result.get("events", [])
        if not events:
            print("No runtime events recorded yet.")
        for row in events:
            print(f"  - {row.get('command')} success={row.get('success')} query={str(row.get('query',''))[:80]}")
    elif command == "history-status":
        print(result)
    elif command == "reconcile":
        print(f"OK: {result.get('ok')}")
        if result.get("missing_docs"):
            print("Missing docs:")
            for item in result["missing_docs"]:
                print(f"  - {item}")
        if result.get("undocumented_commands_in_function_list"):
            print("Commands not mentioned in FUNCTION_LIST.md:")
            for item in result["undocumented_commands_in_function_list"]:
                print(f"  - {item}")
    else:
        print(result)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""User-facing command line tools for LLM Wiki MCP release.

The MCP tool surface is intentionally JSON-shaped for agents. This CLI is the
opposite by default: readable tables, short summaries, and helpful prompts for
humans. Use --json, or `json on` in shell mode, when scripts need structured
output.
"""

import argparse
import difflib
import json
import os
import shlex
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .context_api import LLMWikiContextEngine, tool_self_question_context, wiki_usage_snapshot, release_context_settings, release_debug_context
from .server import WikiStore, WikiConfig, set_vault, safe_slug

ART = r'''
 _     _     __  __
| |   | |   |  \/  |
| |   | |   | |\/| |
| |___| |___| |  | |
|_____|_____|_|  |_|

 __        __ ___  _  __ ___
 \ \      / /|_ _|| |/ /|_ _|
  \ \ /\ / /  | | | ' /  | |
   \ V  V /   | | | . \  | |
    \_/\_/   |___||_|\_\|___|

        L L M   W I K I
        maintained context, not disposable chunks
'''

SUPPORTED_PATTERNS = ["*.md", "*.markdown", "*.txt", "*.rtf", "*.rst", "*.py", "*.json", "*.csv", "*.pdf", "*.docx", "*.doc"]
COMMANDS = [
    "help", "search", "find", "search-following", "follow-search", "why", "diagnose", "search-debug", "retrieve", "articles",
    "ask", "context", "read", "stats", "lint", "repair", "graph", "mermaid", "map",
    "neighbourhood", "neighborhood", "ingest", "edit", "export", "pages", "json", "mode",
    "config", "reindex", "self", "usage", "scope", "recursive", "compress", "history",
    "history-status", "askrec", "recursive-preview", "tokens", "self-stats", "self-usage",
    "capabilities", "runtime-journal", "command-map", "runtime-graph", "reconcile",
    "notes", "notes-iterate", "notes-all", "notes-search", "notes-links", "notes-status",
    "notes-graph", "ask-mode", "ask-plain", "intent-dry", "planner-tools", "tool-count",
    "tool-catalog", "ask-agentic", "ask-agentic-dry", "ask-agentic-protocol",
    "limitations", "provenance", "startup", "docs-consolidate", "history-build",
    "context-settings", "debug-context",
    "screen-width", "wrap",
    "exit", "quit", "bye", "q",
]
SLASH_COMMANDS = [f"/{name}" for name in COMMANDS]
RAW_TEXT_COMMANDS = {
    # These commands take one natural-language question/title argument. Keep the
    # raw text intact so ordinary apostrophes do not need shell escaping.
    "ask", "ask-plain", "ask-agentic", "ask-agentic-dry", "ask-agentic-protocol",
    "askrec", "self", "context", "read", "edit", "notes", "notes-iterate",
    "notes-links", "recursive-preview", "intent-dry", "debug-context",
}

def _parse_interactive_line(line: str) -> tuple[str, List[str], str, bool]:
    """Parse one interactive shell line.

    Slash-prefixed input is treated as an explicit command, for example
    `/search architecture`. Input without a slash is treated as a natural
    language `/ask` question, so names and apostrophes such as
    `Tell me about Karpathy's work!` are preserved exactly.
    """
    raw_line = line.strip()
    if not raw_line:
        return "", [], "", False
    lowered = raw_line.lower()
    if lowered in {"quit", "exit", "bye", "q"}:
        return lowered, [], "", False
    if not raw_line.startswith("/"):
        return "ask", [raw_line], raw_line, True
    body = raw_line[1:].strip()
    if not body:
        return "help", [], "", False
    cmd, _, raw_args = body.partition(" ")
    cmd = cmd.strip().lower()
    raw_args = raw_args.strip()
    if cmd in RAW_TEXT_COMMANDS:
        return cmd, ([raw_args] if raw_args else []), raw_args, False
    try:
        parts = shlex.split(body)
    except ValueError:
        # Be forgiving for command arguments containing apostrophes without
        # shell-style quoting. `posix=False` treats an apostrophe inside a word
        # as an ordinary character, while still splitting flags for commands
        # such as `/retrieve architecture --top-k 2`.
        parts = shlex.split(body, posix=False)
    if not parts:
        return "help", [], "", False
    return parts[0].lower(), parts[1:], raw_args, False

def _visible_turn_signature(row: Dict[str, Any]) -> tuple[str, str]:
    """Return a stable comparison key for a recorded visible ask turn."""
    question = " ".join(str(row.get("question", "")).split())
    answer = " ".join(str(row.get("answer", "")).split())[:500]
    return question, answer


def _record_visible_cli_ask_turn(vault: Path, question: str, payload: Dict[str, Any], session_turns: List[Dict[str, Any]]) -> None:
    """Persist the exact answer shown by the CLI and keep an in-session copy.

    The lower-level agentic ask normally records history itself. This CLI-level
    guard makes the user-visible `/history` command robust even if an older
    agent path, compression edge case, or write failure prevents the lower layer
    from appending a turn. It de-duplicates against the recent JSONL history so
    normal operation does not create duplicate turns.
    """
    answer = str(payload.get("answer") or "").strip()
    if not question or not answer:
        return
    tools = list(payload.get("tools_called") or [])
    prompt = str(payload.get("llm_prompt") or payload.get("prompt") or "")
    if not prompt:
        prompt = "User request: " + question
    record = {
        "question": question,
        "prompt": prompt,
        "answer": answer,
        "sources": tools,
        "metadata": {"recorded_by": "cli_visible_turn_guard"},
        "prompt_tokens_estimate": release_estimate_tokens(prompt),
        "answer_tokens_estimate": release_estimate_tokens(answer),
    }
    sig = _visible_turn_signature(record)
    try:
        recent = release_load_history(str(vault), 12)
    except Exception:
        recent = []
    if any(_visible_turn_signature(row) == sig for row in recent):
        pass
    else:
        try:
            release_record_ask_turn_with_metrics(str(vault), question, prompt, answer, tools, None, {"agentic": True, "recorded_by": "cli_visible_turn_guard"})
        except Exception:
            # The in-memory session history below still keeps `/history` useful.
            pass
    if not any(_visible_turn_signature(row) == sig for row in session_turns[-20:]):
        session_turns.append(record)


def _merge_history_rows(file_rows: List[Dict[str, Any]], session_rows: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    """Merge persistent and in-session ask history without duplicate rows."""
    merged: List[Dict[str, Any]] = []
    seen = set()
    for row in list(file_rows or []) + list(session_rows or []):
        sig = _visible_turn_signature(row)
        if sig in seen:
            continue
        seen.add(sig)
        merged.append(row)
    return merged[-int(limit):]


class Colours:
    """Represent the Colours component used by the local wiki runtime."""
    user = "\033[96m"
    answer = "\033[92m"
    title = "\033[95m"
    warning = "\033[93m"
    error = "\033[91m"
    reset = "\033[0m"
    bold = "\033[1m"

COLOUR_ENABLED = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

def colour(text: Any, code: str) -> str:
    """Implement the colour operation for the local LLM Wiki workflow."""
    s = str(text)
    return f"{code}{s}{Colours.reset}" if COLOUR_ENABLED else s

def user_line(text: str) -> str:
    """Implement the user line operation for the local LLM Wiki workflow."""
    return colour(text, Colours.user)


DEFAULT_SCREEN_WIDTH = 120
SCREEN_WIDTH = DEFAULT_SCREEN_WIDTH
SCREEN_WRAP_ENABLED = True


def _env_screen_width() -> int:
    """Return the configured screen width from the environment or default."""
    raw = os.environ.get("LLM_WIKI_SCREEN_WIDTH", "").strip()
    if not raw:
        return DEFAULT_SCREEN_WIDTH
    try:
        width = int(raw)
    except ValueError:
        return DEFAULT_SCREEN_WIDTH
    return max(0, width)


def configure_screen_output(width: Optional[int] = None, enabled: Optional[bool] = None) -> None:
    """Configure terminal-only line wrapping.

    A width of 0 disables wrapping. JSON and exported Markdown are deliberately
    left untouched; this setting is only for text printed to the terminal.
    """
    global SCREEN_WIDTH, SCREEN_WRAP_ENABLED
    if width is not None:
        SCREEN_WIDTH = max(0, int(width))
    if enabled is not None:
        SCREEN_WRAP_ENABLED = bool(enabled) and SCREEN_WIDTH > 0


def _screen_wrap_status() -> str:
    """Return a user-facing description of the current screen wrapping mode."""
    if not SCREEN_WRAP_ENABLED or SCREEN_WIDTH <= 0:
        return "Screen wrapping is disabled."
    return f"Screen wrapping width: {SCREEN_WIDTH} characters."


def wrap_screen_text(text: Any, width: Optional[int] = None, enabled: Optional[bool] = None) -> str:
    """Wrap terminal output at word boundaries without altering Markdown files.

    The wrapper preserves blank lines, fenced code blocks, indented/preformatted
    lines, Markdown tables, and obvious list items. Long words are never split;
    if a single token is wider than the screen width, it is left intact so the
    terminal may still wrap it visually rather than the CLI inserting a broken
    word.
    """
    s = str(text if text is not None else "")
    actual_width = SCREEN_WIDTH if width is None else max(0, int(width))
    actual_enabled = SCREEN_WRAP_ENABLED if enabled is None else bool(enabled)
    if not actual_enabled or actual_width <= 0:
        return s
    wrapped: List[str] = []
    in_fence = False
    for line in s.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            wrapped.append(line)
            in_fence = not in_fence
            continue
        if in_fence or not stripped:
            wrapped.append(line)
            continue
        if len(line) <= actual_width:
            wrapped.append(line)
            continue
        # Keep structures where inserted line breaks are more likely to damage
        # the meaning or layout than improve readability. Markdown block quotes
        # are handled below so quoted prose wraps neatly on screen too.
        if line.startswith((" ", "\t")) or stripped.startswith(("|", "- ", "* ", "+ ")):
            wrapped.append(line)
            continue
        if set(stripped) <= {"-", "="}:
            wrapped.append(line)
            continue
        quote_prefix = ""
        content = line
        if stripped.startswith(">"):
            leading = line[: len(line) - len(line.lstrip())]
            rest = line.lstrip()
            depth = len(rest) - len(rest.lstrip(">"))
            quote_prefix = leading + (">" * depth) + " "
            content = rest[depth:].lstrip()
        wrap_width = max(8, actual_width - len(quote_prefix)) if quote_prefix else actual_width
        chunks = textwrap.wrap(
            content,
            width=wrap_width,
            break_long_words=False,
            break_on_hyphens=False,
            replace_whitespace=False,
            drop_whitespace=True,
        ) or [content]
        wrapped.extend((quote_prefix + chunk if quote_prefix else chunk) for chunk in chunks)
    # Preserve a trailing newline when the caller supplied one.
    result = "\n".join(wrapped)
    if s.endswith("\n"):
        result += "\n"
    return result


def screen_print(text: Any = "", *, end: str = "\n") -> None:
    """Print terminal text using the configured word-boundary wrapper."""
    print(wrap_screen_text(text), end=end)




def _parse_shell_retrieve_args(args: List[str]) -> Dict[str, Any]:
    """Parse shell retrieve/articles options without treating flags as query text."""
    opts = {"query": "", "top_k": 5, "show": False, "max_chars_per_article": 4000, "max_total_chars": 12000}
    query: List[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in {"--show", "show"}:
            opts["show"] = True; i += 1; continue
        if a in {"--top-k", "--top_k", "-k"} and i + 1 < len(args):
            opts["top_k"] = int(args[i+1]); i += 2; continue
        if a.startswith("--top-k=") or a.startswith("--top_k="):
            opts["top_k"] = int(a.split("=", 1)[1]); i += 1; continue
        if a == "--max-chars-per-article" and i + 1 < len(args):
            opts["max_chars_per_article"] = int(args[i+1]); i += 2; continue
        if a.startswith("--max-chars-per-article="):
            opts["max_chars_per_article"] = int(a.split("=", 1)[1]); i += 1; continue
        if a == "--max-total-chars" and i + 1 < len(args):
            opts["max_total_chars"] = int(args[i+1]); i += 2; continue
        if a.startswith("--max-total-chars="):
            opts["max_total_chars"] = int(a.split("=", 1)[1]); i += 1; continue
        query.append(a); i += 1
    opts["query"] = " ".join(query).strip()
    return opts


def _parse_shell_search_args(args: List[str]) -> Dict[str, Any]:
    """Internal helper for parse shell search args."""
    opts = {"query": "", "limit": 8}
    query: List[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in {"--limit", "-n"} and i + 1 < len(args):
            opts["limit"] = int(args[i+1]); i += 2; continue
        if a.startswith("--limit="):
            opts["limit"] = int(a.split("=", 1)[1]); i += 1; continue
        query.append(a); i += 1
    opts["query"] = " ".join(query).strip()
    return opts




def _parse_shell_search_following_args(args: List[str]) -> Dict[str, Any]:
    """Parse `/search-following` options for long-document navigation."""
    opts = {"query": "", "limit": 5, "following_pages": 2, "context_chars": 4000, "max_chars": 16000}
    query: List[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in {"--limit", "-n"} and i + 1 < len(args):
            opts["limit"] = int(args[i+1]); i += 2; continue
        if a.startswith("--limit="):
            opts["limit"] = int(a.split("=", 1)[1]); i += 1; continue
        if a in {"--pages", "--following-pages", "--following", "-p"} and i + 1 < len(args):
            opts["following_pages"] = int(args[i+1]); i += 2; continue
        if a.startswith("--pages=") or a.startswith("--following-pages="):
            opts["following_pages"] = int(a.split("=", 1)[1]); i += 1; continue
        if a in {"--context-chars", "--chars"} and i + 1 < len(args):
            opts["context_chars"] = int(args[i+1]); i += 2; continue
        if a.startswith("--context-chars=") or a.startswith("--chars="):
            opts["context_chars"] = int(a.split("=", 1)[1]); i += 1; continue
        if a == "--max-chars" and i + 1 < len(args):
            opts["max_chars"] = int(args[i+1]); i += 2; continue
        if a.startswith("--max-chars="):
            opts["max_chars"] = int(a.split("=", 1)[1]); i += 1; continue
        query.append(a); i += 1
    opts["query"] = " ".join(query).strip()
    return opts


def format_search_following(data: Dict[str, Any]) -> str:
    """Format long-document search windows for terminal output."""
    results = data.get("results", [])
    query = data.get("query", "")
    if not results:
        return f"No long-document search windows for: {query!r}"
    lines = [
        f"Search-following results for: {query!r} ({len(results)} found)",
        f"Following pages requested: {data.get('following_pages')}",
        "",
    ]
    for i, row in enumerate(results, 1):
        page_bits = []
        if row.get("start_page") is not None:
            page_bits.append(f"pages {row.get('start_page')}–{row.get('end_page')}")
        if row.get("page_markers_found"):
            page_bits.append(f"markers={row.get('page_markers_found')}")
        lines.append(
            f"{i}. {row.get('title','')} score={row.get('score')}"
            + (" (" + ", ".join(page_bits) + ")" if page_bits else "")
        )
        if row.get("matched_terms"):
            lines.append("   matched: " + ", ".join(row.get("matched_terms", [])[:10]))
        excerpt = str(row.get("excerpt") or row.get("snippet") or "").strip()
        if excerpt:
            lines.append("\n" + excerpt[: int(row.get("excerpt_chars") or len(excerpt))])
            lines.append("\n---")
    return "\n".join(lines).rstrip("-\n")

def _parse_shell_ask_args(args: List[str]) -> Dict[str, Any]:
    """Internal helper for parse shell ask args."""
    opts = {"question": "", "dry_run": False, "top_k": None, "model": None, "host": None}
    question: List[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a in {"--dry-run", "dry"}:
            opts["dry_run"] = True; i += 1; continue
        if a in {"--top-k", "--top_k", "-k"} and i + 1 < len(args):
            opts["top_k"] = int(args[i+1]); i += 2; continue
        if a.startswith("--top-k=") or a.startswith("--top_k="):
            opts["top_k"] = int(a.split("=", 1)[1]); i += 1; continue
        if a == "--model" and i + 1 < len(args):
            opts["model"] = args[i+1]; i += 2; continue
        if a.startswith("--model="):
            opts["model"] = a.split("=", 1)[1]; i += 1; continue
        if a == "--host" and i + 1 < len(args):
            opts["host"] = args[i+1]; i += 2; continue
        if a.startswith("--host="):
            opts["host"] = a.split("=", 1)[1]; i += 1; continue
        question.append(a); i += 1
    opts["question"] = " ".join(question).strip()
    return opts

def _truncate(text: Any, width: int) -> str:
    """Internal helper for truncate."""
    s = str(text if text is not None else "")
    s = s.replace("\n", " ").strip()
    if width <= 3:
        return s[:width]
    return s if len(s) <= width else s[: width - 1] + "…"


def _plain_tags(tags: Any) -> str:
    """Internal helper for plain tags."""
    if tags is None:
        return ""
    if isinstance(tags, list):
        return ", ".join(str(t) for t in tags)
    s = str(tags)
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            return ", ".join(str(t) for t in parsed)
    except Exception:
        pass
    return s.strip("[]'")


def _table(rows: List[Dict[str, Any]], columns: Sequence[tuple[str, str, int]]) -> str:
    """Internal helper for table."""
    if not rows:
        return ""
    widths = []
    for key, header, max_width in columns:
        max_cell = max([len(str(header))] + [len(_truncate(r.get(key, ""), max_width)) for r in rows])
        widths.append(min(max_cell, max_width))
    header = "  ".join(str(h).ljust(w) for (_, h, _), w in zip(columns, widths))
    rule = "  ".join("-" * w for w in widths)
    lines = [header, rule]
    for row in rows:
        lines.append("  ".join(_truncate(row.get(key, ""), w).ljust(w) for (key, _, _), w in zip(columns, widths)))
    return "\n".join(lines)


def _print_json(data: Any) -> None:
    """Internal helper for print json."""
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))



def format_search_diagnostics(data: Dict[str, Any]) -> str:
    """Search or retrieve wiki content for format search diagnostics."""
    diag = data.get("diagnostics", {})
    lines = [f"Search diagnostics for: {data.get('query', '')!r}", ""]
    lines.append(f"Case dependent: {'yes' if diag.get('case_sensitive') else 'no'}")
    lines.append(f"Plural/singular expansion: {'yes' if diag.get('plural_singular_supported') else 'no'}")
    if diag.get('plain_words'):
        lines.append("Query words: " + ", ".join(diag.get('plain_words', [])))
    if diag.get('expanded_terms'):
        lines.append("Expanded terms: " + ", ".join(diag.get('expanded_terms', [])))
    titles = data.get('top_titles') or []
    if titles:
        lines.append("\nTop result titles:")
        for t in titles:
            lines.append(f"  - {t}")
    suggestions = data.get('title_suggestions') or []
    if suggestions:
        lines.append("\nTitle suggestions:")
        for t in suggestions:
            lines.append(f"  - {t}")
    notes = data.get('notes') or []
    if notes:
        lines.append("\nNotes:")
        for n in notes:
            lines.append(f"  - {n}")
    return "\n".join(lines)

def format_search(data: Dict[str, Any]) -> str:
    """Search or retrieve wiki content for format search."""
    query = data.get("query", "")
    results = data.get("results", [])
    if not results:
        return f"No results for: {query!r}\nSearch is case-insensitive and Release tries singular/plural variants. Try `/why {query}`, `/pages`, or run `/ingest <directory>` for the expected files."
    lines = [f"Search results for: {query!r}  ({len(results)} found)", ""]
    for i, r in enumerate(results, 1):
        try:
            score = f"{float(r.get('score', 0)):.3g}"
        except Exception:
            score = str(r.get('score', ''))
        lines.append(f"{i}. {r.get('title', '')}  score={score}")
        snippet = _truncate(r.get("snippet", ""), 220)
        if snippet:
            lines.append(f"   {snippet}")
        links = r.get("links") or []
        if links:
            lines.append(f"   links: {', '.join(links[:6])}")
    return "\n".join(lines)



def format_retrieve(data: Dict[str, Any]) -> str:
    """Search or retrieve wiki content for format retrieve."""
    articles = data.get("articles", [])
    prompt = data.get("prompt", data.get("query", ""))
    if not articles:
        return f"No articles retrieved for: {prompt!r}\nTry a fuller query, run `/pages`, or ingest more documents with `/ingest <directory>`."
    lines = [f"Retrieved top articles for: {prompt!r}", f"Retrieved: {data.get('retrieved_count', len(articles))} | Context chars: {data.get('chars', 0)}", ""]
    rows=[]
    for a in articles:
        try:
            score=f"{float(a.get('score', 0)):.3g}"
        except Exception:
            score=str(a.get('score',''))
        rows.append({"rank": a.get("rank"), "title": a.get("title"), "score": score, "chars": a.get("chars"), "trunc": "yes" if a.get("truncated") else "no"})
    lines.append(_table(rows, [("rank","#",3),("title","Title",44),("score","Score",9),("chars","Chars",8),("trunc","Trunc",6)]))
    lines.append("\nUse `llm-wiki retrieve <prompt> --show` outside shell, or `/articles <prompt>` inside shell, to print the LLM-ready context text.")
    return "\n".join(lines)



def format_ask(data: Dict[str, Any]) -> str:
    """Build or execute the local LLM ask workflow for format ask."""
    question = data.get("question", "")
    lines = [user_line(f"User request: {question}"), ""]
    if data.get("dry_run"):
        lines.append("Dry run: built the Ollama prompt but did not call the model.")
        lines.append(f"Model: {data.get('model')} | Host: {data.get('host')} | Top-k: {data.get('top_k')}")
        lines.append(f"Prompt chars: {len(data.get('llm_prompt',''))}")
        return "\n".join(lines)
    if not data.get("ok"):
        ollama = data.get("ollama", {})
        lines.append(colour("Ollama request failed", Colours.error))
        lines.append(ollama.get("error", data.get("error", "unknown error")))
        if ollama.get("hint"):
            lines.append(ollama["hint"])
        return "\n".join(lines)
    lines.append(colour("Answer:", Colours.answer))
    lines.append(data.get("answer", "").strip() or "(empty response)")
    retrieval = data.get("retrieval", {})
    sources = [a.get("title") for a in retrieval.get("articles", [])]
    if sources:
        lines.append("")
        lines.append("Sources: " + ", ".join(f"[[{s}]]" for s in sources[:8]))
    return "\n".join(lines)
def format_pages(data: Dict[str, Any]) -> str:
    """Implement the format pages operation for the local LLM Wiki workflow."""
    pages = data.get("pages", [])
    if not pages:
        return "No pages found. Use `init` or `ingest <directory>` first."
    rows=[]
    for p in pages:
        rows.append({
            "title": p.get("title", ""),
            "words": p.get("words", 0),
            "tags": _plain_tags(p.get("tags", "")),
            "links": len(p.get("links") or []),
            "updated": str(p.get("updated", ""))[:19],
        })
    return f"Pages: {data.get('count', len(pages))}\n\n" + _table(rows, [("title","Title",42),("words","Words",7),("tags","Tags",24),("links","Links",6),("updated","Updated",19)])


def format_lint(data: Dict[str, Any]) -> str:
    """Implement the format lint operation for the local LLM Wiki workflow."""
    lines = ["Wiki lint report"]
    ok = data.get("ok", False)
    lines.append("Status: " + ("OK" if ok else "Needs attention"))
    broken = data.get("broken_links", [])
    orphans = data.get("orphans", [])
    short = data.get("very_short_pages", [])
    lines.append(f"Pages: {data.get('page_count', '?')} | Broken links: {len(broken)} | Orphans: {len(orphans)} | Very short pages: {len(short)}")
    if broken:
        lines.append("\nBroken links:")
        for b in broken[:20]:
            lines.append(f"  - {b.get('from')} -> {b.get('to')}")
        if len(broken) > 20:
            lines.append(f"  … {len(broken)-20} more")
    if orphans:
        lines.append("\nOrphan pages:")
        lines.append("  " + ", ".join(orphans[:20]) + (f", … {len(orphans)-20} more" if len(orphans)>20 else ""))
    if short:
        lines.append("\nVery short pages:")
        lines.append("  " + ", ".join(short[:20]) + (f", … {len(short)-20} more" if len(short)>20 else ""))
    if not ok:
        lines.append("\nSuggested next steps: edit broken links, add backlinks between source pages, and expand very short seed pages.")
    return "\n".join(lines)



def format_repair(data: Dict[str, Any]) -> str:
    """Implement the format repair operation for the local LLM Wiki workflow."""
    lines = ["Wiki repair plan" if data.get("dry_run", True) else "Wiki repair result"]
    lines.append("Mode: " + ("dry run" if data.get("dry_run", True) else "applied"))
    before = data.get("before") or {}
    after = data.get("after") or {}
    lines.append(f"Actions: {data.get('action_count', 0)}")
    lines.append(f"Before: broken={len(before.get('broken_links', []))}, orphans={len(before.get('orphans', []))}, short={len(before.get('very_short_pages', []))}")
    if after:
        lines.append(f"After:  broken={len(after.get('broken_links', []))}, orphans={len(after.get('orphans', []))}, short={len(after.get('very_short_pages', []))}")
    actions = data.get("actions", [])
    if actions:
        rows=[]
        for a in actions[:40]:
            detail = a.get("title") or f"{a.get('from','')} -> {a.get('new_target') or a.get('target') or a.get('old_target','')}"
            rows.append({"kind": a.get("kind"), "detail": detail, "apply": "yes" if a.get("apply") else "no"})
        lines.append("\nActions:")
        lines.append(_table(rows, [("kind","Kind",30),("detail","Detail",54),("apply","Apply",6)]))
        if len(actions) > 40:
            lines.append(f"… {len(actions)-40} more actions")
    changed = data.get("changed_pages") or []
    if changed:
        lines.append("\nChanged pages: " + ", ".join(changed[:30]) + (f", … {len(changed)-30} more" if len(changed)>30 else ""))
    notes = data.get("notes") or []
    if notes:
        lines.append("\nNotes:")
        for n in notes:
            lines.append(f"  - {n}")
    if data.get("dry_run", True):
        lines.append("\nNothing was changed. Run `/repair --apply` to apply the safe repairs.")
    return "\n".join(lines)

def format_stats(data: Dict[str, Any]) -> str:
    """Implement the format stats operation for the local LLM Wiki workflow."""
    status = data.get("status", data)
    health = data.get("health", {})
    lint = data.get("lint", health.get("lint", {}))
    cats = health.get("categories", {})
    lines = ["LLM Wiki status", ""]
    rows = [
        {"metric":"Vault", "value": status.get("vault", "")},
        {"metric":"Pages", "value": status.get("page_count", 0)},
        {"metric":"Raw files", "value": status.get("raw_file_count", 0)},
        {"metric":"Word estimate", "value": status.get("word_count_estimate", 0)},
        {"metric":"SQLite index", "value": "yes" if status.get("db_exists") else "no"},
    ]
    lines.append(_table(rows, [("metric","Metric",16),("value","Value",90)]))
    if lint:
        lines.append("")
        lines.append(f"Health: broken links={len(lint.get('broken_links', []))}, orphans={len(lint.get('orphans', []))}, short pages={len(lint.get('very_short_pages', []))}")
    if cats:
        tags = cats.get("tags", {})
        if tags:
            lines.append("Tags: " + ", ".join(f"{k}={v}" for k,v in sorted(tags.items())[:12]))
        categories = cats.get("categories", {})
        if categories:
            lines.append("Categories: " + ", ".join(f"{k}={v}" for k,v in sorted(categories.items())[:12]))
    lines.append("\nUse `lint` for maintenance detail, `pages` to inspect pages, or `search <query>` to test retrieval.")
    return "\n".join(lines)


def format_graph(data: Dict[str, Any]) -> str:
    """Create graph-oriented output for format graph."""
    return f"Graph summary\nNodes: {data.get('nodes', data.get('node_count', 0))}\nEdges: {data.get('edges', data.get('edge_count', 0))}\nBacklink targets: {data.get('backlinks', 0)}"

def format_mermaid(data: Dict[str, Any]) -> str:
    """Create graph-oriented output for format mermaid."""
    lines = ["Mermaid graph generated", f"Nodes: {data.get('node_count', 0)} | Edges: {data.get('edge_count', 0)}"]
    if data.get("output_path"):
        lines.append(f"Written: {data.get('output_path')}")
        lines.append("Open the .md file in a Mermaid-aware viewer, GitHub, Obsidian, or paste into mermaid.live.")
    else:
        lines.append("")
        lines.append("```mermaid")
        lines.append(data.get("mermaid", "").rstrip())
        lines.append("```")
    return "\n".join(lines)


def format_ingest(data: Dict[str, Any]) -> str:
    """Ingest source content into Markdown wiki pages for format ingest."""
    results = data.get("results", [])
    lines = [f"Ingested {data.get('ingested_count', len(results))} files from {data.get('directory', '')}"]
    if results:
        rows=[]
        for r in results[:60]:
            rows.append({"title": r.get("title", ""), "suffix": r.get("suffix", ""), "chars": r.get("chars", 0), "source": Path(str(r.get("source", ""))).name})
        lines.append("")
        lines.append(_table(rows, [("title","Wiki page",42),("suffix","Type",6),("chars","Chars",8),("source","Source file",40)]))
        if len(results) > 60:
            lines.append(f"… {len(results)-60} more files omitted from display. Use --json for full output.")
    lines.append("\nRun `search <term>`, `pages`, or `lint` next.")
    return "\n".join(lines)


def format_export(data: Dict[str, Any]) -> str:
    """Implement the format export operation for the local LLM Wiki workflow."""
    return f"Exported llms.txt\nPath: {data.get('output_path')}\nChars: {data.get('chars')}\nSHA256: {data.get('sha256')}"


def format_init(data: Dict[str, Any]) -> str:
    """Implement the format init operation for the local LLM Wiki workflow."""
    return f"Initialised wiki vault\nVault: {data.get('vault')}\nSeed pages: {', '.join(data.get('seed_pages') or data.get('created', [])) or '(already present)'}"


def human_print(data: Any, kind: str = "generic", as_json: bool = False) -> None:
    """Print user-facing CLI output, applying screen wrapping when enabled."""
    if as_json:
        _print_json(data); return
    if isinstance(data, str):
        screen_print(data); return
    if kind == "search": screen_print(format_search(data)); return
    if kind == "search_diagnostics": screen_print(format_search_diagnostics(data)); return
    if kind == "search_following": screen_print(format_search_following(data)); return
    if kind == "retrieve": screen_print(format_retrieve(data)); return
    if kind == "ask": screen_print(format_ask(data)); return
    if kind == "pages": screen_print(format_pages(data)); return
    if kind == "lint": screen_print(format_lint(data)); return
    if kind == "repair": screen_print(format_repair(data)); return
    if kind == "stats": screen_print(format_stats(data)); return
    if kind == "graph": screen_print(format_graph(data)); return
    if kind == "mermaid": screen_print(format_mermaid(data)); return
    if kind == "ingest": screen_print(format_ingest(data)); return
    if kind == "export": screen_print(format_export(data)); return
    if kind == "init": screen_print(format_init(data)); return
    if kind == "config": screen_print("Config file: " + str(data.get("config_path", "")) + "\nOllama model: " + str(data.get("config",{}).get("ollama",{}).get("model", "")) + "\nOllama host: " + str(data.get("config",{}).get("ollama",{}).get("host", ""))); return
    if kind == "reindex": screen_print(f"Reindexed {data.get('indexed_pages', '?')} pages\nDatabase: {data.get('db_path', '')}"); return
    _print_json(data)


def strip_rtf_to_text(raw: str) -> str:
    """Convert common RTF markup into readable plain text for ingestion."""
    import re
    text = str(raw or "")

    def _hex(match):
        """Document the `_hex` function used by the LLM Wiki MCP release."""
        try:
            return bytes.fromhex(match.group(1)).decode("latin-1")
        except Exception:
            return " "

    def _unicode(match):
        """Document the `_unicode` function used by the LLM Wiki MCP release."""
        try:
            value = int(match.group(1))
            if value < 0:
                value += 65536
            return chr(value)
        except Exception:
            return " "

    text = re.sub(r"\\'([0-9a-fA-F]{2})", _hex, text)
    text = re.sub(r"\\u(-?\d+)\??", _unicode, text)
    text = re.sub(r"\\(par|line|tab)\b ?", "\n", text)
    text = re.sub(r"\\[{}\\]", lambda m: m.group(0)[1:], text)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_text(path: Path) -> str:
    """Extract text from supported files with optional dependencies."""
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".txt", ".rst", ".py", ".json", ".csv", ".yaml", ".yml", ".toml", ".html", ".htm"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".rtf":
        return strip_rtf_to_text(path.read_text(encoding="utf-8", errors="replace"))
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore
            reader = PdfReader(str(path))
            total = len(reader.pages)
            parts = []
            for idx, page in enumerate(reader.pages, 1):
                page_text = page.extract_text() or ""
                parts.append(f"--- Page {idx} of {total} ---\n\n{page_text}")
            return "\n\n".join(parts).strip()
        except Exception as exc:
            return f"[PDF text extraction unavailable or failed for {path.name}: {exc}. Install pypdf for better extraction.]"
    if suffix == ".docx":
        try:
            import docx  # type: ignore
            document = docx.Document(str(path))
            return "\n".join(p.text for p in document.paragraphs)
        except Exception as exc:
            return f"[DOCX text extraction unavailable or failed for {path.name}: {exc}. Install python-docx for better extraction.]"
    if suffix == ".doc":
        return f"[Legacy .doc extraction is not built in for {path.name}. Convert to .docx/.pdf or add an external extractor.]"
    return path.read_text(encoding="utf-8", errors="ignore")


def ingest_path(vault: Path, directory: Path, patterns: Sequence[str], recursive: bool, limit: int,
                overwrite: bool = True, json_output: bool = False, progress_callback: Any = None) -> Dict[str, Any]:
    """Ingest a directory or one source document into generated wiki pages."""
    set_vault(vault)
    store = WikiStore(WikiConfig(vault))
    if not any(store.cfg.wiki_dir.glob("*.md")):
        store.init_seed()
    files: List[Path] = []
    scan_seen: set[str] = set()
    def _scan_add(candidate: Path) -> None:
        """Document the `_scan_add` function used by the LLM Wiki MCP release."""
        if not candidate.is_file():
            return
        try:
            key = str(candidate.resolve())
        except Exception:
            key = str(candidate)
        if key in scan_seen:
            return
        scan_seen.add(key)
        files.append(candidate)
        if progress_callback:
            try:
                progress_callback(len(files), 0, candidate, "scan")
            except TypeError:
                progress_callback(len(files), 0, candidate)

    if directory.is_file():
        _scan_add(directory)
    else:
        for pattern in patterns:
            iterator = directory.rglob(pattern) if recursive else directory.glob(pattern)
            for candidate in iterator:
                _scan_add(candidate)
    unique: List[Path] = []
    seen=set()
    vault_root = vault.expanduser().resolve()
    for p in files:
        rp_path = p.resolve()
        try:
            rp_path.relative_to(vault_root)
            continue
        except ValueError:
            pass
        rp=str(rp_path)
        if p.is_file() and rp not in seen:
            unique.append(p); seen.add(rp)
    unique = unique[:limit]
    results=[]
    total_files = len(unique)
    for idx, path in enumerate(unique, 1):
        if progress_callback:
            try:
                progress_callback(idx, total_files, path, "ingest")
            except TypeError:
                progress_callback(idx, total_files, path)
        text = extract_text(path)
        title = safe_slug(f"Source - {path.stem}")
        body = f"# {title}\n\nSource file: `{path}`\n\n## Extracted Content\n\n{text.strip()}\n"
        page = store.create_page(title, body, tags=["source", "ingested", path.suffix.lower().lstrip('.') or "file"], source=str(path), overwrite=overwrite)
        try:
            raw = store.cfg.raw_dir / path.name
            if path.resolve() != raw.resolve():
                raw.write_bytes(path.read_bytes())
        except Exception:
            pass
        results.append({"source": str(path), "title": page["title"], "chars": len(text), "suffix": path.suffix})
    store.reindex()
    report = {"vault": str(vault), "directory": str(directory), "patterns": list(patterns), "recursive": recursive,
              "ingested_count": len(results), "results": results}
    human_print(report, "ingest", json_output)
    return report


def print_help() -> None:
    """Print the slash-command help for the interactive shell."""
    print(textwrap.dedent("""
    Interactive shell input
      /command ...            Run an explicit command.
      anything else           Ask the wiki using /ask.

    Examples
      /ingest .
      /ingest ./notes/meeting.txt
      /ingest ./notes/project-brief.rtf
      /search architecture
      /search-following quantum foam --pages 3
      /config host http://localhost:11434
      /config model llama3.2:3b
      /ask Tell me about this wiki.
      Tell me about Karpathy's work!
      /screen-width 120
      /screen-width off
      /context-settings context-budget 24000
      /debug-context tell me about Vishva

    Commands
      /search <query>          Search page snippets centred around the hit
      /find <query>            Alias for /search
      /search-following <q>    Return the matched page plus N following pages from long books
      /why <query>             Explain search normalisation and suggestions
      /retrieve <query>        Search and retrieve top-k full wiki articles
      /articles <query>        Retrieve and print LLM-ready article context
      /ask <question>          Retrieve wiki context and ask local Ollama
      /context <query>         Build LLM-ready context pack
      /read <title>            Read a page
      /stats                   Show status and health summary
      /lint                    Show broken links, orphans, and short pages
      /repair [--apply]        Plan/apply safe wiki lint repairs
      /graph                   Show graph summary
      /mermaid [path]          Render full wiki graph as Mermaid Markdown
      /map <title> [path]      Render a page-centred Mermaid neighbourhood
      /ingest <directory>      Ingest supported files; compact by default, use --verbose for file list
      /edit <title>            Open page in $EDITOR, or print path if no editor
      /export [path]           Export llms.txt
      /pages                   List pages in a table
      /config                  Show config
      /config host <url>       Set Ollama host and save immediately
      /config model <name>     Set Ollama model and save immediately
      /config set <key> <val>  Set any config key, e.g. ollama.timeout_seconds
      /config test             Test configured Ollama connection
      /config edit             Open config in $EDITOR and reload
      /config reset            Reset config to defaults
      /reindex                 Rebuild the SQLite index
      /self <question>         Ask the tool/wiki about itself and print self-context
      /recursive on|off        Enable/disable recursive ask and save config
      /compress on|off         Enable/disable history compression and save config
      /history                 Show recent ask history
      /context-settings         Show/tune ask context budgets
      /debug-context <question> Show the assembled ask context without Ollama
      /history-status          Show recursive memory/compression status
      /askrec <question>       Recursive ask preview using saved history
      /usage                   Show estimated wiki/query token usage
      /tokens                  Show token/s and ask metrics summary
      /self-stats              Structured self-access status, usage and metrics
      /self-usage              Usage snapshot for the tool/wiki/history
      /capabilities            Show live runtime capability surface
      /runtime-journal         Show recent runtime execution journal
      /command-map             Show command-to-tool mapping
      /runtime-graph           Print Mermaid runtime execution graph
      /reconcile               Check docs vs CLI/MCP function surfaces
      /notes <page>            Show/create AI sidecar notes for a page
      /notes-iterate <page>    Iterate/write AI notes and candidate links
      /notes-all [limit]       Iterate notes for all pages
      /notes-search <query>    Search source pages plus AI notes
      /notes-links <page>      Show candidate links for a page
      /notes-status            Show AI notes coverage
      /notes-graph             Mermaid graph from AI note links
      /ask-agentic <question>  Tool-calling ask with Ollama final answer
      /ask-mode agentic|plain  Show/set default ask mode
      /ask-plain <question>    Non-agentic ask without tool loop
      /tool-catalog            Show unified MCP-style tool catalogue
      /tool-count              Show Release full catalogue count
      /provenance              Show ingest provenance summary
      /startup                 Show startup command list
      /startup default         Set startup commands to /ingest ./docs + /notes-all
      /startup set <cmd;cmd>   Set startup command list
      /history-build           Build GitHub-friendly DEVELOPMENT_HISTORY.md
      /docs-consolidate        Consolidate docs into fewer category files
      /planner-tools           Show Release planner tool groups
      /intent-dry <question>   Show Release resolved intent and planned tools
      /ask-agentic-dry <q>     Build agentic evidence pack without Ollama
      /ask-agentic-protocol <q> LLM JSON tool-call protocol mode
      /limitations             Show known/fixed/remaining limitations
      /scope wide|normal       Explain wider query scope modes
      /screen-width [n|off]    Set terminal wrapping width; 0/off disables
      /wrap on|off             Enable/disable terminal-only word wrapping
      /json on|off             Toggle raw JSON output inside shell mode
      /exit                    Leave shell

    Input history: ↑/↓ browse commands, Ctrl-R reverse-searches history.
    Long file/page operations show a one-line counter, e.g. `Ingest: 12/78 files`.
    Shell flags work, e.g. `/retrieve architecture --top-k 2`.
    """).strip())


def interactive_shell(vault: Path, json_output: bool = False) -> int:
    """Run the interactive slash-command shell."""
    engine = LLMWikiContextEngine(vault)
    session_ask_turns: List[Dict[str, Any]] = []
    # Enable persistent command history before the first prompt. Without this,
    # some terminals echo arrow-key escape sequences such as ^[[A/^[[B.
    setup_release_readline_history(vault)
    print(ART)
    print("Based on a design pattern by Andrej Karpathy")
    print("Created by Martin Timms and Vishva AI")
    print()
    pdf_status = release_pdf_extraction_status()
    print(pdf_status["message"])
    docx_status = release_docx_extraction_status()
    print(docx_status["message"])
    print(_screen_wrap_status())
    print("Type /help for commands, /ingest . to absorb folders, /ingest <file> to absorb one file, /ask <question> to ask explicitly, or type a question directly.")
    while True:
        try:
            line = input(colour("wiki> ", Colours.user)).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return 0
        if not line:
            continue
        try:
            cmd, args, raw_args, implicit_ask = _parse_interactive_line(line)
            if cmd in {"exit", "quit", "bye", "q"}:
                return 0
            if cmd == "help":
                print_help(); continue
            store = engine.store
            if cmd in {"screen-width", "wrap"}:
                value = args[0].lower() if args else ""
                if cmd == "wrap":
                    if value in {"off", "false", "0", "no", "disable", "disabled"}:
                        configure_screen_output(enabled=False)
                    elif value in {"on", "true", "1", "yes", "enable", "enabled"}:
                        configure_screen_output(width=SCREEN_WIDTH or DEFAULT_SCREEN_WIDTH, enabled=True)
                    else:
                        print(_screen_wrap_status())
                        print("Use: /wrap on | /wrap off")
                        continue
                else:
                    if not value:
                        print(_screen_wrap_status())
                        print("Use: /screen-width 120 | /screen-width off")
                        continue
                    if value in {"off", "none", "false", "disable", "disabled"}:
                        configure_screen_output(width=0, enabled=False)
                    else:
                        try:
                            new_width = int(value)
                        except ValueError:
                            print("Usage: /screen-width <characters> | /screen-width off")
                            continue
                        configure_screen_output(width=new_width, enabled=new_width > 0)
                print(_screen_wrap_status())
            elif cmd in {"json", "mode"}:
                if not args or args[0].lower() not in {"on", "off", "json", "text"}:
                    print(f"JSON output is currently {'on' if json_output else 'off'}. Use `/json on` or `/json off`.")
                else:
                    json_output = args[0].lower() in {"on", "json"}
                    print(f"JSON output {'enabled' if json_output else 'disabled'}.")
            elif cmd in {"search", "find"}:
                opts = _parse_shell_search_args(args)
                human_print(engine.search(opts["query"], limit=opts["limit"]), "search", json_output)
            elif cmd in {"search-following", "follow-search"}:
                opts = _parse_shell_search_following_args(args)
                if not opts["query"]:
                    print("Usage: /search-following <query> [--pages 2] [--limit 5] [--context-chars 4000]")
                    continue
                payload = release_search_following_pages(str(vault), opts["query"], limit=opts["limit"], following_pages=opts["following_pages"], context_chars=opts["context_chars"], max_chars=opts["max_chars"])
                human_print(payload, "search_following", json_output)
            elif cmd in {"why", "diagnose", "search-debug"}:
                opts = _parse_shell_search_args(args)
                human_print(engine.store.search_diagnostics(opts["query"], limit=opts["limit"]), "search_diagnostics", json_output)
            elif cmd == "retrieve":
                opts = _parse_shell_retrieve_args(args)
                data = engine.retrieve_articles(opts["query"], top_k=opts["top_k"], max_chars_per_article=opts["max_chars_per_article"], max_total_chars=opts["max_total_chars"])
                if opts["show"] and not json_output:
                    screen_print(data.get("context", ""))
                else:
                    human_print(data, "retrieve", json_output)
            elif cmd == "articles":
                opts = _parse_shell_retrieve_args(args)
                screen_print(engine.retrieve_articles(opts["query"], top_k=opts["top_k"], max_chars_per_article=opts["max_chars_per_article"], max_total_chars=opts["max_total_chars"]).get("context", ""))
            elif cmd == "ask":
                question_text = " ".join(args).strip()
                if not question_text:
                    print("Usage: /ask <question> — or type the question directly without a slash")
                    continue
                mode = release_current_ask_mode(str(vault))
                payload = release_ask(str(vault), question_text, mode=mode, max_tool_calls=14, dry_run=False)
                print(f"Ask mode: {mode}")
                print(f"User request: {question_text}")
                print("")
                if payload.get("tools_called"):
                    print(f"Tools called: {', '.join(payload.get('tools_called', []))}")
                    print("")
                if payload.get("answer"):
                    print("Answer:")
                    screen_print(payload["answer"])
                    _record_visible_cli_ask_turn(vault, question_text, payload, session_ask_turns)
                else:
                    print("No LLM answer was produced; Release should provide an evidence fallback above. If not, use `ask-agentic-dry <question>` to inspect evidence.")
            elif cmd == "context":
                screen_print(engine.context_for_llm(" ".join(args), max_chars=6000))
            elif cmd == "read":
                page = engine.read(" ".join(args))
                human_print(page if json_output else page["body"], as_json=json_output)
            elif cmd == "stats":
                human_print(engine.stats(), "stats", json_output)
            elif cmd == "lint":
                human_print(store.lint(), "lint", json_output)
            elif cmd == "repair":
                apply = "--apply" in args or "apply" in args
                create_missing = "--create-missing" in args or "missing" in args
                link_orphans = "--no-link-orphans" not in args
                expand_short = "--no-expand-short" not in args
                fix_broken = "--no-fix-broken" not in args
                human_print(store.repair_lint(apply=apply, create_missing=create_missing, link_orphans=link_orphans, expand_short=expand_short, fix_broken=fix_broken), "repair", json_output)
            elif cmd == "graph":
                g = store.graph_links(); human_print({"nodes": g["node_count"], "edges": g["edge_count"], "backlinks": len(g["backlinks"])}, "graph", json_output)
            elif cmd == "mermaid":
                out = args[0] if args else None
                human_print(store.mermaid_graph(output_path=out), "mermaid", json_output)
            elif cmd in {"map", "neighbourhood", "neighborhood"}:
                if not args:
                    print("Usage: /map <title> [output.md]"); continue
                title = args[0]
                out = args[1] if len(args) > 1 else None
                human_print(store.mermaid_neighbourhood(title, output_path=out), "mermaid", json_output)
            elif cmd == "pages":
                human_print(store.list_pages(limit=500), "pages", json_output)
            elif cmd == "ingest":
                target = args[0] if args else "."
                dry = "--dry-run" in args or "--plan" in args
                verbose = "--verbose" in args or "-v" in args
                progress = OneLineProgress("Ingest", "files")
                try:
                    result = release_ingest_directory_provenance(str(vault), target, recursive=True, apply=not dry, progress_callback=None if dry else progress.update)
                finally:
                    progress.done()
                print(_compact_ingest_output_text(result["summary"], verbose=verbose))
            elif cmd == "edit":
                title = " ".join(args)
                if not title:
                    print("Usage: /edit <title>"); continue
                resolved = store.resolve(title)
                path = Path(store.read_page(resolved["canonical_title"])["path"])
                editor = os.environ.get("EDITOR")
                if editor:
                    os.system(f"{editor} {shlex.quote(str(path))}")
                    store.reindex()
                    print(f"Edited and reindexed: {resolved['canonical_title']}")
                else:
                    print(f"Set EDITOR or open manually: {path}")
            elif cmd == "export":
                human_print(store.export_llms_txt(args[0] if args else None), "export", json_output)
            elif cmd == "config":
                if not args or args[0] in {"show", "get"}:
                    human_print(engine.config(), "config", json_output)
                elif args[0] in {"host", "model"} and len(args) >= 2:
                    data = store.config_set(args[0], " ".join(args[1:]))
                    print(f"Saved {args[0]} = {' '.join(args[1:])}")
                    human_print(data, "config", json_output)
                elif args[0] == "set" and len(args) >= 3:
                    data = store.config_set(args[1], " ".join(args[2:]))
                    print(f"Saved {args[1]} = {' '.join(args[2:])}")
                    human_print(data, "config", json_output)
                elif args[0] == "reset":
                    human_print(store.config_reset(), "config", json_output)
                elif args[0] == "test":
                    human_print(store.config_test(), "ask", json_output)
                elif args[0] == "edit":
                    cfg = engine.config()
                    path = Path(cfg["config_path"])
                    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
                    if editor:
                        os.system(f"{editor} {shlex.quote(str(path))}")
                        print(f"Reloaded config from: {path}")
                        human_print(engine.config(), "config", json_output)
                    else:
                        print(f"Set EDITOR or VISUAL, or edit manually: {path}")
                else:
                    print("Usage: config [show|host <url>|model <name>|set <key> <value>|test|edit|reset]")
            elif cmd == "self":
                question = " ".join(args).strip() or "What can this tool tell me about itself?"
                payload = tool_self_question_context(str(vault), question)
                screen_print(payload["context"])
            elif cmd == "usage":
                snap = wiki_usage_snapshot(str(vault))
                print("Wiki usage snapshot")
                print(f"Vault: {snap['vault']}")
                print(f"Pages: {snap['pages']} | Words: {snap['words']} | Approx tokens: {snap['tokens_estimate']}")
                print("")
                print("Largest pages:")
                for row in snap["page_rows"][:10]:
                    print(f"  - {row['file']}: ~{row['tokens_estimate']} tokens, {row['words']} words")
            elif cmd == "scope":
                mode = args[0] if args else "wide"
                print("Query scope mode")
                print(f"Requested: {mode}")
                print("normal = literal + basic plural/singular/title matching")
                print("wide   = query expansion + filenames + headings + related/backlink pages")
                print("Release documents wide scope and prepares the CLI/MCP roadmap for agentic ask.")
            elif cmd == "askrec":
                question = " ".join(args).strip()
                if not question:
                    print("Usage: askrec <question>")
                    continue
                payload = release_recursive_ask_preview(str(vault), question, recursive=True)
                print("Recursive ask is enabled for this request.")
                print(f"Approx prompt tokens: {payload['total_tokens_estimate']} | history tokens: {payload['history_tokens_estimate']}")
                print("")
                screen_print(payload["context"][:6000])
                print("")
                print("This preview shows recursive context assembly. Use `recursive on` to enable by default.")
                release_append_history(str(vault), {"question": question, "answer": "[recursive preview only]", "sources": ["ask_history.jsonl"]})
            elif cmd == "recursive":
                value = args[0].lower() if args else ""
                if value in {"on", "true", "yes", "1"}:
                    release_set_config_value(str(vault), "ask.recursive_enabled", True)
                    print("Recursive ask: enabled")
                elif value in {"off", "false", "no", "0"}:
                    release_set_config_value(str(vault), "ask.recursive_enabled", False)
                    print("Recursive ask: disabled")
                else:
                    cfg = release_load_config(str(vault))
                    print(f"Recursive ask: {cfg.get('ask', {}).get('recursive_enabled', False)}")
                    print("Use: recursive on | recursive off")
            elif cmd == "compress":
                value = args[0].lower() if args else ""
                if value in {"on", "true", "yes", "1"}:
                    release_set_config_value(str(vault), "ask.compress_history", True)
                    print("History compression: enabled")
                elif value in {"off", "false", "no", "0"}:
                    release_set_config_value(str(vault), "ask.compress_history", False)
                    print("History compression: disabled")
                else:
                    cfg = release_load_config(str(vault))
                    print(f"History compression: {cfg.get('ask', {}).get('compress_history', True)}")
                    print("Use: compress on | compress off")
            elif cmd == "history-status":
                cfg = release_load_config(str(vault))
                result = release_compress_history_if_needed(str(vault))
                compressed = release_read_compressed_history(str(vault))
                ask_cfg = cfg.get("ask", {})
                print("Recursive memory status")
                print(f"Recursive enabled: {ask_cfg.get('recursive_enabled', True)}")
                print(f"Compression enabled: {ask_cfg.get('compress_history', True)}")
                print(f"Max history tokens: {ask_cfg.get('max_history_tokens', 4000)}")
                print(f"Keep recent turns: {ask_cfg.get('keep_recent_turns', 8)}")
                print(f"Compressed memory present: {bool(compressed)}")
                print(f"Compression check: {result}")
            elif cmd == "context-settings":
                settings = release_context_settings(str(vault))
                aliases = {
                    "context-budget": "ask.context_budget_tokens",
                    "history-budget": "ask.history_budget_tokens",
                    "source-budget": "ask.source_budget_tokens",
                    "max-sources": "ask.max_sources",
                    "full-page-threshold": "ask.full_page_threshold",
                    "debug-chars": "ask.debug_context_chars",
                }
                if not args:
                    print("Ask context settings")
                    for k, v in settings.items():
                        print(f"  {k}: {v}")
                    print("\nSet with: /context-settings context-budget 24000")
                    print("Aliases: context-budget, history-budget, source-budget, max-sources, full-page-threshold, debug-chars")
                elif len(args) >= 2 and args[0] in aliases:
                    try:
                        value = int(args[1])
                    except ValueError:
                        print("Value must be an integer.")
                        continue
                    release_set_config_value(str(vault), aliases[args[0]], value)
                    print(f"Saved {aliases[args[0]]} = {value}")
                elif len(args) >= 2:
                    try:
                        value = int(args[1])
                    except ValueError:
                        print("Value must be an integer.")
                        continue
                    key = args[0] if args[0].startswith("ask.") else "ask." + args[0]
                    release_set_config_value(str(vault), key, value)
                    print(f"Saved {key} = {value}")
                else:
                    print("Usage: /context-settings [context-budget|history-budget|source-budget|max-sources|full-page-threshold|debug-chars] <integer>")
            elif cmd == "debug-context":
                question = " ".join(args).strip()
                if not question:
                    print("Usage: /debug-context <question>")
                    continue
                payload = release_debug_context(str(vault), question)
                pack = payload.get("context_pack", {})
                settings = pack.get("settings", {})
                print("Ask context debug")
                print(f"Question: {question}")
                print(f"Prompt chars: {pack.get('prompt_chars')} | Prompt tokens est: {pack.get('prompt_tokens_estimate')} | History tokens est: {pack.get('history_tokens_estimate')}")
                if settings:
                    print("Settings: " + ", ".join(f"{k}={v}" for k, v in settings.items()))
                if pack.get("source_titles"):
                    print("Sources: " + ", ".join(pack.get("source_titles", [])[:12]))
                print("Tools: " + ", ".join(payload.get("tools_called", [])))
                print("\n--- Context preview ---")
                cfg = release_context_settings(str(vault))
                preview = pack.get("prompt", "")[: int(cfg.get("debug_context_chars", 12000))]
                screen_print(preview)
                if len(pack.get("prompt", "")) > len(preview):
                    print("\n[debug context preview truncated; increase ask.debug_context_chars to show more]")
            elif cmd == "history":
                rows = _merge_history_rows(release_load_history(str(vault), 10), session_ask_turns, limit=10)
                print("Recent ask history")
                if not rows:
                    print("  No ask history yet.")
                for i, row in enumerate(rows, 1):
                    q = str(row.get("question", ""))[:140]
                    a = " ".join(str(row.get("answer", "")).split())[:260]
                    prompt_tokens = row.get("prompt_tokens_estimate")
                    answer_tokens = row.get("answer_tokens_estimate")
                    print(f"  {i}. User: {q}")
                    if a:
                        print(f"     Assistant: {a}{' ...' if len(a) >= 260 else ''}")
                    if prompt_tokens is not None or answer_tokens is not None:
                        print(f"     Tokens est: prompt={prompt_tokens} answer={answer_tokens}")
            elif cmd == "recursive-preview":
                question = " ".join(args).strip() or "What is this project?"
                payload = release_recursive_ask_preview(str(vault), question, recursive=None)
                print("Recursive ask preview")
                print(f"Enabled: {payload['recursive_enabled']} | Compress: {payload['compress_history']} | Approx tokens: {payload['total_tokens_estimate']}")
                screen_print(payload["context"][:4000])
            elif cmd == "tokens":
                summary = release_metrics_summary(str(vault), 100)
                print("Token/s and ask metrics")
                print(f"Recorded asks: {summary.get('count', 0)}")
                print(f"Total prompt tokens estimate: {summary.get('total_prompt_tokens_estimate', 0)}")
                print(f"Total answer tokens estimate: {summary.get('total_answer_tokens_estimate', 0)}")
                avg_out = summary.get("avg_output_tokens_per_second")
                avg_total = summary.get("avg_total_tokens_per_second")
                print(f"Average output tokens/s: {avg_out:.2f}" if avg_out is not None else "Average output tokens/s: n/a")
                print(f"Average total tokens/s: {avg_total:.2f}" if avg_total is not None else "Average total tokens/s: n/a")
                if summary.get("recent"):
                    print("")
                    print("Recent:")
                    for row in summary["recent"][-5:]:
                        print(f"  - {row.get('question','')[:80]} | out tok/s={row.get('output_tokens_per_second')}")
            elif cmd == "self-stats":
                snap = release_self_access_snapshot(str(vault))
                print("Self-access snapshot")
                print(f"Recursive enabled: {snap.get('config', {}).get('ask', {}).get('recursive_enabled')}")
                print(f"Pages: {snap.get('usage', {}).get('pages')} | Wiki tokens: {snap.get('usage', {}).get('tokens_estimate')}")
                print(f"Ask turns: {snap.get('usage', {}).get('ask_history_turns')} | Ask history tokens: {snap.get('usage', {}).get('ask_history_tokens_estimate')}")
                print(f"Metric records: {snap.get('metrics', {}).get('count')}")
                avg = snap.get('metrics', {}).get('avg_output_tokens_per_second')
                print(f"Average output tokens/s: {avg:.2f}" if avg is not None else "Average output tokens/s: n/a")
            elif cmd == "self-usage":
                usage = release_wiki_usage_snapshot(str(vault))
                print("Self usage snapshot")
                print(f"Vault: {usage['vault']}")
                print(f"Pages: {usage['pages']} | Words: {usage['words']} | Wiki tokens: {usage['tokens_estimate']}")
                print(f"Ask turns: {usage['ask_history_turns']} | Ask history tokens: {usage['ask_history_tokens_estimate']} | Compressed tokens: {usage['compressed_history_tokens_estimate']}")
                print("Largest pages:")
                for row in usage["largest_pages"][:10]:
                    print(f"  - {row['file']}: ~{row['tokens_estimate']} tokens, {row['words']} words")
            elif cmd == "capabilities":
                caps = release_runtime_capabilities(str(vault))
                print("Capabilities")
                print("------------")
                print(f"LLM: Ollama host={caps['llm']['host']} model={caps['llm']['model']} recursive={caps['llm']['recursive_ask']}")
                print(f"Retrieval: sqlite_fts={caps['retrieval']['sqlite_fts']} markdown_source={caps['retrieval']['markdown_source_of_truth']}")
                print(f"Runtime: self_introspection={caps['runtime']['self_introspection']} journaling={caps['runtime']['runtime_journaling']} token_metrics={caps['runtime']['token_metrics']}")
                print(f"Maintenance: lint={caps['maintenance']['lint']} repair={caps['maintenance']['repair']} reconcile_docs={caps['maintenance']['reconcile_docs']}")
            elif cmd == "runtime-journal":
                rows = release_load_runtime_journal(str(vault), 10)
                print("Runtime journal")
                if not rows:
                    print("  No runtime events recorded yet.")
                for row in rows:
                    print(f"  - {row.get('command')} success={row.get('success')} latency={row.get('latency_seconds')} query={str(row.get('query',''))[:80]}")
            elif cmd == "command-map":
                print("Command to tool mapping")
                for command, tools in release_command_tool_map().items():
                    print(f"  {command}: {', '.join(tools)}")
            elif cmd == "runtime-graph":
                print(release_runtime_graph_mermaid())
            elif cmd == "reconcile":
                report = release_reconcile_docs(str(vault))
                print("Documentation reconciliation")
                print(f"OK: {report['ok']}")
                print(f"Docs dir: {report['docs_dir']}")
                if report["missing_docs"]:
                    print("Missing docs:")
                    for item in report["missing_docs"]:
                        print(f"  - {item}")
                if report["undocumented_commands_in_function_list"]:
                    print("Commands not mentioned in FUNCTION_LIST.md:")
                    for item in report["undocumented_commands_in_function_list"]:
                        print(f"  - {item}")
            elif cmd == "notes":
                title = " ".join(args).strip()
                if not title:
                    print("Usage: /notes <page title>")
                else:
                    payload = release_build_page_note(str(vault), title, mode="show")
                    if not payload.get("ok"):
                        print(payload.get("error"))
                    else:
                        print(f"AI notes written: {payload['note_path']}")
                        print(f"Candidate links: {len(payload.get('candidate_links', []))}")
            elif cmd == "notes-iterate":
                title = " ".join(args).strip()
                if not title:
                    print("Usage: /notes-iterate <page title>")
                else:
                    payload = release_build_page_note(str(vault), title, mode="iterate")
                    if not payload.get("ok"):
                        print(payload.get("error"))
                    else:
                        print(f"Iterated AI notes for: {payload['title']}")
                        print(f"Note: {payload['note_path']}")
                        print("Candidate links:")
                        for row in payload.get("candidate_links", [])[:12]:
                            print(f"  - [[{row['title']}]] score={row['score']} matched={', '.join(row['matched_terms'][:6])}")
            elif cmd == "notes-all":
                limit = int(args[0]) if args and args[0].isdigit() else None
                progress = OneLineProgress("Notes", "pages")
                try:
                    payload = release_iterate_all_notes(str(vault), limit, progress_callback=progress.update)
                finally:
                    progress.done()
                print(f"Iterated notes for {payload['count']} pages.")
            elif cmd == "notes-search":
                query = " ".join(args).strip()
                if not query:
                    print("Usage: notes-search <query>")
                else:
                    payload = release_search_with_notes(str(vault), query)
                    print(f"Search with notes for: {query} ({payload['count']} found)")
                    for i, row in enumerate(payload["results"], 1):
                        print(f"{i}. {row['title']} score={row['score']} note={row['has_note']}")
                        print(f"   matched: {', '.join(row['matched_terms'])}")
            elif cmd == "notes-links":
                title = " ".join(args).strip()
                if not title:
                    print("Usage: /notes-links <page title>")
                else:
                    rows = release_find_candidate_links(str(vault), title)
                    print(f"Candidate links for {title}:")
                    for row in rows:
                        print(f"  - [[{row['title']}]] score={row['score']} matched={', '.join(row['matched_terms'][:8])}")
            elif cmd == "notes-status":
                status = release_notes_status(str(vault))
                print("AI notes status")
                print(f"Pages: {status['pages']} | Notes: {status['notes']} | Coverage: {status['coverage_percent']}%")
                print(f"Notes dir: {status['notes_dir']}")
                if status["missing_notes"]:
                    print("Missing notes for:")
                    for item in status["missing_notes"][:20]: print(f"  - {item}")
                    if len(status["missing_notes"]) > 20: print(f"  ... {len(status['missing_notes']) - 20} more")
            elif cmd == "notes-graph":
                print(release_notes_graph_mermaid(str(vault)))
            elif cmd == "ask-mode":
                if not args:
                    print(f"Ask mode: {release_current_ask_mode(str(vault))}")
                    print("Use: /ask-mode agentic | /ask-mode plain")
                else:
                    release_set_ask_mode(str(vault), args[0])
                    print(f"Ask mode set to: {release_current_ask_mode(str(vault))}")
            elif cmd == "ask-plain":
                question = " ".join(args).strip()
                if not question:
                    print("Usage: /ask-plain <question>")
                else:
                    payload = release_plain_ask(str(vault), question, dry_run=False)
                    print("Ask mode: plain")
                    print("")
                    screen_print(payload.get("answer") or "No answer produced. Check Ollama/config.")
                    if payload.get("answer"):
                        _record_visible_cli_ask_turn(vault, question, payload, session_ask_turns)
            elif cmd == "intent-dry":
                question_text = " ".join(args).strip()
                payload = release_agentic_ask(str(vault), question_text, max_tool_calls=12, dry_run=True)
                print("Resolved intent:")
                print(json.dumps(payload.get("resolved_intent"), indent=2))
                print("Tools planned:")
                for t in payload.get("tools_called", []):
                    print(f"  - {t}")
            elif cmd == "planner-tools":
                print("Release planner tool groups")
                for group, names in release_tool_groups().items():
                    print(f"{group}:")
                    for name in names:
                        print(f"  - {name}")
            elif cmd == "tool-count":
                summary = release_tool_catalog_summary()
                print(f"Full MCP catalogue tools: {summary['tool_count']}")
                print(f"Read-only tools visible to agent: {summary['read_only_count']}")
            elif cmd == "tool-catalog":
                print(release_tool_catalog_markdown())
            elif cmd == "ask-agentic":
                question = " ".join(args).strip()
                if not question:
                    print("Usage: /ask-agentic <question>")
                else:
                    payload = release_agentic_ask(str(vault), question, max_tool_calls=5, dry_run=False, synthesize=True, protocol_mode=False)
                    print("Agentic ask")
                    print(f"Question: {payload.get('question')}")
                    if payload.get("repaired_question") != payload.get("question"):
                        print(f"Repaired query: {payload.get('repaired_question')}")
                    print(f"Tools called: {', '.join(payload.get('tools_called', []))}")
                    print("")
                    if payload.get("answer"):
                        print("Answer:")
                        screen_print(payload["answer"])
                        _record_visible_cli_ask_turn(vault, question, payload, session_ask_turns)
                    else:
                        print("No answer produced. Use ask-agentic-dry to inspect evidence.")
            elif cmd == "ask-agentic-dry":
                question = " ".join(args).strip()
                if not question:
                    print("Usage: /ask-agentic-dry <question>")
                else:
                    payload = release_agentic_ask(str(vault), question, max_tool_calls=5, dry_run=True, synthesize=False)
                    print("Agentic evidence pack")
                    print(f"Question: {payload['question']}")
                    if payload.get("repaired_question") != payload.get("question"):
                        print(f"Repaired query: {payload.get('repaired_question')}")
                    print(f"Tools called: {', '.join(payload['tools_called'])}")
                    print("Trace:")
                    for row in payload["trace"]:
                        print(f"  - {row['tool']} -> {row.get('result_type')}")
                    print("")
                    print("Prompt preview:")
                    screen_print(payload["llm_prompt"][:5000])
            elif cmd == "ask-agentic-protocol":
                question = " ".join(args).strip()
                if not question:
                    print("Usage: /ask-agentic-protocol <question>")
                else:
                    payload = release_agentic_ask(str(vault), question, max_tool_calls=5, dry_run=False, synthesize=True, protocol_mode=True)
                    print("Agentic protocol ask")
                    print(f"Tools called: {', '.join(payload.get('tools_called', []))}")
                    print("")
                    screen_print(payload.get("answer") or "No final answer produced.")
                    if payload.get("answer"):
                        _record_visible_cli_ask_turn(vault, question, payload, session_ask_turns)
            elif cmd == "limitations":
                report = release_limitations_report(str(vault))
                print("Limitations report")
                print("Fixed or reduced:")
                for item in report["known_limitations_fixed_or_reduced"]:
                    print(f"  - {item}")
                print("Remaining:")
                for item in report["remaining_limitations"]:
                    print(f"  - {item}")
                print("Next steps:")
                for item in report["recommended_next_steps"]:
                    print(f"  - {item}")
            elif cmd == "provenance":
                s=release_provenance_summary(str(vault))
                print(f"Provenance DB: {s['db']}")
                print(f"Directories: {s['directories']} | Source files: {s['source_files']} | Versions: {s['file_versions']}")
                for row in s["recent"][:10]:
                    print(f"- {row.get('filename')} | {row.get('directory')} | {str(row.get('current_sha256'))[:12]} | {row.get('mtime_iso')} | {row.get('wiki_title')}")
            elif cmd == "startup":
                if not args:
                    print(release_startup_commands_markdown(str(vault)))
                elif args[0]=="default":
                    release_set_startup_commands(str(vault), release_default_startup_commands())
                    print(release_startup_commands_markdown(str(vault)))
                elif args[0]=="set":
                    release_set_startup_commands(str(vault), " ".join(args[1:]))
                    print(release_startup_commands_markdown(str(vault)))
                else:
                    print("Usage: /startup | /startup default | /startup set /ingest ./docs; /notes-all")
            elif cmd == "docs-consolidate":
                result = release_consolidate_docs(Path.cwd(), archive=True)
                print(f"Docs consolidated. Category files written: {len(result['written'])}; archived: {result['archived']}")
            elif cmd == "history-build":
                r=release_build_development_history(Path.cwd())
                print(f"Development history written: {r['path']}")
            elif cmd == "reindex":
                progress = OneLineProgress("Reindex", "pages")
                try:
                    result = release_reindex_with_progress(str(vault), progress_callback=progress.update)
                finally:
                    progress.done()
                human_print(result, "reindex", json_output)
            else:
                suggestion = difflib.get_close_matches(cmd, COMMANDS, n=1)
                if suggestion:
                    print(f"Unknown command: /{cmd}. Did you mean `/{suggestion[0]}`?")
                else:
                    print(f"Unknown command: /{cmd}. Type `/help` for commands, or omit the slash to ask a question.")
        except Exception as exc:
            print(f"Error: {exc}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Implement the main operation for the local LLM Wiki workflow."""
    parser = argparse.ArgumentParser(description="LLM Wiki user CLI")
    parser.add_argument("--vault", default=os.environ.get("LLM_WIKI_VAULT", "./wiki_vault"), help="Named wiki vault path")
    parser.add_argument("--json", action="store_true", help="Print raw JSON where applicable")
    parser.add_argument("--color", choices=["auto", "on", "off"], default="auto", help="Colour output mode")
    parser.add_argument("--screen-width", type=int, default=None, help="Terminal output wrap width in characters; default 120, 0 disables")
    parser.add_argument("--no-screen-wrap", action="store_true", help="Disable terminal-only word wrapping")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialise a wiki vault")
    p_ing = sub.add_parser("ingest-dir", help="Ingest a named directory or a single file into the wiki")
    p_ing.add_argument("directory", help="Directory or single supported file to ingest")
    p_ing.add_argument("--pattern", action="append", dest="patterns", help="Glob pattern; may repeat")
    p_ing.add_argument("--no-recursive", action="store_true")
    p_ing.add_argument("--limit", type=int, default=1000)

    p_search = sub.add_parser("search", help="Search the wiki")
    p_search.add_argument("query", nargs="+")
    p_search.add_argument("--limit", type=int, default=10)
    p_follow = sub.add_parser("search-following", help="Search and return the matched page plus N following pages/excerpt")
    p_follow.add_argument("query", nargs="+")
    p_follow.add_argument("--limit", type=int, default=5)
    p_follow.add_argument("--pages", "--following-pages", dest="following_pages", type=int, default=2)
    p_follow.add_argument("--context-chars", type=int, default=4000)
    p_follow.add_argument("--max-chars", type=int, default=16000)
    p_diag = sub.add_parser("why", help="Explain search normalisation and suggestions")
    p_diag.add_argument("query", nargs="+")
    p_diag.add_argument("--limit", type=int, default=8)
    p_ret = sub.add_parser("retrieve", help="Prompt -> search -> retrieve top-k wiki articles")
    p_ret.add_argument("query", nargs="+")
    p_ret.add_argument("--top-k", type=int, default=5)
    p_ret.add_argument("--max-chars-per-article", type=int, default=4000)
    p_ret.add_argument("--max-total-chars", type=int, default=12000)
    p_ret.add_argument("--show", action="store_true", help="Print the LLM-ready context text instead of the summary table")
    p_ask = sub.add_parser("ask", help="Retrieve wiki context and ask local Ollama")
    p_ask.add_argument("question", nargs="+")
    p_ask.add_argument("--top-k", type=int)
    p_ask.add_argument("--model")
    p_ask.add_argument("--host")
    p_ask.add_argument("--temperature", type=float)
    p_ask.add_argument("--timeout-seconds", type=int)
    p_ask.add_argument("--max-context-chars", type=int)
    p_ask.add_argument("--dry-run", action="store_true", help="Build prompt and show metadata without calling Ollama")
    p_cfg = sub.add_parser("config", help="Show/edit/update/test llm_wiki_config.json")
    p_cfg.add_argument("config_args", nargs="*", help="show | host <url> | model <name> | set <key> <value> | test | edit | reset")
    p_context = sub.add_parser("context", help="Build LLM-ready context")
    p_context.add_argument("query", nargs="+")
    p_context.add_argument("--max-chars", type=int, default=8000)
    p_context.add_argument("--limit", type=int, default=6)
    p_read = sub.add_parser("read", help="Read a page")
    p_read.add_argument("title", nargs="+")
    p_edit = sub.add_parser("edit", help="Open a page in $EDITOR")
    p_edit.add_argument("title", nargs="+")
    sub.add_parser("stats", help="Show stats and health")
    sub.add_parser("lint", help="Run lint checks")
    p_rep = sub.add_parser("repair", help="Plan/apply safe wiki lint repairs")
    p_rep.add_argument("--apply", action="store_true", help="Apply proposed safe repairs. Default is dry-run.")
    p_rep.add_argument("--create-missing", action="store_true", help="Create stub pages for unresolved missing link targets.")
    p_rep.add_argument("--no-fix-broken", action="store_true", help="Do not rewrite broken links to resolved canonical pages.")
    p_rep.add_argument("--no-link-orphans", action="store_true", help="Do not link orphan pages from the index.")
    p_rep.add_argument("--no-expand-short", action="store_true", help="Do not add retrieval scaffolds to very short pages.")
    p_rep.add_argument("--index-page", default="index", help="Page used to link orphan pages")
    sub.add_parser("reindex", help="Rebuild SQLite index")
    sub.add_parser("pages", help="List pages")
    p_mer = sub.add_parser("mermaid", help="Render the wiki graph as Mermaid")
    p_mer.add_argument("--output", "-o", help="Write Mermaid Markdown to this file")
    p_mer.add_argument("--direction", default="TD", help="Mermaid direction: TD, LR, RL, BT")
    p_mer.add_argument("--max-edges", type=int, default=200)
    p_mer.add_argument("--no-orphans", action="store_true")
    p_map = sub.add_parser("map", help="Render a page-centred Mermaid neighbourhood")
    p_map.add_argument("title", nargs="+")
    p_map.add_argument("--output", "-o", help="Write Mermaid Markdown to this file")
    p_map.add_argument("--depth", type=int, default=1)
    p_map.add_argument("--direction", default="LR")
    sub.add_parser("shell", help="Interactive sub-CLI mode")
    sub.add_parser("export", help="Export llms.txt")

    args = parser.parse_args(argv)
    global COLOUR_ENABLED
    if args.color == "on":
        COLOUR_ENABLED = True
    elif args.color == "off" or args.json:
        COLOUR_ENABLED = False
    requested_width = args.screen_width if args.screen_width is not None else _env_screen_width()
    configure_screen_output(width=requested_width, enabled=(not args.no_screen_wrap and not args.json and requested_width > 0))
    vault = Path(args.vault).expanduser().resolve()
    cmd = args.command or "shell"

    if cmd == "init":
        set_vault(vault)
        store = WikiStore(WikiConfig(vault))
        human_print(store.init_seed(), "init", args.json); return 0

    engine = LLMWikiContextEngine(vault)
    store = engine.store
    if cmd == "ingest-dir":
        patterns = args.patterns or SUPPORTED_PATTERNS
        progress = OneLineProgress("Ingest", "files")
        try:
            ingest_path(vault, Path(args.directory).expanduser().resolve(), patterns, not args.no_recursive, args.limit, json_output=args.json, progress_callback=progress.update)
        finally:
            progress.done()
        return 0
    if cmd == "search":
        human_print(engine.search(" ".join(args.query), limit=args.limit), "search", args.json); return 0
    if cmd == "search-following":
        payload = release_search_following_pages(str(vault), " ".join(args.query), limit=args.limit, following_pages=args.following_pages, context_chars=args.context_chars, max_chars=args.max_chars)
        human_print(payload, "search_following", args.json); return 0
    if cmd == "why":
        human_print(store.search_diagnostics(" ".join(args.query), limit=args.limit), "search_diagnostics", args.json); return 0
    if cmd == "retrieve":
        data = engine.retrieve_articles(" ".join(args.query), top_k=args.top_k, max_chars_per_article=args.max_chars_per_article, max_total_chars=args.max_total_chars)
        if args.show and not args.json:
            screen_print(data.get("context", ""))
        else:
            human_print(data, "retrieve", args.json)
        return 0
    if cmd == "ask":
        data = engine.ask_ollama(" ".join(args.question), top_k=args.top_k, model=args.model, host=args.host, temperature=args.temperature, timeout_seconds=args.timeout_seconds, max_context_chars=args.max_context_chars, dry_run=args.dry_run)
        human_print(data, "ask", args.json); return 0
    if cmd == "config":
        cargs = args.config_args or ["show"]
        action = cargs[0]
        if action in {"show", "get"}:
            human_print(engine.config(), "config", args.json); return 0
        if action in {"host", "model"} and len(cargs) >= 2:
            data = store.config_set(action, " ".join(cargs[1:]))
            human_print(data, "config", args.json); return 0
        if action == "set" and len(cargs) >= 3:
            data = store.config_set(cargs[1], " ".join(cargs[2:]))
            human_print(data, "config", args.json); return 0
        if action == "reset":
            human_print(store.config_reset(), "config", args.json); return 0
        if action == "test":
            human_print(store.config_test(), "ask", args.json); return 0
        if action == "edit":
            cfg = engine.config(); path = Path(cfg["config_path"])
            editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
            if editor:
                os.system(f"{editor} {shlex.quote(str(path))}")
                human_print(engine.config(), "config", args.json)
            else:
                print(path)
            return 0
        print("Usage: config [show|host <url>|model <name>|set <key> <value>|test|edit|reset]")
        return 2
    if cmd == "context":
        screen_print(engine.context_for_llm(" ".join(args.query), limit=args.limit, max_chars=args.max_chars)); return 0
    if cmd == "read":
        page = engine.read(" ".join(args.title)); human_print(page if args.json else page["body"], as_json=args.json); return 0
    if cmd == "edit":
        resolved = store.resolve(" ".join(args.title)); path = Path(store.read_page(resolved["canonical_title"])["path"])
        editor = os.environ.get("EDITOR")
        if editor:
            os.system(f"{editor} {shlex.quote(str(path))}"); store.reindex(); print(f"Edited and reindexed: {resolved['canonical_title']}")
        else:
            print(path)
        return 0
    if cmd == "stats":
        human_print(engine.stats(), "stats", args.json); return 0
    if cmd == "lint":
        human_print(store.lint(), "lint", args.json); return 0
    if cmd == "repair":
        human_print(store.repair_lint(apply=args.apply, fix_broken=not args.no_fix_broken, link_orphans=not args.no_link_orphans, expand_short=not args.no_expand_short, create_missing=args.create_missing, index_page=args.index_page), "repair", args.json); return 0
    if cmd == "reindex":
        progress = OneLineProgress("Reindex", "pages")
        try:
            result = release_reindex_with_progress(str(vault), progress_callback=progress.update)
        finally:
            progress.done()
        human_print(result, "reindex", args.json); return 0
    if cmd == "pages":
        human_print(store.list_pages(limit=1000), "pages", args.json); return 0
    if cmd == "export":
        human_print(store.export_llms_txt(), "export", args.json); return 0
    if cmd == "mermaid":
        human_print(store.mermaid_graph(direction=args.direction, include_orphans=not args.no_orphans, max_edges=args.max_edges, output_path=args.output), "mermaid", args.json); return 0
    if cmd == "map":
        human_print(store.mermaid_neighbourhood(" ".join(args.title), depth=args.depth, direction=args.direction, output_path=args.output), "mermaid", args.json); return 0
    if cmd == "shell":
        return interactive_shell(vault, json_output=args.json)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

# ---------------------------------------------------------------------------
# Versionless launcher compatibility
# ---------------------------------------------------------------------------
# Some releases used subcommands by default, while the user workflow expects
# `python3 llm_wiki_cli.py` to open the interactive shell. Keep both behaviours:
# - no args -> shell
# - args supplied -> normal argparse main
try:
    _original_main = main
    def _versionless_main_wrapper():
        """Internal helper for versionless main wrapper."""
        import sys as _sys
        if len(_sys.argv) == 1:
            _sys.argv.append("shell")
        return _original_main()
    main = _versionless_main_wrapper
except Exception:
    pass
