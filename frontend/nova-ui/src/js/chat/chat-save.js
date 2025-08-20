import { conversationHistory } from "./chat-state.js";

const API_BASE = "http://127.0.0.1:56969";

export async function saveChat() {
  const title = prompt("Enter a title for this chat:");
  if (!title) return;

  const model = localStorage.getItem("novaSelectedModel") || "unknown";

  try {
    const chatRes = await fetch(`${API_BASE}/chat-memory`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, model }),
    });

    const chatData = await chatRes.json();
    const chatId = chatData.chat_id;

    for (const message of conversationHistory) {
      await fetch(`${API_BASE}/chat-memory/${chatId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: message.role,
          content: message.content,
        }),
      });
    }

    await fetch(`${API_BASE}/chat-memory/embed/${chatId}`, {
      method: "POST",
    });

    alert("Chat saved and embedded successfully.");
  } catch (error) {
    console.error("Failed to save chat:", error);
    alert("Failed to save chat.");
  }
}

// Optional: keep the bindSaveChat function if still used elsewhere
export function bindSaveChat() {
  const btn = document.getElementById("save-chat-btn");
  if (!btn) return;

  btn.addEventListener("click", saveChat);
}
