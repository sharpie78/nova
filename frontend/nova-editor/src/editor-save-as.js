
let currentFilePath = null;  // Track the open file path
let editorInstance = null;

// file saving section
// Adds a toast for file saved feedback
function showFileSavedToast(path) {
  let toast = document.getElementById("file-saved-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "file-saved-toast";
    toast.style.position = "fixed";
    toast.style.bottom = "70px";
    toast.style.left = "50%";
    toast.style.transform = "translateX(-50%)";
    toast.style.backgroundColor = "#2e2e2e";
    toast.style.color = "#f0f0f0";
    toast.style.padding = "12px 24px";
    toast.style.border = "1px solid #555";
    toast.style.borderRadius = "6px";
    toast.style.fontSize = "1.4rem";
    toast.style.zIndex = "9999";
    document.body.appendChild(toast);
  }
  toast.textContent = `File saved at: ${path}`;
  toast.style.display = "block";
  setTimeout(() => toast.style.display = "none", 2500);
}

// SAVE override with toast
async function save() {
  if (!currentFilePath) {
    saveAs();
    return;
  }
  const content = cm.getValue();
  try {
    const response = await fetch("http://127.0.0.1:56969/save_file", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: currentFilePath, content })
    });
    if (!response.ok) throw new Error("Failed to save file");
    showFileSavedToast(currentFilePath);
  } catch (err) {
    alert("Error saving file: " + err.message);
  }
}


