
# NOVA Project Documentation

NOVA is for people who want local AI but dont really get all the jargon or terminology. It’s simple, intuitive, and functional with no deep programming or AI knowledge required.

I tried the excellent OpenWebUI and the localAI/localRecall/localAGI bundle, but the sheer number of options was overwhelming. NOVA borrows the good ideas from them and other apps whilst keeps things easy to understand.

Tech stack

OS: Kubuntu 24.04 LTS

Built with: Python, HTML, CSS, JavaScript

Packaging: Tauri (native desktop app – not browser-based)
I am not a seasoned coder. I’m learning as I go and using ChatGPT to write all the code under my direction. I can read some code, but I don’t write much yet. If you’re up for code reviews or contributions, I’d love help.

What it does (or will do)

Chat with a local AI - works

File access (RAG) - works

Web search - works

Injectible “memories” -sorks

Editor window (like ChatGPT’s Canvas) - works

Optional access to local media - wip

To-do list - wip

home-automation hooks; chat via WhatsApp/WebApp/IRC using AI - wip

There’s already an agent in place to help with functions in chat window but it needs refining

Voice interaction with pc via Agent (think alexa like capabilities) - wip

Platform support

Now: Linux (Kubuntu 24.04 LTS) only.
Some README steps may not work for every setup. Another dev could help expand support.

Status

Usable, basic, and designed to be intuitive. Install it and have a poke around.

Call for collaborators

Help with code review, cleanup, or cross-platform support would be massively appreciated. It is currently highly tailored to my system and preferences so I need help making it more generalised for other peoples systems and preferences


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
cd /mnt/nova
/usr/bin/python3.10 -m venv --copies venv
source venv/bin/activate
```

### Installing python Dependencies
Upgrade `pip`:

```bash
pip install --upgrade pip
```

Then install the required dependencies:

```bash
pip install -r $HOME/nova/docs/requirements.txt
```

If you encounter issues with `requirements.txt`, you can try installing the dependencies manually:

```bash
pip install requests PyQt6 setproctitle loguru fastapi pydantic psutil websocket-client sounddevice numpy pyjwt tinydb bcrypt "uvicorn[standard]" onnxruntime-gpu piper-tts "piper-tts[http]"
```

### Installing system dependencies
To install **PyQt6**:

```bash
sudo apt install python3-pyqt6 neofetch wmctrl
```

To install **Ollama**:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```
...and set up however you would normally...i.e....download a model etc....if you've never used Ollama before, full instructions avaiable
at https://github.com/ollama/ollama

Setup Tauri

```bash
sudo apt update
```
```bash
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget file libxdo-dev libssl-dev libayatana-appindicator3-dev librsvg2-dev
```

```bash
curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh  ---press enter to install default
```

```bash
. "$HOME/.cargo/env"
```

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
```

```bash
source ~/.zshrc
```

```bash
nvm install 22
```

```bash
nvm use 22
```

```bash
node -v
```
 should show v22.x

```bash
npm -v
```
should show ~10.x

```bash
source ~/.cargo/env

source ~/.zshrc
```

Add something like this to your README.md:

## 🔉 Download Voice Model Files (Required for TTS)

Due to size, the ONNX voice models are not included in this repository.

Please download them manually and place them in:

backend/audio/voices/


### Download Links:

- Alba: [Download en_GB-alba-medium.onnx](https://your-hosting.com/alba/en_GB-alba-medium.onnx)
- Male: [Download en_GB-northern_english_male-medium.onnx](https://your-hosting.com/male/en_GB-northern_english_male-medium.onnx)
- VCTK: [Download en_GB-vctk-medium.onnx](https://your-hosting.com/vctk/en_GB-vctk-medium.onnx)

After downloading, the folder structure should look like:


backend/audio/voices/
├── alba/
│ ├── en_GB-alba-medium.onnx
│ └── en_GB-alba-medium.onnx.json
├── male/
│ ├── en_GB-northern_english_male-medium.onnx
│ └── en_GB-northern_english_male-medium.onnx.json
├── vctk/
│ ├── en_GB-vctk-medium.onnx
│ └── en_GB-vctk-medium.onnx.json


Setup Docker

install docker as per instructions for your setup and then run

```bash
cd /mnt/nova/services/web
```

```bash
docker compose build webfox
```

```bash
docker compose up -d
```
to verify docker working....
WebFox (headless Firefox microservice)
```bash
curl -s -X POST http://127.0.0.1:8070/browse \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'
```

SearXNG (private search)
```bash
curl 'http://127.0.0.1:8888/search?q=test&format=json' | head
```


## Enabling Nova to Start on Boot

To enable **Nova** to start on every boot, follow one of these methods:

### Method 1: Systemd Integration - preferred
- Run `setup_tray.sh` from the `setup` folder or double-click the `setup_tray.desktop` file.
- This will create a "secret.key" file in  config folder which is used throughout app for authentication. It will then install the `novatray.service` to `~/.config/systemd/user` and should open an instance of the tray app.

### Method 2: Manual Startup and Integration - dunno if this works anymore----test
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

You should be able to just go to [start-here](http://127.0.0.1:56969/index.html) and use a browser if you dont want to bother with the App.
