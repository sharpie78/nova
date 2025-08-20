import requests
import subprocess
import os
import sys
import time

from threading import Thread
from PyQt6.QtGui import QAction
from setproctitle import setproctitle

from utils.logger import logger, setup_logger

# Set up the logger
setup_logger()  # Initialize logger with the desired configuration

# Bind the logger to the "audio" context
logger = logger.bind(name="Tray")

# Track the process globally
mic_server_process = None
monitor_mic_server_thread = None

# Audio parameters
sample_rate = 16000
chunk_size = 1024

def is_mic_server_up():
    try:
        resp = requests.get("http://127.0.0.1:57000/stream_audio", timeout=1)
        return resp.status_code == 200
    except Exception:
        return False

def monitor_mic_server(mic_server_action, icons):
    """Starts a background thread to monitor the mic server process."""
    global monitor_mic_server_thread  # Declare global here
    if monitor_mic_server_thread is None:
        logger.info("Starting mic server monitoring thread.")
        monitor_mic_server_thread = threading.Thread(target=monitor_mic_process, args=(mic_server_action, icons))
        monitor_mic_server_thread.daemon = True
        monitor_mic_server_thread.start()

def monitor_mic_process(mic_server_action, icons):
    """Periodically check the mic server's state."""
    while True:
        if mic_server_process and mic_server_process.poll() is None:
            logger.info("Mic server is running.")
            mic_server_action.setText(f"{icons['quit']} Stop Audio Server")
        else:
            logger.info("Mic server is stopped or not running.")
            mic_server_action.setText(f"{icons['audio']} Start Audio Server")
        time.sleep(2)  # Adjust sleep time if needed

def start_mic_server():
    global mic_server_process
    """Start the mic server using subprocess."""
    if mic_server_process is None:
        try:
            logger.debug("Attempting to start the mic server process.")
            # Start the mic server process
            mic_server_process = subprocess.Popen(
                [os.path.join(os.path.dirname(__file__), '..', '..', 'venv', 'bin', 'python3.10'),
                 os.path.join(os.path.dirname(__file__), '..', 'servers', 'mic_server.py')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            logger.info("Mic server started ✅ ")
        except Exception as e:
            logger.error(f"Error starting mic server: {e}")
            mic_server_process = None

def stop_mic_server(mic_server_action, icons):
    global mic_server_process
    """Stop the mic server if running."""
    if mic_server_process:
        try:
            logger.debug("Attempting to stop the mic server process.")
            mic_server_process.terminate()  # Gracefully stop the server
            mic_server_process.wait(timeout=5)  # Wait for it to stop
            logger.info("Mic server stopped ✅ ")
            if mic_server_action and icons:
                mic_server_action.setText(f"{icons['audio']} Start Mic Server")  # Update tray action text

        except subprocess.TimeoutExpired:
            logger.debug("Mic server didn't stop in time, force killing.")
            mic_server_process.kill()  # Force kill if timeout occurs
            mic_server_process.wait()  # Ensure it terminates
            logger.debug("Mic server killed successfully.")
            if mic_server_action and icons:
                mic_server_action.setText(f"{icons['audio']} Start Mic Server")  # Update tray action text

        except Exception as e:
            logger.error(f"Error stopping mic server: {e}")

        finally:
            mic_server_process = None  # Clear the process reference
    else:
        logger.debug("Mic server is not running.")

def toggle_mic_server(mic_server_action, icons):
    """Toggle between 'Start Audio Server' and 'Stop Audio Server'."""
    if mic_server_action.text() == f"{icons['audio']} Start Audio Server":
        logger.debug("Starting the mic server...")
        start_mic_server()
        mic_server_action.setText(f"{icons['quit']} Stop Audio Server")
    else:
        logger.debug("Stopping the mic server...")
        stop_mic_server(mic_server_action, icons)
        mic_server_action.setText(f"{icons['audio']} Start Audio Server")


# Clean up old TTS flag on server start
if os.path.exists("/tmp/tts_playing.flag"):
    os.remove("/tmp/tts_playing.flag")
    logger.debug("Cleaned up stale /tmp/tts_playing.flag on audio server start.")


def NoiseTorchHeadsetMic():
    mic_device = "alsa_input.pci-0000_10_00.4.analog-stereo.5"  # Headset mic
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


def rename_noisetorch_sources():
    try:
        output = subprocess.check_output(["pactl", "list", "short", "sources"], text=True)

        count = 0
        for line in output.splitlines():
            if "NoiseTorch Microphone" in line:
                source_name = line.split()[1]
                label = "Sound Blaster (NoiseTorch)" if count == 0 else "Headset Mic (NoiseTorch)"
                subprocess.run(["pactl", "set-source-description", source_name, label])
                print(f"Renamed {source_name} → {label}")
                count += 1

    except Exception as e:
        print(f"Error: {e}")


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


# Graceful shutdown
def shutdown(signum, frame):
    logger.info("🚩 Shutting down the Audio server...")
    stop_noisetorch()
    sys.exit(0)
