"""project_knowledge_base.kb_core — Ядро локальной базы знаний проекта VideoGenerator.

Обеспечивает:
1. Индексацию всей проектной документации (docs/, .agents/rules/, сценарии, регламенты, плейбуки).
2. Полнотекстовый поиск SQLite FTS5 (unicode61 tokenizer) с BM25 ранжированием и сниппетами.
3. Автоматическую категоризацию и детекцию используемых инструментов/технологий.
4. Доступ через CLI (scripts/knowledge_base.py) и REST API (/api/knowledge/*).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
DB_PATH = HERE / "knowledge.db"
SCHEMA_VERSION = 1

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
WORD_RE = re.compile(r"[\wÄÖÜäöüßА-Яа-яЁё-]+", re.UNICODE)

KNOWN_TOOLS = {
    "ffmpeg": "FFmpeg",
    "moviepy": "MoviePy",
    "edge-tts": "Edge-TTS",
    "edge_tts": "Edge-TTS",
    "veo": "Google Veo",
    "google flow": "Google Flow",
    "flow": "Google Flow",
    "kling": "Kling AI",
    "seedance": "Seedance",
    "suno": "Suno AI",
    "fastapi": "FastAPI",
    "vue": "Vue 3",
    "tailwind": "Tailwind CSS",
    "vite": "Vite",
    "pydantic": "Pydantic",
    "lut": "3D LUT",
    "lut3d": "3D LUT",
    "whisper": "Whisper",
    "faster-whisper": "Faster-Whisper",
    "docker": "Docker",
    "cdp": "Chrome DevTools Protocol",
    "mcp": "Model Context Protocol",
}


@dataclass
class SearchResult:
    document_id: int
    rel_path: str
    title: str
    category: str
    heading: str
    snippet: str
    score: float
    modified_at: str


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            return super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.close()


def connect() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH), timeout=15.0, factory=_ClosingConnection)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    if str(c.execute("PRAGMA journal_mode").fetchone()[0]).lower() != "wal":
        c.execute("PRAGMA journal_mode=WAL")
    return c


def reset_schema(c: sqlite3.Connection) -> None:
    c.executescript("""
    DROP TABLE IF EXISTS section_search;
    DROP TABLE IF EXISTS document_tools;
    DROP TABLE IF EXISTS tools;
    DROP TABLE IF EXISTS sections;
    DROP TABLE IF EXISTS documents;

    CREATE TABLE documents (
        id INTEGER PRIMARY KEY,
        rel_path TEXT NOT NULL UNIQUE,
        abs_path TEXT NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        word_count INTEGER NOT NULL,
        modified_at TEXT NOT NULL,
        indexed_at TEXT NOT NULL
    );

    CREATE TABLE sections (
        id INTEGER PRIMARY KEY,
        document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        heading TEXT NOT NULL,
        body TEXT NOT NULL,
        level INTEGER NOT NULL,
        position INTEGER NOT NULL
    );

    CREATE TABLE tools (
        id INTEGER PRIMARY KEY,
        canonical_name TEXT NOT NULL UNIQUE COLLATE NOCASE
    );

    CREATE TABLE document_tools (
        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
        tool_id INTEGER REFERENCES tools(id) ON DELETE CASCADE,
        PRIMARY KEY(document_id, tool_id)
    );

    CREATE VIRTUAL TABLE section_search USING fts5(
        heading,
        body,
        section_id UNINDEXED,
        document_id UNINDEXED,
        tokenize='unicode61 remove_diacritics 2'
    );

    CREATE INDEX idx_docs_category ON documents(category);
    CREATE INDEX idx_docs_hash ON documents(content_hash);
    PRAGMA user_version = 1;
    """)


def ensure_schema(c: sqlite3.Connection, rebuild: bool = False) -> None:
    version = c.execute("PRAGMA user_version").fetchone()[0]
    if rebuild or version != SCHEMA_VERSION:
        reset_schema(c)


def detect_category(rel_path: str) -> str:
    norm = rel_path.replace("\\", "/").lower()
    if norm.startswith("docs/dev/"):
        return "Architecture & Dev"
    elif norm.startswith("docs/plans/"):
        return "Plans & Roadmaps"
    elif norm.startswith("docs/public/"):
        return "User Guides & FAQ"
    elif norm.startswith(".agents/rules/"):
        return "Rules & Standards"
    elif "сценарий" in norm or "паспорт" in norm or "план" in norm:
        return "Screenplays & Playbooks"
    elif norm.startswith("docs/"):
        return "Documentation"
    return "Project Guidelines"


def extract_title(text: str, filename: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            cleaned = line.lstrip("#").strip()
            # Убираем эмодзи и префиксы если нужно
            return cleaned[:120]
    return Path(filename).stem.replace("_", " ").title()


def split_sections(text: str) -> List[Tuple[str, str, int]]:
    sections = []
    lines = text.replace("\r\n", "\n").split("\n")
    current_heading = "Overview"
    current_body = []
    current_level = 1

    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            if current_body or current_heading != "Overview":
                sections.append((current_heading, "\n".join(current_body).strip(), current_level))
            hashes, title = m.groups()
            current_level = len(hashes)
            current_heading = title.strip()
            current_body = []
        else:
            current_body.append(line)

    sections.append((current_heading, "\n".join(current_body).strip(), current_level))
    return [(h, b, lvl) for h, b, lvl in sections if h or b]


def detect_tools(text: str) -> List[str]:
    lower_text = text.lower()
    detected = set()
    for needle, canonical in KNOWN_TOOLS.items():
        if re.search(rf"\b{re.escape(needle)}\b", lower_text):
            detected.add(canonical)
    return sorted(detected)


def index_file(c: sqlite3.Connection, path: Path, project_root: Path, now: str) -> bool:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Failed to read file {path}: {e}")
        return False

    rel_path = str(path.relative_to(project_root)).replace("\\", "/")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()

    existing = c.execute("SELECT id, content_hash FROM documents WHERE rel_path = ?", (rel_path,)).fetchone()
    if existing and existing["content_hash"] == content_hash:
        return False  # Up to date

    title = extract_title(content, path.name)
    category = detect_category(rel_path)
    words = len(WORD_RE.findall(content))

    if existing:
        doc_id = existing["id"]
        c.execute("DELETE FROM section_search WHERE document_id = ?", (doc_id,))
        c.execute("DELETE FROM sections WHERE document_id = ?", (doc_id,))
        c.execute("DELETE FROM document_tools WHERE document_id = ?", (doc_id,))
        c.execute("""
            UPDATE documents 
            SET title = ?, category = ?, content_hash = ?, word_count = ?, modified_at = ?, indexed_at = ?
            WHERE id = ?
        """, (title, category, content_hash, words, mtime, now, doc_id))
    else:
        doc_id = c.execute("""
            INSERT INTO documents (rel_path, abs_path, title, category, content_hash, word_count, modified_at, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (rel_path, str(path), title, category, content_hash, words, mtime, now)).lastrowid

    sections = split_sections(content)
    for pos, (h, b, lvl) in enumerate(sections):
        sec_id = c.execute(
            "INSERT INTO sections (document_id, heading, body, level, position) VALUES (?, ?, ?, ?, ?)",
            (doc_id, h, b, lvl, pos)
        ).lastrowid
        c.execute(
            "INSERT INTO section_search (heading, body, section_id, document_id) VALUES (?, ?, ?, ?)",
            (h, b, sec_id, doc_id)
        )

    tools = detect_tools(content)
    for tool_name in tools:
        c.execute("INSERT OR IGNORE INTO tools (canonical_name) VALUES (?)", (tool_name,))
        tool_id = c.execute("SELECT id FROM tools WHERE canonical_name = ?", (tool_name,)).fetchone()["id"]
        c.execute("INSERT OR IGNORE INTO document_tools (document_id, tool_id) VALUES (?, ?)", (doc_id, tool_id))

    return True


