// editor-bridge.js
(() => {
  const WS_ORIGIN = "ws://127.0.0.1:56969";
  const WS_PATH = "/editor/ws";
  const clientIdKey = "nova.editor.client_id";

  // Stable client id per device/window
  const clientId = (() => {
    let id = localStorage.getItem(clientIdKey);
    if (!id && crypto?.randomUUID) {
      id = crypto.randomUUID();
      localStorage.setItem(clientIdKey, id);
    }
    return id || String(Date.now());
  })();

  let ws = null;
  let backoff = 500;

  const cm = () => (window.Nova && Nova.cm) || window.cm;

  function inject({ content = "", mode = "insert", position = "cursor" } = {}) {
    const e = cm();
    if (!e) return;
    const allLen = e.getValue().length;

    let pos;
    if (position === "start") pos = { line: 0, ch: 0 };
    else if (position === "end") pos = e.posFromIndex(allLen);
    else pos = e.getCursor();

    if (mode === "replace") {
      e.setValue(content);
    } else if (mode === "append") {
      e.replaceRange(content, e.posFromIndex(allLen));
    } else {
      e.replaceRange(content, pos);
    }
    e.focus();
    // mark dirty if you track it
    if (window.Nova) { Nova.isDirty = true; Nova.updateTitle?.(); }
  }

  function snapshot(selection = false) {
    const e = cm();
    return {
      path: window.Nova?.currentPath ?? null,
      content: e ? e.getValue() : "",
      selection: selection && e ? e.getSelection() : null,
    };
  }

  function handleMessage(msg) {
    if (!msg || typeof msg !== "object") return;
    switch (msg.type) {
      case "inject":
        inject(msg);
        break;
      case "snapshot_request": {
        const snap = snapshot(!!msg.selection);
        const reply = { type: "snapshot", id: msg.id, ...snap };
        try { ws?.send(JSON.stringify(reply)); } catch {}
        break;
      }
    }
  }

  function connect() {
    try {
      ws = new WebSocket(`${WS_ORIGIN}${WS_PATH}?client_id=${encodeURIComponent(clientId)}`);
    } catch (e) {
      return setTimeout(connect, backoff = Math.min(5000, backoff * 1.5));
    }

    ws.onopen = () => { backoff = 500; };
    ws.onmessage = (ev) => {
      try { handleMessage(JSON.parse(ev.data)); } catch {}
    };
    ws.onclose = () => {
      setTimeout(connect, backoff = Math.min(5000, backoff * 1.5));
    };
    ws.onerror = () => {
      try { ws.close(); } catch {}
    };
  }

  // Optional global helpers (useful for quick tests)
  window.NovaEditor = {
    inject,
    snapshot,
    getPath: () => window.Nova?.currentPath ?? null,
    clientId,
  };

  window.addEventListener("beforeunload", () => { try { ws?.close(); } catch {} });
  // Start once CM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", connect);
  } else {
    connect();
  }
})();
