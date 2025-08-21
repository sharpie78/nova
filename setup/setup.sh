#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Determine the real user and home (when run via sudo) — do this FIRST
TARGET_USER=${SUDO_USER:-$(logname)}
TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)

# Absolute dir of this script
SCRIPT_DIR="$(cd -- "$(dirname "$0")" && pwd -P)"

# Setup log file
LOG_DIR="$TARGET_HOME/nova/logs"
mkdir -p "$LOG_DIR"
chown -R "$TARGET_USER:$TARGET_USER" "$LOG_DIR" || true
LOG_FILE="$LOG_DIR/setup.log"

# Redirect: keep colors in terminal, strip ANSI for the logfile
exec > >(tee >(sed -r 's/\x1B\[[0-9;]*[A-Za-z]//g' >> "$LOG_FILE")) 2>&1


# ===== Colors & Symbols =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # reset

TICK="${GREEN}✔${NC}"
CROSS="${RED}✖${NC}"
INFO="${BLUE}ℹ${NC}"
WARN="${YELLOW}⚠${NC}"

info(){ echo -e "${INFO} ${*:-}"; }
ok(){   echo -e "${TICK} ${*:-}"; }
warn(){ echo -e "${WARN} ${*:-}"; }
err(){  echo -e "${CROSS} ${*:-}"; }

trap 'err "Error on line $LINENO. Exiting."' ERR

info "Logging to: $LOG_FILE"

# Require root (sudo) to avoid docker permission issues
if [ "$EUID" -ne 0 ]; then
  err "Please run this script with: sudo $0"
  exit 1
fi



# =========================
# 1) Secret key
# =========================
SECRET_KEY_FILE="$TARGET_HOME/.local/share/nova-ui/nova.key"
mkdir -p "$(dirname "$SECRET_KEY_FILE")"

if [ ! -f "$SECRET_KEY_FILE" ]; then
  info "Generating new secret key..."
  head -c 32 /dev/urandom | base64 > "$SECRET_KEY_FILE"
  chmod 600 "$SECRET_KEY_FILE"
  chown -R "$TARGET_USER":"$TARGET_USER" "$(dirname "$SECRET_KEY_FILE")"
  ok "Secret key saved to $SECRET_KEY_FILE"
else
  ok "Secret key already exists at $SECRET_KEY_FILE"
fi

# =========================
# 2) Python 3.10 + deps
# =========================
desired_python_version="3.10"

if ! command -v python3.10 >/dev/null 2>&1; then
  info "Python3.10 not found. Installing..."
  apt update
  apt install -y software-properties-common
  add-apt-repository -y ppa:deadsnakes/ppa
  apt update
  apt install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pyqt6 \
    python3.10-distutils \
    python3-pyaudio \
    neofetch \
    wmctrl \
    curl \
    wget
  ok "Python 3.10 and deps installed."
else
  info "Python3.10 present. Ensuring deps..."
  apt install -y python3-pyqt6 python3.10-distutils python3-pyaudio neofetch wmctrl curl wget
  ok "Deps ensured."
fi

# Pin python3.10
info "Creating pinning file for Python3.10..."
cat <<EOF >/etc/apt/preferences.d/python_pinning
Package: python3.10
Pin: version ${desired_python_version}*
Pin-Priority: 1001
EOF
ok "Pinning applied."

# Ensure pip for python3.10
if ! python3.10 -m pip --version >/dev/null 2>&1; then
  info "Installing pip for Python3.10..."
  curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
  ok "pip installed for Python3.10."
else
  ok "pip for Python3.10 already installed."
fi

# =========================
# 3) Nova venv + reqs
# =========================
if [ ! -d "$TARGET_HOME/nova/venv" ]; then
  info "Creating Python virtual environment..."
  if /usr/bin/python3.10 -m venv --copies "$TARGET_HOME/nova/venv"; then
    chown -R "$TARGET_USER":"$TARGET_USER" "$TARGET_HOME/nova/venv"
    ok "Virtual env created at $TARGET_HOME/nova/venv"
  else
    err "Failed to create virtual environment."
    exit 1
  fi
else
  ok "Virtual environment already exists at $TARGET_HOME/nova/venv"
fi

