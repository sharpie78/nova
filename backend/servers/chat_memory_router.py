import os
import uuid
import sqlite3
import numpy as np
import json

from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from numpy.linalg import norm

ChatMemoryRouter = APIRouter()

BASE_DIR = os.path.expanduser('~/nova')
DB_PATH = os.path.join(BASE_DIR, "vault", "vault.db")
CONFIG_DIR = os.path.join(BASE_DIR, "config")

model = None
def get_model():
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()

    with get_db() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT,
            model TEXT,
            summary TEXT DEFAULT ''
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            chat_id TEXT,
            embedding BLOB
        )
        """)
        db.execute("""
        CREATE TABLE IF NOT EXISTS message_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            tag TEXT
        )
        """)

@ChatMemoryRouter.on_event("startup")
def startup_event():
    init_db()

@ChatMemoryRouter.get("/chat-memory/core")
def get_core_memory():
    with get_db() as db:
        row = db.execute("SELECT id FROM chats WHERE title = 'Core'").fetchone()
        if not row:
            return {"chat_id": None, "messages": []}

        chat_id = row["id"]
        messages = db.execute(
            "SELECT id, role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY id ASC",
            (chat_id,)
        ).fetchall()

        results = []
        for m in messages:
            message_id = m["id"]
            tags = db.execute(
                "SELECT tag FROM message_tags WHERE message_id = ?",
                (message_id,)
            ).fetchall()
            tag_list = [t["tag"] for t in tags]
            results.append({
                "id": message_id,
                "role": m["role"],
                "content": m["content"],
                "timestamp": m["timestamp"],
                "tags": tag_list
            })

        return {
            "chat_id": chat_id,
            "messages": results
        }


@ChatMemoryRouter.post("/chat-memory/core")
async def append_core_memory(request: Request):
    data = await request.json()
    role = data.get("role")
    content = data.get("content")
    if not role or not content:
        return JSONResponse(status_code=400, content={"error": "Missing role or content"})

    with get_db() as db:
        row = db.execute("SELECT id FROM chats WHERE title = 'Core'").fetchone()
        if row:
            chat_id = row["id"]
        else:
            chat_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()
            db.execute(
                "INSERT INTO chats (id, title, created_at, model) VALUES (?, ?, ?, ?)",
                (chat_id, "Core", created_at, "unknown")
            )

        timestamp = datetime.utcnow().isoformat()
        cursor = db.execute(
            "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, timestamp)
        )
        message_id = cursor.lastrowid

        emb = get_model().encode(content)
        db.execute(
            "INSERT INTO embeddings (message_id, chat_id, embedding) VALUES (?, ?, ?)",
            (message_id, chat_id, sqlite3.Binary(np.array(emb, dtype=np.float32).tobytes()))
        )

        # Tagging
        TAGS = ["personal", "preferences", "hardware", "software", "ui", "limits"]
        tag_embeddings = {tag: np.array(get_model().encode(tag), dtype=np.float32) for tag in TAGS}

        emb_array = np.array(emb, dtype=np.float32)
        best_tag = None
        best_score = -1
        for tag, tag_emb in tag_embeddings.items():
            score = float(np.dot(emb_array, tag_emb) / (np.linalg.norm(emb_array) * np.linalg.norm(tag_emb)))
            print(f"Tag: {tag}, Score: {score}")  # Debug print
            if score > best_score:
                best_tag = tag
                best_score = score

        print(f"Best tag chosen: {best_tag} with score {best_score}")  # Debug print

        if best_tag:
            try:
                db.execute("INSERT INTO message_tags (message_id, tag) VALUES (?, ?)", (message_id, best_tag))
                print(f"Inserted tag '{best_tag}' for message {message_id}")  # Debug print
            except Exception as e:
                print(f"Failed to insert tag: {e}")

        db.commit()

    return {"status": "ok", "message_id": message_id}


@ChatMemoryRouter.get("/chat-memory/new")
def create_fresh_new_chat(username: str = Query("default"), temp: str = Query("false")):
    temp = temp.lower() == "true"
    print(f"🔥 Hitting /chat-memory/new for user: {username}, temp: {temp}")

    settings_path = os.path.join(CONFIG_DIR, f"{username}.settings.json")
    chat_history_enabled = True
    try:
        with open(settings_path, "r") as f:
            user_settings = json.load(f)
            chat_history_enabled = user_settings.get("chat", {}).get("chat_history", {}).get("default", True)
    except Exception:
        pass

    with get_db() as db:
        old_row = db.execute("SELECT id FROM chats WHERE title = 'new-chat'").fetchone()
        if old_row:
            old_id = old_row["id"]
            db.execute("DELETE FROM embeddings WHERE chat_id = ?", (old_id,))
            db.execute("DELETE FROM messages WHERE chat_id = ?", (old_id,))
            db.execute("DELETE FROM chats WHERE id = ?", (old_id,))
            print("🗑️ Deleted old new-chat:", old_id)

        chat_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        db.execute(
            "INSERT INTO chats (id, title, created_at, model) VALUES (?, ?, ?, ?)",
            (chat_id, "new-chat", created_at, "unknown")
        )
        db.commit()
        print("📆 Created fresh new-chat:", chat_id)

        # in create_fresh_new_chat()
        core_messages = []
        if chat_history_enabled and not temp:
            core_row = db.execute("SELECT id FROM chats WHERE title = 'Core'").fetchone()
            if core_row:
                core_messages = db.execute(
                    "SELECT id, role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY id ASC",
                    (core_row["id"],)
                ).fetchall()

        return {
            "chat_id": chat_id,
            "messages": [dict(m) for m in core_messages]
        }



@ChatMemoryRouter.get("/chat-memory/tags")
def get_all_tags():
    with get_db() as db:
        rows = db.execute("SELECT DISTINCT tag FROM message_tags ORDER BY tag ASC").fetchall()
        return [row["tag"] for row in rows]




@ChatMemoryRouter.post("/chat-memory/{chat_id}")
async def append_message(chat_id: str, request: Request):
    data = await request.json()
    role = data.get("role")
    content = data.get("content")
    if not role or not content:
        return JSONResponse(status_code=400, content={"error": "Missing role or content."})

    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, datetime.utcnow().isoformat())
        )
        message_id = cursor.lastrowid
        emb = get_model().encode(content)
        db.execute(
            "INSERT INTO embeddings (message_id, chat_id, embedding) VALUES (?, ?, ?)",
            (message_id, chat_id, sqlite3.Binary(np.array(emb, dtype=np.float32).tobytes()))
        )
        db.commit()

    return {"status": "ok", "message_id": message_id}

@ChatMemoryRouter.get("/chat-memory/{chat_id}")
def get_chat(chat_id: str):
    with get_db() as db:
        messages = db.execute(
            "SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY id ASC",
            (chat_id,)
        ).fetchall()
        return {"chat_id": chat_id, "messages": [dict(m) for m in messages]}

@ChatMemoryRouter.get("/chat-memory")
def list_chats():
    with get_db() as db:
        rows = db.execute(
            "SELECT id, title, created_at, model FROM chats ORDER BY created_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]

@ChatMemoryRouter.post("/chat-memory")
async def create_chat(request: Request):
    data = await request.json()
    title = data.get("title", "Untitled")
    model = data.get("model", "unknown")
    chat_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    with get_db() as db:
        db.execute(
            "INSERT INTO chats (id, title, created_at, model) VALUES (?, ?, ?, ?)",
            (chat_id, title, created_at, model)
        )
        db.commit()

    return {"chat_id": chat_id, "title": title, "created_at": created_at, "model": model}

@ChatMemoryRouter.delete("/chat-memory/core/{message_id}")
def delete_core_memory_message(message_id: int):
    with get_db() as db:
        # Find the core chat
        row = db.execute("SELECT id FROM chats WHERE title = 'Core'").fetchone()
        if not row:
            return JSONResponse(status_code=404, content={"error": "Core chat not found"})

        core_chat_id = row["id"]

        # Ensure the message belongs to Core chat
        message_row = db.execute(
            "SELECT id FROM messages WHERE id = ? AND chat_id = ?",
            (message_id, core_chat_id)
        ).fetchone()
        if not message_row:
            return JSONResponse(status_code=404, content={"error": "Message not found in Core chat"})

        # Delete related entries
        db.execute("DELETE FROM embeddings WHERE message_id = ?", (message_id,))
        db.execute("DELETE FROM message_tags WHERE message_id = ?", (message_id,))
        db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        db.commit()

        return {"status": "ok", "message_id": message_id}



@ChatMemoryRouter.post("/chat-memory/embed/{chat_id}")
def embed_chat(chat_id: str):
    with get_db() as db:
        messages = db.execute("SELECT id, content FROM messages WHERE chat_id = ?", (chat_id,)).fetchall()
        for m in messages:
            emb = get_model().encode(m["content"])
            db.execute(
                "INSERT INTO embeddings (message_id, chat_id, embedding) VALUES (?, ?, ?)",
                (m["id"], chat_id, sqlite3.Binary(np.array(emb, dtype=np.float32).tobytes()))
            )
        db.commit()
    return {"status": "ok"}

@ChatMemoryRouter.get("/chat-memory/query")
def query_memory(q: str):
    query_emb = get_model().encode(q)
    query_emb = np.array(query_emb, dtype=np.float32)

    with get_db() as db:
        rows = db.execute("SELECT e.embedding, m.role, m.content FROM embeddings e JOIN messages m ON m.id = e.message_id").fetchall()

    scored = []
    for row in rows:
        emb = np.frombuffer(row["embedding"], dtype=np.float32)
        score = float(np.dot(query_emb, emb) / (norm(query_emb) * norm(emb)))
        scored.append((score, row["role"], row["content"]))

    scored.sort(reverse=True)
    return {
        "matches": [{"role": role, "content": content, "score": score} for score, role, content in scored[:5]]
    }

@ChatMemoryRouter.post("/chat-memory/tag/{message_id}")
async def tag_message(message_id: int, request: Request):
    data = await request.json()
    tag = data.get("tag")
    if not tag:
        return JSONResponse(status_code=400, content={"error": "Missing tag"})

    with get_db() as db:
        db.execute("INSERT INTO message_tags (message_id, tag) VALUES (?, ?)", (message_id, tag))
        db.commit()

    return {"status": "ok"}

@ChatMemoryRouter.get("/chat-memory/tag/{tag}")
def get_messages_by_tag(tag: str):
    with get_db() as db:
        rows = db.execute("""
            SELECT m.id, m.chat_id, m.role, m.content, m.timestamp
            FROM messages m
            JOIN message_tags t ON m.id = t.message_id
            WHERE t.tag = ?
            ORDER BY m.timestamp ASC
        """, (tag,)).fetchall()

    return {"messages": [dict(row) for row in rows]}

