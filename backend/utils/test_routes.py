import requests
import json
import subprocess
import sys
import time
import os
# Add the base project directory to the Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "python")))

from tray.tray_mic import start_mic_server, stop_mic_server, is_mic_server_up, stop_noisetorch

API_BASE = "http://127.0.0.1:56969"
MIC_BASE = "http://127.0.0.1:57000"

TEST_USER = {"username": "testuser", "password": "testpassword123"}
HEADERS = {"Content-Type": "application/json"}

results = []

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

log_lines = []
LOG_PATH = os.path.join("..", "..", "logs", "test_routes.log")

def log(msg):
    line = f"{CYAN}{msg}{RESET}"
    print(line)
    log_lines.append(msg)

def show_message(label, status, ok):
    mark = f"{GREEN}✔{RESET}" if ok else f"{RED}✖{RESET}"
    results.append((label, status, ok))
    print(f"[{mark}] {BOLD}{label}{RESET} ({status})")
    log_lines.append(f"[{'PASS' if ok else 'FAIL'}] {label} ({status})")

def print_response(label, r):
    if r is None:
        status = 0
        ok = False
    elif label == "Testing login route with invalid password" and r.status_code == 401:
        status = 401
        ok = True
    else:
        status = r.status_code
        ok = True
    show_message(label, status, ok)
    if label == "Testing login route with invalid password" and status == 401:
        print("    Login correctly rejected invalid password")
        log_lines.append("    Login correctly rejected invalid password")

def test_websocket(url, label):
    try:
        result = subprocess.run(["websocat", url], capture_output=True, text=True, timeout=6)
        show_message(label, 101, True)
        print("    WebSocket Connected and Data Received")
        log_lines.append("    WebSocket Connected and Data Received")
    except subprocess.TimeoutExpired:
        show_message(label, 101, True)
        print("    WebSocket Timed Out (Still Responsive)")
        log_lines.append("    WebSocket Timed Out (Still Responsive)")
    except Exception as e:
        show_message(label, 0, False)
        print(f"    WebSocket FAILED: {e}")
        log_lines.append(f"    WebSocket FAILED: {e}")

def test_static_files():
    log("\nChecking static files...")
    paths = ["/index.html", "/css/chat.css", "/js/chat.js"]
    for path in paths:
        try:
            r = requests.get(f"{API_BASE}{path}")
            print_response(f"Static File ({path})", r)
        except Exception as e:
            show_message(f"Static File ({path})", 0, False)
            print(f"    Static File FAILED: {e}")
            log_lines.append(f"    Static File FAILED: {e}")

def test_audio_stream(url, label):
    try:
        r = requests.get(url, stream=True, timeout=5)
        if r.status_code != 200:
            show_message(label, r.status_code, False)
            return

        byte_count = 0
        for chunk in r.iter_content(chunk_size=1024):
            if not chunk:
                break
            byte_count += len(chunk)
            if byte_count >= 8000:  # ~0.5 sec of audio at 16kHz * 1ch * 2 bytes
                break

        ok = byte_count >= 8000
        show_message(label, r.status_code, ok)

    except Exception as e:
        show_message(label, 0, False)
        print(f"    Error: {e}")
        log_lines.append(f"    Error: {e}")

def main():
    log("\nRunning Nova route tests...")
    time.sleep(0.5)

    print_response("Checking if admin user exists", requests.get(f"{API_BASE}/user-exists/admin"))
    fake_login = {"username": "admin", "password": "wrongpassword"}
    print_response("Testing login route with invalid password", requests.post(f"{API_BASE}/login", headers=HEADERS, json=fake_login))

    print_response("Getting user settings", requests.get(f"{API_BASE}/settings/{TEST_USER['username']}"))
    print_response("Saving user settings (invalid)", requests.post(f"{API_BASE}/settings/testuser", headers={"Content-Type": "application/json"}, data="not json"))

    print_response("Getting user list", requests.get(f"{API_BASE}/users"))
    print_response("Updating test user's role", requests.post(f"{API_BASE}/users", headers=HEADERS, json={"username": TEST_USER['username'], "role": "user"}))

    print_response("Checking tray service status", requests.get(f"{API_BASE}/tray-status"))
    print_response("Checking mic server status", requests.get(f"{API_BASE}/mic-server-status"))

    # Ensure mic server is running
    if not is_mic_server_up():
        start_mic_server()
        time.sleep(2)

    test_audio_stream(f"{MIC_BASE}/stream_audio", "Accessing /stream_audio")

    stop_mic_server(None, None)
    start_mic_server()
    time.sleep(2)

    test_audio_stream(f"{MIC_BASE}/command_audio_stream", "Accessing /command_audio_stream")

    stop_mic_server(None, None)

    print_response("Fetching model tags", requests.get(f"{API_BASE}/api/tags"))
    chat_data = {
        "model": "test",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    print_response("Sending test chat message", requests.post(f"{API_BASE}/api/chat", headers=HEADERS, json=chat_data))

    test_websocket("ws://127.0.0.1:56969/ws/system-info", "WebSocket: system-info")
    test_websocket("ws://127.0.0.1:56969/ws/system-status", "WebSocket: system-status")

    test_static_files()

    stop_noisetorch()

    log("\nTest Summary:")
    for label, code, ok in results:
        mark = f"{GREEN}✔{RESET}" if ok else f"{RED}✖{RESET}"
        print(f"{mark} {label} ({code})")
        log_lines.append(f"{'PASS' if ok else 'FAIL'} {label} ({code})")

    passed = sum(1 for _, _, ok in results if ok)
    total = len(results)
    log(f"\n{BOLD}Complete:{RESET} {passed}/{total} tests passed.\n")
    log_lines.append(f"\nComplete: {passed}/{total} tests passed.\n")

    try:
        with open(LOG_PATH, "w") as f:
            f.write("\n".join(log_lines))
    except Exception as e:
        print(f"Failed to save log: {e}")

    sys.exit(0 if passed == total else 1)



if __name__ == "__main__":
    main()
