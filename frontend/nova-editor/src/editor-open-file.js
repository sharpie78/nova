

// open files section
async function openFromVault() {
  const modal = document.getElementById("open-modal");
  const container = document.getElementById("file-tree-root");
  container.innerHTML = "";

  async function renderFolder(folderPath, parentEl) {
    try {
      const response = await fetch(`http://127.0.0.1:56969/list_directory?folder=${encodeURIComponent(folderPath)}`);
      const data = await response.json();

      for (const item of data.items) {
        if (item.is_dir) {
          const folderEl = document.createElement("div");
          folderEl.classList.add("tree-folder", "file-item");
          folderEl.textContent = item.name;

          const childrenContainer = document.createElement("div");
          childrenContainer.classList.add("tree-indent");
          childrenContainer.style.display = "none";

          folderEl.onclick = async (e) => {
            e.stopPropagation();
            if (childrenContainer.childElementCount === 0) {
              await renderFolder(item.path, childrenContainer);
            }
            childrenContainer.style.display = childrenContainer.style.display === "none" ? "block" : "none";
          };

          parentEl.appendChild(folderEl);
          parentEl.appendChild(childrenContainer);
        } else {
          ((filePath, fileName) => {
            const fileEl = document.createElement("div");
            fileEl.classList.add("tree-file", "file-item");
            fileEl.textContent = fileName;

            fileEl.onclick = (e) => {
              e.stopPropagation();
              loadFile(filePath);
              modal.classList.add("hidden");
            };
            parentEl.appendChild(fileEl);
          })(item.path, item.name);
        }
      }
    } catch (err) {
      alert("Failed to load directory: " + err.message);
    }
  }

  await renderFolder("/mnt/nova/vault", container);
  modal.classList.remove("hidden");

  document.addEventListener("click", function closeModal(e) {
    if (!modal.contains(e.target)) {
      modal.classList.add("hidden");
      document.removeEventListener("click", closeModal);
    }
  });
}



async function loadFile(path) {
  try {
    const response = await fetch(`http://127.0.0.1:56969/load_file?path=${encodeURIComponent(path)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Failed to load file");
    cm.setValue(data.content);
    currentFilePath = path;
    document.getElementById("open-modal").classList.add("hidden");

    const statusBar = document.querySelector(".editor-status-bar");
    let pathLabel = document.getElementById("current-file-path");
    if (!pathLabel) {
      pathLabel = document.createElement("div");
      pathLabel.id = "current-file-path";
      pathLabel.style.marginRight = "auto";
      pathLabel.style.fontSize = "1.2rem";
      pathLabel.style.overflow = "hidden";
      pathLabel.style.textOverflow = "ellipsis";
      pathLabel.style.whiteSpace = "nowrap";
      pathLabel.style.maxWidth = "70%";
      statusBar.prepend(pathLabel);
    }
    pathLabel.innerHTML = `<em>Currently loaded file:</em> ${path}`;
  } catch (err) {
    alert("Error loading file: " + err.message);
  }
}
