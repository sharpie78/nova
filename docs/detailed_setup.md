# Nova Detailed Setup Guide

This guide covers manual setup steps for Nova. Most users should just run `setup.sh`.  
Use this only if you need finer control or troubleshooting.

## Install Python 3.10

Nova requires **Python 3.10**. The setup script installs it automatically via the deadsnakes PPA, but you can do it manually:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

Verify installation:

```bash
which python3.10
```

---

## Virtual Environment

```bash
cd ~/nova
/usr/bin/python3.10 -m venv --copies venv
source venv/bin/activate
```

Upgrade pip and install dependencies:

```bash
pip install --upgrade pip
pip install -r docs/requirements.txt
```

If issues occur, install manually:

```bash
pip install requests PyQt6 setproctitle loguru fastapi pydantic psutil websocket-client sounddevice numpy pyjwt tinydb bcrypt "uvicorn[standard]" onnxruntime-gpu piper-tts "piper-tts[http]"
```

---

## System Dependencies

```bash
sudo apt install python3-pyqt6 neofetch wmctrl
```

---

## Docker Setup

Install Docker as per your system instructions, then run:

```bash
cd ~/nova/backend/services/web
docker compose build webfox
docker compose up -d
```

Verify:

```bash
curl -s -X POST http://127.0.0.1:8070/browse -H 'Content-Type: application/json' -d '{"url":"https://example.com"}'
curl 'http://127.0.0.1:8888/search?q=test&format=json' | head
```

---

## Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Follow Ollama’s instructions to download and run a model:  
👉 https://github.com/ollama/ollama

---

## Setup Tauri

```bash
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
```

Install Rust:

```bash
curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh
. "$HOME/.cargo/env"
```

Install Node.js (via NVM):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.zshrc
nvm install 22
nvm use 22
```

Verify:

```bash
node -v   # should show v22.x
npm -v    # should show ~10.x
```
