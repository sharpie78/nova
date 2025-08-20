// --- find the CodeMirror instance ---
function getCM() {
  if (window.cm) return window.cm;
  if (window.Nova && Nova.cm) return Nova.cm;
  const el = document.querySelector('.CodeMirror');
  return el && el.CodeMirror ? el.CodeMirror : null;
}

// JSON should use JSONLint adapter
if (window.CodeMirror) {
  CodeMirror.defineMIME("application/json", { name: "javascript", json: true });
}

// Map the HTML linter to htmlmixed (so HTML files get real messages, not just red boxes)
(function mapHtmlMixedToLinter(){
  if (!window.CodeMirror) return;
  if (CodeMirror.lint && CodeMirror.lint.html && !CodeMirror.__htmlMixedLintMapped) {
    CodeMirror.registerHelper("lint", "htmlmixed", function(text, options){
      return CodeMirror.lint.html(text, options || {});
    });
    CodeMirror.__htmlMixedLintMapped = true;
  }
})();

// XML well-formedness helper (DOMParser)
let xmlHelperRegistered = false;
function ensureXmlHelper() {
  if (xmlHelperRegistered || !window.CodeMirror) return;
  CodeMirror.registerHelper("lint", "xml", function(text) {
    const doc = new DOMParser().parseFromString(text, "application/xml");
    const err = doc.getElementsByTagName("parsererror")[0];
    if (!err) return [];
    // DOMParser doesn't give precise line/col; show a single doc-level error.
    return [{
      from: CodeMirror.Pos(0, 0),
      to: CodeMirror.Pos(0, 1),
      message: err.textContent.replace(/\s+/g, ' ').trim(),
      severity: "error"
    }];
  });
  xmlHelperRegistered = true;
}

// Lightweight Python checks (format/structure only)
let pyHelperRegistered = false;
function ensurePythonHelper() {
  if (pyHelperRegistered || !window.CodeMirror) return;
  CodeMirror.registerHelper("lint", "python", function(text) {
    const msgs = [];

    // Mixed tabs/spaces
    const lines = text.split(/\r?\n/);
    let sawTab = false, sawSpace = false;
    for (const ln of lines) {
      if (/^\t+/.test(ln)) sawTab = true;
      if (/^ +/.test(ln)) sawSpace = true;
      if (sawTab && sawSpace) {
        msgs.push({
          from: CodeMirror.Pos(0,0), to: CodeMirror.Pos(0,1),
          message: "Mixed tabs and spaces for indentation.",
          severity: "warning"
        });
        break;
      }
    }

    // Bracket/brace/paren balance
    const pairs = { '(': ')', '[': ']', '{': '}' };
    const stack = [];
    let inS=false, inD=false;
    for (let i=0;i<text.length;i++){
      const ch=text[i];
      if (!inD && ch==="'" && text[i-1] !== "\\") inS = !inS;
      else if (!inS && ch === '"' && text[i-1] !== "\\") inD = !inD;
      if (inS || inD) continue;
      if (pairs[ch]) stack.push(pairs[ch]);
      else if (ch===')'||ch===']'||ch==='}'){
        const need = stack.pop();
        if (need !== ch) {
          msgs.push({
            from: CodeMirror.Pos(0,0), to: CodeMirror.Pos(0,1),
            message: "Unbalanced brackets/braces/parentheses.",
            severity: "error"
          });
          break;
        }
      }
    }
    if (stack.length) {
      msgs.push({
        from: CodeMirror.Pos(0,0), to: CodeMirror.Pos(0,1),
        message: "Unclosed brackets/braces/parentheses.",
        severity: "error"
      });
    }
    return msgs;
  });
  pyHelperRegistered = true;
}

// --- live lint wiring ---
window.Nova = window.Nova || {};
Nova.lintEnabled = false;

function applyLintForCurrentMode() {
  const cm = getCM();
  if (!cm) return;

  // gutters for markers
  const baseGutters = ['CodeMirror-linenumbers'];
  cm.setOption('gutters', Nova.lintEnabled ? baseGutters.concat('CodeMirror-lint-markers') : baseGutters);

  if (!Nova.lintEnabled) {
    cm.setOption('lint', false);
    return;
  }

  let mode = cm.getOption('mode');
  let name =
    (typeof mode === 'string' && mode) ||
    (mode && (mode.name || mode.mime)) ||
    '';

  // Helpers for specific modes
  if (name === 'xml' || name === 'application/xml' || name === 'text/xml') ensureXmlHelper();
  if (name === 'python' || name === 'text/x-python') ensurePythonHelper();

  // Per-language configs; enable tooltips so messages appear above the text,
  // and set a small delay so it's essentially "live".
  const TOOLTIPY = { tooltips: true, delay: 150 };

  if (name === 'application/json' || (mode && mode.json === true)) {
    cm.setOption('lint', Object.assign({ json: true }, TOOLTIPY));                       // JSONLint
  } else if (name === 'javascript' || name === 'text/javascript') {
    cm.setOption('lint', Object.assign({
      esversion: 11,
      undef: true,
      unused: true,
      asi: false,
      browser: true,
      node: true,
      globals: { console: true, window: true, document: true }
    }, TOOLTIPY));                                                                        // JSHint
  } else if (name === 'css') {
    cm.setOption('lint', TOOLTIPY);                                                       // CSSLint
  } else if (name === 'htmlmixed' || name === 'text/html') {
    const htmlRules = {
      'tag-pair': true,
      'id-unique': true,
      'attr-value-double-quotes': true
    };
    // Explicitly use the adapter and rules so we get real HTMLHint messages.
    if (CodeMirror.lint && CodeMirror.lint.html) {
      cm.setOption('lint', Object.assign({
        getAnnotations: CodeMirror.lint.html,
        rules: htmlRules
      }, TOOLTIPY));
    } else {
      cm.setOption('lint', Object.assign({ rules: htmlRules }, TOOLTIPY));
    }
  } else if (name === 'xml' || name === 'application/xml' || name === 'text/xml') {
    cm.setOption('lint', TOOLTIPY);                                                       // our DOMParser helper
  } else if (name === 'python' || name === 'text/x-python') {
    cm.setOption('lint', TOOLTIPY);                                                       // lightweight helper
  } else {
    cm.setOption('lint', TOOLTIPY);                                                       // default
  }

  cm.performLint && cm.performLint();
}

// checkbox handler
function toggleLinting(el) {
  Nova.lintEnabled = !!el.checked;
  applyLintForCurrentMode();
}

// expose
window.toggleLinting = toggleLinting;
Nova.relintForMode = applyLintForCurrentMode;
