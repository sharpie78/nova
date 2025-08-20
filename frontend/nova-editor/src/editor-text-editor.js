

let cm = CodeMirror.fromTextArea(document.getElementById("editor"), {
  lineNumbers: true,
  mode: "plaintext",
  theme: "material",
  lineWrapping: true,
  placeholder: "Start typing...",
});
cm.setSize('100%', '100%');

// ✅ expose the instance so the toolbar handlers can find it
window.Nova = window.Nova || {};
window.Nova.cm = cm;

cm.getWrapperElement().addEventListener('dragover', function (e) {
  e.preventDefault();
});
cm.getWrapperElement().addEventListener('drop', function (e) {
  e.preventDefault();
});


function stopAll() {
  document.getElementById('speak-button')?.classList.remove('active');
  document.getElementById('listen-button')?.classList.remove('active');
  updateStopButtonVisibility();
}

function readText(el) {
  el.classList.toggle('active');
  updateStopButtonVisibility();
}

function startDictation(el) {
  el.classList.toggle('active');
  updateStopButtonVisibility();
}

function toggleLinting(el) {
  // placeholder for linting toggle
}

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

  // Paste that prefers Tauri clipboard, falls back to backend route
  window.paste = async () => {
    const e = (window.Nova && Nova.cm) || window.cm;
    if (!e) return;
    e.focus();

    // 1) Tauri clipboard (native system clipboard in the app)
    try {
      if (window.__TAURI__?.clipboard?.readText) {
        const t = await window.__TAURI__.clipboard.readText();
        if (t) e.replaceSelection(t);
        return;
      }
      // If using v2 and globals aren't injected, this will be undefined.
    } catch {}

    // 2) Backend fallback (see Option B route below)
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



  // Select All: focus first, then select so it's visible
  window.selectAll = () => {
    const e = (window.Nova && Nova.cm) || window.cm;
    if (!e) return;
    e.focus();
    e.execCommand('selectAll'); // or: e.setSelection({line:0,ch:0}, e.posFromIndex(e.getValue().length));
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
