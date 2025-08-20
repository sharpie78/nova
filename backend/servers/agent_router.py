# =============================
# File: /home/nova/nova-tray/servers/agent_router.py
# Full replacement
# =============================
from __future__ import annotations
import os
import re
import json
from typing import List, Dict, Any, Tuple, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from utils.ollama_client import OllamaClient
from utils.logger import logger, setup_logger

import servers.agent_tools as agent_tools
import servers.rag_store as rag_store

setup_logger()
logger = logger.bind(name="Agent")

AgentRouter = APIRouter()

# Sticky editor choice per-chat (or per-username fallback)
PREFERRED_EDITOR: Dict[str, str] = {}

AGENT_PROMPT = """You are NovaAgent. Decide whether to answer or call a tool.
Tools:
- search_memory(input: string) — chat/notes memory.
- rag_search(input: string) — local documents & code.
- web_search(input: string) — the web (SearXNG + sandboxed browser).
- web_ground(input: string) — Ground News only (browsed).
- web_metoffice(input: string) — Met Office only (browsed).
- time_now(input: string) — return local system date/time.
- editor_snapshot(input: string) — read the active editor.
  INPUT format: "client_id=<id>; selection=true|false"
- editor_inject(input: string) — write to the editor live buffer.
  INPUT format: "client_id=<id>; mode=insert|replace|append; position=cursor|start|end; text=…"
- editor_clipboard_read(input: string) — read system clipboard (ignores input).
- editor_clipboard_write(input: string) — write to system clipboard.
  INPUT format: "text=…"
Rules:
- If user asks about code/files/paths ("where in my code", filenames, ~/ or /home/), call rag_search first.
- If message contains a URL or a domain, prefer web_search.
- News/headlines → web_ground. Weather/forecast → web_metoffice.
- "what's the date/time/today/now" → time_now.
- For editor tools:
  • Never invent a client_id. If unknown, omit it or set client_id=null; the system will resolve.
  • Read before write: call editor_snapshot to inspect buffer/selection first.
  • Respect selection/cursor: if user says "replace my selection" or "insert at cursor", use position=cursor and confirm selection=true in snapshot.
  • Prefer insert/append; use replace only when the user is explicit about overwriting.
  • Verify after write: snapshot again and confirm the change landed (contains/length check). Retry once if needed.
  • If multiple editor windows are open, ask the user which to use using the IDs provided by the system, then include that client_id in subsequent editor tool calls.
- After any tool call, return a clear final answer.
- For rag_search: include top file paths & 1–2 short quoted lines per file.
- For web_*: summarize and include the domains in text.
Reply ONLY with compact JSON on one line:
{"action":"answer","input":"..."}
{"action":"search_memory","input":"..."}
{"action":"rag_search","input":"..."}
{"action":"web_search","input":"..."}
{"action":"web_ground","input":"..."}
{"action":"web_metoffice","input":"..."}
{"action":"time_now","input":"..."}
{"action":"editor_snapshot","input":"client_id=...; selection=true"}
{"action":"editor_inject","input":"client_id=...; mode=insert; position=cursor; text=..."}
{"action":"editor_clipboard_read","input":""}
{"action":"editor_clipboard_write","input":"text=..."}
"""


def _call_llm_json(model: str, messages: List[Dict[str, str]]):
    ol = OllamaClient()
    txt = ""
    for chunk in ol.fetch_chat_stream_result(messages, model):
        txt += chunk
    try:
        return json.loads(txt.strip())
    except Exception:
        m = re.search(r"\{.*\}", txt, flags=re.S)
        if not m:
            raise ValueError("Model did not return JSON")
        return json.loads(m.group(0))


def _choose_auto_tool(msg: str) -> str | None:
    s = (msg or "").lower()
    if any(k in s for k in ["headline", "front page", "top news", "today in news"]):
        return "web:ground"
    if any(k in s for k in ["weather", "forecast", "met office", "metoffice"]):
        return "web:metoffice"
    if any(k in s for k in ["what's the date", "what is the date", "today's date", "what's the time", "time now", "date today", "today now", "what day is it"]):
        return "time"
    if "http://" in s or "https://" in s or re.search(r"\b([a-z0-9-]+\.)+[a-z]{2,}\b", s):
        return "web"
    if any(k in s for k in ["readme", "readme.md", "/mnt/", "/home/", "~/", "where in my code", "path", "file", ".py", ".js", ".ts", ".html", ".css", ".json"]):
        return "rag"
    if any(k in s for k in ["what did i say", "notes", "last time", "my hardware", "you said"]):
        return "memory"
    # intentionally do not auto-pick editor tools here (require ID resolution)
    return None


