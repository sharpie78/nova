// File: nova-ui/js/chat/agent-ui.js
// Restores eager "Sources" rendering with auto-fetch of each URL.

// ---------- Agent toggle + chips ----------
(function () {
  const state = {
    enabled: JSON.parse(localStorage.getItem("novaAgentEnabled") || "false"),
    hint: localStorage.getItem("novaAgentHint") || "auto",
  };
  window.NOVA_AGENT = state;

  // API base for fetch buttons + auto-fetch
  window.API_BASE = window.API_BASE || "http://127.0.0.1:56969";

  function chip(text, value) {
    const b = document.createElement("button");
    b.textContent = text;
    b.dataset.value = value;
    Object.assign(b.style, {
      padding: "4px 8px",
      borderRadius: "6px",
      border: "1px solid #444",
      background: "#2a2a2a",
      color: "#ddd",
      cursor: "pointer",
      fontSize: "12px",
      opacity: value === state.hint ? "1" : "0.6",
    });
    b.addEventListener("click", () => {
      state.hint = value;
      localStorage.setItem("novaAgentHint", state.hint);
      [...b.parentElement.children].forEach((x) => {
        x.style.opacity = x.dataset.value === state.hint ? "1" : "0.6";
      });
    });
    return b;
  }

  function renderControls() {
    const top =
      document.querySelector(".top-controls-container") ||
      document.getElementById("chat-options");
    if (!top || document.getElementById("agent-controls")) return;

    const wrap = document.createElement("div");
    wrap.id = "agent-controls";
    Object.assign(wrap.style, {
      display: "flex",
      alignItems: "center",
      gap: "10px",
      marginLeft: "10px",
    });

    const label = document.createElement("label");
    Object.assign(label.style, { display: "flex", alignItems: "center", gap: "6px" });
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = !!state.enabled;
    cb.addEventListener("change", () => {
      state.enabled = cb.checked;
      localStorage.setItem("novaAgentEnabled", JSON.stringify(state.enabled));
    });
    const span = document.createElement("span");
    span.textContent = "Agent mode";
    label.append(cb, span);

    const chips = document.createElement("div");
    Object.assign(chips.style, { display: "flex", gap: "6px" });
    chips.append(chip("Auto", "auto"), chip("Memory", "memory"), chip("RAG", "rag"), chip("Web", "web"));

    wrap.append(label, chips);
    top.appendChild(wrap);
  }

  document.addEventListener("DOMContentLoaded", renderControls);
})();

// ---------- Badge ----------
window.renderAgentBadge = function (parentEl, used) {
  if (!parentEl) return;
  const badge = document.createElement("span");
  badge.textContent = used ? `Used: ${used}` : "Agent";
  Object.assign(badge.style, {
    marginLeft: "8px",
    padding: "2px 6px",
    border: "1px solid #444",
    borderRadius: "6px",
    fontSize: "11px",
    opacity: "0.7",
  });
  parentEl.appendChild(badge);
};

