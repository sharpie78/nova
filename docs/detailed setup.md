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

### instwll cuda
???


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








### install **Ollama**:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```
...and set up however you would normally...i.e....download a model etc....if you've never used Ollama before, full instructions avaiable
at https://github.com/ollama/ollama

### Setup Tauri

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
