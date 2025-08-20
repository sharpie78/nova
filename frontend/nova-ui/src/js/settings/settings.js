import { renderModelSettings, updatePreferredModelLabel } from './model-settings.js';
import { renderGeneralSettings } from './general-settings.js';
import { renderVoiceSettings } from './voice-settings.js';
import { renderAudioSettings } from './audio-settings.js';
import { renderChatSettings } from './chat-settings.js';
import { renderInterfaceSettings } from './interface-settings.js';
import { renderNotificationsSettings } from './notifications-settings.js';
import { renderLogsSettings } from './logs-settings.js';
import { initMemoryModal } from "./settings-memory-modal.js";



let currentSettings = {};
let originalSettings = {};
let availableModels = {};
let username; // declared globally so it's accessible in all handlers

// Load settings on page load
document.addEventListener("DOMContentLoaded", async () => {
  username = localStorage.getItem("username") || "default";
  if (!username) return;

  try {
    const settingsResponse = await fetch(`http://127.0.0.1:56969/settings/${username}`);
    const settingsData = await settingsResponse.json();
    currentSettings = JSON.parse(JSON.stringify(settingsData));
    originalSettings = JSON.parse(JSON.stringify(settingsData));

    // Fetch available models and update the options in select_preferred_model_index
    const modelResponse = await fetch("http://127.0.0.1:56969/api/tags");
    const modelData = await modelResponse.json();

    if (modelData.models && Array.isArray(modelData.models)) {
      const options = {};
      modelData.models.forEach((model, index) => {
        options[index + 1] = model;
      });

      if (!currentSettings.ai_model.select_preferred_model_index) {
        currentSettings.ai_model.select_preferred_model_index = {
          label: "Select Preferred Model",
          type: "dropdown",
          options: options,
          preferred_model: modelData.models[0] || null
        };
      } else {
        currentSettings.ai_model.select_preferred_model_index.options = options;
      }
    }

    setTimeout(() => {
      const generalTab = document.querySelector('.settings-sidebar li[data-category="general"]');
      if (generalTab) {
        generalTab.click();
      }
    }, 0);

    const roleEl = document.getElementById('role');
    if (roleEl) {
      roleEl.style.display = username === "admin" ? 'block' : 'none';
    }

  } catch (err) {
    console.error("Failed to load settings or models:", err);
  }
});

function renderSettings(category) {
  const container = document.getElementById("settings-fields");
  container.innerHTML = "";

  switch (category) {
    case "general":
      renderGeneralSettings(container, currentSettings);
      break;
    case "model":
      renderModelSettings(container, currentSettings);
      break;
    case "voice":
      renderVoiceSettings(container, currentSettings);
      break;
    case "audio":
      renderAudioSettings(container, currentSettings);
      break;
    case "chat": {
      const container = document.getElementById("settings-fields");
      if (!container) return;
      renderChatSettings(container, currentSettings);
      initMemoryModal();
      break;
    }
    case "interface":
      renderInterfaceSettings(container, currentSettings);
      break;
    case "notifications":
      renderNotificationsSettings(container, currentSettings);
      break;
    case "logs":
      renderLogsSettings(container, currentSettings);
      break;
  }
}

function createInput(container, key, value) {
  const label = document.createElement("label");
  label.textContent = key;
  const input = document.createElement("input");
  input.type = "text";
  input.value = value;
  input.oninput = () => currentSettings[key] = input.value;
  container.appendChild(label);
  container.appendChild(input);
}

function createCheckbox(container, key, value) {
  const label = document.createElement("label");
  label.textContent = key;
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = value;
  input.onchange = () => currentSettings[key] = input.checked;
  container.appendChild(label);
  container.appendChild(input);
}

document.querySelectorAll(".settings-sidebar li").forEach(item => {
  item.addEventListener("click", () => {
    renderSettings(item.dataset.category);
  });
});

document.getElementById("apply-settings").addEventListener("click", async () => {
  if (!username) return alert("Username not set.");

  try {
    const response = await fetch(`http://127.0.0.1:56969/settings/${username}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentSettings)
    });
    if (response.ok) {
      originalSettings = JSON.parse(JSON.stringify(currentSettings));
      alert("Settings saved.");
      updatePreferredModelLabel(currentSettings);
    } else {
      alert("Failed to save settings.");
    }
  } catch (err) {
    console.error("Save error:", err);
  }
});

document.getElementById("cancel-settings").addEventListener("click", () => {
  currentSettings = JSON.parse(JSON.stringify(originalSettings));
  renderSettings("general");
});

document.getElementById("reset-defaults").addEventListener("click", async () => {
  try {
    const response = await fetch("/config/default.settings.json");
    const defaults = await response.json();
    currentSettings = JSON.parse(JSON.stringify(defaults));
    renderSettings("general");
  } catch (err) {
    console.error("Reset error:", err);
  }
});
