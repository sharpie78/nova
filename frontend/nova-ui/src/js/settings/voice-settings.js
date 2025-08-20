export function renderVoiceSettings(container, currentSettings) {
  // Voice Settings Title
  const title = document.createElement("h2");
  title.textContent = "Voice Settings";
  title.classList.add("settings-title");

  const spacer = document.createElement("div");
  spacer.style.height = "2.4rem"; // Two lines of spacing

  container.appendChild(title);
  container.appendChild(spacer);

  const voiceSettings = currentSettings.voice;

  for (const key in voiceSettings) {
    const setting = voiceSettings[key];
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
          currentSettings.voice[key].default = input.checked;
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
          currentSettings.voice[key].default = input.value;
        };
        break;

      case "range":
        input = document.createElement("input");
        input.type = "range";
        input.min = setting.min;
        input.max = setting.max;
        input.value = setting.default;
        input.oninput = () => {
          currentSettings.voice[key].default = parseInt(input.value, 10);
        };
        break;
    }

    container.appendChild(input);
  }
}
