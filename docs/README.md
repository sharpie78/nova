
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

Run the setup.sh script in the nova/setup folder. This should check for and install all pre-requisites and leave you with a tray icon you can use to start interacting with nova.

A detailed setup instructions file can be fouind in the docs folder




very rough version below....

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
