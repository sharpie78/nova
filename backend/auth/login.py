import jwt
import os
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from tinydb import TinyDB, Query
import bcrypt
import base64
from datetime import datetime, timedelta
from utils.logger import logger, setup_logger
import json  # Import json for handling file writing

setup_logger()
logger = logger.bind(name="UI")

# Secret key for JWT encoding and decoding
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Initialize TinyDB (path to users.json)
db = TinyDB(os.path.join(os.path.dirname(__file__), "..", "..", "config", "users.json"))
User = Query()

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
    expiration = timedelta(minutes=1)  # Token expires in 1 minute
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + expiration
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"JWT token created for {username}. Token expiration: {payload['exp']}")
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

# Function to save the username to settings.json
def save_username_to_file(username: str):
    settings_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "settings.json")

    # Prepare the data to be saved
    data = {"username": username}

    # Write the data to the settings.json file
    with open(settings_path, "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Username {username} saved to settings.json")

# Initialize the router for login functionality
login_router = APIRouter()

# Login route to authenticate user and issue JWT token
@login_router.post("/login")
async def login(request: LoginRequest):
    logger.debug(f"Received login request for username: {request.username}")

    # Search for the user in the database
    user = db.search(User.username == request.username)

    if user:
        stored_hash = user[0]['password']
        if verify_password(stored_hash, request.password):
            # Create JWT token for authenticated user
            token = create_jwt_token(request.username)
            logger.info(f"User {request.username} successfully authenticated.")

            # Save the username to settings.json
            save_username_to_file(request.username)

            return {"token": token}  # Just return the token now, username is stored server-side
        else:
            logger.warning(f"Invalid password attempt for user {request.username}")
            raise HTTPException(status_code=401, detail="Invalid password")
    else:
        logger.warning(f"User {request.username} not found.")
        raise HTTPException(status_code=404, detail="User not found")

# Protect a route that requires login
@login_router.get("/protected")
async def protected_route(payload: dict = Depends(verify_jwt_token)):
    logger.debug(f"Accessing protected route by user {payload['sub']}")
    # If the token is valid, this route will return user data or success message
    return {"message": "This is a protected route", "user": payload['sub']}  # 'sub' is typically the username


# Create the SettingsRoot route to serve the settings.json content as JSON
@login_router.get("/settings")
async def SettingsRoot():
    settings_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "settings.json")

    # Read the settings.json file
    try:
        with open(settings_path, "r") as f:
            settings_data = json.load(f)  # Load the JSON data from the file

        # Log the settings data to confirm it's correct
        print("Settings data:", settings_data)

        # Return the settings data as a JSON response
        return JSONResponse(content=settings_data)
    except Exception as e:
        print("Error reading settings.json:", e)
        return JSONResponse(status_code=500, content={"error": "Error reading settings.json"})
