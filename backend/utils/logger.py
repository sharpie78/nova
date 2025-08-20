from loguru import logger as base_logger
import sys
import os
import time
from pathlib import Path
import json

# Global logger object
logger = base_logger
logger.remove()  # remove default sink

# Where logs are written
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

UI_LOG_PATH = os.path.join(LOG_DIR, "UI.log")
OLLAMA_LOG_PATH = os.path.join(LOG_DIR, "ollama.log")
UTILS_LOG_PATH = os.path.join(LOG_DIR, "utils.log")
TRAY_LOG_PATH = os.path.join(LOG_DIR, "tray.log")
SERVERS_ROUTES_LOG_PATH = os.path.join(LOG_DIR, "servers-routes.log")

# Where settings are read from
CONFIG_DIR = os.environ.get("NOVA_CONFIG_DIR", str(Path.home() / "nova" / "config"))

# remember the last applied level to avoid redundant re-inits
_configured_level = None


def _current_username():
    # Prefer NOVA_USER (launcher can set it), else OS user, else "default"
    return (os.environ.get("NOVA_USER")
            or os.environ.get("USER")
            or os.environ.get("USERNAME")
            or "default")


def _settings_path() -> Path:
    cfg = Path(CONFIG_DIR)
    user_file = cfg / f"{_current_username()}.settings.json"
    return user_file if user_file.exists() else (cfg / "default.settings.json")


def _read_log_level_from_settings() -> str:
    """Read the effective log level from settings JSON."""
    try:
        data = json.loads(_settings_path().read_text())

        # Your current shape: logs["default log level"] -> object with "default" (or maybe "value"/"current")
        val = data.get("logs", {}).get("default log level")
        if isinstance(val, dict):
            lvl = val.get("value") or val.get("current") or val.get("default")
        elif isinstance(val, str):
            lvl = val
        else:
            lvl = None

        # Future-proof: also accept logging.level
        if not lvl:
            lvl = data.get("logging", {}).get("level")

        allowed = {"TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "OFF"}
        lvl = (str(lvl).upper() if lvl else "INFO")
        return lvl if lvl in allowed else "INFO"
    except Exception:
        return "INFO"


def setup_logger(level: str | None = None):
    """
    Configure sinks. If 'level' is None, read it from settings.
    Calling this repeatedly with the same level is a no-op.
    """
    global _configured_level

    if level is None:
        level = _read_log_level_from_settings()

    # Avoid reconfiguring if nothing changed
    if _configured_level == level:
        return logger
    _configured_level = level

    # Visibility: show exactly which file/level we're using
    print(f"[logger] settings={_settings_path()} level={level}")

    logger.remove()

    if level.upper() == "OFF":
        logger.add(lambda _: None)  # Disable all logging
        return logger

    # Terminal output
    logger.add(
        sys.stdout,
        level=level,
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    )

    # File sinks filtered by component name
    logger.add(
        SERVERS_ROUTES_LOG_PATH,
        level=level,
        rotation="10 MB",
        retention="1 days",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        filter=lambda record: record["extra"].get("name") == "Servers-Routes",
        format="{time:DD-MM-YYYY HH:mm:ss} | {level} | {message}",
    )

    logger.add(
        TRAY_LOG_PATH,
        level=level,
        rotation="10 MB",
        retention="1 days",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        filter=lambda record: record["extra"].get("name") == "Tray",
        format="{time:DD-MM-YYYY HH:mm:ss} | {level} | {message}",
    )

    logger.add(
        UI_LOG_PATH,
        level=level,
        rotation="10 MB",
        retention="1 days",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        filter=lambda record: record["extra"].get("name") == "UI",
        format="{time:DD-MM-YYYY HH:mm:ss} | {level} | {message}",
    )

    logger.add(
        OLLAMA_LOG_PATH,
        level=level,
        rotation="10 MB",
        retention="1 days",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        filter=lambda record: record["extra"].get("name") == "Ollama",
        format="{time:DD-MM-YYYY HH:mm:ss} | {level} | {message}",
    )

    logger.add(
        UTILS_LOG_PATH,
        level=level,
        rotation="10 MB",
        retention="1 days",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        filter=lambda record: record["extra"].get("name") == "Utils",
        format="{time:DD-MM-YYYY HH:mm:ss} | {level} | {message}",
    )

    logger.debug("FILE LOGGER ACTIVE")

    # Best-effort fixup of file ownership so you can read logs without sudo
    try:
        import getpass, pwd
        user = getpass.getuser()
        uid = pwd.getpwnam(user).pw_uid
        gid = pwd.getpwnam(user).pw_gid
        for p in (UI_LOG_PATH, OLLAMA_LOG_PATH, UTILS_LOG_PATH, TRAY_LOG_PATH, SERVERS_ROUTES_LOG_PATH):
            os.chown(p, uid, gid)
    except Exception as e:
        logger.warning(f"Could not set log file ownership: {e}")

    return logger


# Auto-configure on import using the value in settings
setup_logger(level=None)
