import { conversationHistory } from "./chat-state.js";

document.getElementById("load-chat-btn").addEventListener("click", async () => {
  const res = await fetch("http://127.0.0.1:56969/chat-memory");
  const chats = await res.json();

  if (!chats.length) {
    alert("No saved chats.");
    return;
  }

  const options = chats.map(chat => `${chat.title} — ${new Date(chat.created_at).toLocaleString()}`);
  const selected = prompt("Select a chat to load:\n" + options.map((opt, i) => `${i + 1}. ${opt}`).join("\n"));
  const index = parseInt(selected) - 1;

  if (isNaN(index) || index < 0 || index >= chats.length) {
    alert("Invalid selection.");
    return;
  }

  const chatId = chats[index].id;
  const chatData = await fetch(`http://127.0.0.1:56969/chat-memory/${chatId}`).then(r => r.json());

  const chatWindow = document.getElementById("chat-window");
  chatWindow.innerHTML = "";
  conversationHistory.length = 0;

  for (const message of chatData.messages) {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${message.role === "user" ? "user" : "ai"}`;
    bubble.textContent = message.content;
    chatWindow.appendChild(bubble);
    conversationHistory.push({ role: message.role, content: message.content });
  }

  chatWindow.scrollTop = chatWindow.scrollHeight;
});

document.getElementById("delete-chat-btn").addEventListener("click", async () => {
  const res = await fetch("http://127.0.0.1:56969/chat-memory");
  const chats = await res.json();

  if (!chats.length) {
    alert("No saved chats to delete.");
    return;
  }

  const list = chats.map((c, i) => `${i + 1}. ${c.title} — ${new Date(c.created_at).toLocaleString()}`).join("\n");
  const selection = prompt("Select a chat to delete:\n" + list);
  const index = parseInt(selection) - 1;

  if (isNaN(index) || index < 0 || index >= chats.length) {
    alert("Invalid selection.");
    return;
  }

  const chatId = chats[index].id;
  const confirmDelete = confirm(`Are you sure you want to delete "${chats[index].title}"?`);

  if (!confirmDelete) return;

  const delRes = await fetch(`http://127.0.0.1:56969/chat-memory/${chatId}`, {
    method: "DELETE",
  });

  const data = await delRes.json();
  if (data.status === "deleted") {
    alert("Chat deleted.");
  } else {
    alert("Something went wrong.");
  }
});
