# NOVA  

NOVA is a local AI assistant for people who don’t want to drown in jargon. I've tried to make it simple, intuitive, and functional — no deep coding or AI knowledge needed.  

## Status  
Usable, basic, and under active development. Expect things to change.  

## Features (current & planned)  
- ✅ Chat with a local AI  
- ✅ File access (RAG)  
- ✅ Web search  
- ✅ Editor window (like ChatGPT’s Canvas)  
- ⚙️ Injectible “memories”  
- ⚙️ Voice interaction (agent-style, Alexa-like)  
- ⚙️ Optional media & home automation hooks  

## Platform Support  
- **Now:** Linux (tested on Kubuntu 24.04 LTS)  
- **Future:** Community contributions for other platforms welcome  

## Install & Setup  
Clone the repo into your home folder and run the setup script:  

```bash
git clone https://github.com/sharpie78/nova.git
cd nova/setup
chmod +x setup.sh
sudo ./setup.sh
```  

The script will:  
- Install dependencies (Python 3.10, PyQt, Docker, etc.)  
- Configure Nova’s environment  
- Enable the tray app (systemd service)  

After install, you’ll have a tray icon to start interacting with Nova.  
The first run may take a while, and you’ll need to **respond to some prompts**.  
If you want the latest version of the project, run the following:


```bash
cd $HOME/nova
git pull origin main
cd setup
chmod +x setup.sh
sudo ./setup.sh
```

## Usage  
- Nova runs from the tray app (auto-start at boot by default).  
- You can also access the UI in a browser at:  
  [http://127.0.0.1:56969/index.html](http://127.0.0.1:56969/index.html) *(planned, not yet working)*  

## Documentation  
- **Detailed User setup instructions:** [detailed_setup.md](detailed_setup.md)
- **Developer guide:** [dev_readme.md](dev_readme.md)  
- **Developer Tauri setup process:** [dev_tauri_setup.md](dev_tauri_setup.md)


## Contributing  
Help with code review, cleanup, or cross-platform support would be massively appreciated.  
