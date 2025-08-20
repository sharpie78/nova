# File: servers/rag_store.py
import os
import sqlite3
import numpy as np
from typing import List, Dict, Any, Iterable
from .chat_memory_router import get_model as get_embed_model
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

# --- Root locations ---
BASE_DIR = os.path.expanduser('~/nova')
                # Scan EVERYTHING under here (by default)
VAULT_DIR = os.path.join(BASE_DIR, "vault") # Vault still used for DB location
DB_PATH = os.path.join(VAULT_DIR, "rag.db")

# --- File/type filters ---
ALLOWED_EXT = {
    ".txt", ".md", ".log",
    ".py", ".pyi", ".js", ".jsx", ".ts", ".tsx",
    ".sh", ".bash", ".zsh",
    ".html", ".css",
    ".json", ".yml", ".yaml", ".toml", ".ini", ".cfg",
    ".go", ".rs", ".java", ".kt", ".c", ".h", ".hpp", ".cpp",
}

# --- Default ignores (can be extended per request) ---
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".cache", "logs", "src-tauri", ".Trash-1000", ".vscode",
}
EXCLUDE_PATHS = {
    os.path.expanduser('~/nova/nova-ui/editor/src-tauri'),
}

IGNORE_ROOT_FILES = {".gitignore"}

# --- Chunking ---
CHUNK_SIZE = 800
OVERLAP = 200


def _get_db():
    os.makedirs(VAULT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT,
            mtime REAL,
            chunk_index INTEGER,
            chunk TEXT,
            embedding BLOB
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS ix_chunks_path ON chunks(path)")
    return conn


def _iter_files(
    paths: List[str] | None = None,
    *,
    ignore_dirs: set | None = None,
    exclude_paths: set | None = None,
    ignore_root_files: set | None = None,
) -> Iterable[str]:
    """Yield files to index under the provided paths (defaults to BASE_DIR)."""
    if paths is None:
        paths = [BASE_DIR]

    eff_ignore_dirs = set(IGNORE_DIRS) | set(ignore_dirs or set())
    eff_exclude_paths = set(EXCLUDE_PATHS) | set(exclude_paths or set())
    eff_ignore_root_files = set(IGNORE_ROOT_FILES) | set(ignore_root_files or set())

    base_abs = os.path.abspath(BASE_DIR)

    seen: set[str] = set()
    for root in paths:
        if not os.path.exists(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Skip entire excluded subtrees
            if any(os.path.abspath(dirpath).startswith(os.path.abspath(p)) for p in eff_exclude_paths):
                dirnames[:] = []
                continue

            # Prune noisy dirs in-place
            dirnames[:] = [d for d in dirnames if d not in eff_ignore_dirs]

            for fn in filenames:
                # Optionally ignore specific files at the BASE_DIR root
                if os.path.abspath(dirpath) == base_abs and fn in eff_ignore_root_files:
                    continue

                p = os.path.join(dirpath, fn)
                ext = os.path.splitext(p)[1].lower()
                if ext in ALLOWED_EXT and p not in seen:
                    seen.add(p)
                    yield p


def _read_file(path: str, max_bytes: int = 1_000_000) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(max_bytes)
    except Exception:
        return ""


def _chunk_text(t: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    if not t:
        return []
    chunks = []
    i = 0
    n = len(t)
    step = max(1, size - overlap)
    while i < n:
        chunks.append(t[i : i + size])
        i += step
    return chunks


def reindex(
    paths: List[str] | None = None,
    clean: bool = False,
    *,
    ignore_dirs: set | None = None,
    exclude_paths: set | None = None,
    ignore_root_files: set | None = None,
) -> Dict[str, Any]:
    """Index text/code across /home/nova by default, writing to vault/rag.db.
    Pass optional overrides for ignores. Safe to re-run; skips up-to-date files.
    """
    model = get_embed_model()
    files_processed = 0
    chunks_indexed = 0

    with _get_db() as db:
        if clean:
            db.execute("DELETE FROM chunks")
        for path in _iter_files(paths, ignore_dirs=ignore_dirs, exclude_paths=exclude_paths, ignore_root_files=ignore_root_files):
            try:
                mtime = os.path.getmtime(path)
            except FileNotFoundError:
                continue
            # Skip up-to-date files
            row = db.execute("SELECT MAX(mtime) as m FROM chunks WHERE path=?", (path,)).fetchone()
            if row and row["m"] and row["m"] >= mtime:
                continue
            db.execute("DELETE FROM chunks WHERE path=?", (path,))

            text = _read_file(path)
            parts = _chunk_text(text)
            if not parts:
                continue

            embs = model.encode(parts)
            for idx, (ck, emb) in enumerate(zip(parts, embs)):
                db.execute(
                    "INSERT INTO chunks(path, mtime, chunk_index, chunk, embedding) VALUES (?,?,?,?,?)",
                    (path, mtime, idx, ck, sqlite3.Binary(np.array(emb, dtype=np.float32).tobytes())),
                )
                chunks_indexed += 1
            files_processed += 1
        db.commit()

    return {"status": "ok", "files_processed": files_processed, "chunks_indexed": chunks_indexed}


def search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    model = get_embed_model()
    q = np.array(model.encode(query), dtype=np.float32)
    with _get_db() as db:
        rows = db.execute("SELECT path, chunk, embedding FROM chunks").fetchall()
    scored = []
    qn = float(np.linalg.norm(q))
    for r in rows:
        emb = np.frombuffer(r["embedding"], dtype=np.float32)
        denom = qn * float(np.linalg.norm(emb))
        score = float(np.dot(q, emb) / denom) if denom else 0.0
        scored.append((score, r["path"], r["chunk"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [{"score": s, "path": p, "content": c} for s, p, c in scored[:top_k]]



RagRouter = APIRouter()

@RagRouter.post("/rag/reindex")
async def rag_reindex(request: Request):
    """
    Rebuild the local RAG index.

    Body (all optional):
      paths: ["/home/nova", ...]
      clean: true|false
      ignore_dirs: [...]
      exclude_paths: [...]
      ignore_root_files: [...]
    """
    body = await request.json()
    paths = body.get("paths") or [BASE_DIR]
    clean = bool(body.get("clean", False))

    # Per-request overrides (your reindex() already supports these)
    ignore_dirs = set(body.get("ignore_dirs", [])) or None
    exclude_paths = set(body.get("exclude_paths", [])) or None
    ignore_root_files = set(body.get("ignore_root_files", [])) or None

    res = reindex(
        paths=paths,
        clean=clean,
        ignore_dirs=ignore_dirs,
        exclude_paths=exclude_paths,
        ignore_root_files=ignore_root_files,
    )
    # res already includes status/files_processed/chunks_indexed
    return JSONResponse(res)

@RagRouter.post("/rag/search")
async def rag_search(request: Request):
    """
    Search the local RAG index.
    Body:
      q: "query string"
      k: top_k (default 5)
    """
    body = await request.json()
    q = body.get("q") or body.get("query") or ""
    k = int(body.get("k", 5))
    hits = search(q, top_k=k)
    return {"hits": hits}

