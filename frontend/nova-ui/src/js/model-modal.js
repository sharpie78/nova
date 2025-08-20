if (!window.modelModalLoaded) {
  window.modelModalLoaded = true;

  if (typeof API_BASE === "undefined") {
    var API_BASE = "http://127.0.0.1:56969";
  }

  // Declare globally
  window.selectedModel = null;
  window.currentSettings = {};
  window.originalSettings = {};
  window.username = null;
  window.availableModels = {};
  window.settingsChanged = false;

  // Leave this global for system-modal.js to call
  window.refreshModels = async function () {
    await fetchUserSettings();

    const preferredModel = localStorage.getItem("novaSelectedModel");
    const list = document.getElementById("model-list");
    const listItems = list.querySelectorAll("li");

    listItems.forEach((li) => {
      if (li.textContent === preferredModel) {
        li.style.background = "#444";
      }
    });
  };

  function getUsername() {
    return localStorage.getItem("username");
  }

  async function fetchModels() {
    const res = await fetch(`${API_BASE}/api/tags`);
    const data = await res.json();
    return data.models || [];
  }

  async function fetchUserSettings() {
    username = getUsername();
    if (!username) {
      console.error("No username found in localStorage.");
      return;
    }

    const settingsPath = `${API_BASE}/settings/${username}`;

    try {
      const response = await fetch(settingsPath);
      if (!response.ok) {
        console.error(`Failed to load settings for user: ${username}`);
        return;
      }

      const settings = await response.json();
      currentSettings = { ...settings };
      originalSettings = { ...settings };

      const preferredModel = currentSettings.ai_model.select_preferred_model_index.preferred_model;
      const modelCard = document.getElementById("model-card-selected-model");
      if (modelCard && preferredModel) {
        modelCard.textContent = preferredModel;
      }

      const list = document.getElementById("model-list");
      if (!list) {
        console.warn("Model list element not found.");
        return;
      }
      list.innerHTML = "";


      availableModels = await fetchModels();

      availableModels.forEach((model) => {
        const li = document.createElement("li");
        li.textContent = model;
        li.setAttribute("role", "option");
        li.id = `model-option-${model}`;
        li.tabIndex = -1;

        if (model === preferredModel) {
          li.style.background = "#444";
          selectedModel = model;
        }

        li.addEventListener("click", () => selectModel(model));
        list.appendChild(li);
      });

      if (selectedModel) {
        updateModelCard(selectedModel);
      }
    } catch (error) {
      console.error("Error fetching user settings:", error);
    }
  }

  async function selectModel(model) {
    selectedModel = model;
    updateModelCard(model);

    const currentUser = localStorage.getItem("username");
    if (!currentUser) {
      console.error("No username found in localStorage.");
      return;
    }

    const settingsPath = `${API_BASE}/settings/${currentUser}`;

    try {
      const response = await fetch(settingsPath);
      if (!response.ok) {
        console.error(`Failed to load settings for user: ${currentUser}`);
        return;
      }

      const settings = await response.json();
      settings.ai_model.select_preferred_model_index.preferred_model = model;

      await fetch(settingsPath, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });

      const allListItems = document.querySelectorAll("#model-list li");
      allListItems.forEach((el) => (el.style.background = ""));
      const selectedItem = document.getElementById(`model-option-${model}`);

      if (selectedItem) {
        selectedItem.style.background = "#444";
      }

      const modelCard = document.getElementById("model-card-selected-model");
      if (modelCard) {
        modelCard.textContent = model;
      }
    } catch (error) {
      console.error("Error saving model to settings:", error);
    }
  }

  function updateModelCard(model) {
    const modelCard = document.getElementById("model-card-selected-model");
    if (!model) {
      modelCard.innerHTML = "<p>No model selected.</p>";
      return;
    }
    modelCard.innerHTML = `<p>Selected Model: ${model}</p>`;
  }

  document.addEventListener("DOMContentLoaded", async () => {
    await fetchUserSettings();

    const refreshBtn = document.querySelector("button");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", async () => {
        await fetchUserSettings();
      });
    }
  });
}
