let selectedLabel = null; // Declare at top-level for access by update function

export function renderModelSettings(container, currentSettings) {
  // AI Model Settings Title
  const title = document.createElement("h2");
  title.textContent = "AI Model Settings";
  title.classList.add("settings-title");

  const spacer = document.createElement("div");
  spacer.style.height = "2.4rem"; // Two lines of spacing

  container.appendChild(title);
  container.appendChild(spacer);

  const options = currentSettings.ai_model.select_preferred_model_index.options || {};
  const preferred = currentSettings.ai_model.select_preferred_model_index.preferred_model;

  // Dropdown label
  const dropdownLabel = document.createElement("label");
  dropdownLabel.textContent = "Select Preferred Model";
  container.appendChild(dropdownLabel);

  // Dropdown
  const dropdown = document.createElement("select");
  Object.entries(options).forEach(([index, model]) => {
    const option = document.createElement("option");
    option.value = index;
    option.textContent = model;
    if (model === preferred) option.selected = true;
    dropdown.appendChild(option);
  });

  dropdown.addEventListener("change", () => {
    const selectedModel = options[dropdown.value];
    if (selectedModel) {
      currentSettings.ai_model.select_preferred_model_index.preferred_model = selectedModel;
      if (selectedLabel) {
        selectedLabel.textContent = `Model that will be set as default: ${selectedModel}`;
      }
    }
  });

  container.appendChild(dropdown);

  // Selected label
  selectedLabel = document.createElement("p");
  selectedLabel.id = "preferred-model-label";
  selectedLabel.style.marginTop = "12px";
  selectedLabel.textContent = `Current preferred model: ${preferred || 'None'}`;
  container.appendChild(selectedLabel);
}

// Called from settings.js after Apply
export function updatePreferredModelLabel(currentSettings) {
  const label = document.getElementById("preferred-model-label");
  const confirmed = currentSettings.ai_model.select_preferred_model_index.preferred_model;
  if (label && confirmed) {
    label.textContent = `Current preferred model: ${confirmed}`;
  }
}
