# Tauri Toolchain Setup (UI + Editor)

## 1) System packages
Use for WebKitGTK, appindicator, SSL, etc.
```bash
cd $HOME/nova/frontend
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
```

## 2) Rust (rustup)
Runs an interactive installer — pick option **1** (default).
```bash
curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh
```
select option 1

Load Rust env for this shell:
```bash
. "$HOME/.cargo/env"
```

## 3) NVM install
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
```

Load NVM (one-time in this shell) + add to your shell RC going forward:
```bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"
```

Persist NVM for future shells (auto-append if missing):
```bash
if [ -n "$ZSH_VERSION" ] || [ "$(basename "${SHELL:-}")" = "zsh" ]; then
  RC="$HOME/.zshrc"
else
  RC="$HOME/.bashrc"
fi

if ! grep -q 'export NVM_DIR="$HOME/.nvm"' "$RC" 2>/dev/null; then
cat >> "$RC" <<'ZSHNVM'
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"
ZSHNVM
fi
```

Reload your shell RC (zsh ok; bash ignored):
```bash
. "$HOME/.zshrc" 2>/dev/null || true
```

Source NVM now
```bash
. "$HOME/.nvm/nvm.sh"
```

## 4) Node 22 + verify
```bash
nvm install 22
node -v
nvm current
npm -v
```
# Should print  the follwing underneath setup completion
"v22.xx.x".
"v22.xx.x".
"10.x.x".

## 5) Ensure env is loaded (Rust + shell RC)
```bash
[ -s "$HOME/.cargo/env" ] && source "$HOME/.cargo/env"

if [ -f "$HOME/.zshrc" ]; then
  source "$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
  source "$HOME/.bashrc"
fi
```

---

# Create the two Tauri apps

## nova-ui
```bash
cd $HOME/nova/frontend/
```
```bash
sh <(curl https://create.tauri.app/sh)
```
Answers:
- Project name · **nova-ui**
- Identifier · **nova-ui**
- nova-ui directory is not empty, do you want to overwrite? · **yes**
- Choose which language to use for your frontend · **TypeScript / JavaScript - (pnpm, yarn, npm, deno, bun)**
- Choose your package manager · **npm**
- Choose your UI template · **Vanilla**
- Choose your UI flavor · **JavaScript**

Install CLI + reset src:
```bash
cd $HOME/nova/frontend/nova-ui
npm install -D @tauri-apps/cli@latest
```
```bash
rm -rf src
mkdir -p src
```

## nova-editor
```bash
cd $HOME/nova/frontend/
```
```bash
sh <(curl https://create.tauri.app/sh)
```
Answers:
- Project name · **nova-editor**
- Identifier · **nova-editor**
- nova-editor directory is not empty, do you want to overwrite? · **yes**
- Choose which language to use for your frontend · **TypeScript / JavaScript - (pnpm, yarn, npm, deno, bun)**
- Choose your package manager · **npm**
- Choose your UI template · **Vanilla**
- Choose your UI flavor · **JavaScript**

Install CLI + reset src:
```bash
cd $HOME/nova/frontend/nova-editor
npm install -D @tauri-apps/cli@latest
```
```bash
rm -rf src
mkdir -p src
```

## Restore tracked frontend (warning)
```bash
cd  $HOME/nova
git restore frontend
```

---

# Run / Build

## Run nova-ui (dev)
```bash
cd $HOME/nova/frontend/nova-ui
npx tauri dev
```

## Build nova-ui (AppImage)
```bash
cd $HOME/nova/frontend/nova-ui
npx tauri build
```

## Run nova-editor (dev)
```bash
cd $HOME/nova/frontend/nova-editor
npx tauri dev
```

## Build nova-editor (AppImage)
```bash
cd $HOME/nova/frontend/nova-editor
npx tauri build
```
