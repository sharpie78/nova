# 🛠️ Nova Developer Guide

## 🔀 Branch Structure

- **main**: Production setup  
  - Clean repo for users  
  - No raw frontend source or AppImages  
  - `setup.sh` downloads AppImages

- **nova-dev**: Developer branch  
  - Includes raw frontend source in `src/`  
  - Excludes AppImages and `src-tauri/`  
  - Used for active dev work

---

## 📁 Folder Structure

```
frontend/
├── nova-editor/
│   └── src/           # HTML/CSS/JS source
│   └── [src-tauri/]   # Ignored (local only)
├── nova-ui/
│   └── src/           # HTML/CSS/JS source
│   └── [src-tauri/]   # Ignored (local only)
config/
├── default.settings.json
├── admin.settings.json  # Ignored
├── users.json           # Ignored
setup.sh                 # Main install script
```

---

## ⚙️ Developer Setup

1. Clone the repo and checkout `nova-dev`:

```bash
git clone https://github.com/your-org/nova.git
cd nova
git checkout nova-dev
```

2. Create user config:

```bash
cp config/default.settings.json config/admin.settings.json
```

3. Restore `src-tauri/` (optional for native app dev):  
   - Download from GitHub Releases (or backup)  
   - Extract into `frontend/nova-editor/src-tauri/` and `frontend/nova-ui/src-tauri/`

4. Install frontend deps:

```bash
cd frontend/nova-editor
npm install
npm run tauri dev
```

Repeat for `nova-ui` if needed.

---

## 🚫 Git Ignore Strategy

| File/Folder                | Tracked? | Notes                    |
|-----------------------------|----------|--------------------------|
| `frontend/nova-*/src/`      | ✅ Yes   | Actual source code       |
| `frontend/nova-*/src-tauri/`| ❌ No    | Too large, ignored       |
| `*.AppImage`                | ❌ No    | Downloaded by setup      |
| `config/admin.settings.json`| ❌ No    | User config              |
| `config/users.json`         | ❌ No    | User config              |

---

## 🔄 Merging nova-dev → main

- Only `src/` folders merge into `main`  
- Manually restore/exclude `src-tauri/` and AppImages  
- `setup.sh` handles AppImage downloads for users  

---

## 🧪 Tools & Scripts

- `setup.sh` → Installs backend, downloads AppImages  
- `dev-tauri-setup.sh` → Restores `src-tauri/` for dev  
- `scripts/backup-frontend.sh` → Optional backup helper  

---

## 📎 Tips

- Always stash/backup `src-tauri/` before branch switching  
- Keep `nova-dev` as source of truth for UI/HTML/CSS/JS  
- Document non-Git-tracked files here or in README  
