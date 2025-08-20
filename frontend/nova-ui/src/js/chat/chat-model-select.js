const API_BASE = "http://127.0.0.1:56969";

export const dropdownButton = document.getElementById("dropdown-button");
export const dropdownList = document.getElementById("dropdown-list");
export const dropdownSelected = document.getElementById("dropdown-selected");

export let models = [];
export let selectedModel = null;

export async function fetchModels() {
  const res = await fetch(`${API_BASE}/api/tags`);
  const data = await res.json();
  models = data.models || [];
  dropdownList.innerHTML = "";

  models.forEach((model, i) => {
    const li = document.createElement("li");
    li.textContent = model;
    li.setAttribute("role", "option");
    li.id = `model-option-${i}`;
    li.tabIndex = -1;
    li.addEventListener("click", () => selectModel(model));
    dropdownList.appendChild(li);
  });
}

export async function selectModel(model) {
  selectedModel = model;
  dropdownSelected.textContent = model;
  closeDropdown();

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
      body: JSON.stringify(settings)
    });

    console.log("Model saved to settings:", model);
  } catch (error) {
    console.error("Error saving model to settings:", error);
  }
}

export async function fetchSettingsAndModels() {
  const currentUser = localStorage.getItem("username");
  if (!currentUser) {
    console.error("No username found in localStorage.");
    return;
  }

  await fetchModels();

  const settingsPath = `${API_BASE}/settings/${currentUser}`;
  try {
    const response = await fetch(settingsPath);
    if (!response.ok) {
      console.error(`Failed to load settings for user: ${currentUser}`);
      return;
    }

    const settings = await response.json();
    console.log("User settings loaded:", settings);

    const preferredModel = settings.ai_model.select_preferred_model_index.preferred_model;
    if (preferredModel && models.includes(preferredModel)) {
      selectModel(preferredModel);
    } else if (models.length > 0) {
      selectModel(models[0]);
    }
  } catch (error) {
    console.error("Error fetching user settings:", error);
  }
}

function toggleDropdown() {
  const expanded = dropdownButton.getAttribute("aria-expanded") === "true";
  if (expanded) {
    closeDropdown();
  } else {
    openDropdown();
  }
}

function openDropdown() {
  dropdownList.hidden = false;
  dropdownButton.setAttribute("aria-expanded", "true");
  const selectedIndex = models.indexOf(selectedModel);
  const focusItem =
    selectedIndex >= 0 ? dropdownList.children[selectedIndex] : dropdownList.children[0];
  if (focusItem) focusItem.focus();
}

function closeDropdown() {
  dropdownList.hidden = true;
  dropdownButton.setAttribute("aria-expanded", "false");
}

export function setupModelDropdownHandlers() {
  dropdownButton.addEventListener("click", () => toggleDropdown());

  dropdownButton.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      openDropdown();
    }
  });

  document.addEventListener("click", (e) => {
    if (!dropdownButton.contains(e.target) && !dropdownList.contains(e.target)) {
      closeDropdown();
    }
  });
}
