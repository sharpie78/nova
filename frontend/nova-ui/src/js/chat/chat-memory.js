// chat-memory.js (cleaned + corrected)

const API_BASE = "http://127.0.0.1:56969";

// === Embed all messages in a chat ===
export async function embedChatMessages(chatId) {
  const res = await fetch(`${API_BASE}/chat-memory/embed/${chatId}`, {
    method: "POST"
  });
  const data = await res.json();
  if (data.status !== "ok") {
    alert("Embedding failed.");
  } else {
    alert("Chat embedded into memory.");
  }
}

// === Query memory for relevant messages ===
export async function queryMemory(question) {
  const res = await fetch(`${API_BASE}/chat-memory/query?q=${encodeURIComponent(question)}`);
  const data = await res.json();
  return data.matches || [];
}

// === Optional: Tag a message ===
export async function tagMessage(messageId, tag) {
  const res = await fetch(`${API_BASE}/chat-memory/tag/${messageId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tag })
  });
  const data = await res.json();
  return data.status === "ok";
}

// === Optional: Get messages by tag ===
export async function getMessagesByTag(tag) {
  const res = await fetch(`${API_BASE}/chat-memory/tag/${encodeURIComponent(tag)}`);
  const data = await res.json();
  return data.messages || [];
}

// === Inject relevant memory results into conversation if needed ===
export async function injectSearchMemory(text, conversationHistory) {
  const memoryEnabled = window.currentSettings?.chat?.chatHistory?.default;
  if (!memoryEnabled) return;

  // If no chatId exists yet, create one and save it
  if (!localStorage.getItem("currentChatId")) {
    const firstUserInputs = conversationHistory
      .filter(m => m.role === "user")
      .slice(0, 2)
      .map(m => m.content.trim().split(" ").slice(0, 6).join(" "))
      .join(" | ") || "Untitled";

    const title = firstUserInputs.length > 100 ? firstUserInputs.slice(0, 100) + "..." : firstUserInputs;
    const model = localStorage.getItem("novaSelectedModel") || "unknown";

    const res = await fetch(`${API_BASE}/chat-memory`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, model })
    });

    const data = await res.json();
    localStorage.setItem("currentChatId", data.chat_id);
  }

  const chatId = localStorage.getItem("currentChatId");
  const lastMessage = conversationHistory[conversationHistory.length - 1];

  if (lastMessage) {
    const saveRes = await fetch(`${API_BASE}/chat-memory/${chatId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: lastMessage.role, content: lastMessage.content })
    });

    const saveData = await saveRes.json();
    const messageId = saveData.message_id;

    await fetch(`${API_BASE}/chat-memory/embed/${chatId}`, {
      method: "POST"
    });

    if (messageId) {
      await fetch(`${API_BASE}/chat-memory/tag/${messageId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tag: lastMessage.role })
      });
    }
  }

  const lower = text.toLowerCase();
  if (
    lower.includes("remember") ||
    lower.includes("did i say") ||
    lower.includes("what did i") ||
    lower.startsWith("search memory for")
  ) {
    const queryText = text.replace(/search memory for/i, "").trim() || text;
    const matches = await queryMemory(queryText);
    const topMatches = matches.filter(m => m.score >= 0.80).slice(0, 3);

    if (topMatches.length) {
      const memorySummary = topMatches.map(m => {
        const source = m.role === "user" ? "You previously said" : "I previously replied";
        return `${source}: \"${m.content}\"`;
      }).join("\n");

      conversationHistory.push({
        role: "system",
        content: `These may help answer the user's question. Use them only if relevant.\n\n${memorySummary}`
      });
    }
  }
}

export async function saveMessageToCore(role, content) {
  const response = await fetch("http://127.0.0.1:56969/chat-memory/core", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ role, content })
  });

  if (!response.ok) {
    console.error("Failed to save core memory:", await response.text());
    return false;
  }

  return true;
}

export async function loadCoreMemory() {
  const res = await fetch("http://127.0.0.1:56969/chat-memory/core");
  const data = await res.json();
  return data.messages || [];
}
export async function deleteMessageFromCore(id) {
  const res = await fetch(`/chat-memory/core/${id}`, {
    method: "DELETE"
  });
  if (!res.ok) throw new Error("Failed to delete core message");
}
