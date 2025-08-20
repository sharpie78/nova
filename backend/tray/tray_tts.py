# tray/tray_tts.py
# -*- coding: utf-8 -*-
"""Non-blocking TTS server toggle used by the tray.
- Start/stop is run on a background thread so the Qt UI never hangs.
- Minimal changes; same public functions: start_tts_server, stop_tts_server, toggle_tts_server, monitor_tts_server, tts_create.
"""
from __future__ import annotations

import os
import sys
import subprocess
import threading
import time
import wave
from typing import Optional

# Ensure project root on path
sys.path.append(os.path.abspath(os.path.expanduser('~/nova/backend')))

from piper import PiperVoice
from utils.logger import logger, setup_logger



setup_logger()
logger = logger.bind(name="tray")

# -----------------------------
# Globals
# -----------------------------

tts_server_process: Optional[subprocess.Popen] = None
monitor_tts_server_thread: Optional[threading.Thread] = None
_MONITOR_INTERVAL = 1.0


# -----------------------------
# Helpers
# -----------------------------

def _run_bg(func, *args, **kwargs) -> None:
    """Run a callable in a daemon thread (avoid blocking the Qt UI)."""
    threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()


# -----------------------------
# Lifecycle
# -----------------------------

def start_tts_server():
    """Start your FastAPI TTS server (servers/tts_server.py) without blocking the UI."""
    global tts_server_process
    if tts_server_process is not None and tts_server_process.poll() is None:
        return  # already running

    try:
        script = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "servers", "tts_server.py"
        )
        python_bin = sys.executable

        tts_server_process = subprocess.Popen(
            [python_bin, script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        logger.info(f"TTS server (FastAPI) started: {python_bin} {script}")
    except Exception as e:
        logger.error(f"Error starting TTS server: {e}")
        tts_server_process = None



def _stop_tts_impl(tts_server_action, icons) -> None:
    """Internal: blocking stop, intended to run on a background thread."""
    global tts_server_process
    if not tts_server_process:
        return
    try:
        tts_server_process.terminate()
        try:
            tts_server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            tts_server_process.kill()
            tts_server_process.wait(timeout=3)
            logger.warning("TTS server force-killed after timeout.")
    except Exception as e:
        logger.error(f"Error stopping TTS server: {e}")
    finally:
        tts_server_process = None
        # Update label back on the GUI thread (Qt is generally tolerant of setText from other threads on QAction,
        # but if you see warnings we can route this via a signal later.)
        if tts_server_action:
            try:
                tts_server_action.setText(f"{icons['audio']} Start TTS Server")
            except Exception:
                pass


def stop_tts_server(tts_server_action, icons) -> None:
    """Public stop; schedules the blocking stop on a background thread."""
    _run_bg(_stop_tts_impl, tts_server_action, icons)


def toggle_tts_server(tts_server_action, icons):
    """Run start/stop off the GUI thread to guarantee no freeze."""
    if tts_server_action.text() == f"{icons['audio']} Start TTS Server":
        threading.Thread(target=start_tts_server, daemon=True).start()
        tts_server_action.setText(f"{icons['quit']} Stop TTS Server")
    else:
        threading.Thread(target=stop_tts_server, args=(tts_server_action, icons), daemon=True).start()
        tts_server_action.setText(f"{icons['audio']} Start TTS Server")


# -----------------------------
# Optional monitor (safe, throttled)
# -----------------------------

def monitor_tts_server(tts_server_action, icons) -> None:
    global monitor_tts_server_thread
    if monitor_tts_server_thread and monitor_tts_server_thread.is_alive():
        return

    def _loop():
        while True:
            running = tts_server_process is not None and tts_server_process.poll() is None
            try:
                if running:
                    tts_server_action.setText(f"{icons['quit']} Stop TTS Server")
                else:
                    tts_server_action.setText(f"{icons['audio']} Start TTS Server")
            except Exception:
                pass
            time.sleep(_MONITOR_INTERVAL)

    monitor_tts_server_thread = threading.Thread(target=_loop, name="TTSMonitor", daemon=True)
    monitor_tts_server_thread.start()


# -----------------------------
# Direct WAV synthesis (unchanged)
# -----------------------------

def tts_create(text: str) -> None:
    try:
        logger.info(f"Starting TTS generation for text: {text}")
        voice = PiperVoice.load(os.path.expanduser('~/nova/backend/audio/voices/alba/en_GB-alba-medium.onnx'))
        os.makedirs(os.path.expanduser('~/nova/backend/audio/tts'), exist_ok=True)
        with wave.open(os.path.expanduser('~/nova/backend/audio/tts/piper-out.wav'), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        logger.info("TTS generation completed successfully.")
    except Exception as e:
        logger.error(f"Error during TTS generation: {e}")
        raise
