import { saveMessageToCore, loadCoreMemory } from "../chat/chat-memory.js";

let editedMemory = [];
let deletedMemory = [];
let allTags = [];

export function initMemoryModal() {
  const tryBind = () => {
    const manageBtn = document.getElementById("manage-memory-button");
    if (!manageBtn) {
      requestAnimationFrame(tryBind);
      return;
    }

    manageBtn.addEventListener("click", async () => {
      const messages = await loadCoreMemory();
      const tagResp = await fetch("http://localhost:56969/chat-memory/tags");
      const tagJson = await tagResp.json();
      allTags = Array.isArray(tagJson) ? tagJson : Object.values(tagJson);

      editedMemory = messages.map(m => ({
        id: m.id,
        text: m.content,
        tags: m.tags || [m.role],
        originalText: m.content,
        originalTags: m.tags || [m.role],
        _deleted: false
      }));
      deletedMemory = [];
      openMemoryModal();
    });
  };

  tryBind();
}

function openMemoryModal() {
  if (document.querySelector('.memory-modal')) return;
  const modal = document.createElement("div");
  modal.classList.add("modal");

  const modalContent = document.createElement("div");
  modalContent.classList.add("modal-content", "memory-modal");

  modalContent.innerHTML = `
    <div class="modal-header">
      <h2>Core Memory</h2>
      <button class="modal-close">×</button>
    </div>
    <div class="modal-body" id="memory-list"></div>
    <div class="modal-footer">
      <button id="add-memory">+ New Memory</button>
      <button id="save-memory">Save Changes</button>
    </div>
  `;

  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  modal.querySelector(".modal-close").onclick = () => modal.remove();
  modal.querySelector("#add-memory").onclick = () => addBlankMemory();
  modal.querySelector("#save-memory").onclick = async () => {
    await saveChanges();
    modal.remove();
  };

  renderMemoryList();
}

function renderMemoryList() {
  const list = document.getElementById("memory-list");
  if (!list) return;
  list.innerHTML = "";

  editedMemory.forEach((item) => {
    if (item._deleted) return;
    const entry = createMemoryEntry(item);
    list.appendChild(entry);
  });

  deletedMemory.forEach((item) => {
    const entry = document.createElement("div");
    entry.classList.add("memory-entry", "deleted-entry");

    const tagSpan = document.createElement("span");
    tagSpan.textContent = (item.tags || []).join(", ");
    tagSpan.classList.add("memory-tag");

    const textSpan = document.createElement("span");
    textSpan.textContent = item.text;
    textSpan.classList.add("memory-text");

    const undoBtn = document.createElement("button");
    undoBtn.textContent = "↩";
    undoBtn.classList.add("memory-undo");
    undoBtn.addEventListener("click", () => {
      item._deleted = false;
      deletedMemory = deletedMemory.filter(m => m !== item);
      editedMemory.push(item);
      renderMemoryList();
    });

    entry.appendChild(tagSpan);
    entry.appendChild(textSpan);
    entry.appendChild(undoBtn);
    list.appendChild(entry);
  });
}

function createMemoryEntry(item) {
  const entry = document.createElement("div");
  entry.classList.add("memory-entry");

  const tagContainer = document.createElement("div");
  tagContainer.classList.add("memory-tags");
  allTags.forEach(tag => {
    const tagBtn = document.createElement("button");
    tagBtn.textContent = tag;
    tagBtn.classList.add("tag-chip");
    if (item.tags.includes(tag)) tagBtn.classList.add("selected");

    tagBtn.onclick = () => {
      if (item.tags.includes(tag)) {
        item.tags = item.tags.filter(t => t !== tag);
        tagBtn.classList.remove("selected");
      } else {
        item.tags.push(tag);
        tagBtn.classList.add("selected");
      }
    };

    tagContainer.appendChild(tagBtn);
  });

  const textArea = document.createElement("textarea");
  textArea.value = item.text || "";
  textArea.classList.add("memory-text");
  textArea.addEventListener("input", () => {
    item.text = textArea.value;
  });

  const deleteBtn = document.createElement("button");
  deleteBtn.textContent = "🗑️";
  deleteBtn.classList.add("memory-delete");
  deleteBtn.addEventListener("click", () => deleteMemoryEntry(item));

  entry.appendChild(tagContainer);
  entry.appendChild(textArea);
  entry.appendChild(deleteBtn);
  return entry;
}

function deleteMemoryEntry(item) {
  const index = editedMemory.indexOf(item);
  if (index > -1) {
    editedMemory.splice(index, 1);
    item._deleted = true;
    deletedMemory.push(item);
    renderMemoryList();
  }
}

function addBlankMemory() {
  editedMemory.push({ text: "", tags: [], originalText: "", originalTags: [], _deleted: false });
  renderMemoryList();
}

async function saveChanges() {
  for (const memory of editedMemory) {
    if (memory._deleted) continue;
    const changed =
      memory.text.trim() !== memory.originalText?.trim() ||
      memory.tags.join() !== memory.originalTags?.join();
    if (!memory.text.trim()) continue;
    if (!memory.id || changed) {
      const result = await saveMessageToCore(memory.tags[0] || "user", memory.text.trim());
      if (result && result.message_id) {
        for (const tag of memory.tags) {
          await fetch(`http://localhost:56969/chat-memory/tag/${result.message_id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tag })
          });
        }
      }
    }
  }
  for (const memory of deletedMemory) {
    if (memory.id) {
      const url = `http://localhost:56969/chat-memory/core/${memory.id}`;
      try {
        const res = await fetch(url, { method: "DELETE" });
        const body = await res.text();
        if (!res.ok) console.error("Delete failed", body);
        else console.log("Delete success:", body);
      } catch (err) {
        console.error("Error deleting memory:", err);
      }
    }
  }
  editedMemory = [];
  deletedMemory = [];
}
