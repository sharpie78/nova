# 🛠️ Nova Dev Guide

## 🔀 Branch Structure

- `main`: Production setup
  - Clean repo for users
  - No raw frontend source
  - No Tauri files or AppImages in Git
  - Setup script downloads AppImages

- `nova-dev`: Developer branch
  - Includes raw frontend source in `src/`
  - Excludes `.AppImage` binaries
  - Ignores `src-tauri/`
  - Used for ongoing dev work

---

## 📁 Folder Structure

```
frontend/
├── nova-editor/
│   └── src/           # HTML/CSS/JS source (included)
│   └── [src-tauri/]   # Ignored, local only
├── nova-ui/
│   └── src/           # HTML/CSS/JS source (included)
│   └── [src-tauri/]   # Ignored, local only
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

3. Restore `src-tauri/` folders (optional for native app dev):
- Download from GitHub Releases (or backup)
- Extract to `frontend/nova-editor/src-tauri/` and `frontend/nova-ui/src-tauri/`

4. Install frontend deps:
```bash
cd frontend/nova-editor
npm install
npm run tauri dev
```

Repeat for `nova-ui` if needed.

---

## 🚫 Git Ignore Strategy

| File/Folder                        | Tracked? | Notes                        |
|----------------------------------|----------|------------------------------|
| `frontend/nova-*/src/`           | ✅ Yes   | Your actual source code     |
| `frontend/nova-*/src-tauri/`     | ❌ No    | Too large, ignored          |
| `*.AppImage`                     | ❌ No    | Downloaded by setup         |
| `config/admin.settings.json`     | ❌ No    | User-specific config        |
| `config/users.json`              | ❌ No    | User-specific config        |
| `package.json`, `README.md` etc. | ❌ No    | Not required in `main`      |

---

## 🔄 Merging nova-dev → main

When merging:
- Only `src/` folders are merged into `main`
- You must manually restore or exclude `src-tauri/` and AppImages before commit
- `setup.sh` takes care of downloading AppImages for users

---

## 🧪 Tools & Scripts

- `setup.sh`: Installs backend, downloads AppImages
- `dev-tauri-setup.sh` (optional): Restores `src-tauri/` for dev
- `scripts/backup-frontend.sh`: (optional) Save `src/` for merge protection

---

## 📎 Tips

- Always stash or backup `src-tauri/` before switching branches
- Keep `nova-dev` as your source of truth for UI/HTML/CSS/JS
- Document all non-Git-tracked files in this guide or README

