import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from tinydb import Query
from auth.login import db
from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Servers-Routes")

AdminRouter = APIRouter()
User = Query()

@AdminRouter.get("/users")
async def get_users():
    try:
        users_data = db.all()
        return JSONResponse(content=users_data)
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@AdminRouter.post("/users")
async def update_user(request: Request):
    try:
        body = await request.json()
        username_to_update = body.get("username")
        new_role = body.get("role")

        if username_to_update == "admin":
            raise HTTPException(status_code=400, detail="Cannot modify the admin user")

        user_data = db.search(User.username == username_to_update)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        user = user_data[0]
        if new_role:
            user["role"] = new_role
            db.update(user, User.username == username_to_update)

        return {"message": f"User {username_to_update} updated successfully", "user": user}

    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")

