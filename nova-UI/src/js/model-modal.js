const API_BASE = "http://127.0.0.1:56969";
let selectedModel = null;

async function downloadModel() {
  const name = document.getElementById("model-name-input").value.trim();
  if (!name) return;
  const res = await fetch(`${API_BASE}/api/pull`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, stream: true })
  });
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    console.log(decoder.decode(value));
  }
  refreshModels();
}

async function refreshModels() {
  const res = await fetch(`${API_BASE}/api/tags`);
  const models = await res.json();
  const list = document.getElementById("model-list");
  list.innerHTML = "";
  selectedModel = null;
  const savedModel = localStorage.getItem("novaSelectedModel");

  models.models.forEach((model) => {  // Make sure we access the 'models' array properly
    const li = document.createElement("li");
    li.textContent = model;
    li.style.padding = "6px 10px";
    li.style.cursor = "pointer";
    if (model === savedModel) {
      li.style.background = "#444";  // highlight saved model
      selectedModel = model;
    }
    li.onclick = () => {
      const all = document.querySelectorAll("#model-list li");
      all.forEach(el => el.style.background = "");
      li.style.background = "#444";
      selectedModel = model;
      localStorage.setItem("novaSelectedModel", model);
      updateModelCard();  // live update card
    };
    li.ondblclick = () => {
      alert(`Active model set to ${model}`);
    };
    list.appendChild(li);
  });
}

async function deleteSelectedModel() {
  if (!selectedModel) {
    alert("Select a model to delete.");
    return;
  }
  const res = await fetch(`${API_BASE}/api/delete`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: selectedModel })
  });
  const text = await res.text();
  console.log(text);
  if (selectedModel === localStorage.getItem("novaSelectedModel")) {
    localStorage.removeItem("novaSelectedModel");
    updateModelCard();
  }
  refreshModels();
}

function setActiveModel() {
  if (!selectedModel) {
    alert("Select a model first.");
    return;
  }
  localStorage.setItem("novaSelectedModel", selectedModel);
  alert(`Active model set to ${selectedModel}.`);
  updateModelCard();
}

function updateModelCard() {
  const el = document.getElementById('model-card-selected-model');
  if (el) {
    el.textContent = localStorage.getItem('novaSelectedModel') || 'No model selected';
  }
}

document.addEventListener("DOMContentLoaded", () => {
  refreshModels();  // Fetch and display models when the page loads

});