# Upgrade pip (as target user)
runuser -l "$TARGET_USER" -c "source '$TARGET_HOME/nova/venv/bin/activate' && pip install --upgrade pip && echo 'pip upgraded successfully.'" || warn "pip upgrade failed."

# Install requirements (as target user)
if runuser -l "$TARGET_USER" -c "cd '$TARGET_HOME/nova' && source venv/bin/activate && pip install -r '$TARGET_HOME/nova/docs/requirements.txt'"; then
  ok "Python requirements installed."
else
  err "Failed to install requirements. Check requirements.txt."
  exit 1
fi

# =========================
# 4) Docker setup
# =========================
info "Checking Docker..."
if dpkg -l | grep -q "^ii.*docker-ce" && grep -q "download.docker.com" /etc/apt/sources.list.d/docker.list 2>/dev/null; then
  ok "Docker already installed with official repo."
else
  info "Installing Docker..."
  apt-get update
  apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" >/etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  if command -v nvidia-smi >/dev/null 2>&1; then
    info "Setting up NVIDIA container toolkit..."
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
      | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
      | tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null
    apt-get update
    apt-get install -y nvidia-container-toolkit
    nvidia-ctk runtime configure --runtime=docker || warn "nvidia-ctk runtime configure failed"
    systemctl restart docker || warn "Failed to restart docker"
    ok "NVIDIA toolkit configured."
  else
    info "No NVIDIA GPU detected. Skipping NVIDIA toolkit."
  fi

  systemctl enable --now docker || warn "Failed to enable/start docker"
  groupadd docker 2>/dev/null || true
  usermod -aG docker "$TARGET_USER" && ok "Added $TARGET_USER to docker group (log out/in to take effect)."
fi

# 4a) Web services
info "Building and starting web services (searxng + webfox)..."
mkdir -p "$TARGET_HOME/nova/tmp/webshots"
chown -R "$TARGET_USER":"$TARGET_USER" "$TARGET_HOME/nova/tmp/webshots"

cd "$TARGET_HOME/nova/backend/services/web"

info "Building webfox image..."
docker compose build webfox || { err "Failed to build webfox image."; exit 1; }
ok "webfox image built."

info "Starting web services (searxng + webfox)..."
docker compose up -d || { err "Failed to start web services."; exit 1; }
ok "Containers up."

# =========================
# 5) Ollama
# =========================
info "Checking Ollama..."

if command -v ollama >/dev/null 2>&1; then
  ok "Ollama already installed."
else
  info "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
  ok "Ollama installed."
fi

# Ensure the service is enabled/running (idempotent)
systemctl enable --now ollama || warn "Failed to enable/start ollama (system)."

# Confirm CLI is accessible for the target user
runuser -l "$TARGET_USER" -c "ollama --version" >/dev/null 2>&1 || warn "Ollama CLI not in PATH for $TARGET_USER yet."

# Count installed models for the user (skip header line safely)
MODEL_COUNT=$(runuser -l "$TARGET_USER" -c "ollama list 2>/dev/null | tail -n +2 | awk 'NF>0' | wc -l" || echo 0)


if [ "${MODEL_COUNT:-0}" -gt 0 ]; then
  ok "Detected ${MODEL_COUNT} Ollama model(s). Skipping starter model pull."
else
  read -p "No models found. Pull llama3.2:3b? (y/N): " pullmodel
  if [[ "${pullmodel:-N}" =~ ^[Yy]$ ]]; then
    runuser -l "$TARGET_USER" -c "ollama pull llama3.2:3b" || warn "Model pull failed."
  else
    info "Skipping starter model pull."
  fi
fi

# =========================
# 6) Piper models
# =========================
echo -e "${BOLD}=== Step 6: Downloading Piper TTS models ===${NC}"

VOICE_BASE="$TARGET_HOME/nova/backend/audio/voices"
mkdir -p "$VOICE_BASE/female" "$VOICE_BASE/male" "$VOICE_BASE/vctk"

download_model() {
    local url=$1
    local outdir=$2
    local filename
    filename=$(basename "$url" | sed 's/?download=true//')

    if [ -s "$outdir/$filename" ]; then
        info "Already present: $outdir/$filename"
        return 0
    fi

    info "Downloading: $filename → $outdir"
    curl -L --retry 3 --fail -o "$outdir/$filename" "$url"
    if [ ! -s "$outdir/$filename" ]; then
        err "$filename failed to download or is empty"
        exit 1
    fi
    ok "Downloaded: $outdir/$filename"
}