// MODIFY SAVE AS TO SUPPORT SUBFOLDER NAVIGATION + BACK BUTTON + FILE LISTING + OVERWRITE CONFIRMATION
async function saveAs() {
  const modal = document.createElement("div");
  modal.id = "save-as-modal";
  modal.style.position = "fixed";
  modal.style.top = "50%";
  modal.style.left = "50%";
  modal.style.transform = "translate(-50%, -50%)";
  modal.style.background = "#2e2e2e";
  modal.style.padding = "20px";
  modal.style.border = "1px solid #555";
  modal.style.borderRadius = "8px";
  modal.style.color = "#f0f0f0";
  modal.style.fontSize = "1.4rem";
  modal.style.zIndex = "10000";
  modal.style.minWidth = "400px";

  const heading = document.createElement("div");
  heading.textContent = "Save As";
  heading.style.fontSize = "1.6rem";
  heading.style.marginBottom = "12px";

  const list = document.createElement("div");
  list.style.maxHeight = "200px";
  list.style.overflowY = "auto";
  list.style.marginBottom = "12px";

  let selectedFolder = "";
  let inputField = null;
  let confirmText = null;
  let previouslySelected = null;
  let currentPath = "/home/jack/nova/vault";

  let existingFiles = [];

  async function renderFolders(folderPath, container) {
    container.innerHTML = "";
    const folders = await fetch(`http://127.0.0.1:56969/list_directory?folder=${encodeURIComponent(folderPath)}`).then(r => r.json());

    existingFiles = folders.items.filter(f => !f.is_dir).map(f => f.name);

    if (folderPath !== "/home/jack/nova/vault") {
      const back = document.createElement("div");
      back.textContent = "⬅️ ..";
      back.className = "file-item";
      back.onclick = () => {
        const up = folderPath.split("/").slice(0, -1).join("/") || "/";
        currentPath = up;
        renderFolders(up, container);
      };
      container.appendChild(back);
    }

    for (const item of folders.items) {
      const div = document.createElement("div");
      div.className = item.is_dir ? "tree-folder file-item" : "tree-file file-item";
      div.textContent = item.name;

      div.onclick = async () => {
        if (previouslySelected) previouslySelected.style.backgroundColor = "";
        div.style.backgroundColor = "#3a3a3a";
        previouslySelected = div;

        if (item.is_dir) {
          selectedFolder = item.path;
          currentPath = item.path;
          await renderFolders(item.path, list);
        } else {
          selectedFolder = folderPath;
          if (inputField) inputField.value = item.name;
        }

        if (!inputField) {
          inputField = document.createElement("input");
          inputField.type = "text";
          inputField.placeholder = "Enter file name...";
          inputField.style.marginTop = "12px";
          inputField.style.width = "100%";
          inputField.style.padding = "8px";
          inputField.style.fontSize = "1.4rem";
          inputField.style.border = "1px solid #555";
          inputField.style.borderRadius = "6px";
          inputField.style.backgroundColor = "#1e1e1e";
          inputField.style.color = "#f0f0f0";
          modal.appendChild(inputField);

          confirmText = document.createElement("div");
          confirmText.style.marginTop = "8px";
          confirmText.style.fontSize = "1.2rem";
          modal.appendChild(confirmText);

          const buttonRow = document.createElement("div");
          buttonRow.style.marginTop = "12px";
          buttonRow.style.display = "flex";
          buttonRow.style.justifyContent = "flex-end";

          const cancelBtn = document.createElement("button");
          cancelBtn.textContent = "Cancel";
          cancelBtn.className = "editor-button";
          cancelBtn.onclick = () => modal.remove();

          const saveBtn = document.createElement("button");
          saveBtn.textContent = "Save";
          saveBtn.className = "editor-button";
          saveBtn.onclick = async () => {
            const filename = inputField.value;
            const newPath = selectedFolder + "/" + filename;
            const content = cm.getValue();

            if (existingFiles.includes(filename)) {
              if (!document.getElementById("overwrite-confirm")) {
                const confirmBox = document.createElement("div");
                confirmBox.id = "overwrite-confirm";
                confirmBox.style.position = "fixed";
                confirmBox.style.top = "40%";
                confirmBox.style.left = "50%";
                confirmBox.style.transform = "translate(-50%, -50%)";
                confirmBox.style.background = "#2e2e2e";
                confirmBox.style.padding = "20px";
                confirmBox.style.border = "1px solid #555";
                confirmBox.style.borderRadius = "8px";
                confirmBox.style.color = "#f0f0f0";
                confirmBox.style.zIndex = "10001";
                confirmBox.style.fontSize = "1.3rem";
                confirmBox.textContent = `Overwrite existing file: ${filename}?`;

                const yesBtn = document.createElement("button");
                yesBtn.textContent = "Yes";
                yesBtn.className = "editor-button";
                yesBtn.style.margin = "12px";
                yesBtn.onclick = async () => {
                  confirmBox.remove();
                  try {
                    const response = await fetch("http://127.0.0.1:56969/save_file", {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ path: newPath, content })
                    });
                    if (!response.ok) throw new Error("Failed to save file");
                    currentFilePath = newPath;
                    modal.remove();
                    showFileSavedToast(currentFilePath);
                  } catch (err) {
                    alert("Error saving file: " + err.message);
                  }
                };

                const noBtn = document.createElement("button");
                noBtn.textContent = "No";
                noBtn.className = "editor-button";
                noBtn.onclick = () => confirmBox.remove();

                const btnRow = document.createElement("div");
                btnRow.className = "btn-row";
                btnRow.appendChild(yesBtn);
                btnRow.appendChild(noBtn);
                confirmBox.appendChild(btnRow);
                document.body.appendChild(confirmBox);
              }
              return;
            }

            try {
              const response = await fetch("http://127.0.0.1:56969/save_file", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ path: newPath, content })
              });
              if (!response.ok) throw new Error("Failed to save file");
              currentFilePath = newPath;
              modal.remove();
              showFileSavedToast(currentFilePath);
            } catch (err) {
              alert("Error saving file: " + err.message);
            }
          };

          buttonRow.append(cancelBtn, saveBtn);
          modal.appendChild(buttonRow);

          inputField.addEventListener("keydown", (e) => {
            if (e.key === "Enter") saveBtn.click();
          });
        }

        inputField.focus();
        confirmText.textContent = `Save file as: ${selectedFolder}/${inputField.value}`;
        inputField.oninput = () => {
          confirmText.textContent = `Save file as: ${selectedFolder}/${inputField.value}`;
        };
      };

      container.appendChild(div);
    }
  }

  modal.appendChild(heading);
  modal.appendChild(list);
  document.body.appendChild(modal);
  await renderFolders(currentPath, list);
}
