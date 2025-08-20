const API_BASE = "http://127.0.0.1:56969";

function appendBubble(text, className, chatWindow) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${className}`;
  bubble.textContent = text;
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return bubble;
}

import { conversationHistory, currentChatId } from "./chat-state.js";
import { injectSearchMemory, saveMessageToCore } from "./chat-memory.js";
import { saveMessageToMemory } from "./chat.js";
import { createThinkingBubble, handleThinkingText } from "./chat-thinking.js";

function appendMemoryTagButton(bubble, role, content) {
  const tagBtn = document.createElement("span");
  tagBtn.textContent = "🏷";
  tagBtn.title = "Save to Core Memory";
  tagBtn.style.cursor = "pointer";
  tagBtn.style.marginLeft = "8px";
  tagBtn.style.opacity = "0.6";
  tagBtn.style.fontSize = "1.2rem";

  tagBtn.addEventListener("click", async () => {
    tagBtn.textContent = "⏳";
    const success = await saveMessageToCore(role, content);
    tagBtn.textContent = success ? "✅ - added to core-memory" : "❌";
  });

  bubble.appendChild(tagBtn);
}

/* -------------------- Core handling helpers -------------------- */

function mapRole(role) {
  if (!role) return "system";
  const r = String(role).toLowerCase();
  if (r === "assistant" || r === "user" || r === "system") return r;
  if (r === "ui") return "system"; // normalize custom 'ui' to 'system'
  return "system";
}

async function fetchCoreMessages() {
  const res = await fetch(`${API_BASE}/chat-memory/core`);
  if (!res.ok) return [];
  const data = await res.json();
  const raw = Array.isArray(data?.messages) ? data.messages : [];
  return raw.map(m => ({ role: mapRole(m.role), content: m.content }));
}

function mergeSystemMessages(msgs) {
  const systems = msgs.filter(m => m.role === "system").map(m => m.content.trim()).filter(Boolean);
  const nonSystem = msgs.filter(m => m.role !== "system");
  const merged = [];
  if (systems.length) {
    merged.push({ role: "system", content: systems.join("\n\n") });
  }
  return [...merged, ...nonSystem];
}

function arraysStartEqual(a, b) {
  if (a.length < b.length) return false;
  for (let i = 0; i < b.length; i++) {
    if (a[i]?.role !== b[i]?.role) return false;
    if (a[i]?.content !== b[i]?.content) return false;
  }
  return true;
}

function buildMessagesToSend(coreMsgs, history) {
  const coreMerged = mergeSystemMessages(coreMsgs);
  const offset = arraysStartEqual(history, coreMerged) ? coreMerged.length : 0;
  const sessionTail = history.slice(offset);
  return [...coreMerged, ...sessionTail];
}

/* -------------------- Main send -------------------- */

export async function sendMessage({ userInput, chatWindow, selectedModel }) {
  const text = userInput.value.trim();
  if (!text || !selectedModel) return;

  const userBubble = appendBubble(text, 'user', chatWindow);
  appendMemoryTagButton(userBubble, 'user', text);

  conversationHistory.push({ role: 'user', content: text });
  await saveMessageToMemory('user', text);
  userInput.value = '';
  userInput.focus();

  await injectSearchMemory('user', text);

  const thinkingBubble = createThinkingBubble(chatWindow);

  // ---------- AGENT PATH ----------
  const useAgent = !!(window.NOVA_AGENT && window.NOVA_AGENT.enabled);
  let agentSucceeded = false;

  if (useAgent) {
    try {
      const body = { model: selectedModel, message: text };
      const hint = (window.NOVA_AGENT && window.NOVA_AGENT.hint) || 'auto';
      if (hint && hint !== 'auto') body.tool_hint = hint;

      // *** IMPORTANT: pass chat_id so router can remember which editor window to use ***
      if (typeof currentChatId === "string" && currentChatId) {
        body.chat_id = currentChatId;
      } else if (localStorage.getItem("username")) {
        body.username = localStorage.getItem("username");
      }

      const res = await fetch(`${API_BASE}/agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!res.ok) throw new Error(`agent HTTP ${res.status}`);

      const data = await res.json();

      if (data?.error) throw new Error(data.error);
      const answer = (typeof data?.answer === 'string' ? data.answer.trim() : '');
      if (!answer) throw new Error('agent empty answer');

      thinkingBubble.remove();
      const aiBubble = document.createElement('div');
      aiBubble.className = 'bubble ai';
      aiBubble.textContent = answer;
      chatWindow.appendChild(aiBubble);
      chatWindow.scrollTop = chatWindow.scrollHeight;

      if (window.renderAgentBadge) {
        const kinds = (data?.tools_used ? data.tools_used.map(t => t.kind) : []);
        const used = kinds.length ? Array.from(new Set(kinds)).join(', ') : 'Agent';
        window.renderAgentBadge(aiBubble, used);
      }
      if (window.renderAgentSources && Array.isArray(data?.sources) && data.sources.length) {
        window.renderAgentSources(aiBubble, data.sources);
      }

      const finalText = aiBubble.textContent.trim();
      conversationHistory.push({ role: 'assistant', content: finalText });
      await saveMessageToMemory('ai', finalText);
      await injectSearchMemory('assistant', finalText);
      appendMemoryTagButton(aiBubble, 'assistant', finalText);

      agentSucceeded = true;
    } catch (err) {
      console.error('Agent error → using direct chat fallback:', err);
      thinkingBubble.textContent = '[agent failed] switching to direct chat…';
    }
  }

  if (agentSucceeded) return;

  // ---------- DIRECT STREAMING PATH (/api/chat) ----------
  try {
    const response = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: selectedModel, messages: conversationHistory })
    });

    if (!response.ok) throw new Error('Network response was not OK');

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullText = '';
    let thinkBuffer = '';
    let inThinkBlock = false;
    let visibleText = '';
    let aiBubble = null;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      fullText += chunk;

      for (const char of chunk) {
        if (!inThinkBlock && fullText.endsWith('<think>')) {
          inThinkBlock = true;
          thinkBuffer = '';
          continue;
        }
        if (inThinkBlock) {
          thinkBuffer += char;
          if (thinkBuffer.endsWith('</think>')) {
            inThinkBlock = false;
            thinkBuffer = thinkBuffer.slice(0, -('</think>'.length));
            thinkingBubble.remove();
            aiBubble = document.createElement('div');
            aiBubble.className = 'bubble ai';
            chatWindow.appendChild(aiBubble);
            continue;
          }
        } else {
          if (!aiBubble) {
            thinkingBubble.remove();
            aiBubble = document.createElement('div');
            aiBubble.className = 'bubble ai';
            chatWindow.appendChild(aiBubble);
          }
          visibleText += char;
        }
      }

      if (aiBubble) {
        aiBubble.textContent = visibleText;
        chatWindow.scrollTop = chatWindow.scrollHeight;
      }
    }

    if (aiBubble && visibleText.trim()) {
      conversationHistory.push({ role: 'assistant', content: visibleText.trim() });
      await saveMessageToMemory('ai', visibleText.trim());
      await injectSearchMemory('assistant', visibleText.trim());
      appendMemoryTagButton(aiBubble, 'assistant', visibleText.trim());
    }

    if (thinkBuffer.trim() && aiBubble) {
      handleThinkingText(aiBubble, thinkBuffer);
    }
  } catch (error) {
    console.error('Error streaming LLM response:', error);
    if (thinkingBubble) thinkingBubble.textContent = '[error] Failed to get response.';
  }
}

import { bindSaveChat } from "./chat-save.js";
bindSaveChat();
