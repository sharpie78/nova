import jwt
import os
import bcrypt
import base64
import secrets
import json

from pydantic import BaseModel
from tinydb import TinyDB
from datetime import datetime, timedelta
from fastapi import Request, HTTPException

from utils.logger import logger, setup_logger


setup_logger()
logger = logger.bind(name="UI")

# Secret key for JWT encoding and decoding
# Load the secret key from file
SECRET_KEY_PATH = os.path.expanduser("~/.local/share/nova-UI/nova.key")
try:
    with open(SECRET_KEY_PATH, "r") as f:
        SECRET_KEY = f.read().strip()
except FileNotFoundError:
    raise RuntimeError("Secret key not found. Please run setup_tray.sh first.")

ALGORITHM = "HS256"

# Initialize TinyDB (path to users.json)
db = TinyDB(os.path.join(os.path.dirname(__file__), "..", "..", "config", "users.json"))


# Pydantic model for login request
class LoginRequest(BaseModel):
    username: str
    password: str

# Function to verify password (check against the hashed password)
def verify_password(stored_hash, password):
    stored_hash_bytes = base64.b64decode(stored_hash)  # Decode from base64
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes)

# Function to create a JWT token
def create_jwt_token(username: str):
    base = os.path.dirname(__file__)
    user_path = os.path.join(base, "..", "..", "config", f"{username}.settings.json")
    default_path = os.path.join(base, "..", "..", "config", "default.settings.json")
    path = user_path if os.path.exists(user_path) else default_path

    try:
        with open(path, "r") as f:
            settings = json.load(f)
        label = (
            settings.get("interface", {})
                    .get("Session timeout", {})
                    .get("default", "30 minutes")
        ).strip().lower()
        minutes = 0 if label == "never" else int(label.split()[0])
    except Exception as e:
        logger.warning(f"JWT timeout fallback (reason: {e})")
        minutes = 30

    payload = {"sub": username}
    if minutes > 0:
        payload["exp"] = datetime.utcnow() + timedelta(minutes=minutes)

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"JWT for {username} expires in {'never' if minutes==0 else f'{minutes}m'}")
    return token



# Function to verify JWT token (for protected routes)
def verify_jwt_token(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        logger.warning("Authorization token missing")
        raise HTTPException(status_code=401, detail="Authorization token missing")

    try:
        token = token.split(" ")[1]  # Extract the token (Bearer <token>)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(f"JWT token verified for {payload['sub']}")
        return payload  # Return the decoded payload (e.g., username)
    except jwt.PyJWTError:
        logger.error("Invalid token or token expired")
        raise HTTPException(status_code=401, detail="Invalid token or token expired")

def create_user_settings(username: str):
    default_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "default.settings.json")
    user_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", f"{username}.settings.json")

    try:
        with open(default_path, "r") as f:
            settings = json.load(f)

        # Save as full settings (not just changed values)
        with open(user_path, "w") as f:
            json.dump(settings, f, indent=4)

        logger.info(f"User settings created for {username}")
    except Exception as e:
        logger.error(f"Failed to create settings for {username}: {e}")
