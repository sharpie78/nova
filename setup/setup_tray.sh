#!/bin/bash

# Get the directory of the current script (where this shell script is located)
SCRIPT_DIR=$(dirname "$0")

# Define the service file path dynamically
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$SERVICE_DIR/novatray.service"

# Step 1: Check if the systemd folder exists
if [ ! -d "$SERVICE_DIR" ]; then
    echo "Systemd folder does not exist. Creating it..."
    mkdir -p "$SERVICE_DIR"
fi

# Step 2: Check if the service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Service file does not exist. Copying to .config/systemd folder..."

    # Step 3: Copy the service file from the utils folder (one level up from script directory)
    cp "$SCRIPT_DIR/novatray.service" "$SERVICE_FILE"

    # Step 4: Reload systemd to register the new service
    echo "Reloading systemd to register the new service..."
    systemctl --user daemon-reload

    # Enable the service
    echo "Enabling the Nova Tray service..."
    systemctl --user enable novatray.service
    sleep 5
    systemctl --user start novatray.service
    sleep 5
    systemctl --user restart novatray.service

else
    echo "Service file exists. Ensuring the service is enabled and running..."
    # Ensure the service is enabled and started
    systemctl --user daemon-reload
    sleep 5
    systemctl --user enable novatray.service
    sleep 5
    systemctl --user start novatray.service
fi





