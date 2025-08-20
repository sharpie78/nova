import sounddevice as sd
import numpy as np
import subprocess
import signal
import os
import sys
# Add the base project directory to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "nova-tray")))

import io

from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from setproctitle import setproctitle

from tray.tray_mic import generate_audio_stream, NoiseTorchCommandMic, NoiseTorchHeadsetMic, stop_noisetorch, shutdown, mic_server_process, rename_noisetorch_sources
from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Servers-Routes")

setproctitle("nova_mic_server")

os.environ["DISPLAY"] = ":0"

# Audio parameters
chunk_size = 1024

# FastAPI setup
app = FastAPI()

#MicRouter = APIRouter()

# Streaming route
@app.get("/stream_audio")
async def stream_audio():
    logger.info("🔊 Streaming audio..")
    return StreamingResponse(generate_audio_stream(), media_type='audio/raw')

# Additional stream for commands mic
@app.get("/command_audio_stream")
async def command_audio_stream():
    logger.info("🔊 Streaming command audio..")

    async def generate_command_audio_stream():
        logger.info("🎙️ Starting command audio capture via parec (NoiseTorch mic)...")
        try:
            selected_source = "NoiseTorch Microphone for CA0132 Sound Core3D [Sound Blaster Recon3D / Z-Series / Sound BlasterX AE-5 Plus] (SB1570 SB Audigy Fx)"

            parec_proc = subprocess.Popen(
                [
                    "parec",
                    "-d", selected_source,
                    "--rate=16000",
                    "--channels=1",
                    "--format=s16le"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=chunk_size
            )

            while True:
                chunk = parec_proc.stdout.read(chunk_size)
                if not chunk:
                    logger.warning("🔇 No more audio from parec (command) — stopping stream.")
                    break
                yield chunk

        except Exception as e:
            logger.error(f"❌ Error in generate_command_audio_stream: {e}")

        finally:
            try:
                if parec_proc:
                    parec_proc.terminate()
                    parec_proc.wait(timeout=2)
                    logger.info("✅ parec subprocess (command) terminated.")
            except Exception as e:
                logger.error(f"⚠️ Failed to terminate parec subprocess (command) cleanly: {e}")

    return StreamingResponse(generate_command_audio_stream(), media_type='audio/raw')


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    NoiseTorchCommandMic()

    NoiseTorchHeadsetMic()

    rename_noisetorch_sources()

    logger.info("Audio server running @ http://localhost:57000/stream_audio")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=57000)
