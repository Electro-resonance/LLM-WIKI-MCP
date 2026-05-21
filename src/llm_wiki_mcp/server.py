#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Created By  : Martin Timms
# Created Date: 18th May 2026
# License: MIT License
# Project: https://github.com/Electro-resonance/LLM-WIKI-MCP
# Description: Local-first Markdown wiki, CLI, and MCP server for LLM context
# retrieval, reflective notes, provenance-aware ingestion, and agentic context.
# =============================================================================
"""
LLM Wiki MCP release
===============

A compact, single-file, stdio MCP server for maintaining a local Markdown wiki
as a durable knowledge substrate for LLMs and agents.

This implementation is deliberately patterned after the attached EML MCP server:
- one primary Python module;
- explicit TOOL_HANDLERS and TOOL_DEFS tables;
- lazy official MCP SDK import;
- namespace prefix support through MCP_EXPOSED_NAMESPACE;
- direct examples and regression tests that run without the MCP package;
- server/test modes using the official MCP SDK when installed.

Usage
-----
Run direct examples without MCP SDK:
    python llm_wiki_mcp_server.py examples --vault ./wiki_vault

Run local regression examples:
    python llm_wiki_mcp_server.py local-test --vault ./wiki_vault

Run MCP server over stdio, after installing the official MCP Python SDK:
    python llm_wiki_mcp_server.py server --vault ./wiki_vault

Install:
    pip install -e .
    pip install -e .[mcp]
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as _dt
import difflib
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
import sys
import textwrap
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict, OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s', stream=sys.stderr)
logger = logging.getLogger('llm_wiki_mcp')

# -----------------------------------------------------------------------------
# Namespace helpers copied in spirit from the attached EML MCP server
# -----------------------------------------------------------------------------

def _helper_namespace_prefix() -> str:
    """Internal helper for helper namespace prefix."""
    ns = os.getenv('MCP_EXPOSED_NAMESPACE', '').strip()
    return f'{ns}__' if ns else ''

def _helper_exposed_name(name: str) -> str:
    """Internal helper for helper exposed name."""
    prefix = _helper_namespace_prefix()
    return f'{prefix}{name}' if prefix else name

def _helper_strip_namespace(name: str) -> str:
    """Internal helper for helper strip namespace."""
    prefix = _helper_namespace_prefix()
    if prefix and name.startswith(prefix):
        return name[len(prefix):]
    return name

# -----------------------------------------------------------------------------
# Small TTL cache layer, same pattern as the attached EML MCP server
# -----------------------------------------------------------------------------

class TTLCache:
    """Simple LRU + TTL cache for JSON-like objects."""
    def __init__(self, maxsize: int = 256, ttl_seconds: int = 600):
        """Internal helper for init."""
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._data: OrderedDict[str, Tuple[float, Any]] = OrderedDict()

    def _purge(self) -> None:
        """Internal helper for purge."""
        now = time.time()
        expired = [k for k, (t, _) in self._data.items() if now - t > self.ttl_seconds]
        for k in expired:
            self._data.pop(k, None)
        while len(self._data) > self.maxsize:
            self._data.popitem(last=False)

    def get(self, key: str) -> Any:
        """Implement the get operation for the local LLM Wiki workflow."""
        self._purge()
        if key not in self._data:
            return None
        ts, value = self._data.pop(key)
        self._data[key] = (ts, value)
        return value

    def set(self, key: str, value: Any) -> None:
        """Implement the set operation for the local LLM Wiki workflow."""
        self._data[key] = (time.time(), value)
        self._purge()

search_cache = TTLCache(maxsize=256, ttl_seconds=120)
context_cache = TTLCache(maxsize=128, ttl_seconds=120)

# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------

def canonical_json(data: Any) -> str:
    """Implement the canonical json operation for the local LLM Wiki workflow."""
    return json.dumps(data, sort_keys=True, separators=(',', ':'), default=str)

def sha256_text(text: str) -> str:
    """Implement the sha256 text operation for the local LLM Wiki workflow."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def stable_key(*parts: Any) -> str:
    """Implement the stable key operation for the local LLM Wiki workflow."""
    return sha256_text(canonical_json(parts))

def now_iso() -> str:
    """Implement the now iso operation for the local LLM Wiki workflow."""
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()

def safe_slug(title: str) -> str:
    """Implement the safe slug operation for the local LLM Wiki workflow."""
    title = title.strip().replace('/', ' ').replace('\\', ' ')
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'[^A-Za-z0-9 _\-()]+', '', title).strip()
    return title or 'Untitled'

def extract_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    """Implement the extract front matter operation for the local LLM Wiki workflow."""
    if not text.startswith('---\n'):
        return {}, text
    end = text.find('\n---\n', 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end+5:]
    meta: Dict[str, Any] = {}
    for line in raw.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, body

def make_front_matter(meta: Dict[str, Any]) -> str:
    """Implement the make front matter operation for the local LLM Wiki workflow."""
    lines = ['---']
    for k, v in meta.items():
        if isinstance(v, (list, tuple)):
            v = '[' + ', '.join(json.dumps(str(x), ensure_ascii=False) for x in v) + ']'
        elif isinstance(v, bool):
            v = 'true' if v else 'false'
        else:
            v = str(v).replace('\n', ' ')
        lines.append(f'{k}: {v}')
    lines.append('---')
    return '\n'.join(lines) + '\n\n'

def wiki_links(text: str) -> List[str]:
    """Implement the wiki links operation for the local LLM Wiki workflow."""
    return sorted(set(m.group(1).strip() for m in re.finditer(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]', text)))

def plain_words(text: str) -> List[str]:
    """Implement the plain words operation for the local LLM Wiki workflow."""
    return [w.lower() for w in re.findall(r'[A-Za-z][A-Za-z0-9_\-]{2,}', text)]


def _singular_plural_variants(token: str) -> List[str]:
    """Return tiny dependency-free singular/plural variants for search UX.

    This is not a full stemmer. It is deliberately conservative and only helps
    common English cases such as `article/articles`, `category/categories`,
    `wiki/wikis`, and `architecture/architectures`.
    """
    token = token.lower().strip()
    if not token:
        return []
    variants = {token}
    if len(token) > 4 and token.endswith('ies'):
        variants.add(token[:-3] + 'y')
    if len(token) > 3 and token.endswith('y'):
        variants.add(token[:-1] + 'ies')
    if len(token) > 4 and token.endswith(('ches', 'shes', 'xes', 'zes', 'ses')):
        variants.add(token[:-2])
    if len(token) > 3 and token.endswith('s') and not token.endswith('ss'):
        variants.add(token[:-1])
    else:
        variants.add(token + 's')
    return sorted(v for v in variants if len(v) >= 2)


def expand_search_terms(query: str) -> List[str]:
    """Expand query terms for case-insensitive, prefix, singular/plural search."""
    terms = []
    for word in plain_words(query):
        for variant in _singular_plural_variants(word):
            if variant not in terms:
                terms.append(variant)
    return terms


def search_query_diagnostics(query: str) -> Dict[str, Any]:
    """Search or retrieve wiki content for search query diagnostics."""
    return {
        'query': query,
        'case_sensitive': False,
        'case_note': 'SQLite FTS5 unicode61 matching is case-insensitive for normal Latin text; the fallback scorer lowercases both query and page text.',
        'plural_singular_supported': True,
        'plural_singular_note': 'The search layer adds conservative singular/plural variants before fallback scoring. It is not a full linguistic stemmer.',
        'plain_words': plain_words(query),
        'expanded_terms': expand_search_terms(query),
    }

@dataclass
class WikiConfig:
    """Represent the Wiki Config component used by the local wiki runtime."""
    vault: Path

    @property
    def wiki_dir(self) -> Path:
        """Implement the wiki dir operation for the local LLM Wiki workflow."""
        return self.vault / 'wiki'

    @property
    def raw_dir(self) -> Path:
        """Implement the raw dir operation for the local LLM Wiki workflow."""
        return self.vault / 'raw'

    @property
    def db_path(self) -> Path:
        """Implement the db path operation for the local LLM Wiki workflow."""
        return self.vault / 'index.sqlite3'

CONFIG = WikiConfig(vault=Path(os.environ.get('LLM_WIKI_VAULT', './wiki_vault')).resolve())

def set_vault(path: str | Path) -> None:
    """Implement the set vault operation for the local LLM Wiki workflow."""
    CONFIG.vault = Path(path).expanduser().resolve()


# -----------------------------------------------------------------------------
# Release Ollama configuration and local LLM Q&A
# -----------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "ollama": {
        "host": "http://localhost:11434",
        "model": "llama3.2:3b",
        "temperature": 0.2,
        "timeout_seconds": 120,
        "top_k": 5,
        "max_context_chars": 12000,
        "max_chars_per_article": 4000
    }
}

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the deep merge operation for the local LLM Wiki workflow."""
    out = json.loads(json.dumps(base))
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out

def strip_json_comments(text: str) -> str:
    """Remove // and # comments from JSON-like config while preserving strings."""
    lines: List[str] = []
    for line in str(text or "").splitlines():
        out: List[str] = []
        in_string = False
        escape = False
        i = 0
        while i < len(line):
            ch = line[i]
            nxt = line[i + 1] if i + 1 < len(line) else ""
            if escape:
                out.append(ch)
                escape = False
            elif ch == "\\" and in_string:
                out.append(ch)
                escape = True
            elif ch == '"':
                out.append(ch)
                in_string = not in_string
            elif not in_string and ch == "#":
                break
            elif not in_string and ch == "/" and nxt == "/":
                break
            else:
                out.append(ch)
            i += 1
        stripped = "".join(out).rstrip()
        if stripped.strip():
            lines.append(stripped)
    return "\n".join(lines)

def load_wiki_config(vault: Optional[Path] = None) -> Dict[str, Any]:
    """Read, write, or update local wiki configuration for load wiki config."""
    vault = Path(vault or CONFIG.vault).expanduser().resolve()
    cfg_path = config_path_for_vault(vault)
    if not cfg_path.exists():
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding='utf-8')
        return json.loads(json.dumps(DEFAULT_CONFIG))
    try:
        user_cfg = json.loads(strip_json_comments(cfg_path.read_text(encoding='utf-8')))
    except Exception:
        user_cfg = {}
    return deep_merge(DEFAULT_CONFIG, user_cfg)



def config_path_for_vault(vault: Optional[Path] = None) -> Path:
    """Read, write, or update local wiki configuration for config path for vault."""
    vault = Path(vault or CONFIG.vault).expanduser().resolve()
    return vault / 'llm_wiki_config.json'

