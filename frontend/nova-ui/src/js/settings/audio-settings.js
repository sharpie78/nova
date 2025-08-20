export function renderAudioSettings(container, currentSettings) {
  // Audio Settings Title
  const title = document.createElement("h2");
  title.textContent = "Audio Settings";
  title.classList.add("settings-title");

  const spacer = document.createElement("div");
  spacer.style.height = "2.4rem"; // Two lines of spacing

  container.appendChild(title);
  container.appendChild(spacer);

  const audioSettings = currentSettings.audio;

  for (const key in audioSettings) {
    const setting = audioSettings[key];
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
          currentSettings.audio[key].default = input.value;
        };
        break;

      case "range":
        input = document.createElement("input");
        input.type = "range";
        input.min = setting.min;
        input.max = setting.max;
        input.value = setting.default;
        input.oninput = () => {
          currentSettings.audio[key].default = parseInt(input.value, 10);
        };
        break;
    }

    container.appendChild(input);
  }
}
