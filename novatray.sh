#!/bin/bash

KEY_DIR="$HOME/.local/share/nova-UI"
SECRET_KEY_FILE="$KEY_DIR/nova.key"

# Ensure key directory exists
mkdir -p "$KEY_DIR"

# Generate a secret key only if it doesn't exist
if [ ! -f "$SECRET_KEY_FILE" ]; then
    echo "Generating new secret key..."
    head -c 32 /dev/urandom | base64 > "$SECRET_KEY_FILE"
    echo "Secret key saved to $SECRET_KEY_FILE"
fi

# Activate the virtual environment
source /mnt/nova/backend/venv/bin/activate

/mnt/nova/backend/novatray.py
