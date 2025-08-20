# =============================
# File: /home/nova/nova-tray/servers/agent_tools.py
# =============================
from __future__ import annotations

import os, re, time
import requests
import numpy as np
from typing import Dict, Any, List
from datetime import datetime

try:
    import zoneinfo  # py3.9+
except Exception:
    zoneinfo = None

from .chat_memory_router import get_db as get_chat_db, get_model as get_embed_model
from . import rag_store

SEARX_URL = os.environ.get("SEARX_URL", "http://127.0.0.1:8888")
WEBFOX_URL = os.environ.get("WEBFOX_URL", "http://127.0.0.1:8070")

# Base URL for this API (FastAPI) so tools can talk to the editor bridge.
# Override with NOVA_API_URL if your port differs.
API_BASE = os.environ.get("NOVA_API_URL", "http://127.0.0.1:56969")

# ----------------
# MEMORY
# ----------------

def search_memory(query: str, top_k: int = 5) -> Dict[str, Any]:
    model = get_embed_model()
    q_emb = np.array(model.encode(query), dtype=np.float32)
    with get_chat_db() as db:
        rows = db.execute(
            "SELECT e.embedding, m.role, m.content FROM embeddings e JOIN messages m ON m.id = e.message_id"
        ).fetchall()
    scored = []
    for r in rows:
        emb = np.frombuffer(r["embedding"], dtype=np.float32)
        denom = float(np.linalg.norm(q_emb) * np.linalg.norm(emb))
        score = float(np.dot(q_emb, emb) / denom) if denom else 0.0
        scored.append((score, r["role"], r["content"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [{"score": s, "role": role, "content": content} for s, role, content in scored[:top_k]]
    return {"type": "memory", "query": query, "hits": hits}

# ----------------
# RAG
# ----------------

def rag_search(query: str, top_k: int = 5) -> Dict[str, Any]:
    results = rag_store.search(query, top_k=top_k)
    return {"type": "rag", "query": query, "hits": results}

# ----------------
# TIME (local system clock)
# ----------------

def time_now(_: str = "") -> Dict[str, Any]:
    tz = None
    if zoneinfo:
        try:
            tz = zoneinfo.ZoneInfo("Europe/London")
        except Exception:
            tz = None
    now = datetime.now(tz) if tz else datetime.now()
    iso = now.isoformat()
    pretty = now.strftime("%A, %d %B %Y, %H:%M")
    return {"type": "time", "now_iso": iso, "pretty": pretty}

# ----------------
# WEB
# ----------------

def _searx_search(query: str, *, engines: List[str] | None = None, site: str | None = None, max_results: int = 5) -> List[Dict[str, Any]]:
    if site:
        query = f"site:{site} {query}" if query else f"site:{site}"
    params = {
        "q": query,
        "format": "json",
        "language": "en-GB",
        "safesearch": 1,
    }
    if engines:
        params["engines"] = ",".join(engines)
    try:
        resp = requests.get(f"{SEARX_URL}/search", params=params, timeout=12)
        data = resp.json()
        results = data.get("results", [])[:max_results]
        return [{"title": r.get("title"), "href": r.get("url"), "content": r.get("content")} for r in results]
    except Exception:
        return []


def _fetch_text(url: str, timeout: int = 12) -> str:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        return " ".join(soup.stripped_strings)[:1600]
    except Exception:
        return ""


def _looks_like_jswall(text: str) -> bool:
    s = (text or "").lower()
    return (len(s) < 200) or ("enable javascript" in s) or ("consent" in s and "cookie" in s)


def _browse(url: str, screenshot: bool = True) -> Dict[str, Any]:
    try:
        r = requests.post(f"{WEBFOX_URL}/browse", json={"url": url, "screenshot": bool(screenshot)}, timeout=20)
        j = r.json()
        return {
            "url": url,
            "snippet": (j.get("text") or "")[:1200],
            "screenshot": j.get("screenshot")
        }
    except Exception:
        return {"url": url, "snippet": _fetch_text(url) or ""}

def browse_url(url: str, screenshot: bool = False) -> Dict[str, Any]:
    return _browse(url, screenshot=bool(screenshot))


def web_search(query: str, *, prefer_site: str | None = None, max_results: int = 5, fetch_pages: int = 1, screenshot: bool = True, ensure_page: bool = False) -> Dict[str, Any]:
    hits = _searx_search(query, site=prefer_site, max_results=max_results)
    pages: List[Dict[str, Any]] = []

    # Try to fetch up to fetch_pages pages, escalating to browser when JS walls suspected
    for h in hits[:fetch_pages]:
        url = (h or {}).get("href")
        if not url:
            continue
        txt = _fetch_text(url)
        if _looks_like_jswall(txt):
            pages.append(_browse(url, screenshot=screenshot))
        else:
            pages.append({"url": url, "snippet": txt})

    # If caller insists on a page and we have none yet, browse the first hit
    if ensure_page and not pages and hits:
        url0 = (hits[0] or {}).get("href")
        if url0:
            pages.append(_browse(url0, screenshot=screenshot))

    return {"type": "web", "query": query, "hits": hits, "pages": pages}


# Site-specific convenience

def web_ground_news(query: str) -> Dict[str, Any]:
    # Always ensure we have at least one browsed page for Ground
    res = web_search(query, prefer_site="ground.news", max_results=5, fetch_pages=1, screenshot=True, ensure_page=True)
    # If still no pages (no hits), direct UK page fallback
    if not res.get("pages"):
        res["hits"] = [{
            "title": "United Kingdom Breaking News Headlines Today | Ground News",
            "href": "https://ground.news/interest/united-kingdom",
            "content": ""
        }]
        res["pages"] = [_browse("https://ground.news/interest/united-kingdom", screenshot=True)]
    return res


def web_metoffice(place: str) -> Dict[str, Any]:
    q = place or ""
    # Always ensure one page for Met Office
    res = web_search(q or "forecast", prefer_site="metoffice.gov.uk", max_results=5, fetch_pages=1, screenshot=False, ensure_page=True)
    return res


# ----------------
# EDITOR BRIDGE (WebSocket-backed HTTP helpers)
# ----------------

def editor_list_clients() -> Dict[str, Any]:
    try:
        r = requests.get(f"{API_BASE}/editor/clients", timeout=4)
        return r.json()
    except Exception as e:
        return {"error": f"editor_list_clients_failed: {e}"}

def _normalize_cid(cid: str | None) -> str:
    s = (cid or "").strip()
    return "" if s.lower() in {"", "null", "none", "undefined"} else s

def _resolve_client_id(preferred: str | None) -> tuple[str | None, Dict[str, Any] | None]:
    """
    Returns (cid, err). If err is not None, it's an error dict to return to the caller.
    Picks the single connected client if preferred is missing/wrong.
    """
    info = editor_list_clients()
    ids = list((info or {}).get("clients") or [])
    want = _normalize_cid(preferred)

    if want and want in ids:
        return want, None
    if len(ids) == 1:
        return ids[0], None
    if len(ids) == 0:
        return None, {"error": "no_editor_client"}
    # multiple
    return None, {"error": "multiple_editor_clients", "clients": ids}

def editor_snapshot(client_id: str, selection: bool = True) -> Dict[str, Any]:
    try:
        cid, err = _resolve_client_id(client_id)
        if err:
            return err
        params = {"selection": str(bool(selection)).lower()}
        if cid:
            params["client_id"] = cid
        r = requests.get(f"{API_BASE}/editor/agent/snapshot", params=params, timeout=6)
        if r.status_code == 404:
            # retry once with auto-pick (omit cid)
            r = requests.get(f"{API_BASE}/editor/agent/snapshot", params={"selection": params["selection"]}, timeout=6)
        if r.status_code != 200:
            return {"error": f"snapshot_failed: {r.text}"}
        j = r.json() or {}
        return {
            "type": "editor_snapshot",
            "client_id": j.get("client_id") or cid,
            "path": j.get("path"),
            "content": j.get("content") or "",
            "selection": j.get("selection"),
        }
    except Exception as e:
        return {"error": f"editor_snapshot_failed: {e}"}

def editor_inject(client_id: str, content: str, mode: str = "insert", position: str = "cursor") -> Dict[str, Any]:
    try:
        cid, err = _resolve_client_id(client_id)
        if err:
            return err
        payload = {"content": content, "mode": mode, "position": position}
        if cid:
            payload["client_id"] = cid
        r = requests.post(f"{API_BASE}/editor/agent/inject", json=payload, timeout=6)
        if r.status_code == 404:
            # retry once with auto-pick (omit cid)
            r = requests.post(f"{API_BASE}/editor/agent/inject", json={"content": content, "mode": mode, "position": position}, timeout=6)
        if r.status_code != 200:
            return {"error": f"inject_failed: {r.text}"}
        j = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
        return {
            "type": "editor_inject",
            "ok": True,
            "client_id": (j or {}).get("client_id") or cid,
            "chars": len(content),
            "mode": mode,
            "position": position
        }
    except Exception as e:
        return {"error": f"editor_inject_failed: {e}"}

def editor_clipboard_read() -> Dict[str, Any]:
    try:
        r = requests.get(f"{API_BASE}/clipboard/read", timeout=4)
        j = r.json()
        return {"type": "clipboard_read", "text": j.get("text", "")}
    except Exception as e:
        return {"error": f"clipboard_read_failed: {e}"}

def editor_clipboard_write(text: str) -> Dict[str, Any]:
    try:
        r = requests.post(f"{API_BASE}/clipboard/write", json={"text": text}, timeout=4)
        if r.status_code != 200:
            return {"error": f"clipboard_write_failed: {r.text}"}
        return {"type": "clipboard_write", "ok": True, "chars": len(text)}
    except Exception as e:
        return {"error": f"clipboard_write_failed: {e}"}