def collect_target_files(project_root: Path) -> List[Path]:
    files = []
    # 1. docs/
    docs_dir = project_root / "docs"
    if docs_dir.exists():
        files.extend(docs_dir.rglob("*.md"))

    # 2. .agents/rules/
    rules_dir = project_root / ".agents" / "rules"
    if rules_dir.exists():
        files.extend(rules_dir.rglob("*.md"))

    # 3. Root markdown files
    for item in project_root.glob("*.md"):
        files.append(item)

    return sorted(set(f for f in files if f.is_file()))


def sync_knowledge_base(project_root: Optional[Path] = None, rebuild: bool = False) -> Dict[str, Any]:
    root = (project_root or PROJECT_ROOT).resolve()
    HERE.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    with connect() as c:
        ensure_schema(c, rebuild=rebuild)
        targets = collect_target_files(root)
        total = len(targets)
        updated = 0

        # Удаляем удаленные файлы из индекса
        valid_rel_paths = {str(t.relative_to(root)).replace("\\", "/") for t in targets}
        indexed_rows = c.execute("SELECT id, rel_path FROM documents").fetchall()
        deleted = 0
        for row in indexed_rows:
            if row["rel_path"] not in valid_rel_paths:
                c.execute("DELETE FROM documents WHERE id = ?", (row["id"],))
                deleted += 1

        for p in targets:
            if index_file(c, p, root, now):
                updated += 1

        total_docs = c.execute("SELECT count(*) FROM documents").fetchone()[0]
        total_sections = c.execute("SELECT count(*) FROM sections").fetchone()[0]

    return {
        "ok": True,
        "total_files": total,
        "indexed_or_updated": updated,
        "removed": deleted,
        "total_documents": total_docs,
        "total_sections": total_sections,
        "database_path": str(DB_PATH)
    }