def _parse_editor_input(value: str) -> Dict[str, str]:
    def grab(pat: str, default: str = "") -> str:
        m = re.search(pat, value or "", flags=re.I | re.S)
        return (m.group(1).strip() if m else default)
    return {
        "client_id": grab(r"client_id\s*=\s*([^;]+)", ""),
        "selection": grab(r"selection\s*=\s*(true|false)", "").lower(),
        "mode":      grab(r"mode\s*=\s*([a-z]+)", "insert").lower(),
        "position":  grab(r"position\s*=\s*([a-z]+)", "cursor").lower(),
        "text":      grab(r"text\s*=\s*(.*)", ""),
    }


def _normalize_cid(cid: Optional[str]) -> str:
    s = (cid or "").strip()
    return "" if s.lower() in {"", "null", "none", "undefined", "auto"} else s


def _resolve_editor_client_id(chat_key: Optional[str], requested_id: Optional[str]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Router-side resolution with sticky per-chat choice:
      - If chat has a preferred id and it's connected → use it (unless request asked for a different connected one).
      - If requested_id is valid and connected → use it (and persist for chat).
      - If none connected → error.
      - If exactly one connected → use it (and persist for chat).
      - If multiple connected → ask user to choose.
    """
    info = agent_tools.editor_list_clients() or {}   # :contentReference[oaicite:0]{index=0}
    ids = list(info.get("clients") or [])
    want = _normalize_cid(requested_id)

    # 1) If user asked for a specific connected id, lock it in
    if want and want in ids:
        if chat_key:
            PREFERRED_EDITOR[chat_key] = want
        return want, None

    # 2) If chat already picked one and it's still connected, use it
    if chat_key:
        pref = PREFERRED_EDITOR.get(chat_key)
        if pref in ids:
            return pref, None
        # drop stale preference
        if pref and pref not in ids:
            PREFERRED_EDITOR.pop(chat_key, None)

    # 3) No preference yet: choose based on how many are connected
    if len(ids) == 0:
        return None, {"error": "no_editor_client"}
    if len(ids) == 1:
        if chat_key:
            PREFERRED_EDITOR[chat_key] = ids[0]
        return ids[0], None

    # 4) Multiple: ask to choose
    return None, {"error": "multiple_editor_clients", "clients": ids}


def _maybe_capture_editor_choice(chat_key: Optional[str], msg: str) -> Optional[str]:
    """
    If the user says 'use editor 2' or pastes an id/prefix, set sticky preference.
    Returns chosen id or None.
    """
    if not chat_key:
        return None
    text = (msg or "").strip().lower()
    info = agent_tools.editor_list_clients() or {}
    ids = list(info.get("clients") or [])

    # 'use editor 2'
    m = re.search(r"\buse\s+editor\s+(\d+)\b", text)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(ids):
            PREFERRED_EDITOR[chat_key] = ids[idx]
            return ids[idx]

    # 'use <uuid>' or prefix
    m2 = re.search(r"\buse\s+([0-9a-f-]{6,})\b", text)
    if m2:
        token = m2.group(1)
        for cid in ids:
            if cid.lower().startswith(token):
                PREFERRED_EDITOR[chat_key] = cid
                return cid
    return None


def _run_tool(kind: str, value: str, tools_used: list, chat_key: Optional[str] = None):
    if kind == "search_memory":
        res = agent_tools.search_memory(value)
        tools_used.append({"kind":"Memory","data":res})
        return res
    if kind == "rag_search":
        res = agent_tools.rag_search(value)
        tools_used.append({"kind":"RAG","data":res})
        return res
    if kind == "web_search":
        res = agent_tools.web_search(value, prefer_site=None)
        tools_used.append({"kind":"Web","data":res})
        return res
    if kind == "web_ground":
        res = agent_tools.web_ground_news(value)
        tools_used.append({"kind":"Web","data":res})
        return res
    if kind == "web_metoffice":
        res = agent_tools.web_metoffice(value)
        tools_used.append({"kind":"Web","data":res})
        return res
    if kind == "time_now":
        res = agent_tools.time_now(value)
        tools_used.append({"kind":"Time","data":res})
        return res

    # ---- Editor tools with router-side client auto-resolution + sticky choice ----
    if kind in {"editor_snapshot", "editor_inject", "editor_clipboard_read", "editor_clipboard_write"}:
        parsed = _parse_editor_input(value)
        requested_id = parsed.get("client_id")
        cid, err = _resolve_editor_client_id(chat_key, requested_id)

        if err and err.get("error") == "no_editor_client":
            answer = "I can't see any editor window connected. Please open the editor and try again."
            tools_used.append({"kind":"Editor","data":err})
            return {"_router_answer": answer}

        if err and err.get("error") == "multiple_editor_clients":
            ids = err.get("clients") or []
            pretty = "\n".join([f"{i+1}) {ids[i]}" for i in range(len(ids))])
            answer = (
                "Multiple editor windows are open. Which one should I use?\n"
                f"{pretty}\n\n"
                "Reply with the client ID, or say 'use editor 1' / 'use editor 2'."
            )
            tools_used.append({"kind":"Editor","data":err})
            return {"_router_answer": answer}

        # With a resolved client id, run the actual editor tool
        if kind == "editor_snapshot":
            sel = parsed.get("selection", "false") == "true"
            res = agent_tools.editor_snapshot(cid or "", selection=sel)
            # store sticky on success
            if chat_key and res.get("type") == "editor_snapshot" and (cid or res.get("client_id")):
                PREFERRED_EDITOR[chat_key] = (cid or res.get("client_id"))
            tools_used.append({"kind":"Editor","data":res})
            return res

        if kind == "editor_inject":
            mode = parsed.get("mode", "insert")
            pos  = parsed.get("position", "cursor")
            text = parsed.get("text", "")
            res = agent_tools.editor_inject(cid or "", text, mode=mode, position=pos)
            if chat_key and (cid or res.get("client_id")):
                PREFERRED_EDITOR[chat_key] = (cid or res.get("client_id"))
            tools_used.append({"kind":"Editor","data":res})
            return res

        if kind == "editor_clipboard_read":
            res = agent_tools.editor_clipboard_read()
            tools_used.append({"kind":"Clipboard","data":res})
            return res

        if kind == "editor_clipboard_write":
            res = agent_tools.editor_clipboard_write(parsed.get("text",""))
            tools_used.append({"kind":"Clipboard","data":res})
            return res

    raise ValueError(f"unknown action {kind}")


def _collect_sources(tools_used: list, max_items: int = 3):
    sources = []
    for t in tools_used:
        kind = t.get("kind")
        data = t.get("data", {})
        if kind == "RAG":
            for h in (data.get("hits") or [])[:max_items]:
                sources.append({"kind":"file", "path": h.get("path"), "snippet": (h.get("content") or "")[:240]})
        elif kind == "Web":
            pages = data.get("pages") or []
            hits = data.get("hits") or []
            if pages:
                for p in pages[:max_items]:
                    src = {"kind":"url", "url": p.get("url"), "snippet": (p.get("snippet") or "")[:240]}
                    if p.get("screenshot"):
                        src["screenshot"] = p.get("screenshot")
                    sources.append(src)
            else:
                for h in hits[:max_items]:
                    sources.append({"kind":"url", "url": h.get("href"), "snippet": (h.get("content") or "")[:240]})
        # Time/Memory/Editor have no external sources
    return sources



@AgentRouter.post("/agent")
async def agent_entry(request: Request):
    body = await request.json()
    model = body.get("model")
    message = body.get("message")
    tool_hint = (body.get("tool_hint") or "").lower().strip()  # 'auto'|'memory'|'rag'|'web'
    chat_id = (body.get("chat_id") or "").strip() or (body.get("username") or "").strip()
    max_steps = int(body.get("max_steps", 3))

    if not model or not message:
        return JSONResponse(status_code=400, content={"error":"model and message are required"})

    # If user said "use editor N/ID", capture sticky choice and acknowledge
    chosen = _maybe_capture_editor_choice(chat_id, message)
    if chosen:
        return {"answer": f"Okay — I’ll use editor `{chosen}` for this chat.", "steps": 0, "tools_used": [], "sources": []}

    messages = [
        {"role":"system","content":AGENT_PROMPT},
        {"role":"user","content":message}
    ]

    tools_used: List[Dict[str, Any]] = []

    # Forced or heuristic first tool (editor tools are intentionally not auto-picked)
    first = None
    if tool_hint in {"memory","rag","web"}:
        first = tool_hint
    else:
        first = _choose_auto_tool(message)

    def map_first(tag: str | None):
        if not tag:
            return None
        if tag == "memory": return "search_memory"
        if tag == "rag": return "rag_search"
        if tag == "web": return "web_search"
        if tag == "web:ground": return "web_ground"
        if tag == "web:metoffice": return "web_metoffice"
        if tag == "time": return "time_now"
        return None

    mapped = map_first(first)
    if mapped:
        tool_res = _run_tool(mapped, message, tools_used, chat_key=chat_id)
        if isinstance(tool_res, dict) and tool_res.get("_router_answer"):
            return {"answer": tool_res["_router_answer"], "steps": 0, "tools_used": tools_used, "sources": _collect_sources(tools_used)}
        messages.extend([
            {"role":"assistant","content":json.dumps({"action": mapped, "input": message})},
            {"role":"user","content":"Tool result:\n" + json.dumps(tool_res) + "\nNow respond ONLY with final JSON: {\"action\":\"answer\",\"input\":\"...\"}"}
        ])
        try:
            action = _call_llm_json(model, messages)
            if action.get("action") == "answer":
                return {"answer": action.get("input",""), "steps": 1, "tools_used": tools_used, "sources": _collect_sources(tools_used)}
        except Exception as e:
            logger.error(f"Parse error after forced tool: {e}")
            return JSONResponse(status_code=500, content={"error": f"agent_parse_error: {e}"})

    # Fallback loop
    for step in range(max_steps):
        try:
            action = _call_llm_json(model, messages)
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return JSONResponse(status_code=500, content={"error": f"agent_parse_error: {e}"})

        kind = action.get("action")
        value = action.get("input", "")
        if kind == "answer":
            return {"answer": value, "steps": step+1, "tools_used": tools_used, "sources": _collect_sources(tools_used)}

        if kind in {
            "search_memory","rag_search","web_search","web_ground","web_metoffice","time_now",
            "editor_snapshot","editor_inject","editor_clipboard_read","editor_clipboard_write"
        }:
            tool_res = _run_tool(kind, value, tools_used, chat_key=chat_id)
        else:
            return JSONResponse(status_code=400, content={"error": f"unknown action {kind}"})

        if isinstance(tool_res, dict) and tool_res.get("_router_answer"):
            return {"answer": tool_res["_router_answer"], "steps": step+1, "tools_used": tools_used, "sources": _collect_sources(tools_used)}

        messages.extend([
            {"role":"assistant","content":json.dumps(action)},
            {"role":"user","content":"Tool result:\n" + json.dumps(tool_res) + "\nNow respond ONLY with final JSON: {\"action\":\"answer\",\"input\":\"...\"}"}
        ])

    return JSONResponse(status_code=500, content={"error":"max_steps_exceeded"})


@AgentRouter.post('/web/browse')
async def web_browse(request: Request):
    try:
        body = await request.json()
        url = (body.get('url') or '').strip()
        shot = bool(body.get('screenshot'))
        if not url:
            return JSONResponse(status_code=400, content={'error':'missing url'})
        page = agent_tools.browse_url(url, screenshot=shot)
        sc = page.get('screenshot')
        if sc and sc.startswith('/shots/'):
            fname = os.path.basename(sc)
            home = os.path.expanduser('~')
            page['screenshot'] = f'file://{home}/nova/tmp/webshots/{fname}'
        return page
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': f'browse_failed: {e}'})


@AgentRouter.post("/rag/reindex")
def rag_reindex(clean: bool = False):
    return rag_store.reindex(clean=clean)
