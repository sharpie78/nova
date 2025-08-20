export function renderNotificationsSettings(container, currentSettings) {
  // Notifications Settings Title
  const title = document.createElement("h2");
  title.textContent = "Notifications Settings";
  title.classList.add("settings-title");

  const spacer = document.createElement("div");
  spacer.style.height = "2.4rem"; // Two lines of spacing

  container.appendChild(title);
  container.appendChild(spacer);

  const notifications = currentSettings.notifications;

  for (const key in notifications) {
    const setting = notifications[key];
    const label = document.createElement("label");
    label.textContent = setting.label;
    container.appendChild(label);

    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = setting.default;
    input.onchange = () => {
      currentSettings.notifications[key].default = input.checked;
    };

    container.appendChild(input);
  }
}
