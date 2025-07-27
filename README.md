
# Nova Project Documentation

This is the very start of the project—lots of placeholders and incomplete instructions. Contributions are welcome, ChatGPT is doing all the coding at the moment. The developer has very limited Python, HTML, CSS, and JS knowledge, can read some of it but can't write a line. You'll need the admin password if you want to contribute.

It's solely developed on **Kubuntu 24.04 LTS**, so keep that in mind when using my example commands. I can't provide support for other platforms. Sorry. You are welcome to create a fork and do so yourself.

## Setup

Create nova folder at /mnt/nova

   ```bash
   sudo mkdir -p /mnt/nova
   ```

   ```bash
   sudo chown <user>:<user> /mnt/nova
   ```

   ```bash
   sudo chmod +x /mnt/nova
   ```

## Install Python 3.10

Ensure you are using **Python 3.10**. If it’s not already installed, you’ll need to add the Deadsnakes repository to your system.

To install Python 3.10:

1. Add the Deadsnakes repository:

   ```bash
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   ```

2. Install Python 3.10:

   ```bash
   sudo apt install python3.10 python3.10-venv python3.10-dev
   ```

3. Verify the installation:

   ```bash
   which python3.10
   ```
This should return `/usr/local/bin/python3.10`

You now have Python 3.10 installed.

## Set Up Your Development Environment - python venv example

### Virtual Environment
Create the virtual environment in the `nova/backend` directory with the following command:

```bash
cd /mnt/nova/backend
/usr/bin/python3.10 -m venv --copies venv
source venv/bin/activate
```

### Installing Dependencies
Upgrade `pip`:

```bash
pip install --upgrade pip
```

Then install the required dependencies:

```bash
pip install -r /mnt/nova/docs/requirements.txt
```

If you encounter issues with `requirements.txt`, you can try installing the dependencies manually:

```bash
pip install requests PyQt6 setproctitle loguru fastapi pydantic psutil websocket-client sounddevice numpy pyjwt tinydb bcrypt "uvicorn[standard]" onnxruntime-gpu piper-tts "piper-tts[http]"
```

### Installing system dependencies
To install **PyQt6**:

```bash
sudo apt install python3-pyqt6 neofetch
```


## Enabling Nova to Start on Boot

To enable **Nova** to start on every boot, follow one of these methods:

### Method 1: Systemd Integration
- Run `setup_tray.sh` from the `setup` folder or double-click the `setup_tray.desktop` file.
- This will install the `novatray.service` to `~/.config/systemd/user` and should open an instance of the tray app.

### Method 2: Manual Startup and Integration
- Run `novatray.sh` or double-click on `novatray.desktop` to open the tray app.
- Once opened, click on "Integrate Nova" to perform the same action. It will close the current tray instance and leave a new one running via the systemd service. Be patient—it will take about 20 seconds.



## General Usage

Once the system is set up, you can interact with the Nova project through the tray application. The tray will allow you to control the system and integrate with various components such as the AI assistant and home automation/media player, etc. 

So far, features are limited. AI chat works, but you'll need to install **Ollama** and have at least one model downloaded. With Ollama installed, you'll be able to select models and chat. 

I have no idea if the **system_status** card/modal will work for anyone else. It's all written to run on my PC.

### Running Nova
- To start Nova, you can use the tray app. If you have followed the systemd integration method, the tray app will start automatically at boot. Otherwise, you can manually start it via the `novatray.sh` or `novatray.desktop` file.

### Interacting with Nova
- **Integrate Nova**: Click the "Integrate Nova" button in the tray app to ensure that the application is running in the background and managed by systemd.
- **General Controls**: You can interact with Nova through the tray app interface to control system settings, run tasks, or configure various features.

## Miscellaneous Information

Expect you'll have to install Tauri to run the Nova UI app. The instructions I used are in the **docs** folder.

You should be able to just go to [dashboard-login](http://127.0.0.1:56969/index.html) and use a browser if you dont want to bother with the App.
