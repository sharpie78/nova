export function createThinkingBubble(chatWindow) {
  const bubble = document.createElement("div");
  bubble.className = "bubble ai thinking-bubble";
  bubble.innerHTML = `<span class=\"thinking-icon green\">🧠 AI is thinking<span class=\"thinking-dots\"></span></span>`;
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return bubble;
}

export function handleThinkingText(aiBubble, thinkBuffer) {
  aiBubble.textContent += "\n";
  const tooltipIcon = document.createElement("span");
  tooltipIcon.className = "tooltip-icon";
  tooltipIcon.textContent = "🧠";

  const tooltipBox = document.createElement("div");
  tooltipBox.className = "tooltip-box";
  tooltipBox.textContent = thinkBuffer.trim();
  tooltipBox.style.display = "none";

  tooltipIcon.addEventListener("click", () => {
    tooltipBox.style.display = tooltipBox.style.display === "none" ? "block" : "none";
  });

  aiBubble.appendChild(document.createElement("br"));
  aiBubble.appendChild(tooltipIcon);
  aiBubble.appendChild(tooltipBox);
}
