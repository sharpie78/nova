const API_BASE = "http://127.0.0.1:56969";

// Custom dropdown elements
const dropdownButton = document.getElementById("dropdown-button");
const dropdownList = document.getElementById("dropdown-list");
const dropdownSelected = document.getElementById("dropdown-selected");

const chatWindow = document.getElementById("chat-window");
const userInput = document.getElementById("user-input");

let models = [];
let selectedModel = null;

// Fetch models from backend (/api/tags)
async function fetchModels() {
    const res = await fetch(`${API_BASE}/api/tags`);
    const data = await res.json();
    models = data.models || [];  // Get the models from the response

    dropdownList.innerHTML = ""; // Clear existing options

    // Populate the dropdown with the models
    models.forEach((model, i) => {
        const li = document.createElement("li");
        li.textContent = model;
        li.setAttribute("role", "option");
        li.id = `model-option-${i}`;
        li.tabIndex = -1;
        li.addEventListener("click", () => selectModel(model));  // Set model when clicked
        dropdownList.appendChild(li);
    });
}

// Handle model selection
function selectModel(model, updateDropdown = true) {
    selectedModel = model;
    dropdownSelected.textContent = model;
    document.getElementById("current-model").textContent = `(${model})`;
    if (updateDropdown) {
        localStorage.setItem("novaSelectedModel", model);
    }

    // Close the dropdown after selecting a model
    closeDropdown();
}


// Append a message bubble to the chat window
function appendBubble(text, className) {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${className}`;
    bubble.textContent = text;
    chatWindow.appendChild(bubble);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}


// Clear chat history
function clearChat() {
    chatWindow.innerHTML = "";
    userInput.value = "";
    userInput.focus();
}

// Handle message send
function sendMessage() {
    let text = userInput.value.trim();
    if (!text || !selectedModel) return;

    appendBubble(text, "user");
    userInput.value = "";
    userInput.focus();

    // Send the message to the backend
    fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: selectedModel, messages: [{ role: "user", content: text }] }),
    })
    .then((res) => res.json())  // Parse the response as JSON
    .then((data) => {
        const aiText = data.message || "";  // Get the assistant's response
        const aiBubble = document.createElement("div");
        aiBubble.className = "bubble ai";
        chatWindow.appendChild(aiBubble);

        aiBubble.textContent = aiText;
        chatWindow.scrollTop = chatWindow.scrollHeight;

    })
    .catch((error) => {
        console.error("Error sending message:", error);
    });
}

// On page load
document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("clear-chat-btn").addEventListener("click", clearChat);

    await fetchModels();

    // Load saved model from localStorage and set as selected
    const savedModel = localStorage.getItem("novaSelectedModel");
    if (savedModel && models.includes(savedModel)) {
        selectModel(savedModel, false);
    } else if (models.length > 0) {
        selectModel(models[0], false);
    }

});

// Handle Enter key to send message
userInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Dropdown functionality
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

document.addEventListener("click", (e) => {
    if (!dropdownButton.contains(e.target) && !dropdownList.contains(e.target)) {
        closeDropdown();
    }
});

dropdownButton.addEventListener("click", () => {
    toggleDropdown();
});

dropdownButton.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        openDropdown();
    }
});