def search_knowledge_base(query: str, category: str = "", limit: int = 10) -> List[SearchResult]:
    clean_q = re.sub(r'[^\w\s-]', ' ', query).strip()
    if not clean_q:
        return []

    tokens = [t for t in clean_q.split() if len(t) >= 2]
    if not tokens:
        return []
    
    # FTS5 prefix match: token*
    fts_query = " ".join(f'"{t}"*' for t in tokens)

    sql = """
        SELECT 
            d.id as doc_id,
            d.rel_path,
            d.title,
            d.category,
            d.modified_at,
            s.heading,
            snippet(section_search, 1, '<b>', '</b>', '...', 24) as snip,
            bm25(section_search) as rank_score
        FROM section_search ss
        JOIN sections s ON ss.section_id = s.id
        JOIN documents d ON ss.document_id = d.id
        WHERE section_search MATCH ?
    """
    params = [fts_query]

    if category:
        sql += " AND d.category = ?"
        params.append(category)

    sql += " ORDER BY rank_score ASC LIMIT ?"
    params.append(limit)

    results = []
    with connect() as c:
        try:
            rows = c.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            # Fallback simple LIKE
            like_sql = """
                SELECT d.id as doc_id, d.rel_path, d.title, d.category, d.modified_at, s.heading,
                       substr(s.body, 1, 160) as snip, 1.0 as rank_score
                FROM sections s JOIN documents d ON s.document_id = d.id
                WHERE s.body LIKE ? OR s.heading LIKE ?
                LIMIT ?
            """
            rows = c.execute(like_sql, (f"%{clean_q}%", f"%{clean_q}%", limit)).fetchall()

        for r in rows:
            results.append(SearchResult(
                document_id=r["doc_id"],
                rel_path=r["rel_path"],
                title=r["title"],
                category=r["category"],
                heading=r["heading"],
                snippet=r["snip"].replace("\n", " ").strip(),
                score=round(float(r["rank_score"]), 3),
                modified_at=r["modified_at"]
            ))

    return results


def get_status() -> Dict[str, Any]:
    if not DB_PATH.exists():
        return {"ready": False, "document_count": 0}

    with connect() as c:
        doc_count = c.execute("SELECT count(*) FROM documents").fetchone()[0]
        sec_count = c.execute("SELECT count(*) FROM sections").fetchone()[0]
        categories = dict(c.execute("SELECT category, count(*) FROM documents GROUP BY category").fetchall())
        tools = [r[0] for r in c.execute("""
            SELECT t.canonical_name FROM tools t 
            JOIN document_tools dt ON t.id = dt.tool_id 
            GROUP BY t.id ORDER BY count(dt.document_id) DESC LIMIT 15
        """).fetchall()]

    return {
        "ready": True,
        "database_path": str(DB_PATH),
        "document_count": doc_count,
        "section_count": sec_count,
        "categories": categories,
        "top_tools": tools
    }


def get_document_content(doc_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает метаданные и полное содержимое документа по ID."""
    with connect() as c:
        row = c.execute(
            "SELECT id, rel_path, abs_path, title, category, word_count, modified_at FROM documents WHERE id = ?",
            (doc_id,)
        ).fetchone()
        if not row:
            return None
        abs_p = Path(row["abs_path"])
        content = ""
        if abs_p.exists():
            try:
                content = abs_p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.warning(f"Error reading doc {abs_p}: {e}")
        return {
            "id": row["id"],
            "rel_path": row["rel_path"],
            "title": row["title"],
            "category": row["category"],
            "word_count": row["word_count"],
            "modified_at": row["modified_at"],
            "content": content
        }


def search_watch_knowledge_base(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Полнотекстовый поиск по внешней базе знаний видеогайдов watch."""
    watch_db = Path("D:/Projects/watch/video_knowledge_base/knowledge.db")
    if not watch_db.exists():
        return []
    clean_q = re.sub(r'[^\w\s-]', ' ', query).strip()
    tokens = [t for t in clean_q.split() if len(t) >= 2]
    if not tokens:
        return []
    fts_query = " ".join(f'"{t}"*' for t in tokens)
    try:
        with sqlite3.connect(str(watch_db)) as c:
            c.row_factory = sqlite3.Row
            rows = c.execute("""
                SELECT d.title, d.category, s.heading, snippet(section_search, 1, '<b>', '</b>', '...', 20) as snip, d.report_path
                FROM section_search ss
                JOIN sections s ON ss.section_id = s.id
                JOIN documents d ON ss.document_id = d.id
                WHERE section_search MATCH ?
                LIMIT ?
            """, (fts_query, limit)).fetchall()
            return [
                {
                    "title": r["title"],
                    "category": r["category"],
                    "heading": r["heading"],
                    "snippet": (r["snip"] or "").replace("\n", " ").strip(),
                    "report_path": r["report_path"],
                    "source": "watch"
                }
                for r in rows
            ]
    except Exception as e:
        logger.warning(f"Error searching watch KB: {e}")
        return []
