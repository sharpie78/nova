export function renderInterfaceSettings(container, currentSettings) {
  // Interface Settings Title
  const title = document.createElement("h2");
  title.textContent = "Interface Settings";
  title.classList.add("settings-title");

  const spacer = document.createElement("div");
  spacer.style.height = "2.4rem"; // Two lines of spacing

  container.appendChild(title);
  container.appendChild(spacer);

  const interfaceSettings = currentSettings.interface;

  for (const key in interfaceSettings) {
    const setting = interfaceSettings[key];
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
          currentSettings.interface[key].default = input.checked;
        };
        break;

      case "dropdown":
        input = document.createElement("select");
        setting.options.forEach(option => {
          const opt = document.createElement("option");
          opt.value = option;
          opt.textContent = option;
          if (option === setting.default) opt.selected = true;
          input.appendChild(opt);
        });
        input.onchange = () => {
          currentSettings.interface[key].default = input.value;
        };
        break;
    }

    container.appendChild(input);
  }
}
