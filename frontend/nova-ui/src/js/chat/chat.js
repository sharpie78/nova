const API_BASE = "http://127.0.0.1:56969";
const CHAT_ID_KEY = "nova.current_chat_id"; // <-- persist current chat id

import { sendMessage } from './chat-send.js';
import {
  dropdownButton,
  dropdownList,
  dropdownSelected,
  models,
  selectedModel,
  fetchSettingsAndModels,
  setupModelDropdownHandlers
} from './chat-model-select.js';

import { currentChatId, setCurrentChatId, conversationHistory } from './chat-state.js';
import { saveChat } from './chat-save.js';

const chatWindow = document.getElementById("chat-window");
const userInput = document.getElementById("user-input");

let chatSettings = {
  chat_history: true
};

const username = localStorage.getItem("username") || "default";

const tempToggleEl = document.getElementById("disable-chat-history");

if (tempToggleEl) {
  tempToggleEl.addEventListener("change", (e) => {
    chatSettings.chat_history = !e.target.checked;
    console.log("⚙️ Temp Chat toggled:", !chatSettings.chat_history);
  });
} else {
  console.log("ℹ️ Temp Chat toggle not found in DOM (possibly hidden on load)");
}

export async function initNewChat() {
  try {
    const userBubbles = chatWindow.querySelectorAll('.bubble.user');
    const aiBubbles = chatWindow.querySelectorAll('.bubble.ai');
    const hasMessages = userBubbles.length > 0 || aiBubbles.length > 0;

    const tempToggleContainer = document.getElementById("chat-options");
    if (tempToggleContainer) tempToggleContainer.style.display = "block";

    // Load server-side default for chat_history
    try {
      const res = await fetch(`${API_BASE}/settings/${username}`);
      const userSettings = await res.json();
      if (userSettings.chat && userSettings.chat.chat_history && typeof userSettings.chat.chat_history.default === "boolean") {
        chatSettings.chat_history = userSettings.chat.chat_history.default;
        if (tempToggleEl) tempToggleEl.checked = !chatSettings.chat_history;
        console.log("✅ chatSettings.chat_history set from server:", chatSettings.chat_history);
      }
    } catch (e) {
      console.warn("⚠️ Failed to fetch user settings, defaulting to true");
      chatSettings.chat_history = true;
    }

    // -------- Persist/restore chat so reloads DON'T create new chats --------
    if (!hasMessages) {
      const storedId = localStorage.getItem(CHAT_ID_KEY);

      // If there's no visible messages and no in-memory history, try to restore existing chat
      if (conversationHistory.length === 0 && storedId) {
        setCurrentChatId(storedId);
        console.log("♻️ Restored existing chat:", storedId);
        return; // <-- do NOT call /chat-memory/new again
      }

      // Otherwise, create a brand-new chat ONCE
      if (conversationHistory.length === 0) {
        const res = await fetch(`${API_BASE}/chat-memory/new?username=${username}&temp=${!chatSettings.chat_history}`);
        const data = await res.json();
        setCurrentChatId(data.chat_id);
        localStorage.setItem(CHAT_ID_KEY, data.chat_id); // <-- remember it

        if (chatSettings.chat_history && data.messages && data.messages.length > 0) {
          console.log("🧠 Injecting Core memory...");
          conversationHistory.length = 0;
          conversationHistory.push(...data.messages.map(m => ({
            role: m.role,
            content: m.content
          })));

          console.log("✅ Core memory injected:", conversationHistory.length, "messages.");
        } else {
          console.log("🚫 Chat history disabled or no core messages returned.");
        }
      } else {
        console.log("💡 Chat already contains core memory. Nothing to do.");
      }
      return;
    }

    // If there are visible bubbles and user wants to start a new chat,
    // we show the save modal (as before)
    showSaveChatModal(
      () => {
        showNameInputModal(async (title) => {
          await saveChat(title);
          await continueToNewChat();
        });
      },
      async () => {
        clearChat();
        setCurrentChatId(null);
        localStorage.removeItem(CHAT_ID_KEY); // <-- we're about to make a new chat

        const res = await fetch(`${API_BASE}/chat-memory/new?username=${username}&temp=${!chatSettings.chat_history}`);
        const data = await res.json();
        setCurrentChatId(data.chat_id);
        localStorage.setItem(CHAT_ID_KEY, data.chat_id); // <-- remember it

        if (chatSettings.chat_history && data.messages && data.messages.length > 0) {
          conversationHistory.length = 0;
          conversationHistory.push(...data.messages.map(m => ({
            role: m.role,
            content: m.content
          })));

          console.log("🧠 Core memory re-injected after clearing unsaved chat.");
        } else {
          console.log("🚫 Chat history disabled or no memory to re-inject.");
        }
      }
    );
  } catch (err) {
    console.error("❌ Failed to start new chat:", err);
  }
}

async function continueToNewChat() {
  clearChat();
  setCurrentChatId(null);
  localStorage.removeItem(CHAT_ID_KEY); // <-- ensure the next /new becomes the active one

  const res = await fetch(`${API_BASE}/chat-memory/new?username=${username}&temp=${!chatSettings.chat_history}`);
  const data = await res.json();
  setCurrentChatId(data.chat_id);
  localStorage.setItem(CHAT_ID_KEY, data.chat_id); // <-- remember it

  if (chatSettings.chat_history && data.messages && Array.isArray(data.messages)) {
    conversationHistory.length = 0;
    conversationHistory.push(...data.messages.map(m => ({
      role: m.role,
      content: m.content
    })));
  }

  const modelFromStorage = localStorage.getItem("novaSelectedModel");
  if (modelFromStorage) {
    const dropdownSelected = document.getElementById("dropdown-selected");
    if (dropdownSelected) dropdownSelected.textContent = modelFromStorage;
  }

  console.log("✅ New chat started with", conversationHistory.length, "core memories.");

  const tempToggleContainer = document.getElementById("chat-options");
  if (tempToggleContainer) tempToggleContainer.style.display = "block";
}

