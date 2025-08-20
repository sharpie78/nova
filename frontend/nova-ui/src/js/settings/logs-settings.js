export function renderLogsSettings(container, currentSettings) {
  const role = currentSettings?.general?.role?.default;
  if (role !== 'Admin') return;

  // Logs Settings Title
  const title = document.createElement("h2");
  title.textContent = "Logs Settings";
  title.classList.add("settings-title");

  const spacer = document.createElement("div");
  spacer.style.height = "2.4rem"; // Two lines of spacing

  container.appendChild(title);
  container.appendChild(spacer);

  const logs = currentSettings.logs;

  for (const key in logs) {
    const setting = logs[key];
    const label = document.createElement("label");
    label.textContent = setting.label;
    container.appendChild(label);

    let input;

    switch (setting.type) {
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
          currentSettings.logs[key].default = input.value;
        };
        break;
    }

    container.appendChild(input);
  }
}
