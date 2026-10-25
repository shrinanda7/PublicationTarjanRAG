"""Durable local source-chunk and embedding store used alongside optional Neo4j graphs."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import settings


class LocalResearchStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or (settings.CACHE_DIR / "research_index.sqlite3"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS chunks (
                paper_id TEXT NOT NULL, chunk_id TEXT NOT NULL, content TEXT NOT NULL,
                section TEXT, page INTEGER, content_sha256 TEXT NOT NULL,
                PRIMARY KEY (paper_id, chunk_id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS embeddings (
                paper_id TEXT NOT NULL, chunk_id TEXT NOT NULL, model TEXT NOT NULL,
                content_sha256 TEXT NOT NULL, vector_json TEXT NOT NULL,
                PRIMARY KEY (paper_id, chunk_id, model))""")
            db.execute("""CREATE TABLE IF NOT EXISTS paper_graphs (
                paper_id TEXT PRIMARY KEY, nodes_json TEXT NOT NULL, edges_json TEXT NOT NULL)""")

    def _connect(self):
        db = sqlite3.connect(str(self.db_path), timeout=30)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _digest(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def upsert_chunks(self, paper_id: str, chunks: List[Dict[str, Any]]) -> int:
        with self._connect() as db:
            for chunk in chunks:
                cid, content = str(chunk.get("chunk_id", "")), str(chunk.get("content", ""))
                if not cid or not content.strip():
                    continue
                digest = self._digest(content)
                old = db.execute("SELECT content_sha256 FROM chunks WHERE paper_id=? AND chunk_id=?", (paper_id, cid)).fetchone()
                if old and old["content_sha256"] != digest:
                    db.execute("DELETE FROM embeddings WHERE paper_id=? AND chunk_id=?", (paper_id, cid))
                db.execute("""INSERT INTO chunks(paper_id,chunk_id,content,section,page,content_sha256)
                    VALUES(?,?,?,?,?,?) ON CONFLICT(paper_id,chunk_id) DO UPDATE SET
                    content=excluded.content, section=excluded.section, page=excluded.page,
                    content_sha256=excluded.content_sha256""",
                    (paper_id, cid, content, chunk.get("section"), chunk.get("page"), digest))
            return db.execute("SELECT COUNT(*) FROM chunks WHERE paper_id=?", (paper_id,)).fetchone()[0]

    def get_chunks(self, paper_id: str, chunk_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        with self._connect() as db:
            if chunk_ids:
                ids = list(dict.fromkeys(map(str, chunk_ids)))
                rows = db.execute(f"SELECT * FROM chunks WHERE paper_id=? AND chunk_id IN ({','.join('?' for _ in ids)})", [paper_id, *ids]).fetchall() if ids else []
                by_id = {row["chunk_id"]: dict(row) for row in rows}
                return [by_id[cid] for cid in ids if cid in by_id]
            return [dict(row) for row in db.execute("SELECT * FROM chunks WHERE paper_id=? ORDER BY chunk_id", (paper_id,)).fetchall()]

    def get_embedding(self, paper_id: str, chunk_id: str, model: str, content: str) -> Optional[List[float]]:
        digest = self._digest(content)
        with self._connect() as db:
            row = db.execute("""SELECT e.vector_json FROM embeddings e JOIN chunks c
                ON c.paper_id=e.paper_id AND c.chunk_id=e.chunk_id
                WHERE e.paper_id=? AND e.chunk_id=? AND e.model=? AND e.content_sha256=? AND c.content_sha256=?""",
                (paper_id, chunk_id, model, digest, digest)).fetchone()
        return json.loads(row["vector_json"]) if row else None

    def save_embedding(self, paper_id: str, chunk_id: str, model: str, content: str, vector: List[float]) -> None:
        digest = self._digest(content)
        with self._connect() as db:
            db.execute("""INSERT INTO embeddings(paper_id,chunk_id,model,content_sha256,vector_json)
                VALUES(?,?,?,?,?) ON CONFLICT(paper_id,chunk_id,model) DO UPDATE SET
                content_sha256=excluded.content_sha256, vector_json=excluded.vector_json""",
                (paper_id, chunk_id, model, digest, json.dumps(vector)))

    def save_graph(self, paper_id: str, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> None:
        with self._connect() as db:
            db.execute("""INSERT INTO paper_graphs(paper_id,nodes_json,edges_json) VALUES(?,?,?)
                ON CONFLICT(paper_id) DO UPDATE SET nodes_json=excluded.nodes_json, edges_json=excluded.edges_json""",
                (paper_id, json.dumps(nodes), json.dumps(edges)))

    def get_graph(self, paper_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as db:
            row = db.execute("SELECT nodes_json,edges_json FROM paper_graphs WHERE paper_id=?", (paper_id,)).fetchone()
        if not row:
            return None
        return {"nodes": json.loads(row["nodes_json"]), "edges": json.loads(row["edges_json"])}

    def clear_paper(self, paper_id: str) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM embeddings WHERE paper_id=?", (paper_id,))
            db.execute("DELETE FROM chunks WHERE paper_id=?", (paper_id,))
            db.execute("DELETE FROM paper_graphs WHERE paper_id=?", (paper_id,))


local_research_store = LocalResearchStore()