export async function saveMessageToMemory(role, content) {
  if (!currentChatId) return;
  try {
    await fetch(`${API_BASE}/chat-memory/${currentChatId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role, content }),
    });
  } catch (err) {
    console.error("Failed to save message to memory:", err);
  }
}

function appendMemoryTagButton(bubble, role, content) {
  const tagBtn = document.createElement("span");
  tagBtn.textContent = "🏷";
  tagBtn.title = "Save to Core Memory";
  tagBtn.style.cursor = "pointer";
  tagBtn.style.marginLeft = "8px";
  tagBtn.style.opacity = "0.6";
  tagBtn.style.fontSize = "1.2rem";

  tagBtn.addEventListener("click", async () => {
    tagBtn.textContent = "⏳"; // loading
    const success = await saveMessageToCore(role, content);
    tagBtn.textContent = success ? "✅" : "❌";
  });

  bubble.appendChild(tagBtn);
}

async function fetchAndMaybeUpdateCoreMemory() {
  console.log("DEBUG chatSettings:", chatSettings);
  if (!chatSettings.chat_history) {
    console.log("🚫 Skipping core memory fetch/update due to chat_history = false.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/chat-memory/core`);
    const data = await res.json();
    const newCoreMessages = data.messages;

    const existingCoreMessages = conversationHistory.slice(0, newCoreMessages.length);

    const isSame = newCoreMessages.every((m, i) =>
      existingCoreMessages[i] &&
      existingCoreMessages[i].role === m.role &&
      existingCoreMessages[i].content === m.content
    );

    if (!isSame) {
      console.log("🔁 Core memory has changed — reinjecting.");
      newCoreMessages.forEach((m, i) => {
        conversationHistory[i] = { role: m.role, content: m.content };
      });
    } else {
      console.log("✅ Core memory already present and up-to-date.");
    }
  } catch (err) {
    console.error("Failed to check/update core memory:", err);
  }
}

function clearChat() {
  chatWindow.innerHTML = "";
  userInput.value = "";
  userInput.focus();
  conversationHistory.length = 0;

  const tempToggleContainer = document.getElementById("chat-options");
  if (tempToggleContainer) tempToggleContainer.style.display = "none";
}

document.addEventListener("DOMContentLoaded", () => {
  initNewChat();
  document.getElementById("clear-chat-btn").addEventListener("click", clearChat);
  document.getElementById("new-chat-btn").addEventListener("click", initNewChat);
  fetchSettingsAndModels();
  setupModelDropdownHandlers();
});

userInput.addEventListener("keydown", async function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    await fetchAndMaybeUpdateCoreMemory();
    sendMessage({ userInput, chatWindow, selectedModel, conversationHistory });
  }
});

document.getElementById("send-btn").addEventListener("click", async function () {
  await fetchAndMaybeUpdateCoreMemory();
  sendMessage({ userInput, chatWindow, selectedModel, conversationHistory });
});

document.getElementById("open-editor-btn").addEventListener("click", () => {
  fetch("http://127.0.0.1:56969/launch_editor", {
    method: "POST",
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "launched") {
        alert("Editor launched.");
      } else {
        alert("Error: " + (data.error || "Unknown error"));
      }
    });
});

// Modal logic unchanged...
// (showSaveChatModal, showNameInputModal)

function showSaveChatModal(onYes, onNo) {
  const modal = document.createElement("div");
  modal.id = "custom-modal";
  modal.style.position = "fixed";
  modal.style.top = "0";
  modal.style.left = "0";
  modal.style.width = "100vw";
  modal.style.height = "100vh";
  modal.style.background = "rgba(0,0,0,0.6)";
  modal.style.display = "flex";
  modal.style.justifyContent = "center";
  modal.style.alignItems = "center";
  modal.style.zIndex = "9999";

  modal.innerHTML = `
    <div style="background:#222; padding:2rem; border-radius:8px; color:#fff; width:300px; text-align:center;">
      <p>Do you want to save the current chat?</p>
      <div style="margin-top:1rem; display:flex; justify-content:space-around;">
        <button id="save-yes">Yes</button>
        <button id="save-no">No</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  document.getElementById("save-yes").onclick = () => {
    modal.remove();
    onYes();
  };

  document.getElementById("save-no").onclick = () => {
    modal.remove();
    onNo();
  };
}

function showNameInputModal(onSubmit) {
  const modal = document.createElement("div");
  modal.id = "name-modal";
  modal.style.position = "fixed";
  modal.style.top = "0";
  modal.style.left = "0";
  modal.style.width = "100vw";
  modal.style.height = "100vh";
  modal.style.background = "rgba(0,0,0,0.6)";
  modal.style.display = "flex";
  modal.style.justifyContent = "center";
  modal.style.alignItems = "center";
  modal.style.zIndex = "9999";

  modal.innerHTML = `
    <div style="background:#222; padding:2rem; border-radius:8px; color:#fff; width:300px; text-align:center;">
      <p>Name this chat:</p>
      <input type="text" id="chat-name" style="width: 100%; margin-top: 1rem; padding: 0.5rem;" />
      <div style="margin-top:1rem;">
        <button id="name-submit">Save</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  document.getElementById("name-submit").onclick = () => {
    const name = document.getElementById("chat-name").value.trim();
    if (!name) return;
    modal.remove();
    onSubmit(name);
  };
}
