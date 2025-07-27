import requests
from websocket import create_connection, WebSocketException
from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Tray")

def is_api_server_up():
    """Checks if the API server and WebSocket are running."""
    try:
        logger.debug("Checking if the API server and WebSocket are running...")

        # Check HTTP server
        resp = requests.get("http://127.0.0.1:56969/tray-status")
        if resp.status_code != 200:
            logger.warning(f"API server returned a non-200 status code: {resp.status_code}")
            return False

        logger.debug("API server responded with status code 200.")

        # Check WebSocket endpoint
        ws = create_connection("ws://127.0.0.1:56969/ws/system-info", timeout=3)
        ws.close()

        logger.debug("WebSocket connection successful.")
        logger.info("API server and WebSocket are up and running.")
        return True
    except requests.exceptions.RequestException as e:
        logger.warning(f"Request error while checking API server - Ignore this when starting tray")
    except WebSocketException as e:
        logger.error(f"WebSocket error while checking WebSocket connection: {e}")

    logger.warning("API server or WebSocket is down. Ignore this when starting tray")
    return False
