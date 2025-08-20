import os
import sys
# Add the base project directory to the Python path for imports
sys.path.append(os.path.abspath(os.path.expanduser('~/nova/nova-tray')))

from fastapi import FastAPI
from pydantic import BaseModel
from setproctitle import setproctitle
from utils.logger import logger, setup_logger
from tray.tray_tts import tts_create
import uvicorn

setproctitle("nova_tts_server")

logger = logger.bind(name="audio")
setup_logger()

app = FastAPI()

class TTSRequest(BaseModel):
    text: str

@app.post("/tts")
async def tts_speak(req: TTSRequest):
    logger.info(f"/tts POST hit with text: {req.text}")
    try:
        tts_create(req.text)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=57001)
