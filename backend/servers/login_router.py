import os
import json
import base64
import secrets
import bcrypt

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from tinydb import Query, where

from auth.login import db, verify_password, create_jwt_token, create_user_settings, LoginRequest

from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Servers-Routes")

# Initialize the router for login functionality
LoginRouter = APIRouter()

User = Query()

@LoginRouter.get("/user-exists/{username}")
async def user_exists(username: str):
    exists = db.contains(User.username == username)
    return {"exists": exists}



# Registration route to create a new user
@LoginRouter.post("/register")
async def register(request: LoginRequest):
    logger.debug(f"Received registration request for username: {request.username}")

    # Check if username already exists
    if db.search(User.username == request.username):
        logger.warning(f"Username {request.username} already exists.")
        raise HTTPException(status_code=400, detail="Username already exists")

    # Validate password length
    if len(request.password) < 10:
        logger.warning("Password too short")
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters")

    # Hash password with bcrypt (cost 12)
    hashed = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    hashed_b64 = base64.b64encode(hashed).decode('utf-8')

    # Generate a 14-character alphanumeric user_id
    user_id = ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(14))

    # Save the user to the database
    db.insert({
        "user_id": user_id,
        "username": request.username,
        "password": hashed_b64,
        "role": "user"
    })

    # Create settings file from default
    create_user_settings(request.username)

    logger.info(f"New user {request.username} registered with ID {user_id}")
    return {"message": "User registered successfully"}
    # Save the username to user-settings.json
    #create_user_settings(request.username)



# Login route to authenticate user and issue JWT token
@LoginRouter.post("/login")
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

            return {"token": token}  # Just return the token now, username is stored server-side
        else:
            logger.warning(f"Invalid password attempt for user {request.username}")
            raise HTTPException(status_code=401, detail="Invalid password")
    else:
        logger.warning(f"User {request.username} not found.")
        raise HTTPException(status_code=404, detail="User not found")



@LoginRouter.delete("/users/{username}")
async def delete_user(username: str):
    if username == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete admin user")

    deleted_count = db.remove(where("username") == username)
    if not deleted_count:
        logger.warning(f"Attempted to delete nonexistent user: {username}")
        raise HTTPException(status_code=404, detail="User not found")

    settings_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", f"{username}.settings.json")

    if os.path.exists(settings_path):
        os.remove(settings_path)
        logger.info(f"Deleted settings file for user: {username}")
    else:
        logger.warning(f"Settings file for user {username} not found.")


    logger.info(f"User deleted: {username}")
    return {"message": f"User '{username}' deleted"}




