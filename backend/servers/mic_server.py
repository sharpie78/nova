from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import sounddevice as sd
import numpy as np
import subprocess
import signal
import os
import sys
# Add the base project directory to the Python path for imports
sys.path.append(os.path.abspath('/mnt/nova/backend'))
import io
from utils.logger import logger, setup_logger
from setproctitle import setproctitle

setproctitle("nova_mic_server")

# Import logger and setup:
setup_logger()
logger = logger.bind(name="Servers-Routes")

os.environ["DISPLAY"] = ":0"

# FastAPI setup
app = FastAPI()

# Audio parameters
sample_rate = 16000
chunk_size = 1024

# Clean up old TTS flag on server start
if os.path.exists("/tmp/tts_playing.flag"):
    os.remove("/tmp/tts_playing.flag")
    logger.info("Cleaned up stale /tmp/tts_playing.flag on audio server start.")


def NoiseTorchHeadsetMic():
    mic_device = "alsa_input.pci-0000_10_00.4.analog-stereo"  # Headset mic
    threshold = 10  # Define threshold for the headset mic here
    try:
        env = os.environ.copy()
        env["DISPLAY"] = env.get("DISPLAY", ":0")
        env["XDG_SESSION_TYPE"] = "x11"

        # Run NoiseTorch with the defined threshold for the headset mic
        result = subprocess.run(
            [os.path.expanduser("~/.local/bin/noisetorch"), "-i", "-s", mic_device, "-t", str(threshold)],  # Changed --threshold to -t
            capture_output=True,
            text=True,
            env=env
        )

        # Log stdout and stderr for debugging
        logger.debug(f"[NoiseTorch STDOUT] {result.stdout}")
        logger.debug(f"[NoiseTorch STDERR] {result.stderr}")

        if result.returncode == 0:
            logger.info(f"✅ NoiseTorch started on Headset Mic: {mic_device} with threshold {threshold}")
        else:
            logger.error(f"❌ NoiseTorch failed to start: {result.stderr.strip()}")

    except Exception as e:
        logger.error(f"⚠️ Error launching NoiseTorch on Headset Mic: {e}")


def NoiseTorchCommandMic():
    mic_device = "alsa_input.pci-0000_06_00.0.analog-stereo"  # Command mic
    threshold = 1  # Define threshold for the command mic here
    try:
        env = os.environ.copy()
        env["DISPLAY"] = env.get("DISPLAY", ":0")
        env["XDG_SESSION_TYPE"] = "x11"

        # Run NoiseTorch with the defined threshold for the command mic
        result = subprocess.run(
            [os.path.expanduser("~/.local/bin/noisetorch"), "-i", "-s", mic_device, "-t", str(threshold)],  # Changed --threshold to -t
            capture_output=True,
            text=True,
            env=env
        )

        # Log stdout and stderr for debugging
        logger.debug(f"[NoiseTorch STDOUT] {result.stdout}")
        logger.debug(f"[NoiseTorch STDERR] {result.stderr}")

        if result.returncode == 0:
            logger.info(f"✅ NoiseTorch started on Command Mic: {mic_device} with threshold {threshold}")
        else:
            logger.error(f"❌ NoiseTorch failed to start: {result.stderr.strip()}")

    except Exception as e:
        logger.error(f"⚠️ Error launching NoiseTorch on Command Mic: {e}")




def stop_noisetorch():
    try:
        # Stop NoiseTorch for Headset Mic
        result_headset = subprocess.run([os.path.expanduser("~/.local/bin/noisetorch"), "-u"], capture_output=True, text=True)

        # Stop NoiseTorch for Command Mic
        result_command = subprocess.run([os.path.expanduser("~/.local/bin/noisetorch"), "-u"], capture_output=True, text=True)

        if result_headset.returncode == 0 and result_command.returncode == 0:
            logger.info("🛑 NoiseTorch stopped on both Headset Mic and Command Mic")
        else:
            logger.warning("⚠️ NoiseTorch uninstall failed for one or both microphones")
            if result_headset.returncode != 0:
                logger.warning(f"⚠️ Failed to stop NoiseTorch on Headset Mic: {result_headset.stderr.strip()}")
            if result_command.returncode != 0:
                logger.warning(f"⚠️ Failed to stop NoiseTorch on Command Mic: {result_command.stderr.strip()}")
    except Exception as e:
        logger.error(f"⚠️ Error stopping NoiseTorch: {e}")


# stream the microphone input
def generate_audio_stream():
    logger.info("🎧 Starting audio capture via parec (echocancel_source if available)...")

    try:
        # Determine source to use
        selected_source = "echocancel_source"

        # Check if echocancel_source exists
        result = subprocess.run(['pactl', 'list', 'short', 'sources'], capture_output=True, text=True)
        if 'echocancel_source' not in result.stdout:
            logger.warning("⚠️ echocancel_source not found — falling back to default source.")
            # Fallback to current default source
            default_source_result = subprocess.run(['pactl', 'get-default-source'], capture_output=True, text=True)
            selected_source = default_source_result.stdout.strip()

        logger.info(f"🎤 Using source: {selected_source}")

        # Start parec
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
            chunk = parec_proc.stdout.read(chunk_size)  # Read exactly one chunk
            if not chunk:
                logger.warning("🔇 No more audio from parec — stopping stream.")
                break
            yield chunk

    except Exception as e:
        logger.error(f"❌ Error in generate_audio_stream with parec: {e}")

    finally:
        try:
            if parec_proc:
                parec_proc.terminate()
                parec_proc.wait(timeout=2)
                logger.info("✅ parec subprocess terminated.")
        except Exception as e:
            logger.error(f"⚠️ Failed to terminate parec subprocess cleanly: {e}")

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

# Graceful shutdown
def shutdown(signum, frame):
    logger.info("🚩 Shutting down the Audio server...")
    stop_noisetorch()
    sys.exit(0)

# start the server
if __name__ == '__main__':
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    NoiseTorchCommandMic()
    NoiseTorchHeadsetMic()

    logger.info("Audio server running @ http://localhost:56969/stream_audio")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=57000)
