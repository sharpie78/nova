import os
import json

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Servers-Routes")

SettingsRouter = APIRouter()

@SettingsRouter.post("/settings/{username}")
async def save_user_settings(username: str, request: Request):
    settings_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", f"{username}.settings.json")
    try:
        body = await request.json()
        with open(settings_path, "w") as f:
            json.dump(body, f, indent=4)
        logger.info(f"Settings updated for user: {username}")
        return {"message": "Settings saved successfully"}
    except Exception as e:
        logger.error(f"Error saving settings for {username}: {e}")
        return JSONResponse(status_code=500, content={"error": "Error saving user-settings.json"})


@SettingsRouter.get("/settings/{username}")
async def get_user_settings(username: str):
    settings_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", f"{username}.settings.json")
    default_settings_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "default.settings.json")

    try:
        # Try to load the user-specific settings
        if os.path.exists(settings_path):
            with open(settings_path, "r") as f:
                settings_data = json.load(f)
        else:
            # If user-specific settings don't exist, load the default settings
            with open(default_settings_path, "r") as f:
                settings_data = json.load(f)

        logger.debug(f"Settings data for {username}: {settings_data}")
        return JSONResponse(content=settings_data)

    except Exception as e:
        logger.error(f"Error reading settings for {username}: {e}")
        return JSONResponse(status_code=500, content={"error": "Error reading user-settings.json"})