def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    """Implement the atomic write json operation for the local LLM Wiki workflow."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)

def save_wiki_config(config: Dict[str, Any], vault: Optional[Path] = None) -> Dict[str, Any]:
    """Read, write, or update local wiki configuration for save wiki config."""
    cfg_path = config_path_for_vault(vault)
    merged = deep_merge(DEFAULT_CONFIG, config or {})
    atomic_write_json(cfg_path, merged)
    return {'ok': True, 'config_path': str(cfg_path), 'config': load_wiki_config(vault)}

def set_nested_config_value(config: Dict[str, Any], dotted_key: str, value: Any) -> Dict[str, Any]:
    """Read, write, or update local wiki configuration for set nested config value."""
    key_map = {
        'host': 'ollama.host',
        'model': 'ollama.model',
        'temperature': 'ollama.temperature',
        'timeout': 'ollama.timeout_seconds',
        'timeout_seconds': 'ollama.timeout_seconds',
        'top_k': 'ollama.top_k',
        'max_context_chars': 'ollama.max_context_chars',
        'max_chars_per_article': 'ollama.max_chars_per_article',
    }
    dotted_key = key_map.get(dotted_key, dotted_key)
    cur = config
    parts = dotted_key.split('.')
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            cur[part] = {}
        cur = cur[part]
    leaf = parts[-1]
    if isinstance(value, str):
        low = value.lower()
        if low in {'true', 'false'}:
            value = low == 'true'
        else:
            try:
                value = int(value) if value.isdigit() or (value.startswith('-') and value[1:].isdigit()) else float(value)
            except Exception:
                pass
    cur[leaf] = value
    return config

def save_default_wiki_config(vault: Optional[Path] = None) -> Dict[str, Any]:
    """Read, write, or update local wiki configuration for save default wiki config."""
    vault = Path(vault or CONFIG.vault).expanduser().resolve()
    cfg_path = config_path_for_vault(vault)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if not cfg_path.exists():
        cfg_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding='utf-8')
    return {'config_path': str(cfg_path), 'config': load_wiki_config(vault)}

def call_ollama_generate(prompt: str, host: str, model: str, temperature: float = 0.2, timeout_seconds: int = 120) -> Dict[str, Any]:
    """Implement the call ollama generate operation for the local LLM Wiki workflow."""
    url = host.rstrip('/') + '/api/generate'
    payload = {'model': model, 'prompt': prompt, 'stream': False, 'options': {'temperature': temperature}}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode('utf-8', errors='replace')
        data = json.loads(raw)
        return {'ok': True, 'host': host, 'model': model, 'elapsed_seconds': round(time.time()-start, 3), 'response': data.get('response',''), 'raw': data}
    except urllib.error.URLError as exc:
        return {'ok': False, 'host': host, 'model': model, 'error': f'Ollama request failed: {exc}', 'hint': 'Check that Ollama is running, e.g. `ollama serve`, and that the configured model is pulled.'}
    except Exception as exc:
        return {'ok': False, 'host': host, 'model': model, 'error': str(exc)}


# -----------------------------------------------------------------------------
# Store/index layer
# -----------------------------------------------------------------------------

class WikiStore:
    """Represent the Wiki Store component used by the local wiki runtime."""
    def _connect_rebuildable_db(self):
        """Connect to SQLite index; rebuild if the bundled/local DB is corrupt."""
        import sqlite3 as _sqlite3
        db_path = self.config.db_path
        try:
            con = _sqlite3.connect(db_path)
            con.execute("PRAGMA schema_version")
            return con
        except _sqlite3.DatabaseError:
            try:
                con.close()
            except Exception:
                pass
            try:
                if db_path.exists():
                    db_path.unlink()
            except Exception:
                pass
            con = _sqlite3.connect(db_path)
            return con

    def __init__(self, cfg: WikiConfig):
        """Internal helper for init."""
        self.cfg = cfg
        self.cfg.wiki_dir.mkdir(parents=True, exist_ok=True)
        self.cfg.raw_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Internal helper for connect."""
        con = sqlite3.connect(self.cfg.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        """Internal helper for init db."""
        self.cfg.vault.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute('CREATE TABLE IF NOT EXISTS pages (title TEXT PRIMARY KEY, path TEXT, sha256 TEXT, updated TEXT, words INTEGER, links INTEGER)')
            con.execute('CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(title, body)')
            con.execute('CREATE TABLE IF NOT EXISTS decisions (id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, title TEXT, decision TEXT, rationale TEXT, links TEXT)')
            con.commit()

    def init_seed(self) -> Dict[str, Any]:
        """Implement the init seed operation for the local LLM Wiki workflow."""
        seeds = {
            'index': '# LLM Wiki Index\n\nStart here. Link durable notes with `[[Page Name]]`.\n\n- [[Overview]]\n- [[Glossary]]\n- [[Open Questions]]\n- [[Contradictions]]\n- [[Decision Log]]\n',
            'Overview': '# Overview\n\nThis local wiki is the maintained source of truth for long-running LLM-assisted work.\n',
            'Glossary': '# Glossary\n\nAdd short definitions for recurring terms.\n',
            'Open Questions': '# Open Questions\n\nUse this page for unresolved issues, hypotheses, and questions to revisit.\n',
            'Contradictions': '# Contradictions\n\nUse this page to track conflicts between sources or interpretations.\n',
            'Decision Log': '# Decision Log\n\nImportant choices made by humans or agents should be mirrored here.\n',
        }
        created=[]
        for title, body in seeds.items():
            if not self.page_path(title).exists():
                self.create_page(title, body, tags=['seed'], source='llm_wiki_mcp')
                created.append(title)
        self.reindex()
        return {'vault': str(self.cfg.vault), 'created': created, 'page_count': len(list(self.cfg.wiki_dir.glob('*.md')))}

    def page_path(self, title: str) -> Path:
        """Implement the page path operation for the local LLM Wiki workflow."""
        return self.cfg.wiki_dir / f'{safe_slug(title)}.md'

    def read_page(self, title: str) -> Dict[str, Any]:
        """Implement the read page operation for the local LLM Wiki workflow."""
        path = self.page_path(title)
        if not path.exists():
            raise FileNotFoundError(f'No wiki page titled {title!r}')
        text = path.read_text(encoding='utf-8')
        meta, body = extract_front_matter(text)
        return {'title': safe_slug(title), 'path': str(path), 'metadata': meta, 'body': body, 'links': wiki_links(body), 'sha256': sha256_text(text)}

    def create_page(self, title: str, body: str, tags: Optional[List[str]] = None, source: str = 'user', overwrite: bool = False) -> Dict[str, Any]:
        """Implement the create page operation for the local LLM Wiki workflow."""
        title = safe_slug(title)
        path = self.page_path(title)
        if path.exists() and not overwrite:
            raise FileExistsError(f'Page already exists: {title}')
        meta = {'title': title, 'created': now_iso(), 'updated': now_iso(), 'tags': tags or [], 'source': source}
        text = make_front_matter(meta) + body.strip() + '\n'
        path.write_text(text, encoding='utf-8')
        self.index_page(title)
        return {'title': title, 'path': str(path), 'created': True, 'sha256': sha256_text(text)}

    def update_page(self, title: str, body: str, mode: str = 'replace') -> Dict[str, Any]:
        """Implement the update page operation for the local LLM Wiki workflow."""
        title = safe_slug(title)
        path = self.page_path(title)
        if not path.exists():
            return self.create_page(title, body, source='update_page')
        old_text = path.read_text(encoding='utf-8')
        meta, old_body = extract_front_matter(old_text)
        meta['updated'] = now_iso()
        if mode == 'append':
            new_body = old_body.rstrip() + '\n\n' + body.strip() + '\n'
        elif mode == 'prepend':
            new_body = body.strip() + '\n\n' + old_body.lstrip()
        elif mode == 'replace':
            new_body = body.strip() + '\n'
        else:
            raise ValueError('mode must be replace, append, or prepend')
        text = make_front_matter(meta) + new_body
        path.write_text(text, encoding='utf-8')
        self.index_page(title)
        return {'title': title, 'path': str(path), 'mode': mode, 'sha256': sha256_text(text)}

    def append_section(self, title: str, heading: str, content: str) -> Dict[str, Any]:
        """Implement the append section operation for the local LLM Wiki workflow."""
        return self.update_page(title, f'## {heading}\n\n{content}', mode='append')

    def index_page(self, title: str) -> None:
        """Implement the index page operation for the local LLM Wiki workflow."""
        page = self.read_page(title)
        body = page['body']
        with self._connect() as con:
            con.execute('INSERT OR REPLACE INTO pages(title,path,sha256,updated,words,links) VALUES (?,?,?,?,?,?)',
                        (page['title'], page['path'], page['sha256'], now_iso(), len(plain_words(body)), len(page['links'])))
            con.execute('DELETE FROM pages_fts WHERE title=?', (page['title'],))
            con.execute('INSERT INTO pages_fts(title,body) VALUES (?,?)', (page['title'], body))
            con.commit()

    def reindex(self) -> Dict[str, Any]:
        """Implement the reindex operation for the local LLM Wiki workflow."""
        count=0
        with self._connect() as con:
            con.execute('DELETE FROM pages')
            con.execute('DELETE FROM pages_fts')
            con.commit()
        for p in self.cfg.wiki_dir.glob('*.md'):
            self.index_page(p.stem)
            count += 1
        return {'indexed_pages': count, 'db_path': str(self.cfg.db_path)}

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search or retrieve wiki content for search."""
        key = stable_key('search-release', str(self.cfg.vault), query, limit)
        cached = search_cache.get(key)
        if cached is not None:
            return cached

        words = plain_words(query)
        expanded = expand_search_terms(query)
        q = ' '.join(words) or query.strip()
        rows=[]
        search_mode = 'fts'
        with self._connect() as con:
            # FTS5 is case-insensitive for normal Latin text. Try exact token FTS,
            # then prefix FTS, then expanded singular/plural prefix FTS. Fall back
            # to a deterministic substring/scoring pass when FTS gives nothing.
            fts_candidates = []
            if q.strip():
                fts_candidates.append(q)
            if words:
                fts_candidates.append(' '.join(w + '*' for w in words))
            if expanded:
                fts_candidates.append(' OR '.join(t + '*' for t in expanded))
            for candidate in fts_candidates:
                if rows or not candidate.strip():
                    continue
                try:
                    for row in con.execute('SELECT title, body, rank FROM pages_fts WHERE pages_fts MATCH ? ORDER BY rank LIMIT ?', (candidate, limit)):
                        d = dict(row); d['match_mode'] = 'fts'; rows.append(d)
                except sqlite3.OperationalError:
                    pass
            if not rows:
                search_mode = 'fallback'
                tokens = set(expanded or words)
                compact_query = re.sub(r'[^a-z0-9]+','', query.lower())
                for row in con.execute('SELECT title, body FROM pages_fts LIMIT 1000'):
                    body = row['body']
                    body_words = plain_words(body)
                    title_l = row['title'].lower()
                    title_compact = re.sub(r'[^a-z0-9]+','', title_l)
                    score = 0
                    for token in tokens:
                        score += sum(1 for w in body_words if w == token or w.startswith(token) or token.startswith(w))
                        if token in title_l or title_l.startswith(token):
                            score += 8
                        if token in title_compact:
                            score += 4
                    if compact_query and compact_query in title_compact:
                        score += 12
                    # Fuzzy title rescue for typos and short probes.
                    for token in tokens:
                        if difflib.SequenceMatcher(None, token, title_compact).ratio() > 0.72:
                            score += 5
                    if score:
                        rows.append({'title': row['title'], 'body': body, 'rank': -score, 'match_mode': 'fallback'})
                rows.sort(key=lambda r: r['rank'])
                rows = rows[:limit]
        results=[]
        for r in rows:
            body = r.get('body','')
            snippet = body[:600].replace('\n',' ')
            results.append({'title': r['title'], 'score': float(r.get('rank', 0.0)), 'snippet': snippet, 'links': wiki_links(body)[:10], 'match_mode': r.get('match_mode', search_mode)})
        payload={'query': query, 'results': results, 'count': len(results), 'diagnostics': search_query_diagnostics(query), 'search_mode': search_mode}
        search_cache.set(key, payload)
        return payload

    def search_diagnostics(self, query: str, limit: int = 8) -> Dict[str, Any]:
        """Search or retrieve wiki content for search diagnostics."""
        result = self.search(query, limit=limit)
        pages = self.list_pages(limit=1000).get('pages', [])
        q_compact = re.sub(r'[^a-z0-9]+', '', query.lower())
        title_suggestions = []
        for p in pages:
            title = str(p.get('title', ''))
            title_compact = re.sub(r'[^a-z0-9]+', '', title.lower())
            if q_compact and (q_compact in title_compact or title_compact in q_compact):
                title_suggestions.append(title)
        if not title_suggestions:
            title_suggestions = difflib.get_close_matches(query, [str(p.get('title','')) for p in pages], n=8, cutoff=0.55)
        return {
            'query': query,
            'diagnostics': result.get('diagnostics', search_query_diagnostics(query)),
            'result_count': result.get('count', 0),
            'top_titles': [r.get('title') for r in result.get('results', [])[:limit]],
            'title_suggestions': title_suggestions[:8],
            'notes': [
                'Search is not intended to be case dependent.',
                'Release expands common singular/plural forms before fallback scoring.',
                'If expected files are missing, ingest that directory; for example `/ingest .` includes top-level README.md while `/ingest ./docs` does not.',
            ],
        }

    def status(self) -> Dict[str, Any]:
        """Implement the status operation for the local LLM Wiki workflow."""
        pages=list(self.cfg.wiki_dir.glob('*.md'))
        raw=list(self.cfg.raw_dir.glob('*'))
        words=0
        for p in pages:
            words += len(plain_words(p.read_text(encoding='utf-8', errors='ignore')))
        return {'vault': str(self.cfg.vault), 'wiki_dir': str(self.cfg.wiki_dir), 'raw_dir': str(self.cfg.raw_dir), 'page_count': len(pages), 'raw_file_count': len(raw), 'word_count_estimate': words, 'db_path': str(self.cfg.db_path), 'db_exists': self.cfg.db_path.exists()}

    def _extract_ingest_text(self, src: Path) -> str:
        """Extract readable text for MCP/server-side single-file ingestion."""
        suffix = src.suffix.lower()
        if suffix == '.rtf':
            raw = src.read_text(encoding='utf-8', errors='replace')

            def _hex(match):
                """Document the `_hex` function used by the LLM Wiki MCP release."""
                try:
                    return bytes.fromhex(match.group(1)).decode('latin-1')
                except Exception:
                    return ' '

            def _unicode(match):
                """Document the `_unicode` function used by the LLM Wiki MCP release."""
                try:
                    value = int(match.group(1))
                    if value < 0:
                        value += 65536
                    return chr(value)
                except Exception:
                    return ' '

            text = re.sub(r"\\'([0-9a-fA-F]{2})", _hex, raw)
            text = re.sub(r"\\u(-?\d+)\??", _unicode, text)
            text = re.sub(r"\\(par|line|tab)\b ?", '\n', text)
            text = re.sub(r"\\[{}\\]", lambda m: m.group(0)[1:], text)
            text = re.sub(r"\\[a-zA-Z]+-?\d* ?", '', text)
            text = re.sub(r"[{}]", '', text)
            text = re.sub(r"\n{3,}", '\n\n', text)
            text = re.sub(r"[ \t]{2,}", ' ', text)
            return text.strip()
        return src.read_text(encoding='utf-8', errors='ignore')

    def ingest_file(self, path: str, title: Optional[str] = None, copy_raw: bool = True) -> Dict[str, Any]:
        """Ingest source content into Markdown wiki pages for ingest file."""
        src=Path(path).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(str(src))
        text=self._extract_ingest_text(src)
        if copy_raw:
            dst=self.cfg.raw_dir/src.name
            if src != dst:
                shutil.copyfile(src, dst)
        page_title = safe_slug(title or f'Source - {src.name}')
        body = f'# {page_title}\n\nSource file: `{src.name}`\n\n## Extracted Content\n\n{text.strip()}\n'
        created = self.create_page(page_title, body, tags=['source','ingested'], source=str(src), overwrite=True)
        return {'source_path': str(src), 'page': created, 'chars': len(text), 'links': wiki_links(text)}

    def ingest_directory(self, directory: str, pattern: str = '*.md', recursive: bool = True, limit: int = 100) -> Dict[str, Any]:
        """Ingest source content from a directory or a single file into wiki pages."""
        base=Path(directory).expanduser().resolve()
        if not base.exists():
            raise FileNotFoundError(str(base))
        if base.is_file():
            paths=[base]
        else:
            paths=list(base.rglob(pattern) if recursive else base.glob(pattern))[:limit]
        ingested=[]
        for p in paths:
            if p.is_file():
                ingested.append(self.ingest_file(str(p), copy_raw=True))
        return {'directory': str(base), 'pattern': pattern, 'recursive': recursive, 'ingested_count': len(ingested), 'pages': [x['page']['title'] for x in ingested]}

    def import_transcript(self, transcript: str, title: str = 'Imported Transcript', speaker_prefixes: Optional[List[str]] = None) -> Dict[str, Any]:
        """Implement the import transcript operation for the local LLM Wiki workflow."""
        lines=[ln.strip() for ln in transcript.splitlines() if ln.strip()]
        bullets=[]
        for ln in lines:
            if len(ln) > 280:
                ln = ln[:277] + '...'
            bullets.append(f'- {ln}')
        page_title=safe_slug(title)
        body=f'# {page_title}\n\nImported transcript summary page.\n\n## Transcript Notes\n\n'+'\n'.join(bullets)+'\n'
        return self.create_page(page_title, body, tags=['transcript','imported'], source='transcript', overwrite=True)


    def retrieve_articles(self, prompt: str, top_k: int = 5, max_chars_per_article: int = 4000, max_total_chars: int = 12000, include_metadata: bool = True) -> Dict[str, Any]:
        """Search the wiki with a user/agent prompt and retrieve the top-k full articles.

        This is the explicit RAG-like retrieval primitive. The returned
        articles are maintained wiki pages, not anonymous vector chunks. Use it
        when an engine or human wants: prompt -> search -> top-k retrieved
        articles -> optional LLM context text.
        """
        top_k = max(1, int(top_k))
        max_chars_per_article = max(200, int(max_chars_per_article))
        max_total_chars = max(500, int(max_total_chars))
        search = self.search(prompt, limit=top_k)
        articles=[]
        used=0
        for rank, item in enumerate(search.get('results', []), 1):
            try:
                page=self.read_page(item['title'])
            except Exception:
                continue
            body=page.get('body','').strip()
            truncated=False
            if len(body) > max_chars_per_article:
                body = body[:max_chars_per_article].rstrip() + '\n\n[...article truncated...]'
                truncated=True
            block_len=len(body)
            if used + block_len > max_total_chars:
                remaining=max_total_chars-used
                if remaining <= 150:
                    break
                body = body[:remaining].rstrip() + '\n\n[...retrieval budget reached...]'
                block_len=len(body)
                truncated=True
            article={
                'rank': rank,
                'title': page.get('title'),
                'score': float(item.get('score', 0.0)),
                'snippet': item.get('snippet',''),
                'path': page.get('path'),
                'links': page.get('links', []),
                'chars': len(body),
                'truncated': truncated,
                'body': body,
            }
            if not include_metadata:
                article={k:v for k,v in article.items() if k in {'rank','title','body','chars','truncated'}}
            articles.append(article)
            used += block_len
            if used >= max_total_chars:
                break
        context_parts=[
            '# Retrieved Wiki Articles\n',
            f'Prompt: `{prompt}`\n',
            f'Top K requested: {top_k} | Retrieved: {len(articles)}\n',
            'Use these maintained wiki articles as grounded context. Cite page titles when answering.\n'
        ]
        for a in articles:
            meta=f"score={a.get('score',0):.4g}; path={a.get('path','')}" if include_metadata else ''
            context_parts.append(f"\n---\n\n## Article {a['rank']}: [[{a['title']}]]\n{meta}\n\n{a['body']}\n")
        context=''.join(context_parts).strip() + '\n'
        return {'prompt': prompt, 'query': prompt, 'top_k': top_k, 'retrieved_count': len(articles), 'chars': len(context), 'article_titles': [a['title'] for a in articles], 'articles': articles, 'context': context}


    def ask_ollama(self, question: str, top_k: Optional[int] = None, model: Optional[str] = None, host: Optional[str] = None,
                   temperature: Optional[float] = None, timeout_seconds: Optional[int] = None,
                   max_context_chars: Optional[int] = None, max_chars_per_article: Optional[int] = None,
                   dry_run: bool = False) -> Dict[str, Any]:
        """Retrieve wiki articles, build an LLM prompt, and ask a local Ollama model."""
        cfg = load_wiki_config(self.cfg.vault).get('ollama', {})
        top_k = int(top_k if top_k is not None else cfg.get('top_k', 5))
        model = str(model or cfg.get('model', 'llama3.2:3b'))
        host = str(host or cfg.get('host', 'http://localhost:11434'))
        temperature = float(temperature if temperature is not None else cfg.get('temperature', 0.2))
        timeout_seconds = int(timeout_seconds if timeout_seconds is not None else cfg.get('timeout_seconds', 120))
        max_context_chars = int(max_context_chars if max_context_chars is not None else cfg.get('max_context_chars', 12000))
        max_chars_per_article = int(max_chars_per_article if max_chars_per_article is not None else cfg.get('max_chars_per_article', 4000))
        retrieved = self.retrieve_articles(question, top_k=top_k, max_chars_per_article=max_chars_per_article, max_total_chars=max_context_chars)
        llm_prompt = (
            "You are answering using a maintained local LLM Wiki.\n"
            "Use the wiki context first. Cite page titles like [[Page Title]] where useful.\n"
            "If the wiki is missing evidence, say what is missing and suggest a maintenance action.\n\n"
            f"# User question\n{question}\n\n"
            f"# Wiki context\n{retrieved.get('context','')}\n\n"
            "# Answer\n"
        )
        result = {'question': question, 'model': model, 'host': host, 'top_k': top_k, 'retrieval': retrieved, 'llm_prompt': llm_prompt, 'dry_run': dry_run}
        if dry_run:
            result['answer'] = ''
            result['ok'] = True
            result['note'] = 'Dry run: prompt built but Ollama was not called.'
            return result
        llm = call_ollama_generate(llm_prompt, host=host, model=model, temperature=temperature, timeout_seconds=timeout_seconds)
        result.update({'ok': bool(llm.get('ok')), 'answer': llm.get('response',''), 'ollama': llm})
        return result

    def config(self) -> Dict[str, Any]:
        """Read, write, or update local wiki configuration for config."""
        return save_default_wiki_config(self.cfg.vault)

    def config_set(self, key: str, value: Any) -> Dict[str, Any]:
        """Read, write, or update local wiki configuration for config set."""
        current = load_wiki_config(self.cfg.vault)
        updated = set_nested_config_value(current, key, value)
        saved = save_wiki_config(updated, self.cfg.vault)
        saved['changed'] = {'key': key, 'value': value}
        return saved

    def config_reset(self) -> Dict[str, Any]:
        """Read, write, or update local wiki configuration for config reset."""
        return save_wiki_config(DEFAULT_CONFIG, self.cfg.vault)

    def config_test(self) -> Dict[str, Any]:
        """Read, write, or update local wiki configuration for config test."""
        cfg = load_wiki_config(self.cfg.vault).get('ollama', {})
        host = cfg.get('host', DEFAULT_CONFIG['ollama']['host'])
        model = cfg.get('model', DEFAULT_CONFIG['ollama']['model'])
        return call_ollama_generate('Reply with exactly: OK', host=host, model=model, temperature=0.0, timeout_seconds=int(cfg.get('timeout_seconds', 20)))

    def build_context_pack(self, query: str, limit: int = 5, max_chars: int = 8000) -> Dict[str, Any]:
        """Implement the build context pack operation for the local LLM Wiki workflow."""
        key=stable_key('context', str(self.cfg.vault), query, limit, max_chars)
        cached=context_cache.get(key)
        if cached is not None:
            return cached
        search=self.search(query, limit=limit)
        chunks=[]; used=0
        for item in search['results']:
            page=self.read_page(item['title'])
            chunk=f'## [[{page["title"]}]]\n\n{page["body"].strip()}\n'
            if used + len(chunk) > max_chars:
                chunk=chunk[:max(0, max_chars-used)]
            if chunk:
                chunks.append(chunk); used += len(chunk)
            if used >= max_chars:
                break
        pack='\n\n---\n\n'.join(chunks)
        payload={'query': query, 'page_titles': [r['title'] for r in search['results']], 'chars': len(pack), 'context_pack': pack}
        context_cache.set(key, payload)
        return payload

    def graph_links(self) -> Dict[str, Any]:
        """Create graph-oriented output for graph links."""
        pages=[]; edges=[]; backlinks=defaultdict(list)
        for p in sorted(self.cfg.wiki_dir.glob('*.md')):
            title=p.stem; text=p.read_text(encoding='utf-8', errors='ignore'); links=wiki_links(text)
            pages.append({'title': title, 'links': links})
            for link in links:
                edges.append({'from': title, 'to': link})
                backlinks[link].append(title)
        return {'nodes': [p['title'] for p in pages], 'edges': edges, 'backlinks': dict(backlinks), 'node_count': len(pages), 'edge_count': len(edges)}


    def mermaid_graph(self, direction: str = 'TD', include_orphans: bool = True, max_edges: int = 200, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Render the wiki link graph as a Mermaid flowchart.

        This is intentionally plain Mermaid text so it can be pasted into
        Markdown, rendered by GitHub/GitLab/Obsidian-style tools, or given to an
        LLM as a compact structural map of the wiki.
        """
        graph = self.graph_links()
        direction = str(direction or 'TD').upper()
        if direction not in {'TD', 'TB', 'BT', 'LR', 'RL'}:
            direction = 'TD'

        def node_id(title: str) -> str:
            """Implement the node id operation for the local LLM Wiki workflow."""
            raw = re.sub(r'[^A-Za-z0-9_]+', '_', safe_slug(title)).strip('_')
            if not raw:
                raw = 'node'
            if raw[0].isdigit():
                raw = 'n_' + raw
            return raw

        nodes = list(graph['nodes'])
        existing = {safe_slug(n) for n in nodes}
        edges = graph['edges'][:max(0, int(max_edges))]
        referenced = {safe_slug(e['from']) for e in edges} | {safe_slug(e['to']) for e in edges}
        if not include_orphans:
            nodes = [n for n in nodes if safe_slug(n) in referenced]

        id_map = {n: node_id(n) for n in nodes}
        lines = [f'flowchart {direction}', '  %% Generated by LLM_WIKI_MCP', '  classDef orphan stroke-dasharray: 4 3;']
        for title in nodes:
            label = str(title).replace('"', "'")
            lines.append(f'  {id_map[title]}["{label}"]')

        edge_count = 0
        for e in edges:
            src = safe_slug(e['from'])
            dst = safe_slug(e['to'])
            if src not in id_map:
                id_map[src] = node_id(src)
                lines.append(f'  {id_map[src]}["{src.replace(chr(34), chr(39))}"]')
            if dst not in id_map:
                # Include broken/missing link targets as visible dashed nodes.
                id_map[dst] = node_id(dst)
                lines.append(f'  {id_map[dst]}["{dst.replace(chr(34), chr(39))}"]')
                lines.append(f'  class {id_map[dst]} orphan')
            lines.append(f'  {id_map[src]} --> {id_map[dst]}')
            edge_count += 1

        if len(graph['edges']) > len(edges):
            lines.append(f'  %% {len(graph["edges"]) - len(edges)} edges omitted by max_edges={max_edges}')

        mermaid = '\n'.join(lines) + '\n'
        written = None
        if output_path:
            out = Path(output_path).expanduser().resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text('```mermaid\n' + mermaid + '```\n', encoding='utf-8')
            written = str(out)
        return {
            'direction': direction,
            'node_count': len(nodes),
            'edge_count': edge_count,
            'total_edges': len(graph['edges']),
            'include_orphans': include_orphans,
            'max_edges': max_edges,
            'output_path': written,
            'mermaid': mermaid,
        }

    def mermaid_neighbourhood(self, title: str, depth: int = 1, direction: str = 'LR', output_path: Optional[str] = None) -> Dict[str, Any]:
        """Render a Mermaid graph centred on one page and nearby links."""
        title = self.resolve(title)['canonical_title']
        graph = self.graph_links()
        depth = max(1, min(int(depth), 4))
        selected = {safe_slug(title)}
        frontier = {safe_slug(title)}
        for _ in range(depth):
            nxt = set()
            for e in graph['edges']:
                a, b = safe_slug(e['from']), safe_slug(e['to'])
                if a in frontier:
                    nxt.add(b)
                if b in frontier:
                    nxt.add(a)
            selected |= nxt
            frontier = nxt
        temp_edges = [e for e in graph['edges'] if safe_slug(e['from']) in selected and safe_slug(e['to']) in selected]
        # Temporarily compose a compact Mermaid document from the selected subgraph.
        direction = str(direction or 'LR').upper()
        if direction not in {'TD', 'TB', 'BT', 'LR', 'RL'}:
            direction = 'LR'
        def node_id(t: str) -> str:
            """Implement the node id operation for the local LLM Wiki workflow."""
            raw = re.sub(r'[^A-Za-z0-9_]+', '_', safe_slug(t)).strip('_') or 'node'
            return 'n_' + raw if raw[0].isdigit() else raw
        labels = sorted(selected)
        id_map = {n: node_id(n) for n in labels}
        lines = [f'flowchart {direction}', f'  %% Neighbourhood around {title}', '  classDef centre stroke-width:4px;']
        for n in labels:
            lines.append(f'  {id_map[n]}["{n.replace(chr(34), chr(39))}"]')
        if safe_slug(title) in id_map:
            lines.append(f'  class {id_map[safe_slug(title)]} centre')
        for e in temp_edges:
            lines.append(f'  {id_map[safe_slug(e["from"])]} --> {id_map[safe_slug(e["to"])]}')
        mermaid = '\n'.join(lines) + '\n'
        written = None
        if output_path:
            out = Path(output_path).expanduser().resolve()
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text('```mermaid\n' + mermaid + '```\n', encoding='utf-8')
            written = str(out)
        return {'title': title, 'depth': depth, 'node_count': len(labels), 'edge_count': len(temp_edges), 'output_path': written, 'mermaid': mermaid}

    def lint(self) -> Dict[str, Any]:
        """Implement the lint operation for the local LLM Wiki workflow."""
        graph=self.graph_links()
        existing=set(graph['nodes'])
        broken=[]
        for e in graph['edges']:
            if safe_slug(e['to']) not in existing and e['to'] not in existing:
                broken.append(e)
        linked=set(e['to'] for e in graph['edges'])
        orphans=[n for n in existing if n not in linked and n.lower() != 'index']
        short=[]
        for p in self.cfg.wiki_dir.glob('*.md'):
            body=extract_front_matter(p.read_text(encoding='utf-8', errors='ignore'))[1]
            if len(plain_words(body)) < 20:
                short.append(p.stem)
        return {'broken_links': broken, 'orphans': sorted(orphans), 'very_short_pages': sorted(short), 'page_count': len(existing), 'ok': not broken}


    def _replace_wiki_link_target(self, body: str, old_target: str, new_target: str) -> Tuple[str, int]:
        """Replace wiki-link targets while preserving aliases/fragments where possible."""
        old_slug = safe_slug(old_target)
        count = 0
        def repl(m: re.Match) -> str:
            """Implement the repl operation for the local LLM Wiki workflow."""
            nonlocal count
            target = m.group(1).strip()
            rest = m.group(2) or ''
            if safe_slug(target) == old_slug or target == old_target:
                count += 1
                return f'[[{new_target}{rest}]]'
            return m.group(0)
        new_body = re.sub(r'\[\[([^\]|#]+)\s*((?:#[^\]|]+)?(?:\|[^\]]+)?)\]\]', repl, body)
        return new_body, count

    def repair_lint(self, apply: bool = False, fix_broken: bool = True, link_orphans: bool = True,
                    expand_short: bool = True, create_missing: bool = False,
                    index_page: str = 'index') -> Dict[str, Any]:
        """Plan or apply safe repairs for common lint findings.

        The default is a dry run. Repairs are intentionally conservative:
        - broken links are only rewritten when they resolve confidently to an
          existing page;
        - missing link targets are only created when create_missing=True;
        - orphan pages are linked from an auto-maintained section in index;
        - very short pages receive a small human-editable scaffold.
        """
        before = self.lint()
        actions: List[Dict[str, Any]] = []
        changed_pages: set[str] = set()

        if fix_broken:
            for b in before.get('broken_links', []):
                source = safe_slug(b.get('from', ''))
                target = str(b.get('to', '')).strip()
                if not source or not target:
                    continue
                resolved = self.resolve(target)
                canonical = resolved.get('canonical_title')
                source_path = self.page_path(source)
                if resolved.get('exists') and canonical and safe_slug(canonical) != safe_slug(target):
                    actions.append({'kind': 'fix_broken_link', 'from': source, 'old_target': target, 'new_target': canonical, 'apply': apply})
                    if apply and source_path.exists():
                        text = source_path.read_text(encoding='utf-8')
                        meta, body = extract_front_matter(text)
                        new_body, replacements = self._replace_wiki_link_target(body, target, canonical)
                        if replacements:
                            meta['updated'] = now_iso()
                            source_path.write_text(make_front_matter(meta) + new_body, encoding='utf-8')
                            changed_pages.add(source)
                elif create_missing:
                    title = safe_slug(target)
                    actions.append({'kind': 'create_missing_page', 'title': title, 'linked_from': source, 'apply': apply})
                    if apply and not self.page_path(title).exists():
                        body = f'# {title}\n\nThis page was created by wiki repair because it was referenced from [[{source}]] but did not yet exist.\n\n## Notes\n\nAdd a clear definition, source summary, or decision here so future retrieval has useful context.\n'
                        self.create_page(title, body, tags=['repair','stub'], source='wiki_repair_lint', overwrite=False)
                        changed_pages.add(title)
                else:
                    actions.append({'kind': 'unresolved_broken_link', 'from': source, 'target': target, 'suggestion': canonical, 'apply': False})

        if link_orphans:
            orphans = [o for o in before.get('orphans', []) if safe_slug(o).lower() != safe_slug(index_page).lower()]
            if orphans:
                actions.append({'kind': 'link_orphans_from_index', 'index_page': safe_slug(index_page), 'count': len(orphans), 'titles': orphans[:100], 'apply': apply})
                if apply:
                    idx = safe_slug(index_page)
                    if not self.page_path(idx).exists():
                        self.create_page(idx, '# LLM Wiki Index\n\n', tags=['index'], source='wiki_repair_lint')
                    page = self.read_page(idx)
                    body = page['body'].rstrip()
                    marker = '## Auto-linked Pages'
                    existing_links = set(wiki_links(body))
                    new_lines = [f'- [[{o}]]' for o in orphans if o not in existing_links]
                    if new_lines:
                        if marker in body:
                            body = body + '\n' + '\n'.join(new_lines) + '\n'
                        else:
                            body = body + f'\n\n{marker}\n\nThese pages were linked by `wiki_repair_lint` so the wiki graph remains navigable. Review and move them into better topic pages later.\n\n' + '\n'.join(new_lines) + '\n'
                        text = make_front_matter(page['metadata']) + body
                        self.page_path(idx).write_text(text, encoding='utf-8')
                        changed_pages.add(idx)

        if expand_short:
            for title in before.get('very_short_pages', []):
                title = safe_slug(title)
                if not self.page_path(title).exists():
                    continue
                actions.append({'kind': 'expand_short_page_scaffold', 'title': title, 'apply': apply})
                if apply:
                    page = self.read_page(title)
                    body = page['body'].rstrip()
                    if '## Retrieval Notes' not in body:
                        body += ('\n\n## Retrieval Notes\n\n'
                                 'This page is part of the maintained LLM Wiki. Add durable definitions, important decisions, source summaries, open questions, and links to related pages here. Better-maintained pages give the context engine stronger material than loose RAG chunks.\n')
                        meta = page['metadata']; meta['updated'] = now_iso()
                        self.page_path(title).write_text(make_front_matter(meta) + body + '\n', encoding='utf-8')
                        changed_pages.add(title)

        after = None
        if apply and actions:
            self.reindex()
            after = self.lint()
        return {
            'dry_run': not apply,
            'applied': bool(apply),
            'before': before,
            'after': after,
            'action_count': len(actions),
            'actions': actions,
            'changed_pages': sorted(changed_pages),
            'notes': [
                'Run repair first as a dry run, then repair --apply when the proposed actions look sensible.',
                'Use --create-missing only when missing link targets really should become stub pages.',
                'Repair improves navigation; it does not replace human review of source meaning.'
            ]
        }

    def export_llms_txt(self, output_path: Optional[str] = None, max_chars: int = 60000) -> Dict[str, Any]:
        """Implement the export llms txt operation for the local LLM Wiki workflow."""
        out=Path(output_path).expanduser().resolve() if output_path else self.cfg.vault/'llms.txt'
        parts=['# llms.txt export', '', f'Generated: {now_iso()}', '']
        used=sum(len(x) for x in parts)
        for p in sorted(self.cfg.wiki_dir.glob('*.md')):
            page=self.read_page(p.stem)
            chunk=f'## {page["title"]}\n\n{page["body"].strip()}\n\n'
            if used+len(chunk) > max_chars:
                break
            parts.append(chunk); used += len(chunk)
        text='\n'.join(parts)
        out.write_text(text, encoding='utf-8')
        return {'output_path': str(out), 'chars': len(text), 'sha256': sha256_text(text)}

    def log_decision(self, title: str, decision: str, rationale: str = '', links: Optional[List[str]] = None) -> Dict[str, Any]:
        """Implement the log decision operation for the local LLM Wiki workflow."""
        links=links or []
        with self._connect() as con:
            cur=con.execute('INSERT INTO decisions(created,title,decision,rationale,links) VALUES (?,?,?,?,?)', (now_iso(), title, decision, rationale, json.dumps(links)))
            con.commit(); rowid=cur.lastrowid
        entry=f'### {now_iso()} — {title}\n\nDecision: {decision}\n\nRationale: {rationale}\n\nLinks: '+', '.join(f'[[{l}]]' for l in links)+'\n'
        self.update_page('Decision Log', entry, mode='append')
        return {'id': rowid, 'title': title, 'decision': decision, 'links': links}


    def list_pages(self, category: Optional[str] = None, tag: Optional[str] = None, limit: int = 200) -> Dict[str, Any]:
        """List wiki pages with metadata, useful for agent navigation and audits."""
        rows=[]
        for p in sorted(self.cfg.wiki_dir.glob('*.md'))[:max(1, limit)]:
            page=self.read_page(p.stem)
            meta=page['metadata']
            tags=str(meta.get('tags',''))
            if category and str(meta.get('category','')).lower()!=category.lower():
                continue
            if tag and tag.lower() not in tags.lower():
                continue
            rows.append({'title': page['title'], 'path': page['path'], 'updated': meta.get('updated',''), 'tags': meta.get('tags',''), 'words': len(plain_words(page['body'])), 'links': page['links']})
        return {'pages': rows, 'count': len(rows), 'category': category, 'tag': tag}

    def resolve(self, handle: str, limit: int = 5) -> Dict[str, Any]:
        """Resolve a loose page handle/id/path/title to canonical title with fuzzy suggestions."""
        raw=str(handle).strip()
        candidate=Path(raw).stem if raw.endswith('.md') or '/' in raw or '\\' in raw else raw
        slug=safe_slug(candidate)
        exact=self.page_path(slug).exists()
        suggestions=[]
        words=set(plain_words(slug)) or {slug.lower()}
        for p in self.cfg.wiki_dir.glob('*.md'):
            title=p.stem
            score=0
            lt=title.lower(); lh=slug.lower()
            nt=re.sub(r'[^a-z0-9]+','',lt); nh=re.sub(r'[^a-z0-9]+','',lh)
            if lt==lh or nt==nh: score+=100
            if lh in lt or lt in lh or nh in nt or nt in nh: score+=20
            score+=len(words & set(plain_words(title))) * 5
            if score:
                suggestions.append({'title': title, 'score': score, 'path': str(p)})
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return {'handle': raw, 'canonical_title': slug if exact else (suggestions[0]['title'] if suggestions else slug), 'exists': exact or bool(suggestions and suggestions[0]['score']>=100), 'suggestions': suggestions[:limit]}

    def backlinks(self, title: str) -> Dict[str, Any]:
        """Implement the backlinks operation for the local LLM Wiki workflow."""
        target=safe_slug(title)
        graph=self.graph_links()
        incoming=[]
        for e in graph['edges']:
            if safe_slug(e['to']) == target or e['to'] == title:
                incoming.append(e['from'])
        outgoing=[]
        if self.page_path(target).exists():
            outgoing=self.read_page(target)['links']
        return {'title': target, 'incoming': sorted(set(incoming)), 'outgoing': outgoing, 'incoming_count': len(set(incoming)), 'outgoing_count': len(outgoing)}

    def rename_page(self, old_title: str, new_title: str, update_links: bool = True) -> Dict[str, Any]:
        """Implement the rename page operation for the local LLM Wiki workflow."""
        old=safe_slug(old_title); new=safe_slug(new_title)
        old_path=self.page_path(old); new_path=self.page_path(new)
        if not old_path.exists():
            raise FileNotFoundError(f'No page titled {old!r}')
        if new_path.exists():
            raise FileExistsError(f'Target page already exists: {new}')
        text=old_path.read_text(encoding='utf-8')
        meta, body=extract_front_matter(text)
        meta['title']=new; meta['updated']=now_iso()
        new_path.write_text(make_front_matter(meta)+body, encoding='utf-8')
        old_path.unlink()
        changed=[]
        if update_links:
            patterns=[(f'[[{old}]]', f'[[{new}]]'), (f'[[{old}|', f'[[{new}|'), (f'[[{old}#', f'[[{new}#')]
            for p in self.cfg.wiki_dir.glob('*.md'):
                t=p.read_text(encoding='utf-8')
                nt=t
                for a,b in patterns:
                    nt=nt.replace(a,b)
                if nt!=t:
                    p.write_text(nt, encoding='utf-8'); changed.append(p.stem)
        self.reindex()
        return {'old_title': old, 'new_title': new, 'updated_links': update_links, 'changed_pages': sorted(changed)}

    def delete_page(self, title: str, tombstone: bool = True) -> Dict[str, Any]:
        """Implement the delete page operation for the local LLM Wiki workflow."""
        title=safe_slug(title); path=self.page_path(title)
        if not path.exists():
            raise FileNotFoundError(f'No page titled {title!r}')
        backlinks=self.backlinks(title)
        deleted_dir=self.cfg.vault/'deleted'; deleted_dir.mkdir(exist_ok=True)
        if tombstone:
            shutil.copyfile(path, deleted_dir/f'{title}.{int(time.time())}.md')
        path.unlink(); self.reindex()
        return {'title': title, 'deleted': True, 'tombstone': tombstone, 'incoming_links_before_delete': backlinks['incoming']}

    def categories(self) -> Dict[str, Any]:
        """Implement the categories operation for the local LLM Wiki workflow."""
        tag_counts=Counter(); category_counts=Counter()
        for p in self.cfg.wiki_dir.glob('*.md'):
            meta,_=extract_front_matter(p.read_text(encoding='utf-8', errors='ignore'))
            cat=str(meta.get('category','uncategorised') or 'uncategorised'); category_counts[cat]+=1
            raw=str(meta.get('tags','')).replace('[','').replace(']','')
            for t in [x.strip().strip('"\'') for x in raw.split(',') if x.strip()]:
                tag_counts[t]+=1
        return {'categories': dict(category_counts), 'tags': dict(tag_counts)}

    def toc(self) -> Dict[str, Any]:
        """Implement the toc operation for the local LLM Wiki workflow."""
        lines=['# Wiki Table of Contents', '']
        for item in self.list_pages(limit=10000)['pages']:
            lines.append(f'- [[{item["title"]}]] — {item["words"]} words, {len(item["links"])} links')
        body='\n'.join(lines)+'\n'
        self.update_page('Table of Contents', body, mode='replace')
        return {'title': 'Table of Contents', 'items': len(lines)-2, 'body': body}

    def schema_doc(self, update: bool = False, body: Optional[str] = None) -> Dict[str, Any]:
        """Implement the schema doc operation for the local LLM Wiki workflow."""
        schema_path=self.cfg.vault/'schema.md'
        if update and body is not None:
            schema_path.write_text(body.strip()+'\n', encoding='utf-8')
        elif not schema_path.exists():
            default="# LLM Wiki Schema\n\n## Page conventions\n- Use Markdown files as the source of truth.\n- Use `[[Wiki Links]]` for durable internal references.\n- Keep source pages factual and synthesis pages interpretive.\n- Add decisions to [[Decision Log]].\n\n## Retrieval conventions\n- Prefer maintained wiki pages over raw source fragments.\n- Use context packs when answering multi-page questions.\n"
            schema_path.write_text(default, encoding='utf-8')
        return {'path': str(schema_path), 'body': schema_path.read_text(encoding='utf-8')}

    def dry_run_write(self, title: str, body: str, mode: str = 'replace') -> Dict[str, Any]:
        """Preview a write and run retrievability lint without changing files."""
        title=safe_slug(title)
        current=''
        if self.page_path(title).exists():
            current=self.read_page(title)['body']
        if mode=='append': preview=current.rstrip()+'\n\n'+body.strip()+'\n'
        elif mode=='prepend': preview=body.strip()+'\n\n'+current.lstrip()
        else: preview=body.strip()+'\n'
        warnings=[]
        wc=len(plain_words(preview))
        if wc<50: warnings.append('doc-too-short: consider adding enough context for retrieval')
        if wc>1800: warnings.append('doc-too-long: consider splitting into linked sub-pages')
        for para in preview.split('\n\n'):
            if len(para)>1500: warnings.append('long-paragraph: split long paragraphs for embedding/search quality')
        links=wiki_links(preview); existing={p.stem for p in self.cfg.wiki_dir.glob('*.md')}
        broken=[l for l in links if safe_slug(l) not in existing and l not in existing and safe_slug(l)!=title]
        if broken: warnings.append('broken-links: '+', '.join(broken[:10]))
        return {'title': title, 'mode': mode, 'would_create': not self.page_path(title).exists(), 'word_count': wc, 'links': links, 'warnings': warnings, 'ok': not warnings, 'preview': preview[:4000]}

    def related(self, title: str, limit: int = 5) -> Dict[str, Any]:
        """Find related pages using shared terms and links. Lightweight fallback for semantic relatedness."""
        page=self.read_page(title); words=set(plain_words(page['body'])); links=set(page['links'])
        scores=[]
        for p in self.cfg.wiki_dir.glob('*.md'):
            if p.stem==page['title']: continue
            other=self.read_page(p.stem)
            ow=set(plain_words(other['body'])); ol=set(other['links'])
            score=len(words & ow) + 10*len(links & ({other['title']}|ol)) + (10 if page['title'] in ol else 0)
            if score:
                scores.append({'title': other['title'], 'score': score, 'shared_terms': sorted(list(words & ow))[:12], 'shared_links': sorted(list(links & ol))})
        scores.sort(key=lambda x:x['score'], reverse=True)
        return {'title': page['title'], 'related': scores[:limit]}

    def health_report(self) -> Dict[str, Any]:
        """Implement the health report operation for the local LLM Wiki workflow."""
        st=self.status(); lint=self.lint(); graph=self.graph_links(); cats=self.categories()
        density=graph['edge_count']/max(graph['node_count'],1)
        return {'status': st, 'lint': lint, 'categories': cats, 'link_density': density, 'pain_points': {'broken_link_count': len(lint['broken_links']), 'orphan_count': len(lint['orphans']), 'short_page_count': len(lint['very_short_pages']), 'notes': ['High orphan count means the wiki is becoming a pile of notes rather than a graph.', 'Very short pages are weak retrieval units.', 'Use dry-run before agent writes, then rename/delete with link maintenance.']}}

STORE: Optional[WikiStore] = None

def store() -> WikiStore:
    """Implement the store operation for the local LLM Wiki workflow."""
    global STORE
    if STORE is None:
        STORE = WikiStore(CONFIG)
    return STORE

# -----------------------------------------------------------------------------
# Tool wrappers
# -----------------------------------------------------------------------------



def tool_wiki_repair_lint(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki repair lint operation for the local LLM Wiki workflow."""
    return store().repair_lint(apply=bool(arguments.get('apply', False)), fix_broken=bool(arguments.get('fix_broken', True)), link_orphans=bool(arguments.get('link_orphans', True)), expand_short=bool(arguments.get('expand_short', True)), create_missing=bool(arguments.get('create_missing', False)), index_page=arguments.get('index_page','index'))

def tool_wiki_list_pages(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki list pages operation for the local LLM Wiki workflow."""
    return store().list_pages(category=arguments.get('category'), tag=arguments.get('tag'), limit=int(arguments.get('limit',200)))

def tool_wiki_resolve(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki resolve operation for the local LLM Wiki workflow."""
    return store().resolve(arguments['handle'], limit=int(arguments.get('limit',5)))

def tool_wiki_backlinks(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki backlinks operation for the local LLM Wiki workflow."""
    return store().backlinks(arguments['title'])

def tool_wiki_rename_page(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki rename page operation for the local LLM Wiki workflow."""
    return store().rename_page(arguments['old_title'], arguments['new_title'], update_links=bool(arguments.get('update_links', True)))

def tool_wiki_delete_page(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki delete page operation for the local LLM Wiki workflow."""
    return store().delete_page(arguments['title'], tombstone=bool(arguments.get('tombstone', True)))

def tool_wiki_categories(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki categories operation for the local LLM Wiki workflow."""
    return store().categories()

def tool_wiki_toc(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki toc operation for the local LLM Wiki workflow."""
    return store().toc()

def tool_wiki_schema(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki schema operation for the local LLM Wiki workflow."""
    return store().schema_doc(update=bool(arguments.get('update', False)), body=arguments.get('body'))

def tool_wiki_dry_run_write(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki dry run write operation for the local LLM Wiki workflow."""
    return store().dry_run_write(arguments['title'], arguments.get('body',''), mode=arguments.get('mode','replace'))

def tool_wiki_related(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki related operation for the local LLM Wiki workflow."""
    return store().related(arguments['title'], limit=int(arguments.get('limit',5)))

def tool_wiki_health_report(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki health report operation for the local LLM Wiki workflow."""
    return store().health_report()

def tool_wiki_init(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki init operation for the local LLM Wiki workflow."""
    if 'vault' in arguments:
        set_vault(arguments['vault'])
        global STORE; STORE = None
    return store().init_seed()

def tool_wiki_status(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki status operation for the local LLM Wiki workflow."""
    return store().status()

def tool_wiki_create_page(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki create page operation for the local LLM Wiki workflow."""
    return store().create_page(arguments['title'], arguments.get('body',''), tags=arguments.get('tags') or [], source=arguments.get('source','mcp'), overwrite=bool(arguments.get('overwrite', False)))

def tool_wiki_read_page(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki read page operation for the local LLM Wiki workflow."""
    return store().read_page(arguments['title'])

def tool_wiki_update_page(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki update page operation for the local LLM Wiki workflow."""
    return store().update_page(arguments['title'], arguments.get('body',''), mode=arguments.get('mode','replace'))

def tool_wiki_append_section(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki append section operation for the local LLM Wiki workflow."""
    return store().append_section(arguments['title'], arguments.get('heading','Notes'), arguments.get('content',''))

def tool_wiki_search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Search or retrieve wiki content for tool wiki search."""
    return store().search(arguments['query'], limit=int(arguments.get('limit',10)))

def tool_wiki_search_diagnostics(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Search or retrieve wiki content for tool wiki search diagnostics."""
    return store().search_diagnostics(arguments['query'], limit=int(arguments.get('limit',8)))

def tool_wiki_reindex(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki reindex operation for the local LLM Wiki workflow."""
    return store().reindex()

def tool_wiki_ingest_file(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest source content into Markdown wiki pages for tool wiki ingest file."""
    return store().ingest_file(arguments['path'], title=arguments.get('title'), copy_raw=bool(arguments.get('copy_raw', True)))

def tool_wiki_ingest_directory(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest source content into Markdown wiki pages for tool wiki ingest directory."""
    return store().ingest_directory(arguments['directory'], pattern=arguments.get('pattern','*.md'), recursive=bool(arguments.get('recursive', True)), limit=int(arguments.get('limit',100)))

def tool_wiki_import_transcript(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki import transcript operation for the local LLM Wiki workflow."""
    return store().import_transcript(arguments['transcript'], title=arguments.get('title','Imported Transcript'), speaker_prefixes=arguments.get('speaker_prefixes'))

def tool_wiki_retrieve_articles(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Search or retrieve wiki content for tool wiki retrieve articles."""
    return store().retrieve_articles(arguments.get('prompt') or arguments.get('query') or '', top_k=int(arguments.get('top_k', arguments.get('limit', 5))), max_chars_per_article=int(arguments.get('max_chars_per_article', 4000)), max_total_chars=int(arguments.get('max_total_chars', 12000)), include_metadata=bool(arguments.get('include_metadata', True)))


def tool_wiki_config(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Read, write, or update local wiki configuration for tool wiki config."""
    action = str(arguments.get('action', 'show')).lower()
    if action in {'show', 'get', 'read'}:
        return store().config()
    if action in {'set', 'update'}:
        return store().config_set(str(arguments.get('key')), arguments.get('value'))
    if action == 'reset':
        return store().config_reset()
    if action == 'test':
        return store().config_test()
    return {'ok': False, 'error': f'Unknown config action: {action}', 'valid_actions': ['show','set','reset','test']}

def tool_wiki_ask_ollama(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Build or execute the local LLM ask workflow for tool wiki ask ollama."""
    return store().ask_ollama(
        arguments.get('question') or arguments.get('prompt') or '',
        top_k=arguments.get('top_k'),
        model=arguments.get('model'),
        host=arguments.get('host'),
        temperature=arguments.get('temperature'),
        timeout_seconds=arguments.get('timeout_seconds'),
        max_context_chars=arguments.get('max_context_chars'),
        max_chars_per_article=arguments.get('max_chars_per_article'),
        dry_run=bool(arguments.get('dry_run', False)),
    )

def tool_wiki_build_context_pack(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki build context pack operation for the local LLM Wiki workflow."""
    return store().build_context_pack(arguments['query'], limit=int(arguments.get('limit',5)), max_chars=int(arguments.get('max_chars',8000)))

def tool_wiki_graph_links(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create graph-oriented output for tool wiki graph links."""
    return store().graph_links()

def tool_wiki_lint(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki lint operation for the local LLM Wiki workflow."""
    return store().lint()

def tool_wiki_mermaid_graph(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create graph-oriented output for tool wiki mermaid graph."""
    return store().mermaid_graph(direction=arguments.get('direction','TD'), include_orphans=bool(arguments.get('include_orphans', True)), max_edges=int(arguments.get('max_edges', 200)), output_path=arguments.get('output_path'))

def tool_wiki_mermaid_neighbourhood(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Create graph-oriented output for tool wiki mermaid neighbourhood."""
    return store().mermaid_neighbourhood(arguments['title'], depth=int(arguments.get('depth', 1)), direction=arguments.get('direction','LR'), output_path=arguments.get('output_path'))

def tool_wiki_export_llms_txt(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki export llms txt operation for the local LLM Wiki workflow."""
    return store().export_llms_txt(output_path=arguments.get('output_path'), max_chars=int(arguments.get('max_chars',60000)))

def tool_wiki_log_decision(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Implement the tool wiki log decision operation for the local LLM Wiki workflow."""
    return store().log_decision(arguments['title'], arguments['decision'], rationale=arguments.get('rationale',''), links=arguments.get('links') or [])

TOOL_HANDLERS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    'wiki_init': tool_wiki_init,
    'wiki_status': tool_wiki_status,
    'wiki_create_page': tool_wiki_create_page,
    'wiki_read_page': tool_wiki_read_page,
    'wiki_update_page': tool_wiki_update_page,
    'wiki_append_section': tool_wiki_append_section,
    'wiki_search': tool_wiki_search,
    'wiki_search_diagnostics': tool_wiki_search_diagnostics,
    'wiki_retrieve_articles': tool_wiki_retrieve_articles,
    'wiki_ask_ollama': tool_wiki_ask_ollama,
    'wiki_config': tool_wiki_config,
    'wiki_config_test': lambda arguments: store().config_test(),
    'wiki_reindex': tool_wiki_reindex,
    'wiki_ingest_file': tool_wiki_ingest_file,
    'wiki_ingest_directory': tool_wiki_ingest_directory,
    'wiki_import_transcript': tool_wiki_import_transcript,
    'wiki_build_context_pack': tool_wiki_build_context_pack,
    'wiki_graph_links': tool_wiki_graph_links,
    'wiki_lint': tool_wiki_lint,
    'wiki_repair_lint': tool_wiki_repair_lint,
    'wiki_export_llms_txt': tool_wiki_export_llms_txt,
    'wiki_log_decision': tool_wiki_log_decision,
    'wiki_list_pages': tool_wiki_list_pages,
    'wiki_resolve': tool_wiki_resolve,
    'wiki_backlinks': tool_wiki_backlinks,
    'wiki_rename_page': tool_wiki_rename_page,
    'wiki_delete_page': tool_wiki_delete_page,
    'wiki_categories': tool_wiki_categories,
    'wiki_toc': tool_wiki_toc,
    'wiki_schema': tool_wiki_schema,
    'wiki_dry_run_write': tool_wiki_dry_run_write,
    'wiki_related': tool_wiki_related,
    'wiki_health_report': tool_wiki_health_report,
    'wiki_mermaid_graph': tool_wiki_mermaid_graph,
    'wiki_mermaid_neighbourhood': tool_wiki_mermaid_neighbourhood,
}

TOOL_DEFS: List[Dict[str, Any]] = [
    {'name':'wiki_init','description':'Initialise the local Markdown wiki vault with seed pages and SQLite index.','inputSchema':{'type':'object','properties':{'vault':{'type':'string'}},'required':[]}},
    {'name':'wiki_status','description':'Return vault paths, page counts, raw counts, estimated word count, and index status.','inputSchema':{'type':'object','properties':{},'required':[]}},
    {'name':'wiki_create_page','description':'Create a wiki page with YAML-style front matter.','inputSchema':{'type':'object','properties':{'title':{'type':'string'},'body':{'type':'string'},'tags':{'type':'array','items':{'type':'string'}},'source':{'type':'string'},'overwrite':{'type':'boolean'}},'required':['title','body']}},
    {'name':'wiki_read_page','description':'Read a wiki page by title, including metadata and outgoing wiki links.','inputSchema':{'type':'object','properties':{'title':{'type':'string'}},'required':['title']}},
    {'name':'wiki_update_page','description':'Replace, append, or prepend content on an existing wiki page.','inputSchema':{'type':'object','properties':{'title':{'type':'string'},'body':{'type':'string'},'mode':{'type':'string','enum':['replace','append','prepend']}},'required':['title','body']}},
    {'name':'wiki_append_section','description':'Append a headed section to a wiki page.','inputSchema':{'type':'object','properties':{'title':{'type':'string'},'heading':{'type':'string'},'content':{'type':'string'}},'required':['title','content']}},
    {'name':'wiki_search','description':'Search wiki pages using SQLite FTS with prefix, singular/plural expansion, and fallback token scoring.','inputSchema':{'type':'object','properties':{'query':{'type':'string'},'limit':{'type':'integer'}},'required':['query']}},
    {'name':'wiki_search_diagnostics','description':'Explain how a query is normalised and show suggestions when search results are surprising.','inputSchema':{'type':'object','properties':{'query':{'type':'string'},'limit':{'type':'integer'}},'required':['query']}},
    {'name':'wiki_retrieve_articles','description':'Given a prompt/query, search the wiki and retrieve the top-k full maintained articles plus an LLM-ready context block.','inputSchema':{'type':'object','properties':{'prompt':{'type':'string'},'query':{'type':'string'},'top_k':{'type':'integer'},'limit':{'type':'integer'},'max_chars_per_article':{'type':'integer'},'max_total_chars':{'type':'integer'},'include_metadata':{'type':'boolean'}},'required':[]}},
    {'name':'wiki_ask_ollama','description':'Prompt -> retrieve wiki context -> ask a local Ollama model using configurable host/model.','inputSchema':{'type':'object','properties':{'question':{'type':'string'},'prompt':{'type':'string'},'top_k':{'type':'integer'},'model':{'type':'string'},'host':{'type':'string'},'temperature':{'type':'number'},'timeout_seconds':{'type':'integer'},'max_context_chars':{'type':'integer'},'max_chars_per_article':{'type':'integer'},'dry_run':{'type':'boolean'}},'required':[]}},
    {'name':'wiki_config','description':'Create/read/update/test the llm_wiki_config.json file containing Ollama host/model defaults.','inputSchema':{'type':'object','properties':{'action':{'type':'string'},'key':{'type':'string'},'value':{}},'required':[]}},
    {'name':'wiki_reindex','description':'Rebuild the SQLite index from Markdown files.','inputSchema':{'type':'object','properties':{},'required':[]}},
    {'name':'wiki_ingest_file','description':'Ingest a Markdown/text file into the wiki as a source page.','inputSchema':{'type':'object','properties':{'path':{'type':'string'},'title':{'type':'string'},'copy_raw':{'type':'boolean'}},'required':['path']}},
    {'name':'wiki_ingest_directory','description':'Bulk ingest Markdown, TXT, RTF, PDF, DOCX, and legacy DOC stub content from a directory or one supported file.','inputSchema':{'type':'object','properties':{'directory':{'type':'string'},'pattern':{'type':'string'},'recursive':{'type':'boolean'},'limit':{'type':'integer'}},'required':['directory']}},
    {'name':'wiki_import_transcript','description':'Convert a transcript or long chat into a durable wiki page.','inputSchema':{'type':'object','properties':{'transcript':{'type':'string'},'title':{'type':'string'},'speaker_prefixes':{'type':'array','items':{'type':'string'}}},'required':['transcript']}},
    {'name':'wiki_build_context_pack','description':'Build a bounded context pack from the most relevant wiki pages.','inputSchema':{'type':'object','properties':{'query':{'type':'string'},'limit':{'type':'integer'},'max_chars':{'type':'integer'}},'required':['query']}},
    {'name':'wiki_graph_links','description':'Return wiki nodes, outgoing edges, and backlinks from [[wiki-links]].','inputSchema':{'type':'object','properties':{},'required':[]}},
    {'name':'wiki_lint','description':'Check for broken links, orphan pages, and very short pages.','inputSchema':{'type':'object','properties':{},'required':[]}},
    {'name':'wiki_repair_lint','description':'Plan or apply safe repairs for broken links, orphan pages, and short pages. Dry-run by default.','inputSchema':{'type':'object','properties':{'apply':{'type':'boolean'},'fix_broken':{'type':'boolean'},'link_orphans':{'type':'boolean'},'expand_short':{'type':'boolean'},'create_missing':{'type':'boolean'},'index_page':{'type':'string'}},'required':[]}},
    {'name':'wiki_export_llms_txt','description':'Export the wiki into an llms.txt style context file.','inputSchema':{'type':'object','properties':{'output_path':{'type':'string'},'max_chars':{'type':'integer'}},'required':[]}},
    {'name':'wiki_log_decision','description':'Log an architectural or project decision into SQLite and the Decision Log page.','inputSchema':{'type':'object','properties':{'title':{'type':'string'},'decision':{'type':'string'},'rationale':{'type':'string'},'links':{'type':'array','items':{'type':'string'}}},'required':['title','decision']}},
    {'name':'wiki_list_pages','description':'List pages with metadata, optional tag/category filters.','inputSchema':{'type':'object','properties':{'category':{'type':'string'},'tag':{'type':'string'},'limit':{'type':'integer'}},'required':[]}},
    {'name':'wiki_resolve','description':'Resolve loose document handles to canonical wiki titles with suggestions.','inputSchema':{'type':'object','properties':{'handle':{'type':'string'},'limit':{'type':'integer'}},'required':['handle']}},
    {'name':'wiki_backlinks','description':'Return incoming and outgoing links for a page.','inputSchema':{'type':'object','properties':{'title':{'type':'string'}},'required':['title']}},
    {'name':'wiki_rename_page','description':'Rename a page and optionally update [[wiki-links]] across the vault.','inputSchema':{'type':'object','properties':{'old_title':{'type':'string'},'new_title':{'type':'string'},'update_links':{'type':'boolean'}},'required':['old_title','new_title']}},
    {'name':'wiki_delete_page','description':'Delete a page with optional tombstone backup and report inbound links.','inputSchema':{'type':'object','properties':{'title':{'type':'string'},'tombstone':{'type':'boolean'}},'required':['title']}},
    {'name':'wiki_categories','description':'List categories and tags in use.','inputSchema':{'type':'object','properties':{},'required':[]}},
    {'name':'wiki_toc','description':'Generate/update a Table of Contents wiki page.','inputSchema':{'type':'object','properties':{},'required':[]}},
    {'name':'wiki_schema','description':'Read or update the wiki schema/conventions document.','inputSchema':{'type':'object','properties':{'update':{'type':'boolean'},'body':{'type':'string'}},'required':[]}},
    {'name':'wiki_dry_run_write','description':'Preview a create/update and lint it without writing.','inputSchema':{'type':'object','properties':{'title':{'type':'string'},'body':{'type':'string'},'mode':{'type':'string','enum':['replace','append','prepend']}},'required':['title','body']}},
    {'name':'wiki_related','description':'Find related pages using shared terms and links.','inputSchema':{'type':'object','properties':{'title':{'type':'string'},'limit':{'type':'integer'}},'required':['title']}},
    {'name':'wiki_health_report','description':'Summarise index, lint, graph density, and operational pain points.','inputSchema':{'type':'object','properties':{},'required':[]}},
    {'name':'wiki_mermaid_graph','description':'Render the wiki document-link graph as Mermaid flowchart text, optionally writing a Markdown file.','inputSchema':{'type':'object','properties':{'direction':{'type':'string'},'include_orphans':{'type':'boolean'},'max_edges':{'type':'integer'},'output_path':{'type':'string'}},'required':[]}},
    {'name':'wiki_mermaid_neighbourhood','description':'Render a Mermaid graph centred on a page and its nearby incoming/outgoing links.','inputSchema':{'type':'object','properties':{'title':{'type':'string'},'depth':{'type':'integer'},'direction':{'type':'string'},'output_path':{'type':'string'}},'required':['title']}},
]

# -----------------------------------------------------------------------------
# Official MCP SDK transport, based on the attached EML MCP shape
# -----------------------------------------------------------------------------

def _require_official_mcp() -> Dict[str, Any]:
    """Internal helper for require official mcp."""
    try:
        import mcp.server.stdio as mcp_server_stdio
        import mcp.types as mcp_types
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        from mcp.server.lowlevel import NotificationOptions, Server
        from mcp.server.models import InitializationOptions
    except Exception as exc:
        raise RuntimeError('Official `mcp` package support is required for server/test modes. Install with: pip install -e .[mcp]') from exc
    return {'mcp_server_stdio':mcp_server_stdio,'types':mcp_types,'ClientSession':ClientSession,'StdioServerParameters':StdioServerParameters,'stdio_client':stdio_client,'NotificationOptions':NotificationOptions,'Server':Server,'InitializationOptions':InitializationOptions}

def _model_to_jsonable(value: Any) -> Any:
    """Internal helper for model to jsonable."""
    if hasattr(value, 'model_dump'):
        try:
            return value.model_dump(mode='json')
        except TypeError:
            return value.model_dump()
    if isinstance(value, dict):
        return {k:_model_to_jsonable(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [_model_to_jsonable(v) for v in value]
    return value

class OfficialSDKHarnessClient:
    """Represent the Official SDKHarness Client component used by the local wiki runtime."""
    def __init__(self, session: Any, loop: Any):
        """Internal helper for init."""
        self.session=session; self.loop=loop
    async def _request_async(self, method: str, params: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """Internal helper for request async."""
        params=params or {}
        if method=='initialize': return _model_to_jsonable(await self.session.initialize())
        if method=='tools/list': return _model_to_jsonable(await self.session.list_tools())
        if method=='tools/call': return _model_to_jsonable(await self.session.call_tool(params['name'], params.get('arguments') or {}))
        if method=='shutdown': return {}
        raise KeyError(f'Unknown method: {method}')
    def request(self, method: str, params: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """Implement the request operation for the local LLM Wiki workflow."""
        future=asyncio.run_coroutine_threadsafe(self._request_async(method, params or {}), self.loop)
        return future.result()
    def notify(self, method: str, params: Optional[Dict[str, Any]]=None) -> None:
        """Implement the notify operation for the local LLM Wiki workflow."""
        return None

def build_official_mcp_server() -> Any:
    """Implement the build official mcp server operation for the local LLM Wiki workflow."""
    sdk=_require_official_mcp(); mcp_types=sdk['types']; Server=sdk['Server']
    server=Server('llm-wiki-mcp-release')
    @server.list_tools()  # type: ignore[no-untyped-call]
    async def list_tools() -> List[Any]:
        """Implement the list tools operation for the local LLM Wiki workflow."""
        tools=[]
        for item in TOOL_DEFS:
            tools.append(mcp_types.Tool(name=_helper_exposed_name(item['name']), description=item.get('description',''), inputSchema=item.get('inputSchema') or {'type':'object','properties':{},'required':[]}))
        logger.info('Listed %d tools via official MCP SDK', len(tools))
        return tools
    @server.call_tool()  # type: ignore[no-untyped-call]
    async def call_tool(name: str, arguments: Dict[str, Any]) -> Any:
        """Implement the call tool operation for the local LLM Wiki workflow."""
        internal_name=_helper_strip_namespace(name)
        if internal_name not in TOOL_HANDLERS:
            raise ValueError(f'Unknown tool: {name}')
        try:
            structured=TOOL_HANDLERS[internal_name](arguments or {})
            text=json.dumps(structured, indent=2, ensure_ascii=False, default=str)
            return mcp_types.CallToolResult(content=[mcp_types.TextContent(type='text', text=text)], structuredContent=structured, isError=False)
        except Exception as exc:
            logger.exception('Tool call failed: %s', name)
            return mcp_types.CallToolResult(content=[mcp_types.TextContent(type='text', text=f'{type(exc).__name__}: {exc}')], structuredContent={'error': str(exc), 'tool': name}, isError=True)
    return server

async def run_stdio_server_async() -> None:
    """Implement the run stdio server async operation for the local LLM Wiki workflow."""
    sdk=_require_official_mcp(); NotificationOptions=sdk['NotificationOptions']; InitializationOptions=sdk['InitializationOptions']
    server=build_official_mcp_server()
    logger.info('LLM Wiki MCP release server starting on stdio')
    async with sdk['mcp_server_stdio'].stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, InitializationOptions(server_name='llm-wiki-mcp-release', server_version="0.1.0", capabilities=server.get_capabilities(notification_options=NotificationOptions(), experimental_capabilities={})))

# -----------------------------------------------------------------------------
# Test harness and examples
# -----------------------------------------------------------------------------

def _extract_structured_content(call_result: Dict[str, Any]) -> Dict[str, Any]:
    """Internal helper for extract structured content."""
    if isinstance(call_result, dict):
        if 'structuredContent' in call_result: return call_result['structuredContent']
        if 'result' in call_result and isinstance(call_result['result'], dict) and 'structuredContent' in call_result['result']: return call_result['result']['structuredContent']
    return call_result

class LocalHarnessClient:
    """Represent the Local Harness Client component used by the local wiki runtime."""
    def request(self, method: str, params: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        """Implement the request operation for the local LLM Wiki workflow."""
        params=params or {}
        if method=='tools/list': return {'tools': [{'name': _helper_exposed_name(t['name']), 'description': t['description'], 'inputSchema': t['inputSchema']} for t in TOOL_DEFS]}
        if method=='tools/call': return {'structuredContent': TOOL_HANDLERS[_helper_strip_namespace(params['name'])](params.get('arguments') or {})}
        if method=='initialize': return {'ok': True}
        return {}

    def notify(self, method: str, params: Optional[Dict[str, Any]]=None) -> None:
        """Accept notifications used by the local regression harness."""
        return None

def run_regression_suite(client: Any) -> Dict[str, Any]:
    """Implement the run regression suite operation for the local LLM Wiki workflow."""
    results=[]
    tools_resp=client.request('tools/list'); tools=tools_resp['tools']; names={row['name'] for row in tools}
    expected={_helper_exposed_name(n) for n in TOOL_HANDLERS}
    results.append({'name':'tools_list_expected_surface','pass':names==expected,'details':{'count':len(names),'names':sorted(names)}})
    init=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_init'), 'arguments':{}}))
    results.append({'name':'wiki_init_seed','pass':init.get('page_count',0)>=6,'details':init})
    create=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_create_page'), 'arguments':{'title':'Agent Memory','body':'# Agent Memory\n\nLLM Wiki stores durable [[Knowledge]] as Markdown pages.','overwrite':True,'tags':['test']}}))
    results.append({'name':'wiki_create_page','pass':create.get('created') is True,'details':create})
    read=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_read_page'), 'arguments':{'title':'Agent Memory'}}))
    results.append({'name':'wiki_read_page_links','pass':'Knowledge' in read.get('links',[]),'details':read})
    search=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_search'), 'arguments':{'query':'durable Markdown memory','limit':5}}))
    results.append({'name':'wiki_search_finds_page','pass':any(r['title']=='Agent Memory' for r in search.get('results',[])),'details':search})
    ctx=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_build_context_pack'), 'arguments':{'query':'durable Markdown memory','limit':3,'max_chars':3000}}))
    results.append({'name':'wiki_context_pack','pass':'Agent Memory' in ctx.get('context_pack',''),'details':{'titles':ctx.get('page_titles'), 'chars':ctx.get('chars')}})
    dec=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_log_decision'), 'arguments':{'title':'Use Markdown as source of truth','decision':'Use wiki pages for durable knowledge','rationale':'Less brittle than one-off retrieved chunks','links':['Agent Memory']}}))
    results.append({'name':'wiki_log_decision','pass':dec.get('id',0)>=1,'details':dec})
    graph=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_graph_links'), 'arguments':{}}))
    results.append({'name':'wiki_graph_links','pass':graph.get('node_count',0)>=6,'details':{'nodes':graph.get('node_count'),'edges':graph.get('edge_count')}})
    lint=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_lint'), 'arguments':{}}))
    results.append({'name':'wiki_lint_runs','pass':'broken_links' in lint,'details':lint})
    rep=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_repair_lint'), 'arguments':{'apply':False}}))
    results.append({'name':'wiki_repair_lint_dry_run','pass':rep.get('dry_run') is True and 'actions' in rep,'details':{'actions':rep.get('action_count')}})
    mer=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_mermaid_graph'), 'arguments':{'direction':'LR','max_edges':50}}))
    results.append({'name':'wiki_mermaid_graph','pass':'flowchart LR' in mer.get('mermaid',''),'details':{'nodes':mer.get('node_count'),'edges':mer.get('edge_count')}})
    nb=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_mermaid_neighbourhood'), 'arguments':{'title':'index','depth':1}}))
    results.append({'name':'wiki_mermaid_neighbourhood','pass':'flowchart LR' in nb.get('mermaid','') and nb.get('node_count',0)>=1,'details':{'nodes':nb.get('node_count'),'edges':nb.get('edge_count')}})
    exp=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_export_llms_txt'), 'arguments':{'max_chars':10000}}))
    results.append({'name':'wiki_export_llms_txt','pass':Path(exp.get('output_path','')).exists(),'details':exp})
    dry=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_dry_run_write'), 'arguments':{'title':'Draft Page','body':'# Draft Page\n\nThis preview references [[Agent Memory]] and has enough words to show the dry run validation process for agent-written pages before any write touches disk. It lets an agent check retrievability and links first.'}}))
    results.append({'name':'wiki_dry_run_write','pass':dry.get('would_create') is True and 'Agent Memory' in dry.get('links',[]),'details':dry})
    listing=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_list_pages'), 'arguments':{'limit':20}}))
    results.append({'name':'wiki_list_pages','pass':listing.get('count',0)>=6,'details':{'count':listing.get('count')}})
    res=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_resolve'), 'arguments':{'handle':'agent-memory.md'}}))
    results.append({'name':'wiki_resolve','pass':res.get('canonical_title')=='Agent Memory','details':res})
    bkl=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_backlinks'), 'arguments':{'title':'Agent Memory'}}))
    results.append({'name':'wiki_backlinks','pass':'Decision Log' in bkl.get('incoming',[]) or isinstance(bkl.get('incoming'), list),'details':bkl})
    rel=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_related'), 'arguments':{'title':'Agent Memory','limit':3}}))
    results.append({'name':'wiki_related','pass':'related' in rel,'details':rel})
    toc=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_toc'), 'arguments':{}}))
    results.append({'name':'wiki_toc','pass':toc.get('items',0)>=6,'details':{'items':toc.get('items')}})
    schema=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_schema'), 'arguments':{}}))
    results.append({'name':'wiki_schema','pass':'Page conventions' in schema.get('body',''),'details':{'path':schema.get('path')}})
    cats=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_categories'), 'arguments':{}}))
    results.append({'name':'wiki_categories','pass':'tags' in cats,'details':cats})
    health=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_health_report'), 'arguments':{}}))
    results.append({'name':'wiki_health_report','pass':'pain_points' in health,'details':{'link_density':health.get('link_density'), 'pain_points':health.get('pain_points')}})
    rn=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_create_page'), 'arguments':{'title':'Rename Source','body':'# Rename Source\n\nThis links to [[Agent Memory]].','overwrite':True}}))
    ren=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_rename_page'), 'arguments':{'old_title':'Rename Source','new_title':'Renamed Source'}}))
    results.append({'name':'wiki_rename_page','pass':ren.get('new_title')=='Renamed Source','details':ren})
    dele=_extract_structured_content(client.request('tools/call', {'name':_helper_exposed_name('wiki_delete_page'), 'arguments':{'title':'Renamed Source','tombstone':True}}))
    results.append({'name':'wiki_delete_page','pass':dele.get('deleted') is True,'details':dele})
    passed=sum(1 for r in results if r['pass'])
    return {'total_cases':len(results),'passed_cases':passed,'failed_cases':len(results)-passed,'all_passed':passed==len(results),'results':results}

async def _run_test_harness_async(script_path: str) -> int:
    """Internal helper for run test harness async."""
    sdk=_require_official_mcp(); StdioServerParameters=sdk['StdioServerParameters']; stdio_client=sdk['stdio_client']; ClientSession=sdk['ClientSession']
    params=StdioServerParameters(command=sys.executable, args=[script_path, 'server', '--vault', str(CONFIG.vault)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            adapter=OfficialSDKHarnessClient(session, asyncio.get_running_loop())
            suite=await asyncio.to_thread(run_regression_suite, adapter)
            print(json.dumps(suite, indent=2, ensure_ascii=False, default=str))
            return 0 if suite['all_passed'] else 1

def run_direct_examples() -> int:
    """Implement the run direct examples operation for the local LLM Wiki workflow."""
    client=LocalHarnessClient()
    suite=run_regression_suite(client)
    print(json.dumps(suite, indent=2, ensure_ascii=False, default=str))
    return 0 if suite['all_passed'] else 1

def main(argv: Optional[Sequence[str]]=None) -> int:
    """Implement the main operation for the local LLM Wiki workflow."""
    parser=argparse.ArgumentParser(description='LLM Wiki MCP release server and harness')
    parser.add_argument('mode', nargs='?', default='local-test', choices=['server','test','local-test','examples','all'])
    parser.add_argument('--vault', default=os.environ.get('LLM_WIKI_VAULT','./wiki_vault'))
    args=parser.parse_args(argv)
    set_vault(args.vault)
    try:
        if args.mode=='server':
            asyncio.run(run_stdio_server_async()); return 0
        if args.mode in {'examples','local-test'}:
            return run_direct_examples()
        if args.mode=='test':
            return asyncio.run(_run_test_harness_async(str(Path(__file__).resolve())))
        if args.mode=='all':
            rc1=run_direct_examples(); rc2=asyncio.run(_run_test_harness_async(str(Path(__file__).resolve())))
            return 0 if rc1==0 and rc2==0 else 1
        return run_direct_examples()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr); return 1

if __name__ == '__main__':
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# Release local tool additions
# ---------------------------------------------------------------------------
try:
    from llm_wiki_mcp.context_api import tool_self_question_context, wiki_usage_snapshot
except Exception:
    tool_self_question_context = None
    wiki_usage_snapshot = None

def tool_wiki_tool_self_question(arguments):
    """Implement the tool wiki tool self question operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    question = arguments.get("question") or "What can this tool tell me about itself?"
    if tool_self_question_context is None:
        return {"ok": False, "error": "tool_self_question_context unavailable"}
    out = tool_self_question_context(vault, question)
    out["ok"] = True
    return out

def tool_wiki_usage_snapshot(arguments):
    """Inspect runtime history, token metrics, or usage state for tool wiki usage snapshot."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    if wiki_usage_snapshot is None:
        return {"ok": False, "error": "wiki_usage_snapshot unavailable"}
    out = wiki_usage_snapshot(vault)
    out["ok"] = True
    return out

try:
    TOOL_HANDLERS["wiki_tool_self_question"] = tool_wiki_tool_self_question
    TOOL_HANDLERS["wiki_usage_snapshot"] = tool_wiki_usage_snapshot
    TOOL_DEFS.append({
        "name": "wiki_tool_self_question",
        "description": "Ask the LLM Wiki tool about itself by building a self-describing context block from config, docs, and wiki files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vault_path": {"type": "string"},
                "question": {"type": "string"}
            },
            "required": []
        }
    })
    TOOL_DEFS.append({
        "name": "wiki_usage_snapshot",
        "description": "Estimate wiki size and token usage for the current vault.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vault_path": {"type": "string"}
            },
            "required": []
        }
    })
except Exception:
    pass


# Release recursive ask/config MCP tools
try:
    from llm_wiki_mcp.context_api import (
        release_load_config,
        release_set_config_value,
        release_recursive_ask_preview,
        release_load_history,
    )
except Exception:
    release_load_config = release_set_config_value = release_recursive_ask_preview = release_load_history = None

def tool_wiki_config_load(arguments):
    """Read, write, or update local wiki configuration for tool wiki config load."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {
        "ok": True,
        "config": release_load_config(vault),
        "config_path": str(__import__("pathlib").Path(vault) / "llm_wiki_config.json")
    }

def tool_wiki_config_set(arguments):
    """Read, write, or update local wiki configuration for tool wiki config set."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    key = arguments.get("key")
    value = arguments.get("value")
    if not key:
        return {"ok": False, "error": "key is required"}
    return {"ok": True, "key": key, "value": value, "config": release_set_config_value(vault, key, value)}

def tool_wiki_recursive_ask_preview(arguments):
    """Build or execute the local LLM ask workflow for tool wiki recursive ask preview."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    question = arguments.get("question") or arguments.get("prompt") or ""
    return {
        "ok": True,
        **release_recursive_ask_preview(
            vault,
            question,
            arguments.get("base_context", ""),
            arguments.get("recursive")
        )
    }

def tool_wiki_ask_history(arguments):
    """Build or execute the local LLM ask workflow for tool wiki ask history."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, "history": release_load_history(vault, int(arguments.get("limit", 20)))}

try:
    TOOL_HANDLERS["wiki_config_load"] = tool_wiki_config_load
    TOOL_HANDLERS["wiki_config_set"] = tool_wiki_config_set
    TOOL_HANDLERS["wiki_recursive_ask_preview"] = tool_wiki_recursive_ask_preview
    TOOL_HANDLERS["wiki_ask_history"] = tool_wiki_ask_history
    TOOL_DEFS.extend([
        {"name": "wiki_config_load", "description": "Load and persist active vault config defaults.", "inputSchema": {"type": "object", "properties": {"vault_path": {"type": "string"}}, "required": []}},
        {"name": "wiki_config_set", "description": "Persistently set a dotted config key, e.g. ask.recursive_enabled.", "inputSchema": {"type": "object", "properties": {"vault_path": {"type": "string"}, "key": {"type": "string"}, "value": {}}, "required": ["key", "value"]}},
        {"name": "wiki_recursive_ask_preview", "description": "Preview recursive ask context with rolling history compression.", "inputSchema": {"type": "object", "properties": {"vault_path": {"type": "string"}, "question": {"type": "string"}, "base_context": {"type": "string"}, "recursive": {"type": "boolean"}}, "required": ["question"]}},
        {"name": "wiki_ask_history", "description": "Read recent ask history records.", "inputSchema": {"type": "object", "properties": {"vault_path": {"type": "string"}, "limit": {"type": "integer"}}, "required": []}},
    ])
except Exception:
    pass


# Release recursive ask memory MCP tools
try:
    from llm_wiki_mcp.context_api import (
        release_record_ask_turn,
        release_compress_history_if_needed,
        release_recursive_context_with_memory,
        release_read_compressed_history,
    )
except Exception:
    release_record_ask_turn = release_compress_history_if_needed = release_recursive_context_with_memory = release_read_compressed_history = None

def tool_wiki_record_ask_turn(arguments):
    """Build or execute the local LLM ask workflow for tool wiki record ask turn."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_record_ask_turn(
        vault,
        arguments.get("question", ""),
        arguments.get("prompt", ""),
        arguments.get("answer", ""),
        arguments.get("sources", []),
        arguments.get("metadata", {})
    )}

def tool_wiki_compress_history(arguments):
    """Inspect runtime history, token metrics, or usage state for tool wiki compress history."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_compress_history_if_needed(vault)}

def tool_wiki_recursive_context(arguments):
    """Implement the tool wiki recursive context operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_recursive_context_with_memory(
        vault,
        arguments.get("question", ""),
        arguments.get("base_context", "")
    )}

try:
    TOOL_HANDLERS["wiki_record_ask_turn"] = tool_wiki_record_ask_turn
    TOOL_HANDLERS["wiki_compress_history"] = tool_wiki_compress_history
    TOOL_HANDLERS["wiki_recursive_context"] = tool_wiki_recursive_context
    TOOL_DEFS.extend([
        {"name":"wiki_record_ask_turn","description":"Record question, prompt, answer, sources and token estimates into ask history, compressing when needed.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"question":{"type":"string"},"prompt":{"type":"string"},"answer":{"type":"string"},"sources":{"type":"array","items":{"type":"string"}},"metadata":{"type":"object"}},"required":["question","answer"]}},
        {"name":"wiki_compress_history","description":"Compress ask history if the configured token budget is exceeded.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"}},"required":[]}},
        {"name":"wiki_recursive_context","description":"Build recursive context from compressed long-term memory, recent ask memory, retrieved wiki context, and the current question.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"question":{"type":"string"},"base_context":{"type":"string"}},"required":["question"]}},
    ])
except Exception:
    pass


# Self-access, usage and token/s MCP tools
try:
    from llm_wiki_mcp.context_api import (
        release_metrics_summary,
        release_record_llm_metrics,
        release_wiki_usage_snapshot,
        release_self_access_snapshot,
        release_record_ask_turn_with_metrics,
    )
except Exception:
    release_metrics_summary = release_record_llm_metrics = release_wiki_usage_snapshot = release_self_access_snapshot = release_record_ask_turn_with_metrics = None

def tool_wiki_llm_metrics(arguments):
    """Inspect runtime history, token metrics, or usage state for tool wiki llm metrics."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_metrics_summary(vault, int(arguments.get("limit", 100)))}

def tool_wiki_usage_snapshot(arguments):
    """Inspect runtime history, token metrics, or usage state for tool wiki usage snapshot."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_wiki_usage_snapshot(vault)}

def tool_wiki_self_access_snapshot(arguments):
    """Implement the tool wiki self access snapshot operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_self_access_snapshot(vault)}

def tool_wiki_record_ask_turn_with_metrics(arguments):
    """Build or execute the local LLM ask workflow for tool wiki record ask turn with metrics."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_record_ask_turn_with_metrics(
        vault,
        arguments.get("question", ""),
        arguments.get("prompt", ""),
        arguments.get("answer", ""),
        arguments.get("sources", []),
        arguments.get("elapsed_seconds"),
        arguments.get("metadata", {})
    )}

try:
    TOOL_HANDLERS["wiki_llm_metrics"] = tool_wiki_llm_metrics
    TOOL_HANDLERS["wiki_usage_snapshot"] = tool_wiki_usage_snapshot
    TOOL_HANDLERS["wiki_self_access_snapshot"] = tool_wiki_self_access_snapshot
    TOOL_HANDLERS["wiki_record_ask_turn_with_metrics"] = tool_wiki_record_ask_turn_with_metrics
    TOOL_DEFS.extend([
        {"name":"wiki_llm_metrics","description":"Return recorded LLM token/s, latency and token usage metrics.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"limit":{"type":"integer"}},"required":[]}},
        {"name":"wiki_usage_snapshot","description":"Return wiki/page/history token estimates and largest pages.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"}},"required":[]}},
        {"name":"wiki_self_access_snapshot","description":"Return config, usage, metrics, history and compression state for tool self-access.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"}},"required":[]}},
        {"name":"wiki_record_ask_turn_with_metrics","description":"Record question, prompt, answer, sources, elapsed seconds and token/s metrics.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"question":{"type":"string"},"prompt":{"type":"string"},"answer":{"type":"string"},"sources":{"type":"array","items":{"type":"string"}},"elapsed_seconds":{"type":"number"},"metadata":{"type":"object"}},"required":["question","answer"]}},
    ])
except Exception:
    pass


# Runtime/capabilities/reconcile MCP tools
try:
    from llm_wiki_mcp.context_api import (
        release_runtime_capabilities,
        release_load_runtime_journal,
        release_record_runtime_event,
        release_command_tool_map,
        release_reconcile_docs,
        release_runtime_graph_mermaid,
    )
except Exception:
    release_runtime_capabilities = release_load_runtime_journal = release_record_runtime_event = None
    release_command_tool_map = release_reconcile_docs = release_runtime_graph_mermaid = None

def tool_wiki_capabilities(arguments):
    """Implement the tool wiki capabilities operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_runtime_capabilities(vault)}

def tool_wiki_runtime_journal(arguments):
    """Implement the tool wiki runtime journal operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, "events": release_load_runtime_journal(vault, int(arguments.get("limit", 50)))}

def tool_wiki_record_runtime_event(arguments):
    """Implement the tool wiki record runtime event operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, "event": release_record_runtime_event(
        vault,
        arguments.get("command", ""),
        arguments.get("query", ""),
        arguments.get("tools_used", []),
        arguments.get("success", True),
        arguments.get("latency_seconds"),
        arguments.get("token_metrics", {}),
        arguments.get("metadata", {}),
    )}

def tool_wiki_command_tool_map(arguments):
    """Implement the tool wiki command tool map operation for the local LLM Wiki workflow."""
    return {"ok": True, "mapping": release_command_tool_map()}

def tool_wiki_reconcile_docs(arguments):
    """Implement the tool wiki reconcile docs operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_reconcile_docs(vault, arguments.get("project_root"))}

def tool_wiki_runtime_graph(arguments):
    """Create graph-oriented output for tool wiki runtime graph."""
    return {"ok": True, "mermaid": release_runtime_graph_mermaid()}

try:
    TOOL_HANDLERS["wiki_capabilities"] = tool_wiki_capabilities
    TOOL_HANDLERS["wiki_runtime_journal"] = tool_wiki_runtime_journal
    TOOL_HANDLERS["wiki_record_runtime_event"] = tool_wiki_record_runtime_event
    TOOL_HANDLERS["wiki_command_tool_map"] = tool_wiki_command_tool_map
    TOOL_HANDLERS["wiki_reconcile_docs"] = tool_wiki_reconcile_docs
    TOOL_HANDLERS["wiki_runtime_graph"] = tool_wiki_runtime_graph
    TOOL_DEFS.extend([
        {"name":"wiki_capabilities","description":"Return live runtime capabilities: LLM, retrieval, runtime self-access, maintenance, and relevant files.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"}},"required":[]}},
        {"name":"wiki_runtime_journal","description":"Return recent runtime execution journal events.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"limit":{"type":"integer"}},"required":[]}},
        {"name":"wiki_record_runtime_event","description":"Record a runtime event with command, query, tools used, success, latency, and token metrics.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"command":{"type":"string"},"query":{"type":"string"},"tools_used":{"type":"array","items":{"type":"string"}},"success":{"type":"boolean"},"latency_seconds":{"type":"number"},"token_metrics":{"type":"object"},"metadata":{"type":"object"}},"required":[]}},
        {"name":"wiki_command_tool_map","description":"Return the mapping from CLI commands to internal/MCP tools.","inputSchema":{"type":"object","properties":{},"required":[]}},
        {"name":"wiki_reconcile_docs","description":"Compare docs, command surface and function list to identify missing or stale documentation.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"project_root":{"type":"string"}},"required":[]}},
        {"name":"wiki_runtime_graph","description":"Return Mermaid graph of runtime execution flow.","inputSchema":{"type":"object","properties":{},"required":[]}},
    ])
except Exception:
    pass


# Release safe natural-language self-access dispatch MCP tools
try:
    from llm_wiki_mcp.context_api import (
        release_detect_safe_self_command,
        release_safe_self_command_result,
    )
except Exception:
    release_detect_safe_self_command = release_safe_self_command_result = None

def tool_wiki_safe_self_dispatch(arguments):
    """Implement the tool wiki safe self dispatch operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    query = arguments.get("query") or arguments.get("question") or ""
    command = release_detect_safe_self_command(query)
    if not command:
        return {"ok": False, "query": query, "matched_command": None, "message": "No safe self-access command matched."}
    return {"ok": True, "query": query, "matched_command": command, **release_safe_self_command_result(vault, command)}

try:
    TOOL_HANDLERS["wiki_safe_self_dispatch"] = tool_wiki_safe_self_dispatch
    TOOL_DEFS.append({
        "name": "wiki_safe_self_dispatch",
        "description": "Map a natural-language request such as 'run self-stats' to a safe read-only self-access tool and execute it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vault_path": {"type": "string"},
                "query": {"type": "string"},
                "question": {"type": "string"}
            },
            "required": []
        }
    })
except Exception:
    pass


# Release AI sidecar notes and self-extending wiki MCP tools
try:
    from llm_wiki_mcp.context_api import release_build_page_note, release_iterate_all_notes, release_search_with_notes, release_notes_status, release_find_candidate_links, release_combined_page_text, release_notes_graph_mermaid
except Exception:
    release_build_page_note = release_iterate_all_notes = release_search_with_notes = release_notes_status = release_find_candidate_links = release_combined_page_text = release_notes_graph_mermaid = None

def tool_wiki_page_notes_iterate(arguments):
    """Read, create, or summarise AI sidecar notes for tool wiki page notes iterate."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"; title = arguments.get("title") or arguments.get("page") or ""
    return release_build_page_note(vault, title, arguments.get("mode", "iterate"), int(arguments.get("max_links", 12)))
def tool_wiki_notes_iterate_all(arguments):
    """Read, create, or summarise AI sidecar notes for tool wiki notes iterate all."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"; return release_iterate_all_notes(vault, arguments.get("limit"))
def tool_wiki_search_with_notes(arguments):
    """Search or retrieve wiki content for tool wiki search with notes."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"; return {"ok": True, **release_search_with_notes(vault, arguments.get("query", ""), int(arguments.get("limit", 8)))}
def tool_wiki_notes_status(arguments):
    """Read, create, or summarise AI sidecar notes for tool wiki notes status."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"; return {"ok": True, **release_notes_status(vault)}
def tool_wiki_candidate_links(arguments):
    """Implement the tool wiki candidate links operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"; title = arguments.get("title") or arguments.get("page") or ""; return {"ok": True, "title": title, "candidate_links": release_find_candidate_links(vault, title, int(arguments.get("limit", 12)))}
def tool_wiki_combined_page_context(arguments):
    """Implement the tool wiki combined page context operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"; title = arguments.get("title") or arguments.get("page") or ""; return {"ok": True, "title": title, "context": release_combined_page_text(vault, title)}
def tool_wiki_notes_graph(arguments):
    """Create graph-oriented output for tool wiki notes graph."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"; return {"ok": True, "mermaid": release_notes_graph_mermaid(vault, int(arguments.get("limit_pages", 80)))}
try:
    TOOL_HANDLERS["wiki_page_notes_iterate"] = tool_wiki_page_notes_iterate
    TOOL_HANDLERS["wiki_notes_iterate_all"] = tool_wiki_notes_iterate_all
    TOOL_HANDLERS["wiki_search_with_notes"] = tool_wiki_search_with_notes
    TOOL_HANDLERS["wiki_notes_status"] = tool_wiki_notes_status
    TOOL_HANDLERS["wiki_candidate_links"] = tool_wiki_candidate_links
    TOOL_HANDLERS["wiki_combined_page_context"] = tool_wiki_combined_page_context
    TOOL_HANDLERS["wiki_notes_graph"] = tool_wiki_notes_graph
    TOOL_DEFS.extend([
        {"name":"wiki_page_notes_iterate","description":"Create/update AI sidecar notes for a page, including key terms and candidate links.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"title":{"type":"string"},"page":{"type":"string"},"mode":{"type":"string"},"max_links":{"type":"integer"}},"required":["title"]}},
        {"name":"wiki_notes_iterate_all","description":"Iterate AI sidecar notes for all pages or a limited number.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"limit":{"type":"integer"}},"required":[]}},
        {"name":"wiki_search_with_notes","description":"Search combined source page text and AI sidecar notes.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"query":{"type":"string"},"limit":{"type":"integer"}},"required":["query"]}},
        {"name":"wiki_notes_status","description":"Return AI notes coverage and missing notes.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"}},"required":[]}},
        {"name":"wiki_candidate_links","description":"Find candidate links for a page using source text and AI notes.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"title":{"type":"string"},"page":{"type":"string"},"limit":{"type":"integer"}},"required":["title"]}},
        {"name":"wiki_combined_page_context","description":"Return a page combined with its AI sidecar notes for retrieval/context.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"title":{"type":"string"},"page":{"type":"string"}},"required":["title"]}},
        {"name":"wiki_notes_graph","description":"Render Mermaid graph from AI note candidate links.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"limit_pages":{"type":"integer"}},"required":[]}},
    ])
except Exception:
    pass


# Bounded agentic ask MCP tools
try:
    from llm_wiki_mcp.context_api import release_agentic_ask, release_limitations_report, release_agentic_tool_manifest
except Exception:
    release_agentic_ask = release_limitations_report = release_agentic_tool_manifest = None

def tool_wiki_ask_agentic(arguments):
    """Build or execute the local LLM ask workflow for tool wiki ask agentic."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    question = arguments.get("question") or arguments.get("prompt") or ""
    return release_agentic_ask(vault, question, int(arguments.get("max_tool_calls", 5)), bool(arguments.get("dry_run", False)), bool(arguments.get("synthesize", True)), bool(arguments.get("protocol_mode", False)))

def tool_wiki_limitations_report(arguments):
    """Implement the tool wiki limitations report operation for the local LLM Wiki workflow."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    return {"ok": True, **release_limitations_report(vault)}

def tool_wiki_agentic_tool_manifest(arguments):
    """Implement the tool wiki agentic tool manifest operation for the local LLM Wiki workflow."""
    return {"ok": True, "tools": release_agentic_tool_manifest()}

try:
    TOOL_HANDLERS["wiki_ask_agentic"] = tool_wiki_ask_agentic
    TOOL_HANDLERS["wiki_limitations_report"] = tool_wiki_limitations_report
    TOOL_HANDLERS["wiki_agentic_tool_manifest"] = tool_wiki_agentic_tool_manifest
    TOOL_DEFS.extend([
        {"name":"wiki_ask_agentic","description":"Bounded read-only agentic ask: plan, call local wiki tools, build evidence pack and LLM prompt.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"question":{"type":"string"},"prompt":{"type":"string"},"max_tool_calls":{"type":"integer"},"dry_run":{"type":"boolean"}},"required":["question"]}},
        {"name":"wiki_limitations_report","description":"Return fixed/reduced and remaining known limitations.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"}},"required":[]}},
        {"name":"wiki_agentic_tool_manifest","description":"Return the safe tool manifest used by bounded agentic ask.","inputSchema":{"type":"object","properties":{},"required":[]}}
    ])
except Exception:
    pass


# ---------------------------------------------------------------------------
# Release unified tool exposure pattern, aligned with Ollama MCP wrapper style
# ---------------------------------------------------------------------------
try:
    from llm_wiki_mcp.context_api import (
        release_ask, release_plain_ask, release_agentic_ask, release_current_ask_mode,
        release_set_ask_mode, release_mcp_tool_catalog, release_tool_defs_from_catalog,
        release_tool_catalog_markdown,
    )
except Exception:
    release_ask = release_plain_ask = release_agentic_ask = None
    release_current_ask_mode = release_set_ask_mode = None
    release_mcp_tool_catalog = release_tool_defs_from_catalog = release_tool_catalog_markdown = None

def tool_wiki_ask(arguments):
    """Build or execute the local LLM ask workflow for tool wiki ask."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    question = arguments.get("question") or arguments.get("prompt") or ""
    return release_ask(vault, question, mode=arguments.get("mode"), max_tool_calls=int(arguments.get("max_tool_calls", 7)), dry_run=bool(arguments.get("dry_run", False)))

def tool_wiki_ask_plain(arguments):
    """Build or execute the local LLM ask workflow for tool wiki ask plain."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    question = arguments.get("question") or arguments.get("prompt") or ""
    return release_plain_ask(vault, question, int(arguments.get("top_k", 5)), bool(arguments.get("dry_run", False)))

def tool_wiki_set_ask_mode(arguments):
    """Build or execute the local LLM ask workflow for tool wiki set ask mode."""
    vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
    mode = arguments.get("mode") or "agentic"
    cfg = release_set_ask_mode(vault, mode)
    return {"ok": True, "mode": release_current_ask_mode(vault), "config": cfg}

def tool_wiki_tool_catalog(arguments):
    """Implement the tool wiki tool catalog operation for the local LLM Wiki workflow."""
    return {"ok": True, "catalog": release_mcp_tool_catalog(), "markdown": release_tool_catalog_markdown()}

try:
    TOOL_HANDLERS["wiki_ask"] = tool_wiki_ask
    TOOL_HANDLERS["wiki_ask_plain"] = tool_wiki_ask_plain
    TOOL_HANDLERS["wiki_set_ask_mode"] = tool_wiki_set_ask_mode
    TOOL_HANDLERS["wiki_tool_catalog"] = tool_wiki_tool_catalog
    existing_names = {t.get("name") for t in TOOL_DEFS if isinstance(t, dict)}
    for tool_def in release_tool_defs_from_catalog():
        if tool_def["name"] not in existing_names:
            TOOL_DEFS.append(tool_def)
            existing_names.add(tool_def["name"])
except Exception:
    pass

# Release planner tools
try:
    from llm_wiki_mcp.context_api import release_ask, release_tool_groups
    TOOL_HANDLERS["wiki_ask"] = lambda arguments: release_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", mode=arguments.get("mode"), max_tool_calls=int(arguments.get("max_tool_calls",10)), dry_run=bool(arguments.get("dry_run",False)))
    TOOL_HANDLERS["wiki_planner_tools"] = lambda arguments: {"ok": True, "groups": release_tool_groups()}
    if not any(t.get("name")=="wiki_planner_tools" for t in TOOL_DEFS if isinstance(t,dict)):
        TOOL_DEFS.append({"name":"wiki_planner_tools","description":"Return Release planner tool groups.","inputSchema":{"type":"object","properties":{},"required":[]}})
except Exception:
    pass

# Release ask override with evidence fallback
try:
    from llm_wiki_mcp.context_api import release_ask
    TOOL_HANDLERS["wiki_ask"] = lambda arguments: release_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", mode=arguments.get("mode"), max_tool_calls=int(arguments.get("max_tool_calls",10)), dry_run=bool(arguments.get("dry_run",False)))
except Exception:
    pass


# Release full MCP catalogue exposure and compatibility handlers
try:
    from llm_wiki_mcp.context_api import (
        release_full_tool_catalog, release_tool_defs_from_catalog, release_tool_catalog_markdown,
        release_tool_catalog_summary, release_agentic_tool_manifest, release_search_with_notes,
        release_read_page_tool, release_list_pages_tool, release_wiki_usage_snapshot,
        release_self_access_snapshot, release_runtime_capabilities, release_metrics_summary,
        release_load_runtime_journal, release_command_tool_map, release_reconcile_docs,
        release_runtime_graph_mermaid, release_limitations_report, release_notes_status,
        release_find_candidate_links, release_notes_graph_mermaid
    )

    def tool_wiki_tool_catalog(arguments):
        """Implement the tool wiki tool catalog operation for the local LLM Wiki workflow."""
        return {"ok": True, **release_tool_catalog_summary(), "markdown": release_tool_catalog_markdown()}

    def tool_wiki_search_with_notes(arguments):
        """Search or retrieve wiki content for tool wiki search with notes."""
        return {"ok": True, **release_search_with_notes(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("query") or arguments.get("question") or "", int(arguments.get("limit",8)))}

    def tool_wiki_read_page(arguments):
        """Read a page from either an explicit vault or the active MCP store."""
        title = arguments.get("title") or arguments.get("page") or ""
        explicit_vault = arguments.get("vault_path") or arguments.get("vault")
        if explicit_vault:
            return release_read_page_tool(explicit_vault, title)
        try:
            return store().read_page(title)
        except Exception as exc:
            return {"ok": False, "title": title, "error": str(exc)}

    def tool_wiki_list_pages(arguments):
        """List pages from either an explicit vault or the active MCP store."""
        explicit_vault = arguments.get("vault_path") or arguments.get("vault")
        if explicit_vault:
            return release_list_pages_tool(explicit_vault, int(arguments.get("limit",300)))
        return store().list_pages(limit=int(arguments.get("limit",300)))

    def tool_wiki_usage_snapshot(arguments):
        """Inspect runtime history, token metrics, or usage state for tool wiki usage snapshot."""
        return release_wiki_usage_snapshot(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault")

    def tool_wiki_self_access_snapshot(arguments):
        """Implement the tool wiki self access snapshot operation for the local LLM Wiki workflow."""
        return release_self_access_snapshot(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault")

    def tool_wiki_capabilities(arguments):
        """Implement the tool wiki capabilities operation for the local LLM Wiki workflow."""
        return release_runtime_capabilities(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault")

    def tool_wiki_llm_metrics(arguments):
        """Inspect runtime history, token metrics, or usage state for tool wiki llm metrics."""
        return release_metrics_summary(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", int(arguments.get("limit",100)))

    def tool_wiki_runtime_journal(arguments):
        """Implement the tool wiki runtime journal operation for the local LLM Wiki workflow."""
        return {"events": release_load_runtime_journal(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", int(arguments.get("limit",20)))}

    def tool_wiki_command_tool_map(arguments):
        """Implement the tool wiki command tool map operation for the local LLM Wiki workflow."""
        return {"mapping": release_command_tool_map()}

    def tool_wiki_reconcile_docs(arguments):
        """Implement the tool wiki reconcile docs operation for the local LLM Wiki workflow."""
        return release_reconcile_docs(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault")

    def tool_wiki_runtime_graph(arguments):
        """Create graph-oriented output for tool wiki runtime graph."""
        return {"mermaid": release_runtime_graph_mermaid()}

    def tool_wiki_limitations_report(arguments):
        """Implement the tool wiki limitations report operation for the local LLM Wiki workflow."""
        return release_limitations_report(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault")

    def tool_wiki_agentic_tool_manifest(arguments):
        """Implement the tool wiki agentic tool manifest operation for the local LLM Wiki workflow."""
        return {"tools": release_agentic_tool_manifest()}

    def tool_wiki_notes_status(arguments):
        """Read, create, or summarise AI sidecar notes for tool wiki notes status."""
        return release_notes_status(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault")

    def tool_wiki_candidate_links(arguments):
        """Implement the tool wiki candidate links operation for the local LLM Wiki workflow."""
        vault = arguments.get("vault_path") or arguments.get("vault") or "wiki_vault"
        title = arguments.get("title") or arguments.get("page") or arguments.get("query") or ""
        return {"title": title, "candidate_links": release_find_candidate_links(vault, title, int(arguments.get("limit",12)))}

    def tool_wiki_notes_graph(arguments):
        """Create graph-oriented output for tool wiki notes graph."""
        return {"mermaid": release_notes_graph_mermaid(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault")}

    for name, fn in {
        "wiki_tool_catalog": tool_wiki_tool_catalog,
        "wiki_search_with_notes": tool_wiki_search_with_notes,
        "wiki_read_page": tool_wiki_read_page,
        "wiki_list_pages": tool_wiki_list_pages,
        "wiki_usage_snapshot": tool_wiki_usage_snapshot,
        "wiki_self_access_snapshot": tool_wiki_self_access_snapshot,
        "wiki_capabilities": tool_wiki_capabilities,
        "wiki_llm_metrics": tool_wiki_llm_metrics,
        "wiki_runtime_journal": tool_wiki_runtime_journal,
        "wiki_command_tool_map": tool_wiki_command_tool_map,
        "wiki_reconcile_docs": tool_wiki_reconcile_docs,
        "wiki_runtime_graph": tool_wiki_runtime_graph,
        "wiki_limitations_report": tool_wiki_limitations_report,
        "wiki_agentic_tool_manifest": tool_wiki_agentic_tool_manifest,
        "wiki_notes_status": tool_wiki_notes_status,
        "wiki_candidate_links": tool_wiki_candidate_links,
        "wiki_notes_graph": tool_wiki_notes_graph,
    }.items():
        TOOL_HANDLERS[name] = fn

    existing = {t.get("name") for t in TOOL_DEFS if isinstance(t, dict)}
    for tool_def in release_tool_defs_from_catalog():
        if tool_def["name"] not in existing:
            TOOL_DEFS.append(tool_def)
            existing.add(tool_def["name"])
except Exception:
    pass

# Release intent-aware ask override
try:
    from llm_wiki_mcp.context_api import release_ask, release_agentic_ask, release_resolve_intent
    TOOL_HANDLERS["wiki_ask"] = lambda arguments: release_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", mode=arguments.get("mode"), max_tool_calls=int(arguments.get("max_tool_calls",12)), dry_run=bool(arguments.get("dry_run",False)))
    TOOL_HANDLERS["wiki_ask_agentic"] = lambda arguments: release_agentic_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", max_tool_calls=int(arguments.get("max_tool_calls",12)), dry_run=bool(arguments.get("dry_run",False)), synthesize=bool(arguments.get("synthesize",True)))
    TOOL_HANDLERS["wiki_resolve_intent"] = lambda arguments: {"ok": True, **release_resolve_intent(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "")}
    if not any(t.get("name")=="wiki_resolve_intent" for t in TOOL_DEFS if isinstance(t,dict)):
        TOOL_DEFS.append({"name":"wiki_resolve_intent","description":"Resolve short/contextual user intent before planning tools.","inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"question":{"type":"string"}},"required":["question"]}})
except Exception:
    pass

# Release provenance/startup/history MCP tools
try:
    from llm_wiki_mcp.context_api import release_provenance_summary,release_provenance_status_for_file,release_startup_commands,release_set_startup_commands,release_default_startup_commands,release_build_development_history
    TOOL_HANDLERS["wiki_provenance_summary"] = lambda a: {"ok":True, **release_provenance_summary(a.get("vault_path") or a.get("vault") or "wiki_vault", int(a.get("limit",20)))}
    TOOL_HANDLERS["wiki_file_provenance_status"] = lambda a: {"ok":True, **release_provenance_status_for_file(a.get("vault_path") or a.get("vault") or "wiki_vault", a.get("path") or a.get("file_path"))}
    TOOL_HANDLERS["wiki_startup_commands"] = lambda a: {"ok":True, "commands": release_startup_commands(a.get("vault_path") or a.get("vault") or "wiki_vault")}
    TOOL_HANDLERS["wiki_set_default_startup"] = lambda a: {"ok":True, "commands": (release_set_startup_commands(a.get("vault_path") or a.get("vault") or "wiki_vault", release_default_startup_commands()) and release_startup_commands(a.get("vault_path") or a.get("vault") or "wiki_vault"))}
    TOOL_HANDLERS["wiki_build_development_history"] = lambda a: release_build_development_history(a.get("project_root"))
    for name,desc in {"wiki_provenance_summary":"Return SQL ingest provenance summary.","wiki_file_provenance_status":"Check whether a file is new, changed or unchanged based on mtime and SHA256.","wiki_startup_commands":"Get startup command list from config.","wiki_set_default_startup":"Set startup commands to /ingest ./docs and /notes-all.","wiki_build_development_history":"Build GitHub-friendly DEVELOPMENT_HISTORY.md."}.items():
        if not any(t.get("name")==name for t in TOOL_DEFS if isinstance(t,dict)):
            TOOL_DEFS.append({"name":name,"description":desc,"inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"path":{"type":"string"},"file_path":{"type":"string"},"project_root":{"type":"string"},"limit":{"type":"integer"}},"required":[]}})
except Exception:
    pass

# Release provenance-aware ingest tools
try:
    from llm_wiki_mcp.context_api import release_ingest_directory_plan, release_ingest_directory_provenance
    TOOL_HANDLERS["wiki_ingest_directory_plan"] = lambda a: {"ok": True, **release_ingest_directory_plan(a.get("vault_path") or a.get("vault") or "wiki_vault", a.get("directory") or a.get("path") or ".", bool(a.get("recursive", True)))}
    TOOL_HANDLERS["wiki_ingest_directory"] = lambda a: {"ok": True, **release_ingest_directory_provenance(a.get("vault_path") or a.get("vault") or "wiki_vault", a.get("directory") or a.get("path") or ".", bool(a.get("recursive", True)), not bool(a.get("dry_run", False)))}
    for name,desc in {
        "wiki_ingest_directory_plan":"Plan a provenance-aware directory or single-file ingest without updating unchanged files.",
        "wiki_ingest_directory":"Run provenance-aware directory or single-file ingest and report new/updated/skipped files."
    }.items():
        if not any(t.get("name")==name for t in TOOL_DEFS if isinstance(t,dict)):
            TOOL_DEFS.append({"name":name,"description":desc,"inputSchema":{"type":"object","properties":{"vault_path":{"type":"string"},"directory":{"type":"string"},"path":{"type":"string"},"recursive":{"type":"boolean"},"dry_run":{"type":"boolean"}},"required":[]}})
except Exception:
    pass

# Release evidence-first ask override
try:
    from llm_wiki_mcp.context_api import release_ask, release_agentic_ask
    TOOL_HANDLERS["wiki_ask"] = lambda arguments: release_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", mode=arguments.get("mode"), max_tool_calls=int(arguments.get("max_tool_calls",12)), dry_run=bool(arguments.get("dry_run",False)))
    TOOL_HANDLERS["wiki_ask_agentic"] = lambda arguments: release_agentic_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", max_tool_calls=int(arguments.get("max_tool_calls",12)), dry_run=bool(arguments.get("dry_run",False)), synthesize=bool(arguments.get("synthesize",True)))
except Exception:
    pass

# Release answer-first ask override
try:
    from llm_wiki_mcp.context_api import release_ask, release_agentic_ask
    TOOL_HANDLERS["wiki_ask"] = lambda arguments: release_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", mode=arguments.get("mode"), max_tool_calls=int(arguments.get("max_tool_calls",14)), dry_run=bool(arguments.get("dry_run",False)))
    TOOL_HANDLERS["wiki_ask_agentic"] = lambda arguments: release_agentic_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", max_tool_calls=int(arguments.get("max_tool_calls",14)), dry_run=bool(arguments.get("dry_run",False)), synthesize=bool(arguments.get("synthesize",True)))
except Exception:
    pass

# Release second-pass ask and docs consolidation tools
try:
    from llm_wiki_mcp.context_api import release_ask, release_agentic_ask, release_consolidate_docs
    TOOL_HANDLERS["wiki_ask"] = lambda arguments: release_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", mode=arguments.get("mode"), max_tool_calls=int(arguments.get("max_tool_calls",14)), dry_run=bool(arguments.get("dry_run",False)))
    TOOL_HANDLERS["wiki_ask_agentic"] = lambda arguments: release_agentic_ask(arguments.get("vault_path") or arguments.get("vault") or "wiki_vault", arguments.get("question") or arguments.get("prompt") or "", max_tool_calls=int(arguments.get("max_tool_calls",14)), dry_run=bool(arguments.get("dry_run",False)), synthesize=bool(arguments.get("synthesize",True)))
    TOOL_HANDLERS["wiki_consolidate_docs"] = lambda arguments: release_consolidate_docs(arguments.get("project_root"), bool(arguments.get("archive", True)))
    if not any(t.get("name")=="wiki_consolidate_docs" for t in TOOL_DEFS if isinstance(t,dict)):
        TOOL_DEFS.append({"name":"wiki_consolidate_docs","description":"Consolidate docs into fewer category files and archive scattered version docs.","inputSchema":{"type":"object","properties":{"project_root":{"type":"string"},"archive":{"type":"boolean"}},"required":[]}})
except Exception:
    pass

# Release long-document search tools
try:
    from llm_wiki_mcp.context_api import release_search_with_notes, release_search_following_pages

    def tool_wiki_search_with_notes_long(arguments):
        """Search source pages/notes and return hit-centred snippets for long docs."""
        return {
            "ok": True,
            **release_search_with_notes(
                arguments.get("vault_path") or arguments.get("vault") or "wiki_vault",
                arguments.get("query") or arguments.get("question") or "",
                int(arguments.get("limit", 8)),
                int(arguments.get("context_chars", 1200)),
            ),
        }

    def tool_wiki_search_following_pages(arguments):
        """Search long documents and return the matched page plus following pages."""
        return {
            "ok": True,
            **release_search_following_pages(
                arguments.get("vault_path") or arguments.get("vault") or "wiki_vault",
                arguments.get("query") or arguments.get("question") or "",
                int(arguments.get("limit", 5)),
                int(arguments.get("following_pages", arguments.get("pages", 2))),
                int(arguments.get("context_chars", 4000)),
                int(arguments.get("max_chars", 16000)),
            ),
        }

    TOOL_HANDLERS["wiki_search_with_notes"] = tool_wiki_search_with_notes_long
    TOOL_HANDLERS["wiki_search_following_pages"] = tool_wiki_search_following_pages
    existing = {t.get("name") for t in TOOL_DEFS if isinstance(t, dict)}
    if "wiki_search_following_pages" not in existing:
        TOOL_DEFS.append({
            "name": "wiki_search_following_pages",
            "description": "Search long source pages/books and return the matched page plus N following pages or a large hit-centred excerpt.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "vault_path": {"type": "string"},
                    "query": {"type": "string"},
                    "question": {"type": "string"},
                    "limit": {"type": "integer"},
                    "following_pages": {"type": "integer"},
                    "pages": {"type": "integer"},
                    "context_chars": {"type": "integer"},
                    "max_chars": {"type": "integer"},
                },
                "required": ["query"],
            },
        })
    for tool_def in TOOL_DEFS:
        if isinstance(tool_def, dict) and tool_def.get("name") == "wiki_search_with_notes":
            props = tool_def.setdefault("inputSchema", {}).setdefault("properties", {})
            props.setdefault("context_chars", {"type": "integer"})
            tool_def["description"] = "Search combined source page text and AI sidecar notes, returning snippets centred around the actual hit."
except Exception:
    pass