// ---------- Sources (auto-fetch) ----------
window.renderAgentSources = function (parentEl, sources) {
  if (!parentEl || !Array.isArray(sources) || sources.length === 0) return;

  const det = document.createElement("details");
  det.style.marginTop = "8px";

  const sum = document.createElement("summary");
  sum.textContent = `Sources (${sources.length})`;
  sum.style.cursor = "pointer";
  det.appendChild(sum);

  const list = document.createElement("div");
  Object.assign(list.style, { display: "grid", gap: "8px" });
  det.appendChild(list);

  sources.forEach((s) => {
    const card = document.createElement("div");
    Object.assign(card.style, {
      border: "1px solid #444",
      borderRadius: "6px",
      padding: "8px",
      background: "#1e1e1e",
    });

    let pre = null;

    if (s.kind === "url") {
      const a = document.createElement("a");
      a.href = s.url || "#";
      a.target = "_blank";
      a.rel = "noreferrer";
      a.textContent = safeHost(s.url || "") || s.url || "(url)";
      a.style.fontWeight = "600";
      card.appendChild(a);

      pre = document.createElement("pre");
      pre.textContent = (s.snippet || "").trim();
      Object.assign(pre.style, {
        whiteSpace: "pre-wrap",
        marginTop: "6px",
        fontSize: "12px",
        background: "#161616",
        padding: "6px",
        borderRadius: "4px",
      });
      card.appendChild(pre);

      if (s.screenshot) {
        const img = document.createElement("img");
        img.src = s.screenshot;
        img.alt = "screenshot";
        Object.assign(img.style, {
          maxWidth: "100%",
          marginTop: "6px",
          borderRadius: "4px",
          border: "1px solid #333",
        });
        card.appendChild(img);
      }

      // Tools row
      const tools = document.createElement("div");
      Object.assign(tools.style, { display: "flex", gap: "8px", marginTop: "6px" });

      const fetchBtn = document.createElement("button");
      fetchBtn.textContent = "Refresh details";
      Object.assign(fetchBtn.style, btnStyle());
      fetchBtn.addEventListener("click", () => runBrowse(s.url, false, pre, tools, fetchBtn, shotBtn));

      const shotBtn = document.createElement("button");
      shotBtn.textContent = "📷";
      shotBtn.title = "Capture screenshot";
      Object.assign(shotBtn.style, btnStyle());
      shotBtn.addEventListener("click", () => runBrowse(s.url, true, pre, tools, fetchBtn, shotBtn));

      tools.append(fetchBtn, shotBtn);
      card.appendChild(tools);

      // Eager fetch (to match the old behavior)
      // If there’s no snippet or it looks too short, fetch; otherwise still refresh to get live text.
      const shouldEager =
        !(s.snippet && s.snippet.trim().length > 40);
      setTimeout(() => runBrowse(s.url, false, pre, tools, fetchBtn, shotBtn, /*silent*/ shouldEager ? false : true), 0);
    }

    if (s.kind === "file") {
      const head = document.createElement("div");
      head.textContent = s.path || "(file)";
      head.style.fontWeight = "600";
      card.appendChild(head);

      const filePre = document.createElement("pre");
      filePre.textContent = (s.snippet || "").trim();
      Object.assign(filePre.style, {
        whiteSpace: "pre-wrap",
        marginTop: "6px",
        fontSize: "12px",
        background: "#161616",
        padding: "6px",
        borderRadius: "4px",
      });
      card.appendChild(filePre);
    }

    list.appendChild(card);
  });

  parentEl.appendChild(det);

  function safeHost(u) {
    try {
      return new URL(u).hostname;
    } catch {
      return u;
    }
  }

  function btnStyle() {
    return {
      fontSize: "11px",
      padding: "2px 6px",
      borderRadius: "6px",
      border: "1px solid #444",
      background: "#262626",
      color: "#ddd",
      cursor: "pointer",
    };
  }

  async function runBrowse(url, screenshot, preEl, toolsEl, fetchBtn, shotBtn, silent = false) {
    const API = String(window.API_BASE || window.API_BASE_URL || "").replace(/\/$/, "");
    try {
      fetchBtn.disabled = true;
      shotBtn.disabled = true;
      if (!silent) fetchBtn.textContent = screenshot ? "Fetching… 📷" : "Fetching…";

      const res = await fetch(`${API}/web/browse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, screenshot: !!screenshot }),
      });
      const j = await res.json();

      if (j && j.snippet && preEl) preEl.textContent = j.snippet;

      if (j && j.screenshot) {
        const cam = document.createElement("a");
        cam.textContent = "📷 open";
        cam.href = j.screenshot; // file:// path provided by server (Tauri displays it)
        cam.target = "_blank";
        cam.style.marginLeft = "8px";
        toolsEl.appendChild(cam);
      }

      fetchBtn.textContent = "Refresh details";
    } catch (e) {
      console.error("browse failed", e);
      fetchBtn.textContent = "Retry fetch";
    } finally {
      fetchBtn.disabled = false;
      shotBtn.disabled = false;
    }
  }
};
