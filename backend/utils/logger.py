from loguru import logger as base_logger
import sys
import os
import time

logger = base_logger
logger.remove()  # Force removal of default sink to prevent fallback logging


LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Directly apply os.path to each log file path
UI_LOG_PATH = os.path.join(LOG_DIR, "UI.log")
OLLAMA_LOG_PATH = os.path.join(LOG_DIR, "ollama.log")
UTILS_LOG_PATH = os.path.join(LOG_DIR, "utils.log")
TRAY_LOG_PATH = os.path.join(LOG_DIR, "tray.log")
SERVERS_ROUTES_LOG_PATH = os.path.join(LOG_DIR, "servers-routes.log")

def setup_logger(level="TRACE"):
    """
    Set up the logger with a given level for terminal and file output.

    Supported levels: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"
    If level is "OFF", no logging will occur.
    """
    logger.remove()  # Clear default handlers

    if level.upper() == "OFF":
        logger.add(lambda _: None)  # Disable all logging
        return logger

    # Terminal output
    logger.add(sys.stdout, level=level, colorize=True,
               enqueue=True, backtrace=True, diagnose=True,
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")

    # WebUiServer-specific log file
    logger.add(SERVERS_ROUTES_LOG_PATH, level=level, rotation="10 KB", retention="1 days",
               enqueue=True, backtrace=True, diagnose=True,
               filter=lambda record: record["extra"].get("name") == "Servers-Routes",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    # NovaTray-specific log file
    logger.add(TRAY_LOG_PATH, level=level, rotation="10 KB", retention="1 days",
               enqueue=True, backtrace=True, diagnose=True,
               filter=lambda record: record["extra"].get("name") == "Tray",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    # webUI-specific log file
    logger.add(UI_LOG_PATH, level=level, rotation="10 KB", retention="1 days",
               enqueue=True, backtrace=True, diagnose=True,
               filter=lambda record: record["extra"].get("name") == "UI",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    # Ollama-specific log file
    logger.add(OLLAMA_LOG_PATH, level=level, rotation="10 KB", retention="1 days",
               enqueue=True, backtrace=True, diagnose=True,
               filter=lambda record: record["extra"].get("name") == "Ollama",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")

    # Ollama-specific log file
    logger.add(UTILS_LOG_PATH, level=level, rotation="10 KB", retention="1 days",
               enqueue=True, backtrace=True, diagnose=True,
               filter=lambda record: record["extra"].get("name") == "Utils",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")


    logger.debug("FILE LOGGER ACTIVE")

    try:
        import getpass
        import pwd
        user = getpass.getuser()
        uid = pwd.getpwnam(user).pw_uid
        gid = pwd.getpwnam(user).pw_gid
        os.chown(UI_LOG_PATH, uid, gid)
        os.chown(OLLAMA_LOG_PATH, uid, gid)
        os.chown(UTILS_LOG_PATH, uid, gid)
        os.chown(TRAY_LOG_PATH, uid, gid)
        os.chown(SERVERS_ROUTES_LOG_PATH, uid, gid)
    except Exception as e:
        logger.warning(f"Could not set log file ownership: {e}")
        pass

    return logger
