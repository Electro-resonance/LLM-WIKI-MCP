#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 21st May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# =============================================================================
"""Regression test: interactive/provenance ingest extracts searchable PDF text."""
from pathlib import Path
import tempfile

from llm_wiki_mcp.context_api import (
    release_ingest_directory_provenance,
    release_record_ingest_result,
    release_wiki_title_for_source_file,
)
from llm_wiki_mcp.server import WikiConfig, WikiStore, set_vault


def make_pdf(path: Path, text: str) -> None:
    """Document the `make_pdf` function used by the LLM Wiki MCP release."""
    try:
        from reportlab.pdfgen import canvas  # type: ignore
    except Exception as exc:  # pragma: no cover - local optional dependency guard
        raise RuntimeError(f"reportlab is required for this regression test: {exc}")
    c = canvas.Canvas(str(path))
    c.drawString(72, 720, text)
    c.save()


def test_pdf_ingest_provenance_extracts_text_and_reindexes() -> None:
    """Document the `test_pdf_ingest_provenance_extracts_text_and_reindexes` function used by the LLM Wiki MCP release."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = root / "wiki_vault"
        docs = root / "docs"
        docs.mkdir()
        pdf = docs / "architecture-note.pdf"
        needle = "Quantum Banana Architecture searchable PDF token"
        make_pdf(pdf, needle)

        result = release_ingest_directory_provenance(str(vault), str(docs), recursive=True, apply=True)
        assert result["counts"]["processed"] == 1

        set_vault(vault)
        store = WikiStore(WikiConfig(vault))
        pages = store.list_pages(limit=20)["pages"]
        title = next(p["title"] for p in pages if "architecture-note" in p["title"])
        page = store.read_page(title)
        assert "Quantum Banana Architecture" in page["body"]

        hits = store.search("Quantum Banana Architecture", limit=5)["results"]
        assert hits, "PDF text should be visible to basic search after ingest"


def test_pdf_placeholder_is_refreshed_when_pypdf_is_available() -> None:
    """An unchanged PDF with an old no-pypdf placeholder should be reprocessed."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = root / "wiki_vault"
        docs = root / "docs"
        wiki = vault / "wiki"
        docs.mkdir()
        wiki.mkdir(parents=True)

        pdf = docs / "transcript-my-first-ai-module.pdf"
        needle = "My First AI Module transcript refreshed from PDF text"
        make_pdf(pdf, needle)

        title = release_wiki_title_for_source_file(pdf, docs)
        page_path = wiki / (title + ".md")
        page_path.write_text(
            f"# {title}\n\n[PDF text extraction unavailable or failed for {pdf.name}: No module named 'pypdf'.]\n",
            encoding="utf-8",
        )
        release_record_ingest_result(str(vault), pdf, wiki_title=title, wiki_path=str(page_path), action="updated_or_new")

        result = release_ingest_directory_provenance(str(vault), str(docs), recursive=True, apply=True)
        assert result["counts"]["processed"] == 1
        assert result["updated"][0]["reason"].startswith("PDF extraction is now available")

        body = page_path.read_text(encoding="utf-8")
        assert needle in body
        assert "No module named 'pypdf'" not in body


if __name__ == "__main__":
    test_pdf_ingest_provenance_extracts_text_and_reindexes()
    test_pdf_placeholder_is_refreshed_when_pypdf_is_available()
    print("pdf_ingest_cli_test: ok")
