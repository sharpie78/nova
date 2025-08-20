export function renderChatSettings(container, currentSettings) {
  // Chat Settings Title
  const title = document.createElement("h2");
  title.textContent = "Chat Settings";
  title.classList.add("settings-title");

  const spacer = document.createElement("div");
  spacer.style.height = "2.4rem"; // Two lines of spacing

  container.appendChild(title);
  container.appendChild(spacer);

  const chatSettings = currentSettings.chat;

  for (const key in chatSettings) {
    const setting = chatSettings[key];
    const label = document.createElement("label");
    label.textContent = setting.label;
    container.appendChild(label);

    let input;

    switch (setting.type) {
      case "toggle":
        input = document.createElement("input");
        input.type = "checkbox";
        input.checked = setting.default;
        input.onchange = () => {
          currentSettings.chat[key].default = input.checked;
        };
        break;

      case "number":
        input = document.createElement("input");
        input.type = "number";
        input.value = setting.default;
        input.oninput = () => {
          currentSettings.chat[key].default = parseInt(input.value, 10);
        };
        break;

      case "range":
        input = document.createElement("input");
        input.type = "range";
        input.min = setting.min;
        input.max = setting.max;
        input.value = setting.default;
        input.oninput = () => {
          currentSettings.chat[key].default = parseInt(input.value, 10);
        };
        break;

      case "button":
        input = document.createElement("button");
        input.textContent = setting.label || key;
        if (key === "manage_memory") {
          input.id = "manage-memory-button";
        }
        break;
    }

    if (input) {
      container.appendChild(input);
    }
  }
}