# Female (Alba)
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/MODEL_CARD?download=true" "$VOICE_BASE/female"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx?download=true" "$VOICE_BASE/female"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx.json?download=true" "$VOICE_BASE/female"

# Male
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/MODEL_CARD?download=true" "$VOICE_BASE/male"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx?download=true" "$VOICE_BASE/male"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json?download=true" "$VOICE_BASE/male"

# VCTK
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/MODEL_CARD?download=true" "$VOICE_BASE/vctk"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx?download=true" "$VOICE_BASE/vctk"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx.json?download=true" "$VOICE_BASE/vctk"

# Ensure ownership for the real user
chown -R "$TARGET_USER":"$TARGET_USER" "$VOICE_BASE"

# Condensed summary: show just the model name (no extensions)
model_name() {
  local dir="${1-}"
  [ -n "$dir" ] || { echo "none"; return 0; }
  local f
  f=$(ls "$dir"/*.onnx 2>/dev/null | head -n1 || true)
  if [ -n "${f:-}" ]; then
    basename "$f" .onnx
  else
    echo "none"
  fi
}

echo -e "${GREEN}Piper TTS models installed:${NC}"
echo -e "  ${YELLOW}female:${NC}       $(model_name "$VOICE_BASE/female")"
echo -e "  ${YELLOW}male:${NC}         $(model_name "$VOICE_BASE/male")"
echo -e "  ${YELLOW}multi-voice:${NC} $(model_name "$VOICE_BASE/vctk")"

ok "Piper TTS models step complete."

# =========================
# 7) novatray user service
# =========================
SERVICE_DIR="$TARGET_HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/novatray.service"

if [ ! -d "$SERVICE_DIR" ]; then
  info "Systemd folder does not exist for $TARGET_USER. Creating it..."
  mkdir -p "$SERVICE_DIR"
  chown -R "$TARGET_USER":"$TARGET_USER" "$TARGET_HOME/.config"
fi

# Allow lingering so user services can run without an active login
loginctl enable-linger "$TARGET_USER" || true

# Avoid clobbering bash's UID; compute user's runtime dir
TARGET_UID=$(id -u "$TARGET_USER")
if [ ! -d "/run/user/$TARGET_UID" ]; then
  info "Creating /run/user/$TARGET_UID"
  mkdir -p "/run/user/$TARGET_UID"
  chown "$TARGET_UID:$TARGET_UID" "/run/user/$TARGET_UID"
  chmod 700 "/run/user/$TARGET_UID"
fi

if [ ! -f "$SERVICE_FILE" ]; then
  info "Service file does not exist. Copying to user's systemd folder..."
  cp "$SCRIPT_DIR/novatray.service" "$SERVICE_FILE"
  chown "$TARGET_USER":"$TARGET_USER" "$SERVICE_FILE"
fi

# Reload + enable + start (split steps for VM reliability)
info "Reloading user systemd and enabling novatray..."
runuser -l "$TARGET_USER" -c "XDG_RUNTIME_DIR=/run/user/$TARGET_UID systemctl --user daemon-reload" || true
runuser -l "$TARGET_USER" -c "XDG_RUNTIME_DIR=/run/user/$TARGET_UID systemctl --user enable novatray.service" || true
runuser -l "$TARGET_USER" -c "XDG_RUNTIME_DIR=/run/user/$TARGET_UID systemctl --user start novatray.service" || true
# Optional restart if already running
runuser -l "$TARGET_USER" -c "XDG_RUNTIME_DIR=/run/user/$TARGET_UID systemctl --user restart novatray.service" || true
ok "novatray user service enabled and started."

# =========================
# Final summary
# =========================
echo -e "${BOLD}====================================================${NC}"
echo -e "${GREEN}Nova setup complete for user: ${BOLD}$TARGET_USER${NC}"
echo -e "If you were added to the docker group, log out and back in for it to take effect."
echo -e "${BOLD}====================================================${NC}"

read -p "Reboot now? (y/N): " answer
if [[ "${answer:-N}" =~ ^[Yy]$ ]]; then
  info "Rebooting system..."
  reboot
else
  info "Reboot skipped. Please reboot later if needed."
fi
