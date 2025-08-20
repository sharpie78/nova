let cm = CodeMirror.fromTextArea(document.getElementById("editor"), {
  lineNumbers: true,
  mode: "plaintext",
  theme: "material",
  lineWrapping: true,
  placeholder: "Start typing...",
});
cm.setSize('100%', '100%');

// expose the instance
window.Nova = window.Nova || {};
window.Nova.cm = cm;

// -------- continuous, lightweight mode auto-detect --------
function guessModeFromContent(text) {
  if (!text || !text.trim()) return "plaintext";
  const head = text.slice(0, 400);

  // HTML?
  if (/^\s*<(!doctype|html|head|body|script|style)\b/i.test(head) || /<\/[a-zA-Z]/.test(head)) {
    return "htmlmixed";
  }

  // JSON?
  try {
    const t = text.trim();
    if (t.startsWith("{") || t.startsWith("[")) {
      JSON.parse(text);
      return { name: "javascript", json: true };
    }
  } catch {}

  // Python?
  if (/^#!.*\bpython\b/.test(head) ||
      /\b(def|class|import|from|self|async\s+def|if\s+__name__\s*==\s*['"]__main__['"])\b/.test(text)) {
    return "python";
  }

  // CSS?
  if (/{[^}]+}/.test(text) && /\b[a-z-]+\s*:\s*[^;{}]+;/.test(head)) {
    return "css";
  }

  // default to JS
  return "javascript";
}

// debounce helper
function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn.apply(null, args), ms); };
}

// set once at startup
(function applyInitialMode() {
  const mode = guessModeFromContent(cm.getValue());
  cm.setOption("mode", mode);
  // if lint is enabled already, make sure it's wired for this mode
  if (window.Nova && Nova.relintForMode) Nova.relintForMode();
})();

// re-detect on EVERY edit (short debounce) so colours + linter stay correct
const reDetect = debounce(() => {
  const newMode = guessModeFromContent(cm.getValue());
  const current = cm.getOption("mode");
  const currName = (typeof current === 'string') ? current : (current && (current.name || current.mime));
  const newName  = (typeof newMode  === 'string') ? newMode  : (newMode  && (newMode.name  || newMode.mime));
  if (currName !== newName) {
    cm.setOption("mode", newMode);
    // tell linting to re-wire for the new mode
    if (window.Nova && Nova.relintForMode) Nova.relintForMode();
  } else {
    // same mode, but if linting is on, re-run so fixed errors clear quickly
    if (window.Nova && Nova.lintEnabled && cm.performLint) cm.performLint();
  }
}, 200);

cm.on("change", () => reDetect());

// -------- misc UI you already had --------

// drag & drop guards
cm.getWrapperElement().addEventListener('dragover', function (e) { e.preventDefault(); });
cm.getWrapperElement().addEventListener('drop', function (e) { e.preventDefault(); });

// Clipboard + edit ops
(function(){
  const cmOK = () => (window.Nova && Nova.cm) || window.cm;

  window.undo = () => { const e = cmOK(); e && e.execCommand('undo'); };
  window.redo = () => { const e = cmOK(); e && e.execCommand('redo'); };

  window.copy = async () => {
    const e = cmOK(); if (!e) return;
    const text = e.getSelection() || e.getValue() || "";
    try { await navigator.clipboard.writeText(text); }
    catch {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.left = '-9999px';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch {}
      document.body.removeChild(ta);
    }
  };

  window.paste = async () => {
    const e = (window.Nova && Nova.cm) || window.cm;
    if (!e) return;
    e.focus();
    try {
      if (window.__TAURI__?.clipboard?.readText) {
        const t = await window.__TAURI__.clipboard.readText();
        if (t) e.replaceSelection(t);
        return;
      }
    } catch {}
    try {
      const r = await fetch("http://127.0.0.1:56969/clipboard/read");
      if (r.ok) {
        const { text } = await r.json();
        if (text) e.replaceSelection(text);
        else alert("Clipboard is empty.");
        return;
      }
    } catch {}
    alert("Paste via button is blocked here. Use Ctrl/Cmd+V.");
  };

  window.selectAll = () => {
    const e = (window.Nova && Nova.cm) || window.cm;
    if (!e) return;
    e.focus();
    e.execCommand('selectAll');
  };

  window.cut = async () => {
    const e = cmOK(); if (!e) return;
    const text = e.getSelection(); if (!text) return;
    try { await navigator.clipboard.writeText(text); }
    catch {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.left = '-9999px';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch {}
      document.body.removeChild(ta);
    }
    e.replaceSelection('');
  };
})();
